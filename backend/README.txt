================================================================================
RATEEDGE v8.1 - IMPORT BUTTONS ON TABS
================================================================================

NEW FEATURE: Dedicated import buttons on each tab!

✓ Benchmark Tab → "Import Benchmark Data" button
✓ OIS Tab → "Import OIS Data" button

No more searching through menus - the button is right where you need it!

================================================================================
INSTALLATION:
================================================================================

1. Copy files to your RateEdge folder:
   - frontend/swap_rate_gui.py → Replace existing
   - backend/market_data_importer.py → Add (if not already there)

2. Delete frontend/__pycache__

3. Restart RateEdge

================================================================================
HOW TO USE:
================================================================================

IMPORT BENCHMARK DATA (BBSW, BKBM, RBA, RBNZ):
-----------------------------------------------
1. Go to "Central Bank & Benchmark Rates" tab
2. Click "📥 Import Benchmark Data" button (top right)
3. Select Excel files with BBSW, BKBM, RBA, or RBNZ data
4. Import starts automatically
5. Watch progress in real-time
6. Click "Close" when done

IMPORT OIS DATA (AONIA, SOFR, SONIA, etc.):
--------------------------------------------
1. Go to "OIS Rates" tab
2. Click "📥 Import OIS Data" button (top right)
3. Select Excel files with AONIA (or other OIS) data
4. Import starts automatically
5. Watch progress in real-time
6. Click "Close" when done

================================================================================
FILE FORMAT REQUIREMENTS:
================================================================================

ALL files must have:
- Column: "Date"
- Column: "Rate"

Filename must contain keywords:

OIS FILES:
- AONIA + tenor (e.g., "AONIA 3M", "AONIA 5Y")
- SOFR + tenor
- SONIA + tenor
- ESTR + tenor
- CORRA + tenor
- OCR + tenor

BENCHMARK FILES:
- BBSW + tenor (e.g., "BBSW 3M", "BBSW 6M")
- BKBM + tenor (e.g., "BKBM 3M")
- RBA or "Cash Rate" (for RBA cash rate)
- RBNZ or OCR (for RBNZ official cash rate)

================================================================================
EXAMPLE FILENAMES THAT WORK:
================================================================================

✓ "2025-11-14 AONIA 3M Historical Swap Rates - BlueGamma.xlsx"
✓ "AONIA 5Y.xlsx"
✓ "BBSW 3M Historical - BlueGamma.xlsx"
✓ "BBSW_6M_Data.xlsx"
✓ "RBA Cash Rate Historical - BlueGamma.xlsx"
✓ "RBA_Cash_Rate.xlsx"
✓ "RBNZ OCR Historical.xlsx"
✓ "BKBM 3M.xlsx"

The importer extracts the important keywords from any filename format.

================================================================================
FEATURES:
================================================================================

✓ Import button on each tab (no menu navigation)
✓ Multi-select files (Ctrl+Click or Shift+Click)
✓ Auto-detects data type from filename
✓ Auto-detects tenor from filename
✓ Auto-converts percentage to decimal (3.6 → 0.036)
✓ Real-time progress display
✓ Shows file-by-file status
✓ Skips duplicates automatically
✓ Detailed error messages
✓ Auto-refreshes tab after import
✓ Import starts automatically (no extra "Start" button)

================================================================================
IMPROVED USER EXPERIENCE:
================================================================================

v8.0: File → Import Market Data Files → Select files → Start
v8.1: Go to tab → Click Import button → Select files → Auto-starts

Fewer clicks, more intuitive!

================================================================================
MULTI-FILE IMPORT:
================================================================================

You can select 50+ files at once:

1. Click "Import OIS Data"
2. Navigate to folder with all your AONIA files
3. Select first file
4. Hold Shift + Click last file (selects all between)
5. Or hold Ctrl + Click individual files
6. Import processes all automatically

Perfect for bulk historical imports or daily updates!

================================================================================
DAILY WORKFLOW:
================================================================================

Every morning:
1. Download today's data from your provider
2. Open RateEdge
3. Go to Benchmark tab
4. Click "Import Benchmark Data"
5. Select today's BBSW/RBA files
6. Done in 30 seconds

No scripts, no command line, no hassle!

================================================================================
STILL WORKS WITH YOUR CURRENT FILES:
================================================================================

✓ Your current Excel downloads work perfectly
✓ No need to rename files
✓ As long as filename contains keywords (AONIA, BBSW, etc.)
✓ Both "BlueGamma" files and custom filenames work
✓ Handles spaces, dashes, underscores in filenames

================================================================================
