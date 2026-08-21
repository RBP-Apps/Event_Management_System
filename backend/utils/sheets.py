# DEPRECATED: the app now reads/writes Supabase (see backend/utils/supabase_client.py).
# Kept only as a historical reference for the old Google Sheets / Apps Script
# integration — no code in this project calls submit_to_sheets() anymore.
import requests
from backend.core.config import APPS_SCRIPT_URL, logger

def submit_to_sheets(payload: dict):
    logger.info("Submitting data to Google Sheets...")
    try:
        resp = requests.post(APPS_SCRIPT_URL, json=payload, timeout=15)
        logger.info(f"Sheets Response: {resp.status_code}")
        return resp
    except Exception as e:
        logger.error(f"Sheets Submission Error: {e}")
        return None
