import sqlite3
conn = sqlite3.connect('swap_rates.db')
c = conn.execute("SELECT floating_rate, COUNT(*) FROM swap_rates WHERE currency='AUD' AND floating_rate IN ('3M BBSW', '6M BBSW') GROUP BY floating_rate")
for row in c:
    print(row)
