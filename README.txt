================================================================================
RATEEDGE WEB - COMPLETE VERSION WITH ALL CALCULATORS
================================================================================

WHAT'S INCLUDED:
✓ Dashboard with quick access to all tools
✓ Swap Rates tab - ALL filters (Currency, Tenor, Floating, Dates, Quick buttons)
✓ Benchmark tab - Currency + Rate Type filters
✓ OIS tab - Currency + Rate Type filters
✓ Import Data - Upload Excel files

ALL 6 CALCULATORS:
✓ Basis Analyzer - 3M vs 6M basis with history charts
✓ Forward Basis Matrix - 6M-3M basis across tenors and forward periods
✓ Forward Swap Matrix - Forward rates across tenors and start periods
✓ Butterfly Analyzer - Calculate and chart butterfly spreads
✓ Basis Spread - Compare basis across multiple tenors
✓ Relative Value - Forward spread analysis for opportunities

================================================================================
INSTALLATION
================================================================================

1. STOP any old app (Ctrl+C in PowerShell)

2. DELETE everything in: C:\Users\willp\IRS_DATA_Manager\RateEdge_v7.2_FINAL\web\

3. EXTRACT this zip and COPY contents of "web" folder to:
   C:\Users\willp\IRS_DATA_Manager\RateEdge_v7.2_FINAL\web\

4. VERIFY file structure:
   web\
     app.py (should be ~18 KB)
     requirements.txt
     templates\
       base.html
       dashboard.html
       login.html
       import.html
       swap_rates.html
       benchmark.html
       ois.html
       calculators\
         basis_analyzer.html
         basis_spread.html
         butterfly_analyzer.html
         forward_basis_matrix.html
         forward_swap_matrix.html
         relative_value.html

5. RUN:
   cd C:\Users\willp\IRS_DATA_Manager\RateEdge_v7.2_FINAL\web
   python app.py

6. OPEN browser:
   http://localhost:5000

7. LOGIN:
   Username: admin
   Password: admin123

8. HARD REFRESH browser (Ctrl+Shift+R)

================================================================================
TESTING CHECKLIST
================================================================================

DATA VIEWING:
☐ Swap Rates - All filters work, table shows data
☐ Benchmark - Filters work
☐ OIS - Filters work
☐ Import - Can upload Excel files

CALCULATORS:
☐ Basis Analyzer - Calculate button shows results, chart loads
☐ Forward Basis Matrix - Generate button creates matrix
☐ Forward Swap Matrix - Generate button creates matrix
☐ Butterfly Analyzer - Calculate button shows results, chart loads
☐ Basis Spread - Load button shows comparison chart
☐ Relative Value - Analyze button shows chart and values

================================================================================
FEATURES
================================================================================

- ALL charts use Chart.js for interactive visualization
- Export to CSV available for matrices
- Date pickers for all analysis tools
- Real-time calculations from your database
- Responsive design works on any screen

================================================================================
