# Business Card Event Reader - Complete System Documentation

## 🎯 Project Overview

**Business Card Event Reader** is an intelligent OCR-powered lead capture system designed for events and networking. It automatically extracts business card data from photos using Google Cloud Vision API, enriches the data with company intelligence, and stores everything in Google Sheets.

The system also includes a **Personal QR Code Profile** feature that allows users to create and share individual QR codes for instant contact saving.

---

## 📁 Project Structure

```
Business_Card_Event_Reader/
├── BotivateScanner/              # React TypeScript Frontend (Scanner & QR Views)
│   ├── src/
│   │   ├── App.tsx               # Main app component with routing & lead forms
│   │   ├── CreateQR.tsx          # Create personal QR code form
│   │   ├── QRListPage.tsx        # List all created QR profiles
│   │   └── main.tsx
│   ├── dist/                      # Built React app (mounted at /scanner)
│   ├── package.json
│   └── tsconfig.json
│
├── backend/
│   ├── main.py                   # FastAPI server (port 8000)
│   ├── run.py                    # Entry point
│   ├── core/
│   │   ├── config.py             # Logger, paths, constants
│   │   └── models.py             # Pydantic request models
│   ├── services/
│   │   ├── ocr_service.py        # Google Cloud Vision OCR
│   │   └── enrichment_service.py # Waterfall enrichment (LinkedIn, Apollo, etc.)
│   └── utils/
│       └── sheets.py             # Google Apps Script integration
│
├── frontend/
│   ├── index.html                # Main Event Hub page (HTML/CSS/JS)
│   ├── leads.html                # Global Leads Database table view
│   ├── style.css                 # Global styles
│   ├── worker.js                 # Service worker
│   └── visitor-form/             # QR event visitor form
│
├── FINAL_APPS_SCRIPT.js          # Google Apps Script (deploy to Google Sheets)
├── Dockerfile                    # Docker containerization
└── .env                          # Environment variables (Google credentials, etc.)
```

---

## 🔑 Key Features

### 1. **Business Card OCR Scanning**
- Upload photos (1 or 2 sides) of business cards
- Automatic extraction using Google Cloud Vision API
- Fields: Name, Phone, Email, Company, Website, LinkedIn, etc.
- Confidence scoring based on enrichment validation

### 2. **Data Enrichment (Waterfall)**
Three-tier enrichment pipeline:
1. **LinkedIn API** → Validate person/company data
2. **Apollo.io API** → Find missing company details
3. **Google Search** → Final fallback for company info

### 3. **Event Management**
- Create events with custom questions
- Capture business cards and visitor responses per event
- View event-specific analytics and lead lists

### 4. **Personal QR Code Profiles** ⭐ NEW
- Users create personal QR codes with Name, Phone, Email, Company
- Generate unique QR codes that link to contact profile
- Share QR codes for instant contact saving
- **Editable**: each profile card in "MY QRs" list has a pencil/Edit icon → inline form to update Name/Phone/Email/Company without changing the QR_ID (so the existing printed/shared QR code keeps working) — `PUT /update-qr/{qr_id}` → `updatePersonalQR()` in Apps Script
- Two views:
  - **QR Scanning View**: Shows person's name + "Scan this QR to save my contact" + QR code
  - **Profile View**: Shows Name, Company, Phone, Email + SAVE CONTACT button (minimal, no form)

### 5. **Global Leads Database**
- Searchable table of all scanned cards
- Filter by company, industry, trust score, validation status
- Export capabilities

### 6. **In-App Back Navigation** ⭐ NEW
- Scanner app (`BotivateScanner`) sub-pages (Create QR, Profile QR List) use real browser history (`window.history.pushState`/`popstate`) instead of a hardcoded "go to profile" reset
- The in-app BACK button and the browser's native back arrow both resolve to `window.history.back()`, so they always return to whichever page the user actually came from
- See `App.tsx` → `goToPage()` / `goBack()`

---

## 🛠️ Tech Stack

### Frontend
- **React 18** + TypeScript (BotivateScanner)
- **Vite** (build tool)
- **Tailwind CSS** (styling)
- **Lucide React** (icons)
- **jsPDF** (PDF generation)
- **html2canvas** (HTML to image)

### Backend
- **FastAPI** (Python web framework)
- **Google Cloud Vision API** (OCR)
- **Google Apps Script** (Sheets integration)
- **httpx** (async HTTP client)

### Data Storage
- **Google Sheets** (primary database)
  - Sheets: "Scanned Cards", "Event Database", "Personal QR Profiles", "Visitors"
- **Apps Script** (backend for Sheets API calls)

### Infrastructure
- **Docker** (containerization)
- **Port 8000** (FastAPI backend)
- **Port 3000** (React dev server, optional)

