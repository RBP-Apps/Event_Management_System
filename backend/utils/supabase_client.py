"""
Supabase client + all data-access functions that replace the old
Google Apps Script (`submit_to_sheets`) round-trips.

Every function here mirrors the equivalent function in FINAL_APPS_SCRIPT.js
so behavior (event ID generation, cascading deletes, profile merging, etc.)
stays identical after the migration off Google Sheets.

Note: business card photos still upload to Google Drive via the Apps Script
`extractData`/OCR flow is unaffected — only structured row data has moved
to Postgres. Photo URLs are stored as plain text columns, same as before.
"""
import base64
import re
import uuid
from datetime import datetime, timezone
from supabase import create_client

from backend.core.config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, logger

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

PHOTO_BUCKET = "business-cards"


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def upload_photo(base64_data: str, prefix: str) -> str:
    """
    Uploads a base64-encoded business card photo to Supabase Storage and
    returns its public URL. Replaces the old DriveApp.createFile() flow.
    Returns "" if no image data was given (mirrors the old Apps Script
    behavior of leaving the cell blank for a missing second photo).
    """
    if not base64_data or not base64_data.strip():
        return ""
    try:
        image_bytes = base64.b64decode(base64_data)
        path = f"{prefix}_{uuid.uuid4().hex}.jpg"
        supabase.storage.from_(PHOTO_BUCKET).upload(
            path, image_bytes, file_options={"content-type": "image/jpeg"}
        )
        return supabase.storage.from_(PHOTO_BUCKET).get_public_url(path)
    except Exception as e:
        logger.error(f"Photo upload failed: {e}")
        return f"Error saving image: {e}"


def _ok(data=None, **extra):
    out = {"success": True}
    if data is not None:
        out["data"] = data
    out.update(extra)
    return out


def _fail(message, **extra):
    out = {"success": False, "message": message}
    out.update(extra)
    return out


# ---------------------------------------------------------------------------
# Ai Card (plain, non-event business card scans)
# ---------------------------------------------------------------------------

def save_data(extracted_data: dict, photo1_base64: str, photo2_base64: str):
    photo1_url = upload_photo(photo1_base64, "aicard_front")
    photo2_url = upload_photo(photo2_base64, "aicard_back")
    key_people = extracted_data.get("key_people")
    if isinstance(key_people, list):
        key_people_string = "\n".join(
            f"{p.get('name', '')} ({p.get('role', '')})" +
            (f" - {p.get('contact')}" if p.get("contact") and p.get("contact") != "Not Found" else "")
            for p in key_people
        )
    else:
        parts = []
        if extracted_data.get("founder"):
            parts.append(f"Founder: {extracted_data['founder']}")
        if extracted_data.get("ceo"):
            parts.append(f"CEO: {extracted_data['ceo']}")
        if extracted_data.get("owner"):
            parts.append(f"Owner: {extracted_data['owner']}")
        key_people_string = "\n".join(parts)

    validation_link = extracted_data.get("validation_source") or ""

    row = {
        "timestamp": _now_iso(),
        "photo1": photo1_url or "",
        "photo2": photo2_url or "",
        "company": extracted_data.get("company") or "",
        "industry": extracted_data.get("industry") or "",
        "name": extracted_data.get("name") or "",
        "title": extracted_data.get("title") or "",
        "phone": extracted_data.get("phone") or "",
        "email": extracted_data.get("email") or "",
        "website": extracted_data.get("website") or "",
        "social_media": extracted_data.get("social_media") or "",
        "address": extracted_data.get("address") or "",
        "services": extracted_data.get("services") or "",
        "company_size": extracted_data.get("company_size") or "",
        "founded_year": extracted_data.get("established_year") or extracted_data.get("founded_year") or "",
        "registration_status": extracted_data.get("registration_status") or "",
        "trust_score": extracted_data.get("trust_score") or "",
        "key_people": key_people_string,
        "is_validated": bool(extracted_data.get("is_validated")),
        "validation_link": validation_link,
        "about_company": extracted_data.get("about_the_company") or "",
        "location": extracted_data.get("location") or "",
    }
    supabase.table("ai_cards").insert(row).execute()
    return {"message": "✅ Data saved successfully!"}


# ---------------------------------------------------------------------------
# Event Details
# ---------------------------------------------------------------------------

