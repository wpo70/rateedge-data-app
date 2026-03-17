import sqlite3
conn = sqlite3.connect('swap_rates.db')

# Total rows
c = conn.execute("SELECT COUNT(*) FROM swap_rates")
print(f"Total rows in swap_rates: {c.fetchone()[0]}")

# Floating rates
c = conn.execute("SELECT DISTINCT floating_rate FROM swap_rates WHERE currency='AUD'")
print("Floating rates for AUD:")
for row in c:
    print(f"  {row[0]}")

# Check 6M BBSW 4Y data
c = conn.execute("SELECT MIN(date), MAX(date), COUNT(*) FROM swap_rates WHERE currency='AUD' AND floating_rate='6M BBSW' AND tenor='4Y'")
row = c.fetchone()
print(f"\n6M BBSW 4Y: {row[0]} to {row[1]}, count: {row[2]}")