---

## 📋 API Endpoints

### Card & Lead Management
- `POST /ocr` → OCR scan business card
- `POST /submit-lead` → Submit lead from visitor form
- `GET /get-events` → Fetch all events
- `POST /save-event` → Create new event
- `GET /get-event/{event_id}` → Get event details
- `GET /get-event-data` → Get event-specific lead data

### Personal QR Profiles
- `POST /create-qr` → Create personal QR profile
- `PUT /update-qr/{qr_id}` → Edit an existing QR profile's Name/Phone/Email/Company ⭐ NEW
- `GET /get-qr-profile/{qr_id}` → Fetch profile by ID
- `GET /get-all-qr-profiles` → List all QR profiles

### Company Profile
- `GET /get-company-profile` → Fetch company details
- `POST /save-company-profile` → Update company profile

### Utilities
- `GET /vcard-direct` → Generate downloadable vCard (.vcf)
- `GET /proxy-image` → CORS-safe image proxy

---

## 📱 QR Code System (Personal Profiles)

### Flow

```
CREATE QR TAB (Modal)
  ↓
User fills: Name, Phone, Email, Company
  ↓
Click "GENERATE MY QR"
  ↓
Backend creates entry in "Personal QR Profiles" sheet
  ↓
Returns: QR_ID + QR_URL
  ↓
Display QR code (via qr-server.com API)

MY QRs TAB (Modal)
  ↓
Click any person card
  ↓
SCANNING VIEW: Show person's name + QR code + "Scan this QR to save my contact"
  ↓
User scans → Navigate to /scanner?qr=<QR_ID>
  ↓
PROFILE VIEW: Show minimal card (Name, Company, Phone, Email, Save Contact)
  ↓
User clicks "SAVE CONTACT" → Download .vcf file
```

### Key Implementation Details

#### Google Sheets Column Naming
- **Important**: The " QR_ID" column header has a **leading space character**
- Code handles this: `profile[' QR_ID']` (note the space)
- Fallback: `Object.keys(profile).find(k => k.includes('QR_ID'))`

#### QR Code Generation
- **API**: `https://api.qrserver.com/v1/create-qr-code/?size=400x400&data=<URL>`
- Why: Better CORS support than Google Charts API
- Format: Links to `http://127.0.0.1:8000/scanner?qr=<QR_ID>`

#### Unique QR ID Generation
- Format: `qr_<timestamp>_<random>`
- Example: `qr_1718962400_7849`
- Stored in Apps Script, returned to frontend

#### Mobile Responsiveness
- QR code size: `w-64 h-64 sm:w-80 sm:h-80` (scales with screen)
- Text sizes: `text-2xl sm:text-3xl` (responsive scaling)
- Padding: `p-3 sm:p-6 lg:p-8` (adaptive spacing)
- Icons: `w-4 h-4 sm:w-5 sm:h-5` (responsive icons)

---

## 🏢 Company Profile — Industry Field

- **Location**: `frontend/index.html`, Profile Drawer → Company Details → `#prof_comp_industry`
- **Fixed options**: Technology, Real Estate, Healthcare, Finance, Education, **Energy & Utilities**, Other
- **"Other" behavior**: selecting `Other` reveals a text input (`#prof_comp_industry_other`); `saveProfile()` swaps the saved `industry` value for whatever was typed there, so a custom industry is stored and round-trips identically to a picklist value
- **On load**: if the saved `industry` value doesn't match any fixed option, the dropdown auto-selects `Other` and fills the text box with the saved value (so old custom entries redisplay correctly)
- Wiring: `toggleIndustryOther()` shows/hides the text box on `<select onchange>`

---

## 🔧 Setup & Deployment

### Environment Setup

1. **Google Cloud Credentials**
   ```
   .env file:
   - Set Google Cloud Vision API key
   - Google Sheets ID
   - Apps Script URL
   ```

2. **Google Apps Script Deployment**
   - Open Google Sheet
   - Extensions → Apps Script
   - Replace code with `FINAL_APPS_SCRIPT.js`
   - Deploy as Web App
   - Update `APPS_SCRIPT_URL` in code

3. **Install Dependencies**
   ```bash
   # Backend
   cd backend && pip install -r requirements.txt
   
   # Frontend
   cd BotivateScanner && npm install
   ```

4. **Build Frontend**
   ```bash
   cd BotivateScanner && npm run build
   ```

5. **Run Backend**
   ```bash
   python run.py
   ```

---

## 🧪 Testing QR Profile Feature

### Manual Testing Steps

1. **Start Backend**
   ```bash
   python run.py
   ```

2. **Access Event Hub**
   - Go to `http://127.0.0.1:8000`

