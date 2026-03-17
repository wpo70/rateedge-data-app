import sqlite3
import csv
conn = sqlite3.connect('swap_rates.db')

# Export 6M BBSW
c = conn.execute("SELECT date, currency, tenor, floating_rate, rate FROM swap_rates WHERE currency='AUD' AND floating_rate='6M BBSW'")
rows = list(c)
print(f"6M BBSW rows: {len(rows)}")

# Check tenors and date range for 6M BBSW
c = conn.execute("SELECT tenor, MIN(date), MAX(date), COUNT(*) FROM swap_rates WHERE currency='AUD' AND floating_rate='6M BBSW' GROUP BY tenor ORDER BY tenor")
for row in c:
    print(f"  {row[0]}: {row[1]} to {row[2]} ({row[3]} rows)")
