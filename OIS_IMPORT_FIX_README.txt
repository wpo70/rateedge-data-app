================================================================================
FIXED OIS IMPORT SCRIPT - V2
================================================================================

PROBLEM:
Your files weren't being found by the import script.

SOLUTION:
This V2 script:
✓ Lists ALL files in your BlueGamma folder
✓ Shows which AONIA files it found
✓ Better pattern matching
✓ Shows which files it can't match

================================================================================
INSTALLATION:
================================================================================

1. Copy import_ois_complete_v2.py to:
   C:\Users\willp\IRS_DATA_Manager\latest RateEdge 13112025\RateEdge_v7.1\

2. Make sure your AONIA Excel files are in:
   C:\Users\willp\IRS_DATA_Manager\BlueGamma\

3. Run: python import_ois_complete_v2.py

================================================================================
WHAT IT WILL SHOW:
================================================================================

First it lists ALL files it finds:

Found 50 Excel files in folder
Found 11 AONIA files:
  - 2025-11-14_AONIA_1W_Historical_Swap_Rates_-_BlueGamma.xlsx
  - 2025-11-14_AONIA_2W_Historical_Swap_Rates_-_BlueGamma.xlsx
  - 2025-11-14_AONIA_3W_Historical_Swap_Rates_-_BlueGamma.xlsx
  ... etc

Then it imports:

================================================================================
IMPORTING FILES
================================================================================
  ✓ 1W  :  245 new,    0 dups - 2025-11-14_AONIA_1W_...
  ✓ 2W  :  245 new,    0 dups - 2025-11-14_AONIA_2W_...
  ... etc

================================================================================
DEBUGGING:
================================================================================

If you see "Found 0 AONIA files":
→ Your Excel files don't have "AONIA" in the filename
→ Files might be in a different folder
→ Check the folder path is correct

If you see "Could not determine tenor for: filename":
→ The filename doesn't have a recognizable pattern like _1W_, _2M_, etc.
→ Send me the exact filename and I'll add support for it

================================================================================
