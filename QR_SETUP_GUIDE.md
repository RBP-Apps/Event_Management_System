# 🚀 Personal QR Feature - Setup Guide

## 3 Simple Steps to Deploy

---

## **STEP 1: Update Google Apps Script** ✅

1. Go to your **Google Sheet**
2. Click **Extensions > Apps Script**
3. **Select ALL code** (Ctrl+A) and **DELETE it**
4. Copy entire code from: `FINAL_APPS_SCRIPT.js`
5. Paste it into Apps Script
6. Click **Deploy** (top right)
7. Select **New Deployment**
8. Type: **Web App**
9. Execute as: Your account
10. Allow access: **Anyone**
11. Click **Deploy**
12. ✅ Done!

---

## **STEP 2: Rebuild React Frontend**

Open terminal in project root:

```bash
cd BotivateScanner
npm install
npm run build
cd ..
```

This creates a production build. Done!

---

## **STEP 3: Test It!**

### **Test 1: Create QR**
```
1. Open: http://127.0.0.1:8000/scanner (or your site)
2. Click "CREATE YOUR QR" button
3. Fill: Name, Phone, Email, Company
4. Click "GENERATE MY QR"
5. ✅ Should see QR code + download button
```

### **Test 2: Scan QR**
```
1. Download the QR image
2. Scan with phone camera
3. Should open: https://yoursite.com/profile?qr=qr_xyz
4. Should show profile (NO FORM!)
5. ✅ Download PDF, Save Contact should work
```

---

## **What Each File Does**

| File | What It Does | Modified? |
|------|-------------|-----------|
| `backend/main.py` | Python backend endpoints | ✅ Yes |
| `FINAL_APPS_SCRIPT.js` | Google Sheet handler functions | ✅ Yes |
| `BotivateScanner/src/App.tsx` | Main React app + routing | ✅ Yes |
| `BotivateScanner/src/CreateQR.tsx` | QR creation form | ✅ New |
| `BotivateScanner/src/index.css` | Styling | ❌ No |

---

## **Google Sheet Setup**

### Already Done! ✅
Your sheet now has: **"Personal QR Profiles"** tab

Check it has columns:
- Name
- Phone
- Email
- Company
- QR_ID
- Created Date

If missing, manually add it (5 columns, header row)

---

## **Testing Checklist**

- [ ] Backend running: `python run.py`
- [ ] React built: `npm run build` in BotivateScanner
- [ ] Apps Script deployed with new code
- [ ] Google Sheet has "Personal QR Profiles" tab
- [ ] Create QR works (form fills + generates QR)
- [ ] QR downloads successfully
- [ ] Scanning QR opens profile (no form)
- [ ] Profile shows correct name/phone/email/company

---

## **Troubleshooting**

### **"Create QR button not showing"**
- Run: `npm run build` in BotivateScanner
- Restart backend: `python run.py`

### **"QR generated but link doesn't work"**
- Check Apps Script deployed correctly
- Check APPS_SCRIPT_URL in App.tsx matches your URL
- Look at browser console for errors

### **"Profile not loading on scan"**
- Check Google Sheet has "Personal QR Profiles" tab
- Check QR_ID column (column E)
- Verify Apps Script `getQRProfile()` function exists

### **"Backend says endpoint not found"**
- Make sure `backend/main.py` has both endpoints:
  - `/create-qr`
  - `/get-qr-profile/{qr_id}`

---

## **Quick Command Reference**

```bash
# Start backend
python run.py

# Rebuild React
cd BotivateScanner && npm run build

# Test in browser
http://127.0.0.1:8000/scanner
```

---

## **Support**

**Error in terminal?**
1. Check Python version: `python --version`
2. Check Node version: `node --version`
3. Check all dependencies installed: `npm install`, `pip install -r requirements.txt`

**QR not scanning?**
1. Check QR image quality
2. Try different phone camera
3. Check URL is correct

---

**You're all set! 🎉**

Start creating QR codes and share profiles instantly!
