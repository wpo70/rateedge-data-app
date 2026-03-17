import sqlite3
conn = sqlite3.connect('swap_rates.db')

# Fix 6M BBSW rates - divide by 100
conn.execute("UPDATE swap_rates SET rate = rate / 100 WHERE currency='AUD' AND floating_rate='6M BBSW'")
print("Fixed 6M BBSW rates")

# Fix 3M BBSW rates - divide by 100
conn.execute("UPDATE swap_rates SET rate = rate / 100 WHERE currency='AUD' AND floating_rate='3M BBSW'")
print("Fixed 3M BBSW rates")

conn.commit()
conn.close()
print("Done!")
