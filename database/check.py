import sqlite3
conn = sqlite3.connect('swap_rates.db')
c = conn.execute("SELECT tenor, MIN(date), MAX(date), COUNT(tenor) FROM swap_rates WHERE currency='AUD' AND floating_rate='3M BBSW' AND tenor IN ('4Y','5Y','10Y','30Y') GROUP BY tenor")
for row in c:
    print(row)
