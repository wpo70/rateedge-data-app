import sqlite3
import csv
conn = sqlite3.connect('swap_rates.db')
c = conn.execute("SELECT date, currency, tenor, floating_rate, rate FROM swap_rates WHERE currency='AUD' AND floating_rate='3M BBSW'")
rows = list(c)
print(f"Total rows: {len(rows)}")
with open('aud_3m_bbsw_export.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['date','currency','tenor','floating_rate','rate'])
    w.writerows(rows)
print("Exported to aud_3m_bbsw_export.csv")
