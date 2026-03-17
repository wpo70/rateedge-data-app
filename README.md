# 📊 Rate Edge v5.1 - Professional IRS Swap Analytics

## 🆕 What's New in v5.1

### **CRITICAL FIX: Basis Calculation Corrected** ✅
- **FIXED**: Basis calculation now correctly shows: `Basis = Long Tenor - Short Tenor`
- **FIXED**: Positive basis now properly indicates long tenor trades HIGHER
- **FIXED**: Clear labeling and documentation in the Basis Analyzer
- **Added**: Visual indicators (green for positive, red for negative basis)
- **Added**: Detailed explanation panel showing how to interpret results

### Database
- **128,476 swap rate records** across 7 currencies
- **Date range**: June 2018 to November 2025 (7.5 years)
- **Currencies**: AUD, CAD, EUR, GBP, JPY, NZD, USD
- **Complete AUD data**: 34,499 records with 3M and 6M BBSW

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch Desktop Application
```bash
python launch.py
```

### 3. Launch Web Application
```bash
python web_app.py
```
Then open: http://localhost:8000

---

## 📦 Package Contents

```
RateEdge_v5.1/
├── launch.py                    # Main desktop app launcher
├── web_app.py                   # Web application
├── basis_analyzer.py            # FIXED basis analyzer (v5.1)
├── forward_swap_analyzer.py     # Forward swap pricing
├── butterfly_analyzer.py        # Butterfly spread analysis
├── swap_relative_value.py       # Relative value analysis
├── basis_spread_analyzer.py     # Spread analysis
├── chart_utils.py               # Charting utilities
├── currency_config.py           # Currency configurations
├── tenor_utils.py               # Tenor utilities
├── requirements.txt             # Python dependencies
│
├── backend/                     # Backend modules
│   ├── database_models.py       # SQLAlchemy models
│   ├── excel_importer.py        # Excel import tools
│   ├── analytics.py             # Analytics engine
│   ├── alerts.py                # Alert system
│   ├── report_generator.py      # PDF reports
│   ├── api.py                   # REST API
│   └── swap_pricer.py           # Swap pricing engine
│
├── frontend/                    # Desktop GUI
│   ├── swap_rate_gui.py         # Main GUI
│   ├── data_upload_gui.py       # Upload interface
│   └── data_upload_handler.py   # Upload handler
│
├── database/                    # Database
│   └── swap_rates.db            # 128K records, 43MB
│
├── templates/                   # Web templates
│   ├── index.html               # Dashboard
│   ├── forward_pricer.html      # Forward pricer
│   ├── data_view.html           # Data viewer
│   ├── pivot_table.html         # Pivot analysis
│   └── ...                      # More templates
│
├── static/                      # Web assets
│   ├── css/main.css
│   └── js/main.js
│
└── resources/                   # Assets
    └── logo.png
```

---

## 🎯 Features

### ✅ Analysis Tools (9 tools)
1. **Basis Analyzer** (FIXED in v5.1) - Tenor basis analysis
2. **Forward Swap Pricer** - Calculate forward rates
3. **Relative Value** - RV opportunities
4. **Butterfly Analyzer** - Curve positioning
5. **Spread Analyzer** - Multi-spread analysis
6. **Yield Curve Viewer** - Interactive curves
7. **Cross-Currency** - Basis relationships
8. **Analytics Charts** - Custom charts
9. **Pivot Table** - Interactive pivot analysis

### ✅ Data Management
- Excel import/export
- CSV templates
- Bulk upload
- Data validation
- Historical analysis

### ✅ Advanced Features
- PDF report generation
- Alert system
- REST API
- Multi-currency support (7 currencies)
- Real-time calculations
- Statistical analysis

---

## 🔧 Usage

### Desktop Application

**Launch:**
```bash
python launch.py
```

**Features:**
- 📊 9 analysis tabs
- 📈 Interactive charts
- 📤 Excel import
- 📥 PDF reports
- 🔔 Alerts
- 📊 Statistics

### Web Application

**Launch:**
```bash
python web_app.py
```

**Access:** http://localhost:8000

**API Endpoints:**
- `GET /api/rates` - Get swap rates
- `GET /api/statistics` - Database stats
- `GET /api/currencies` - Available currencies
- `GET /api/tenors/{currency}` - Available tenors
- `POST /api/forward-pricing` - Calculate forward
- `POST /api/import` - Import Excel data

---

## 📊 Basis Analyzer - How to Use (FIXED in v5.1)

### Understanding Basis (CORRECTED)

**Formula:**
```
Basis = Long Tenor Rate - Short Tenor Rate
```

**Interpretation:**
- **Positive Basis (+)**: Long tenor trades HIGHER than short tenor
- **Negative Basis (-)**: Long tenor trades LOWER than short tenor

**Example:**
```
6M BBSW = 4.50%
3M BBSW = 4.30%
Basis = 4.50% - 4.30% = +0.20% (+20 bps)

Interpretation: 6M trades 20 bps ABOVE 3M
```