def save_event_data(event_data: dict):
    resp = (
        supabase.table("event_details")
        .select("event_id")
        .order("id", desc=True)
        .limit(50)
        .execute()
    )
    last_num = 0
    for row in resp.data:
        eid = row.get("event_id") or ""
        if eid.startswith("EVT-"):
            try:
                n = int(eid.replace("EVT-", "").strip())
                last_num = max(last_num, n)
            except ValueError:
                continue
    event_id = f"EVT-{last_num + 1:03d}"

    timestamp = _now_iso()
    members = event_data.get("teamMembers") or []

    rows = []
    if not members:
        rows.append({
            "timestamp": timestamp,
            "event_id": event_id,
            "event_name": event_data.get("eventName") or "",
            "start_date": event_data.get("startDate") or "",
            "end_date": event_data.get("endDate") or "",
            "location": event_data.get("location") or "",
            "description": event_data.get("description") or "",
            "member_name": "", "designation": "", "phone": "",
        })
    else:
        for i, m in enumerate(members):
            if i == 0:
                rows.append({
                    "timestamp": timestamp,
                    "event_id": event_id,
                    "event_name": event_data.get("eventName") or "",
                    "start_date": event_data.get("startDate") or "",
                    "end_date": event_data.get("endDate") or "",
                    "location": event_data.get("location") or "",
                    "description": event_data.get("description") or "",
                    "member_name": m.get("name") or "",
                    "designation": m.get("designation") or "",
                    "phone": m.get("phone") or "",
                })
            else:
                rows.append({
                    "timestamp": None,
                    "event_id": event_id,
                    "event_name": "", "start_date": "", "end_date": "",
                    "location": "", "description": "",
                    "member_name": m.get("name") or "",
                    "designation": m.get("designation") or "",
                    "phone": m.get("phone") or "",
                })

    supabase.table("event_details").insert(rows).execute()
    return _ok(message=f"✅ Event '{event_data.get('eventName')}' saved. ID: {event_id}", eventId=event_id)


def get_event_list():
    resp = (
        supabase.table("event_details")
        .select("event_id, event_name, start_date, end_date, location")
        .execute()
    )
    events = [
        {
            "id": r["event_id"],
            "name": r["event_name"],
            "startDate": r["start_date"],
            "endDate": r["end_date"],
            "location": r.get("location") or "",
        }
        for r in resp.data
        if r.get("event_id") and r.get("event_name")
    ]
    return _ok(events)


def get_event_by_id(event_id: str):
    if not event_id:
        return _fail("No Event ID provided")
    resp = (
        supabase.table("event_details")
        .select("*")
        .eq("event_id", event_id)
        .limit(1)
        .execute()
    )
    if not resp.data:
        return _fail("Event not found")
    return _ok(resp.data[0])


def delete_event(event_id: str):
    if not event_id:
        return _fail("No Event ID provided")

    deleted_counts = {}
    for table in ["event_details", "event_ai_cards", "visitor_details"]:
        existing = supabase.table(table).select("id").eq("event_id", event_id).execute()
        count = len(existing.data)
        if count:
            supabase.table(table).delete().eq("event_id", event_id).execute()
        deleted_counts[table] = count

    total = sum(deleted_counts.values())
    if total == 0:
        return _fail(f"Event not found: {event_id}")

    return _ok(message=f"✅ Event '{event_id}' and all related data deleted.", deletedCounts=deleted_counts)


# ---------------------------------------------------------------------------
# Event Ai Card (per-event scanned business cards)
# ---------------------------------------------------------------------------

def save_event_card_data(extracted_data: dict, photo1_base64: str, photo2_base64: str, event_info: dict):
    photo1_url = upload_photo(photo1_base64, "eventcard_front")
    photo2_url = upload_photo(photo2_base64, "eventcard_back")
    d = extracted_data or {}
    row = {
        "timestamp": _now_iso(),
        "event_id": event_info.get("id") or "N/A",
        "event_name": event_info.get("name") or "N/A",
        "event_start_date": event_info.get("startDate") or "N/A",
        "event_end_date": event_info.get("endDate") or "N/A",
        "card_photo1": photo1_url or "",
        "card_photo2": photo2_url or "",
        "company_name": d.get("company_name") or d.get("company") or "",
        "industry": d.get("industry") or "",
        "person_name": d.get("person_name") or d.get("name") or "",
        "designation": d.get("designation") or d.get("title") or "",
        "phone": d.get("phone") or "",
        "email": d.get("email") or "",
        "website": d.get("website") or "",
        "social_media": d.get("social_media") or "",
        "address": d.get("address") or "",
        "services": d.get("services") or "",
        "company_size": d.get("company_size") or "",
        "founded_year": d.get("founded_year") or d.get("established_year") or "",
        "registration_status": d.get("registration_status") or "",
        "trust_score": d.get("trust_score") or "",
        "people_founders": d.get("people") or d.get("key_people") or "",
        "is_validated": str(d.get("is_validated") or ""),
        "source_link": d.get("source_link") or d.get("validation_source") or "",
        "about_company": d.get("about_company") or d.get("about_the_company") or "",
        "location": d.get("location") or "",
    }
    supabase.table("event_ai_cards").insert(row).execute()
    return _ok(message="Card saved to Event Hub!")