3. **Create QR Profile**
   - Click blue "PROFILE QR" button
   - Select "CREATE QR" tab
   - Fill: Name, Phone, Email, Company
   - Click "GENERATE MY QR"
   - QR code displays with Download/Copy options

4. **View QR List**
   - Click "MY QRs" tab
   - See all created profiles as cards
   - Click any card → Shows QR code for scanning

5. **Scan QR Code**
   - Use any QR scanner (phone, online tool)
   - Scan the QR code
   - Opens `/scanner?qr=<QR_ID>`
   - Shows minimal profile card: Name, Company, Phone, Email, Save Contact

6. **Save Contact**
   - Click "SAVE CONTACT" button
   - Downloads `.vcf` file
   - Import into phone contacts

---

## 🐛 Known Issues & Fixes

### Issue: QR_ID comes back as `undefined`
**Root Cause**: Google Sheets column header is " QR_ID" (with leading space)
**Fix**: Use `profile[' QR_ID']` or detect with `.find(k => k.includes('QR_ID'))`

### Issue: QR image fails to load
**Root Cause**: Google Charts API blocked by CORS
**Fix**: Use `qr-server.com` API instead (has proper CORS headers)

### Issue: Apps Script functions not deployed
**Root Cause**: Code not updated in Google Sheets
**Fix**: 
1. Open Google Sheet
2. Extensions → Apps Script
3. Delete all existing code
4. Paste `FINAL_APPS_SCRIPT.js` contents
5. Save & Deploy → New Deployment → Web App

### Issue: Text overflow on mobile
**Root Cause**: Fixed text sizes
**Fix**: Use Tailwind responsive classes (`sm:`, `md:`, `lg:`)

### Issue: Company Profile "Save" button spins forever, nothing happens
**Root Cause**: In `frontend/index.html` → `saveProfile()`, `res` was declared with `const` inside the `try` block but referenced again inside `finally`. That's a `ReferenceError` (block-scoped variable used outside its scope), so the `finally` block crashed before it could hide the loading spinner — on every save attempt, success or failure.
**Fix**: Declare `let res;` before the `try` block, then assign it inside (`res = await response.json();`) instead of `const res = ...`. Fixed in commit `19934b1`.
**Related**: once this was fixed, the *real* underlying error becomes visible as a toast — usually `"Company Profile sheet not found!"` (see next issue).

### Issue: "Company Profile sheet not found!" / new Google Sheet doesn't work out of the box
**Root Cause**: A brand-new Google Sheet only has a default `Sheet1` tab. Historically, not every worksheet the Apps Script needed was auto-created — `saveCompanyProfile()` and `getCompanyProfile()` used to hard-fail with `ss.getSheetByName("Company Profile")` returning null.
**Fix (superseded)**: This is now solved properly by the auto-setup system below — every sheet self-heals on first use, and there's a one-click "Setup Sheets" menu for new deployments.

---

## 📄 Auto Sheet Setup (v2.1+)

As of `FINAL_APPS_SCRIPT.js` v2.1, **the whole Google Sheet structure is self-provisioning** — no more manually creating tabs for a new deployment.

### How it works
- `REQUIRED_SHEETS` (top of the file) is a map of `sheetName → [header columns]` for every tab the system needs: `Ai Card`, `Event Details`, `Event Ai Card`, `Visitor Details`, `Company Profile`, `Personal QR Profiles`.
- `ensureSheet(ss, name)` creates the tab if missing and writes the bolded header row if the tab is empty — never touches a tab that already has data.
- Every read/write function (`saveData`, `saveEventData`, `getEventList`, `saveEventCardData`, `saveLeadData`, `saveVisitorAndGetContact`, `getCompanyProfile`, `saveCompanyProfile`, `createPersonalQR`, `getQRProfile`, `getAllQRProfiles`, `getSheetData`) calls `ensureSheet()` instead of a raw `getSheetByName()` — so a missing tab self-heals instead of throwing a hard error.
- `setupAllSheets()` is the one-shot entry point: creates every tab in `REQUIRED_SHEETS` that doesn't exist yet. Safe to run any number of times.
- `onOpen()` adds a **"⚙️ Business Card Reader" → "🛠️ Setup Sheets"** menu that appears automatically when the Google Sheet is opened — click it once right after deploying to a brand-new Sheet and everything gets created in one go.

