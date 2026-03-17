import sqlite3
import csv

conn = sqlite3.connect('swap_rates.db')

# Delete and import 6M BBSW
conn.execute("DELETE FROM swap_rates WHERE currency='AUD' AND floating_rate='6M BBSW'")
with open('C:/Users/willp/Downloads/aud_6m_bbsw_complete.csv', 'r') as f:
    reader = csv.DictReader(f)
    rows = [(r['date'], r['currency'], r['tenor'], r['floating_rate'], float(r['rate'])) for r in reader]
conn.executemany("INSERT INTO swap_rates (date, currency, tenor, floating_rate, rate) VALUES (?, ?, ?, ?, ?)", rows)
print(f"6M BBSW: {len(rows)} rows imported")

# Delete and import 3M BBSW
conn.execute("DELETE FROM swap_rates WHERE currency='AUD' AND floating_rate='3M BBSW'")
with open('C:/Users/willp/Downloads/aud_3m_bbsw_complete.csv', 'r') as f:
    reader = csv.DictReader(f)
    rows = [(r['date'], r['currency'], r['tenor'], r['floating_rate'], float(r['rate'])) for r in reader]
conn.executemany("INSERT INTO swap_rates (date, currency, tenor, floating_rate, rate) VALUES (?, ?, ?, ?, ?)", rows)
print(f"3M BBSW: {len(rows)} rows imported")

conn.commit()
conn.close()
print("Done!")
