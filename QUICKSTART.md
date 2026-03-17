# 🚀 QUICK START GUIDE - Rate Edge v5.1

## ⚡ Get Started in 2 Minutes!

### Step 1: Install Python (if needed)
- Download Python 3.8+ from python.org
- Make sure pip is installed (comes with Python)

### Step 2: Install Dependencies
```bash
cd RateEdge_v5.1
pip install -r requirements.txt
```

### Step 3: Launch!

**Desktop App:**
```bash
python launch.py
```

**Web App:**
```bash
python web_app.py
```
Then open: http://localhost:8000

---

## 🎯 First Time Users - Try This!

### 1. Check Your Data (Desktop App)
- Launch the app: `python launch.py`
- Go to "📊 Data View" tab
- See 128,476 swap rates!
- Filter by currency: Select "AUD"
- See 34,499 AUD records

### 2. Calculate a Basis (FIXED in v5.1!)
- Go to "💹 Basis Analyzer" tab
- Select:
  - Currency: **AUD**
  - Fixed Tenor: **5Y**
  - Short Rate: **3M BBSW**
  - Long Rate: **6M BBSW**
- Click "📊 Calculate Basis"
- See the spread chart!

**What you'll see:**
- Chart showing 3M vs 6M basis over time
- Statistics (current, mean, std dev)
- Data table with historical values
- GREEN areas = 6M trades above 3M
- RED areas = 6M trades below 3M

### 3. Price a Forward Swap
- Go to "📈 Forward Swap" tab
- Select:
  - Currency: **AUD**
  - Start: **2Y**
  - End: **5Y**
- Click "Calculate"
- See 2Y2Y forward rate!

### 4. View Historical Charts
- Go to "📉 Yield Curve" tab
- Select currency and date
- See interactive yield curve
- Hover over points for details

### 5. Export Your Analysis
- Any chart → Right-click → "Save Image"
- Any data table → Click "Export CSV"
- PDF Reports → "📄 Reports" tab

---

## 🐛 What's Fixed in v5.1?

### THE BIG FIX: Basis Calculation ✅

**Before v5.1 (WRONG):**
```
6M BBSW = 4.50%
3M BBSW = 4.30%
Basis = 3M - 6M = -0.20%  ❌ WRONG!
```

**After v5.1 (CORRECT):**
```
6M BBSW = 4.50%
3M BBSW = 4.30%
Basis = 6M - 3M = +0.20%  ✅ CORRECT!

Interpretation: 6M trades 20 bps ABOVE 3M
```

**Now you can trust your basis analysis!** 🎯

---

## 📊 Your Database

**What's Included:**
- **128,476 total records**
- **7 currencies** (AUD, CAD, EUR, GBP, JPY, NZD, USD)
- **7+ years of history** (June 2018 - Nov 2025)
- **43 MB database file**

**Top Currency - AUD:**
- 34,499 records
- 3M BBSW: 6M → 35Y tenors
- 6M BBSW: 4Y → 30Y tenors

**You're ready to analyze!** 🚀

---

## 🔍 Common Use Cases

### 1. Daily Basis Monitoring
**Goal:** Track 3M vs 6M BBSW basis daily

**Steps:**
1. Open Basis Analyzer
2. Set: AUD, 5Y, 3M BBSW, 6M BBSW
3. Date range: Last 30 days
4. Calculate
5. Check current basis in statistics panel
6. Export data if needed

**Use:** Identify basis trading opportunities

### 2. Forward Rate Calculation
**Goal:** Price a 2Y forward starting in 1 year

**Steps:**
1. Open Forward Swap Analyzer
2. Currency: AUD
3. Start: 1Y
4. End: 3Y
5. Calculate
6. Get 1Y1Y forward rate

**Use:** Price forward swaps, manage future exposure

### 3. Historical Spread Analysis
**Goal:** Analyze 2Y-10Y steepness over time

**Steps:**
1. Open Spread Analyzer
2. Select short end: 2Y
3. Select long end: 10Y
4. Date range: Last 2 years
5. View chart and statistics

**Use:** Curve trading strategies

### 4. Multi-Currency Comparison
**Goal:** Compare AUD vs USD swap levels

**Steps:**
1. Open Data View
2. Filter 1: AUD, 5Y
3. Filter 2: USD, 5Y
4. Export both to CSV
5. Compare in Excel or import to charts

**Use:** Cross-currency basis trades

---

## 💡 Pro Tips

### Tip 1: Keyboard Shortcuts
- **Ctrl+R**: Refresh data
- **Ctrl+E**: Export current view
- **Ctrl+P**: Print/PDF report
- **F5**: Reload charts

### Tip 2: Faster Queries
- Use date filters (queries faster)
- Export large datasets to CSV
- Use pivot table for summaries

### Tip 3: Custom Analysis
- Web app has REST API
- Use Python scripts with database
- Create custom reports with report_generator.py

### Tip 4: Data Import
- Excel import: "Import Data" tab
- CSV upload: Web app
- API: POST /api/import

### Tip 5: Backup Your Work
```bash
# Backup database
cp database/swap_rates.db database/swap_rates_backup.db

# Backup on schedule (Windows)
# Create batch file: backup.bat
copy database\swap_rates.db database\swap_rates_%date%.db
```

---

## 🆘 Troubleshooting

### "Module not found" Error
```bash
pip install -r requirements.txt
```

### "Database file not found"
- Check you're in RateEdge_v5.1 directory
- Database should be in: `./database/swap_rates.db`

### "No data found" Message
- Check date range (data is 2018-2025)
- Check currency selected has data
- Try "Select All" to see what's available

### Charts Not Showing
- Update matplotlib: `pip install --upgrade matplotlib`
- Restart application

### Slow Performance
- Filter by date range (faster queries)
- Close unused tabs
- Use web app for large queries

---

## 📚 Next Steps

### Learn More:
1. Read full README.md
2. Check CHANGELOG.md for v5.1 fixes
3. Explore each analysis tool
4. Try the web app features
5. Use the API for automation

### Get Advanced:
- Create custom Python scripts
- Use the REST API
- Build automated reports
- Set up data alerts
- Schedule imports

---

## ✅ Checklist

- [ ] Python 3.8+ installed
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Desktop app launches (`python launch.py`)
- [ ] Can see database records (128K+)
- [ ] Basis analyzer works (v5.1 fixed!)
- [ ] Charts display correctly
- [ ] Can export data

**All checked? You're ready!** 🎉

---

## 🎓 Learning Resources

### Understanding Swaps:
- Fixed-for-Floating exchange
- Tenor = time to maturity
- Floating rate = BBSW, SOFR, etc.
- Basis = spread between rates

### Basis Trading:
- Positive basis = long expensive
- Negative basis = long cheap
- Basis widening = spread increases
- Basis narrowing = spread decreases

### Forward Swaps:
- Start in the future
- Lock in future rate today
- Priced from spot curve
- Used for hedging future exposure

---

## 📞 Need Help?

### Check These First:
1. This Quick Start Guide
2. README.md (full documentation)
3. CHANGELOG.md (what's new)
4. Inline help in the app

### Still Stuck?
- Check code comments
- Review example scripts
- Verify Python version (3.8+)
- Ensure all dependencies installed

---

**You're all set! Start analyzing swaps like a pro!** 🚀💹

Remember: v5.1 has the FIXED basis calculation, so you can trust your analysis!