### New client / new deployment checklist
1. Create a new Google Sheet
2. Extensions → Apps Script → paste `FINAL_APPS_SCRIPT.js`, set `SHEET_ID` to the new Sheet's ID
3. Deploy as Web App, copy the `APPS_SCRIPT_URL`
4. Open the Google Sheet in the browser (triggers `onOpen`) → click **⚙️ Business Card Reader → 🛠️ Setup Sheets** — this creates all 6 tabs with correct headers in one click
   - (Alternative: run `setupAllSheets` directly from the Apps Script editor if you don't want to touch the Sheet UI)
5. Proceed with the rest of the setup (API keys, `.env`, Render deploy)

> Even without running the menu manually, the system now self-heals — the first OCR scan / event save / profile save / QR create will silently create whatever tab it needs. The menu is just the fast, all-at-once option.

---

## 💾 Data Model (Google Sheets)

### "Scanned Cards" Sheet
| Column | Type | Description |
|--------|------|-------------|
| Name | String | Full name |
| Phone | String | Phone number |
| Email | String | Email address |
| Company | String | Organization |
| Website | String | Website URL |
| LinkedIn | String | LinkedIn profile |
| Industry | String | Industry type |
| Trust Score | String | Validation score |
| Is Validated | Boolean | Enrichment verified |
| Photo1 | Image | Front of card |
| Photo2 | Image | Back of card |

### "Personal QR Profiles" Sheet
| Column | Type | Description |
|--------|------|-------------|
| Name | String | Person's name |
| Phone | String | Phone number |
| Email | String | Email address |
| Company | String | Company/Org |
| **QR_ID** | String | Unique ID (with leading space) |
| Created Date | Date | Timestamp |

### "Event Database" Sheet
| Column | Type | Description |
|--------|------|-------------|
| Event ID | String | Unique event ID |
| Event Name | String | Event title |
| Date | Date | Event date |
| Cards Scanned | Number | Count |

### "Company Profile" Sheet
Row 1 must contain these exact headers (order doesn't matter, names must match exactly — `saveCompanyProfile`/`getCompanyProfile` match by header text):

```
Timestamp | Company Name | Tagline | Industry | Founded Year | Official Phone | Alternate Phone | Official Email | WhatsApp Number | Address Line 1 | City | State | Pincode | Country | Website URL | Google Maps Link | LinkedIn | Instagram | Facebook | Twitter | Services Provided | About the company | Key Person Name | Key Person Designation | Key Person Phone | Key Person Email | Logo
```

Only ever holds **one row of data** (row 2) — every save overwrites row 2 rather than appending.

---

## 🎨 UI/UX Design

### Modal System (Frontend)
- **Profile QR Modal**: Blue header, two tabs (Create QR, My QRs)
- **Event Modal**: Create/edit events
- **Profile Drawer**: Company profile sidebar

### Color Scheme
- **Primary**: Blue (`#2563eb`, `bg-blue-600`)
- **Secondary**: Indigo (`#4f46e5`)
- **Accent**: Orange (`#f59e0b`)
- **Background**: Slate (`#f1f5f9`)

### Responsive Breakpoints
- **Mobile**: `<640px`
- **Tablet**: `640px - 1024px` (Tailwind `sm:` and `md:`)
- **Desktop**: `>1024px` (Tailwind `lg:`)

---

## 🚀 Future Enhancements

1. **Scan History** — Track which cards were scanned and when
2. **Contact Sync** — Auto-sync to phone contacts/CRM
3. **Duplicate Detection** — Find duplicate cards in database
4. **Bulk Import** — Import CSV/Excel card lists
5. **Advanced Analytics** — Industry trends, top companies
6. **Custom Branding** — White-label QR profiles

---

## 📝 Git Workflow

- **Main branch**: Production-ready code
- **Commit message**: Descriptive, action-focused
  - Example: `added profile qr code feature`
  - Not: `fix`, `update`, `changes`

---

## 🤝 Collaboration Notes

- **User Preference**: Simple explanations, Hindi mixed with English ("samjha nhi mai" style)
- **Build Process**: React app auto-rebuilds on `npm run build`
- **Backend Restart**: Required after endpoint changes
- **Testing**: Always test features before marking complete
- **Mobile First**: All UI changes must be mobile responsive

---

## 📞 Support & Troubleshooting

### Backend won't start
```bash
# Check if ports 8000/8001 are in use
netstat -ano | findstr ":8000 :8001"

# Kill lingering processes
taskkill /F /PID <PID>
```

### React build fails
```bash
# Clear cache and rebuild
cd BotivateScanner
rm -rf node_modules package-lock.json
npm install
npm run build
```

### QR code not showing
- Check browser console for errors
- Verify qr-server.com is accessible
- Check CORS headers on image response

### Apps Script not saving data
- Verify deployment is active
- Check Google Sheet permissions
- View Apps Script execution logs

---

**Last Updated**: August 18, 2026
**System Version**: v2.1.0 (Back Navigation Fix + Custom Industry + Company Profile Save Fix + Auto Sheet Setup)
