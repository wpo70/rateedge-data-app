================================================================================
CENTRAL BANK & BENCHMARK RATES IMPORT
================================================================================

THIS IS WHAT YOU ASKED FOR:
- Import RBA Cash Rate (AUD Central Bank)
- Import RBNZ Official Cash Rate (NZD Central Bank)
- Import BBSW 1M, 2M, 3M, 4M, 5M, 6M (AUD Benchmark)
- Import BKBM 1M, 2M, 3M (NZD Benchmark)

FROM BLUEGAMMA EXCEL FILES.

NOT TOUCHING OIS TAB.

================================================================================
WHAT FILES TO PUT IN BLUEGAMMA FOLDER:
================================================================================

C:\Users\willp\IRS_DATA_Manager\BlueGamma\

AUD FILES:
- RBA Cash Rate Historical - BlueGamma.xlsx
- BBSW 1M Historical - BlueGamma.xlsx
- BBSW 2M Historical - BlueGamma.xlsx
- BBSW 3M Historical - BlueGamma.xlsx
- BBSW 4M Historical - BlueGamma.xlsx
- BBSW 5M Historical - BlueGamma.xlsx
- BBSW 6M Historical - BlueGamma.xlsx

NZD FILES:
- OCR Historical - BlueGamma.xlsx  (or RBNZ Official Cash Rate)
- BKBM 1M Historical - BlueGamma.xlsx
- BKBM 2M Historical - BlueGamma.xlsx
- BKBM 3M Historical - BlueGamma.xlsx

File format (same as your AONIA files):
- Column 1: Date
- Column 2: Rate

================================================================================
INSTALLATION:
================================================================================

1. Copy import_benchmark_rates.py to:
   C:\Users\willp\IRS_DATA_Manager\RateEdge_v7.2_FINAL\

2. Put your benchmark Excel files in:
   C:\Users\willp\IRS_DATA_Manager\BlueGamma\

3. Run: python import_benchmark_rates.py

================================================================================
WHAT YOU'LL SEE:
================================================================================

Found 10 benchmark rate files:
  - RBA Cash Rate Historical - BlueGamma.xlsx
  - BBSW 1M Historical - BlueGamma.xlsx
  - BBSW 2M Historical - BlueGamma.xlsx
  - BBSW 3M Historical - BlueGamma.xlsx
  - BBSW 4M Historical - BlueGamma.xlsx
  - BBSW 5M Historical - BlueGamma.xlsx
  - BBSW 6M Historical - BlueGamma.xlsx
  - OCR Historical - BlueGamma.xlsx
  - BKBM 1M Historical - BlueGamma.xlsx
  - BKBM 2M Historical - BlueGamma.xlsx
  - BKBM 3M Historical - BlueGamma.xlsx

================================================================================
IMPORTING FILES
================================================================================
  ✓ AUD RBA ON        :  500 new,    0 dups
  ✓ AUD BBSW 1M       :  245 new,    0 dups
  ✓ AUD BBSW 2M       :  245 new,    0 dups
  ✓ AUD BBSW 3M       :  245 new,    0 dups
  ✓ AUD BBSW 4M       :  245 new,    0 dups
  ✓ AUD BBSW 5M       :  245 new,    0 dups
  ✓ AUD BBSW 6M       :  245 new,    0 dups
  ✓ NZD RBNZ ON       :  500 new,    0 dups
  ✓ NZD BKBM 1M       :  245 new,    0 dups
  ✓ NZD BKBM 2M       :  245 new,    0 dups
  ✓ NZD BKBM 3M       :  245 new,    0 dups

================================================================================
IMPORT COMPLETE
================================================================================
Files processed: 11
Files imported: 11
Total records imported: 2,960

================================================================================
BENCHMARK RATES STATISTICS
================================================================================

AUD CENTRAL BANK (RBA Cash Rate):
  Records: 500
  Date range: 2023-01-15 to 2025-11-14

AUD BENCHMARK (BBSW):
  1M :   245 records
  2M :   245 records
  3M :   245 records
  4M :   245 records
  5M :   245 records
  6M :   245 records

NZD CENTRAL BANK (RBNZ Official Cash Rate):
  Records: 500
  Date range: 2023-01-15 to 2025-11-14

NZD BENCHMARK (BKBM):
  1M :   245 records
  2M :   245 records
  3M :   245 records

================================================================================
THEN IN RATEEDGE:
================================================================================

Go to Benchmark tab → Click "📊 Table View"

You'll see:
Date        Cur  O/N     1M      2M      3M      4M      5M      6M
2025-11-14  AUD  3.6000  3.5450  3.6080  3.6335  3.7025  3.8025  3.8832
2025-11-14  NZD  2.5000  2.5200  2.4700  2.4800

================================================================================
NOTES:
================================================================================

- This script ONLY imports benchmark rates
- DOES NOT touch OIS data
- Central bank rates go in as ON (overnight)
- BBSW/BKBM rates go in with their tenors (1M, 2M, etc.)

================================================================================