### Steps:
1. Select currency (e.g., AUD)
2. Select fixed tenor (e.g., 5Y)
3. Select short tenor rate (e.g., 3M BBSW)
4. Select long tenor rate (e.g., 6M BBSW)
5. Set date range
6. Click "Calculate Basis"

### Output:
- **Chart**: Basis over time (green = positive, red = negative)
- **Statistics**: Mean, median, std dev, current basis
- **Data Table**: Historical basis values
- **Export**: CSV export available

---

## 🗄️ Database Schema

### swap_rates table
```sql
CREATE TABLE swap_rates (
    id INTEGER PRIMARY KEY,
    date DATE NOT NULL,
    currency TEXT NOT NULL,
    tenor TEXT NOT NULL,
    floating_rate TEXT NOT NULL,
    rate REAL NOT NULL,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(date, currency, tenor, floating_rate)
);
```

**Indexes:**
- `idx_date` on (date)
- `idx_currency` on (currency)
- `idx_tenor` on (tenor)
- `idx_floating_rate` on (floating_rate)

---

## 🔄 Data Import

### Excel Import (Desktop App)
1. Go to "Import Data" tab
2. Select Excel file
3. Preview data
4. Click "Import"

### CSV Upload (Web App)
1. Go to `/data/import`
2. Drag & drop CSV file
3. Validate
4. Upload

### Supported Formats

**Long Format:**
```csv
date, currency, tenor, floating_rate, rate
2025-11-12, AUD, 5Y, 6M BBSW, 0.0425
```

**Wide Format:**
```csv
date, 1Y, 2Y, 3Y, 5Y, 10Y
2025-11-12, 4.10, 4.20, 4.25, 4.30, 4.40
```

---

## 🛠️ Configuration

### Currency Config (`currency_config.py`)
```python
SUPPORTED_CURRENCIES = ['AUD', 'CAD', 'EUR', 'GBP', 'JPY', 'NZD', 'USD']

FIXING_REFERENCES = {
    'AUD': {'3M': '3M BBSW', '6M': '6M BBSW'},
    'USD': {'3M': '3M SOFR', '6M': '6M SOFR'},
    ...
}
```

### Database Path
```python
# Default: ./database/swap_rates.db
db = DatabaseManager('sqlite:///./database/swap_rates.db')
```

---

## 📈 Examples

### Calculate 3M vs 6M Basis (FIXED)
```python
from basis_analyzer import BasisAnalyzer
from database_models import DatabaseManager

db = DatabaseManager()
analyzer = BasisAnalyzer(root, db)

# Set parameters
analyzer.currency_var.set('AUD')
analyzer.fixed_tenor_var.set('5Y')
analyzer.short_rate_var.set('3M BBSW')
analyzer.long_rate_var.set('6M BBSW')

# Calculate
analyzer.calculate_basis()
```

### Forward Swap Pricing
```python
from forward_swap_analyzer import ForwardSwapAnalyzer

# Calculate 2Y2Y forward
result = analyzer.calculate_forward(
    currency='AUD',
    start_tenor='2Y',
    end_tenor='4Y'
)
```

### API Query
```bash
# Get latest AUD rates
curl http://localhost:8000/api/rates?currency=AUD&limit=10

# Get 5Y tenor history
curl http://localhost:8000/api/rates?currency=AUD&tenor=5Y&start_date=2024-01-01
```

---

## 🐛 Bug Fixes in v5.1

### Critical Fix: Basis Calculation
**Problem**: Basis was calculated incorrectly showing inverted results
**Solution**: Fixed formula to `Basis = Long - Short`
**Impact**: All basis analysis now shows correct spreads

### Documentation Updates
- Added clear explanations of basis interpretation
- Added visual indicators (green/red)
- Updated all help text and tooltips

---

## 📞 Support

### Known Issues
- Ensure Python 3.8+ installed
- SQLite comes with Python (no separate install)
- Large Excel files (>100MB) may take time to import

### Tips
- Use date filters for faster queries
- Export large datasets to CSV for Excel analysis
- Backup database before bulk imports

---

## 🎓 Educational Resources

### Swap Basics
- **Fixed-for-Floating**: Exchange fixed rate for floating rate
- **Tenor**: Time to maturity (e.g., 5Y = 5 years)
- **Floating Rate**: Reference rate (e.g., 3M BBSW)
- **Basis**: Spread between different floating rates

### Basis Trading
- **Positive Basis**: Long tenor expensive vs short tenor
- **Negative Basis**: Long tenor cheap vs short tenor
- **Basis Widening**: Spread increases
- **Basis Narrowing**: Spread decreases

---

## 📄 License

Rate Edge v5.1 - Professional IRS Swap Analytics Platform
© 2025 All Rights Reserved

---

## 🔄 Version History

**v5.1** (November 2025)
- ✅ FIXED: Basis calculation corrected
- ✅ Added 128K production database records
- ✅ Improved documentation
- ✅ Enhanced user interface

**v5.0** (October 2025)
- Multi-currency support (7 currencies)
- 9 analysis tools
- Web + Desktop versions
- REST API
- PDF reports

---

**Ready to analyze swap rates professionally!** 🚀

For questions or support, refer to the documentation or check the example code.
