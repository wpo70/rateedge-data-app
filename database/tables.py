import sqlite3
conn = sqlite3.connect('swap_rates.db')
c = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
for row in c:
    print(row[0])