def delete_event_card(event_id: str, timestamp: str):
    if not event_id or not timestamp:
        return _fail("eventId and timestamp are required")

    resp = (
        supabase.table("event_ai_cards")
        .select("id, timestamp")
        .eq("event_id", event_id)
        .execute()
    )
    target = _parse_iso(timestamp)
    for row in resp.data:
        row_ts = _parse_iso(row.get("timestamp"))
        if row_ts is not None and target is not None and row_ts == target:
            supabase.table("event_ai_cards").delete().eq("id", row["id"]).execute()
            return _ok(message="✅ Card deleted successfully.")

    return _fail("Card not found")


def _parse_iso(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def get_event_specific_data(event_id: str, event_name: str):
    if not event_id and not event_name:
        return _fail("No Event identifier provided")

    cards, visitors = [], []

    if event_id:
        cards = supabase.table("event_ai_cards").select("*").eq("event_id", event_id).execute().data
        visitors = supabase.table("visitor_details").select("*").eq("event_id", event_id).execute().data
    elif event_name:
        cards = supabase.table("event_ai_cards").select("*").eq("event_name", event_name).execute().data
        visitors = supabase.table("visitor_details").select("*").eq("event_name", event_name).execute().data

    return {"success": True, "cards": cards, "visitors": visitors}


# ---------------------------------------------------------------------------
# Visitor Details
# ---------------------------------------------------------------------------

def save_lead_data(lead_data: dict):
    row = {
        "timestamp": _now_iso(),
        "event_id": lead_data.get("eventId") or "N/A",
        "event_name": lead_data.get("eventName") or "N/A",
        "visitor_name": lead_data.get("fullName"),
        "visitor_mobile": lead_data.get("mobile"),
        "visitor_email": lead_data.get("email"),
        "visitor_organization": lead_data.get("organization"),
        "visitor_designation": lead_data.get("designation"),
        "message": lead_data.get("message"),
    }
    supabase.table("visitor_details").insert(row).execute()
    return _ok(message="Lead saved successfully!")


def save_visitor_and_get_contact(visitor_data: dict):
    event_id = visitor_data.get("eventId")
    event_name = "N/A"
    contact_info = None

    if event_id:
        resp = (
            supabase.table("event_details")
            .select("*")
            .eq("event_id", event_id)
            .limit(1)
            .execute()
        )
        if resp.data:
            row = resp.data[0]
            event_name = row.get("event_name") or "N/A"
            manager_name = row.get("member_name") or row.get("event_name")
            contact_info = {
                "name": manager_name,
                "company": row.get("event_name"),
                "tagline": "", "industry": "", "foundedYear": "",
                "phone": row.get("phone") or "N/A",
                "altPhone": "", "email": "N/A", "whatsapp": "",
                "address": row.get("location") or "",
                "city": "", "state": "", "pincode": "", "country": "",
                "website": "", "mapsLink": "", "linkedin": "", "instagram": "",
                "facebook": "", "twitter": "", "services": "", "about": "",
            }

    if not contact_info:
        contact_info = {
            "name": "Event Organizer",
            "company": event_id,
            "phone": "", "email": "", "website": "",
        }

    supabase.table("visitor_details").insert({
        "timestamp": _now_iso(),
        "event_id": event_id or "N/A",
        "event_name": event_name,
        "visitor_name": visitor_data.get("visitorName") or "",
        "visitor_mobile": visitor_data.get("visitorMobile") or "",
        "visitor_email": visitor_data.get("visitorEmail") or "",
        "visitor_organization": visitor_data.get("visitorOrg") or "",
        "visitor_designation": visitor_data.get("visitorDesig") or "",
        "message": visitor_data.get("message") or "",
    }).execute()

    global_profile = get_company_profile().get("profile") or {}
    if global_profile.get("companyName"):
        contact_info = {
            "name": global_profile.get("keyPersonName") or contact_info["name"],
            "company": global_profile.get("companyName"),
            "tagline": global_profile.get("tagline") or "",
            "industry": global_profile.get("industry") or "",
            "foundedYear": global_profile.get("foundedYear") or "",
            "phone": global_profile.get("keyPersonPhone") or global_profile.get("officialPhone") or "N/A",
            "altPhone": global_profile.get("alternatePhone") or "",
            "email": global_profile.get("keyPersonEmail") or global_profile.get("officialEmail") or "N/A",
            "whatsapp": global_profile.get("whatsappNumber") or "",
            "address": global_profile.get("addressLine") or "",
            "city": global_profile.get("city") or "",
            "state": global_profile.get("state") or "",
            "pincode": global_profile.get("pincode") or "",
            "country": global_profile.get("country") or "",
            "website": global_profile.get("websiteUrl") or "",
            "linkedin": global_profile.get("linkedin") or "",
            "twitter": global_profile.get("twitter") or "",
            "facebook": global_profile.get("facebook") or "",
            "instagram": global_profile.get("instagram") or "",
            "services": global_profile.get("services") or "",
            "about": global_profile.get("aboutCompany") or "",
            "mapsLink": global_profile.get("googleMapsLink") or "",
            "logoBase64": global_profile.get("logoBase64") or "",
        }

    return _ok(message="Visitor saved successfully", contactInfo=contact_info)


# ---------------------------------------------------------------------------
# Company Profile (single-row table)
# ---------------------------------------------------------------------------

_PROFILE_COLUMN_MAP = {
    "companyName": "company_name", "tagline": "tagline", "industry": "industry",
    "foundedYear": "founded_year", "officialPhone": "official_phone",
    "alternatePhone": "alternate_phone", "officialEmail": "official_email",
    "whatsappNumber": "whatsapp_number", "addressLine": "address_line1",
    "city": "city", "state": "state", "pincode": "pincode", "country": "country",
    "websiteUrl": "website_url", "googleMapsLink": "google_maps_link",
    "linkedin": "linkedin", "instagram": "instagram", "facebook": "facebook",
    "twitter": "twitter", "services": "services_provided",
    "aboutCompany": "about_company", "keyPersonName": "key_person_name",
    "keyPersonDesignation": "key_person_designation",
    "keyPersonPhone": "key_person_phone", "keyPersonEmail": "key_person_email",
    "logoBase64": "logo",
}


def get_company_profile():
    resp = (
        supabase.table("company_profile")
        .select("*")
        .order("id", desc=True)
        .limit(1)
        .execute()
    )
    if not resp.data:
        return _ok(profile={})

    row = resp.data[0]
    profile = {}
    for frontend_key, col in _PROFILE_COLUMN_MAP.items():
        profile[frontend_key] = row.get(col) or ""
    return _ok(profile=profile)


def save_company_profile(profile_data: dict):
    row = {"timestamp": _now_iso()}
    for frontend_key, col in _PROFILE_COLUMN_MAP.items():
        row[col] = (profile_data or {}).get(frontend_key) or ""

    existing = supabase.table("company_profile").select("id").limit(1).execute()
    if existing.data:
        supabase.table("company_profile").update(row).eq("id", existing.data[0]["id"]).execute()
    else:
        supabase.table("company_profile").insert(row).execute()

    return _ok(message="Company profile explicitly saved in the Sheet.")


# ---------------------------------------------------------------------------
# Personal QR Profiles
# ---------------------------------------------------------------------------

def create_personal_qr(profile_data: dict):
    timestamp_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    import random
    qr_id = f"qr_{timestamp_ms}_{random.randint(0, 9999)}"

    supabase.table("personal_qr_profiles").insert({
        "name": profile_data.get("name") or "",
        "phone": profile_data.get("phone") or "",
        "email": profile_data.get("email") or "",
        "company": profile_data.get("company") or "",
        "qr_id": qr_id,
        "created_date": _now_iso(),
    }).execute()

    # qrUrl intentionally omitted — the frontend builds it from window.location.origin
    # (same reasoning as the old Apps Script version) so it always points at
    # whichever deployment created the QR code.
    return _ok(message="QR Profile created successfully!", qrId=qr_id)


def update_personal_qr(qr_id: str, profile_data: dict):
    if not qr_id:
        return _fail("No QR ID provided")

    resp = supabase.table("personal_qr_profiles").select("id").eq("qr_id", qr_id).limit(1).execute()
    if not resp.data:
        return _fail("QR Profile not found")

    update_row = {}
    if profile_data.get("name") is not None:
        update_row["name"] = profile_data["name"]
    if profile_data.get("phone") is not None:
        update_row["phone"] = profile_data["phone"]
    if profile_data.get("email") is not None:
        update_row["email"] = profile_data["email"]
    if profile_data.get("company") is not None:
        update_row["company"] = profile_data["company"]

    supabase.table("personal_qr_profiles").update(update_row).eq("id", resp.data[0]["id"]).execute()
    return _ok(message="QR Profile updated successfully!", qrId=qr_id)


def get_qr_profile(qr_id: str):
    if not qr_id:
        return _fail("No QR ID provided")
    resp = supabase.table("personal_qr_profiles").select("*").eq("qr_id", qr_id).limit(1).execute()
    if not resp.data:
        return _fail("QR Profile not found")
    return _ok(resp.data[0])


def get_all_qr_profiles():
    resp = supabase.table("personal_qr_profiles").select("*").order("id", desc=True).execute()
    return _ok(resp.data)


# ---------------------------------------------------------------------------
# Generic sheet-style dump — kept for parity with the old `read` action.
# ---------------------------------------------------------------------------

_TABLE_BY_SHEET_NAME = {
    "Ai Card": "ai_cards",
    "Event Details": "event_details",
    "Event Ai Card": "event_ai_cards",
    "Visitor Details": "visitor_details",
    "Company Profile": "company_profile",
    "Personal QR Profiles": "personal_qr_profiles",
}

# Reverse column-name maps (Postgres snake_case -> old Sheet header text), one
# per table, so anything still reading the "read"/getSheetData()-style
# response (e.g. frontend/leads.html) sees the exact same header keys it
# always did — the frontend was never changed as part of the Supabase move.
_SHEET_HEADERS_BY_TABLE = {
    "ai_cards": {
        "timestamp": "Timestamp", "photo1": "Photo1", "photo2": "Photo2",
        "company": "Company", "industry": "Industry", "name": "Name", "title": "Title",
        "phone": "Phone", "email": "Email", "website": "Website",
        "social_media": "Social Media", "address": "Address", "services": "Services",
        "company_size": "Company Size", "founded_year": "Founded Year",
        "registration_status": "Registration Status", "trust_score": "Trust Score",
        "key_people": "Key People", "is_validated": "Is Validated",
        "validation_link": "Validation Link", "about_company": "About Company",
        "location": "Location",
    },
    "event_details": {
        "timestamp": "Timestamp", "event_id": "Event ID", "event_name": "Event Name",
        "start_date": "Start Date", "end_date": "End Date", "location": "Location",
        "description": "Description", "member_name": "Member Name",
        "designation": "Designation", "phone": "Phone",
    },
    "event_ai_cards": {
        "timestamp": "Timestamp", "event_id": "Event ID", "event_name": "Event Name",
        "event_start_date": "Event Start Date", "event_end_date": "Event End Date",
        "card_photo1": "Card Photo 1", "card_photo2": "Card Photo 2",
        "company_name": "Company Name", "industry": "Industry",
        "person_name": "Person Name", "designation": "Designation", "phone": "Phone",
        "email": "Email", "website": "Website", "social_media": "Social Media",
        "address": "Address", "services": "Services", "company_size": "Company Size",
        "founded_year": "Founded Year", "registration_status": "Registration Status",
        "trust_score": "Trust Score", "people_founders": "People (Founders)",
        "is_validated": "Is Validated", "source_link": "Source Link",
        "about_company": "About Company", "location": "Location",
    },
    "visitor_details": {
        "timestamp": "Timestamp", "event_id": "Event ID", "event_name": "Event Name",
        "visitor_name": "Visitor Name", "visitor_mobile": "Visitor Mobile",
        "visitor_email": "Visitor Email", "visitor_organization": "Visitor Organization",
        "visitor_designation": "Visitor Designation", "message": "Message",
    },
    "company_profile": {v: k for k, v in _PROFILE_COLUMN_MAP.items()},  # not used via get_sheet_data, kept for completeness
    "personal_qr_profiles": {
        "name": "Name", "phone": "Phone", "email": "Email", "company": "Company",
        "qr_id": "QR_ID", "created_date": "Created Date",
    },
}


def get_sheet_data(sheet_name: str):
    table = _TABLE_BY_SHEET_NAME.get(sheet_name or "Ai Card", "ai_cards")
    resp = supabase.table(table).select("*").execute()
    if not resp.data:
        return []

    header_map = _SHEET_HEADERS_BY_TABLE.get(table, {})
    remapped = []
    for row in resp.data:
        obj = {}
        for col, value in row.items():
            key = header_map.get(col, col)
            obj[key] = value if value is not None else ""
        remapped.append(obj)

    return _ok(remapped)
