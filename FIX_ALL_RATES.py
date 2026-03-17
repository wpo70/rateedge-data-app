#!/usr/bin/env python3
"""
FIX ALL RATES IN DATABASE
Convert any rates in percentage format to decimal format
This fixes the Forward Swap Calculator and all other calculators
"""

import sqlite3
import os

# EDIT THIS PATH TO YOUR DATABASE
DATABASE_PATH = r'C:\Users\willp\IRS_DATA_Manager\RateEdge_v7.2_FINAL\database\swap_rates.db'

if not os.path.exists(DATABASE_PATH):
    print(f"Database not found at: {DATABASE_PATH}")
    print("\nPlease edit this script and set DATABASE_PATH to your actual database location.")
    input("Press Enter to exit...")
    exit(1)

conn = sqlite3.connect(DATABASE_PATH)
cursor = conn.cursor()

print("="*80)
print("FIX ALL RATES IN DATABASE")
print("="*80)
print()

# Check current state
print("STEP 1: Checking current state...")
print()

# Count rates that need fixing (rate > 1 means percentage format)
cursor.execute("SELECT COUNT(*) FROM swap_rates WHERE rate > 1")
bad_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM swap_rates WHERE rate <= 1 AND rate > 0")
good_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM swap_rates")
total_count = cursor.fetchone()[0]

print(f"Total records: {total_count:,}")
print(f"Records in DECIMAL format (0.036 = 3.6%): {good_count:,}")
print(f"Records in PERCENTAGE format (3.6 = 3.6%): {bad_count:,}")
print()

if bad_count == 0:
    print("✓ All rates are already in decimal format!")
    print("  Your database is correct.")
    print()
    print("If calculators are still broken, the issue is elsewhere.")
    conn.close()
    input("Press Enter to exit...")
    exit(0)

# Show examples of bad data
print("EXAMPLES OF RATES THAT WILL BE FIXED:")
cursor.execute("""
    SELECT date, currency, tenor, floating_rate, rate 
    FROM swap_rates 
    WHERE rate > 1 
    ORDER BY date DESC 
    LIMIT 10
""")
examples = cursor.fetchall()
for date, currency, tenor, floating_rate, rate in examples:
    fixed_rate = rate / 100
    print(f"  {date} {currency:3s} {tenor:4s} {floating_rate:10s}: {rate:8.4f} → {fixed_rate:8.6f}")

print()
print("="*80)
print("WARNING")
print("="*80)
print()
print(f"This will update {bad_count:,} records.")
print("All rates > 1 will be divided by 100.")
print()
print("Example: 3.6000 → 0.0360")
print()
print("This CANNOT be undone. Make a database backup first if unsure.")
print()
print("="*80)

response = input("Type 'FIX' to proceed, or anything else to cancel: ")

if response.strip().upper() != 'FIX':
    print("\nCancelled. No changes made.")
    conn.close()
    input("Press Enter to exit...")
    exit(0)

print()
print("STEP 2: Fixing rates...")
print()

# Update all rates > 1 by dividing by 100
cursor.execute("""
    UPDATE swap_rates 
    SET rate = rate / 100 
    WHERE rate > 1
""")

updated = cursor.rowcount

conn.commit()

print(f"✓ Updated {updated:,} records")
print()

# Verify
print("STEP 3: Verifying fix...")
print()

cursor.execute("SELECT COUNT(*) FROM swap_rates WHERE rate > 1")
remaining_bad = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM swap_rates WHERE rate <= 1 AND rate > 0")
now_good = cursor.fetchone()[0]

print(f"Records now in DECIMAL format: {now_good:,}")
print(f"Records still in PERCENTAGE format: {remaining_bad:,}")
print()

if remaining_bad == 0:
    print("✓ SUCCESS! All rates are now in decimal format.")
    print()
    print("EXAMPLES OF FIXED RATES:")
    cursor.execute("""
        SELECT date, currency, tenor, floating_rate, rate 
        FROM swap_rates 
        WHERE floating_rate IN ('AONIA', 'BBSW', 'BKBM', 'RBA', 'RBNZ')
        ORDER BY date DESC 
        LIMIT 10
    """)
    fixed_examples = cursor.fetchall()
    for date, currency, tenor, floating_rate, rate in fixed_examples:
        print(f"  {date} {currency:3s} {tenor:4s} {floating_rate:10s}: {rate:8.6f}")
else:
    print(f"⚠ Warning: {remaining_bad:,} records are still > 1")
    print("  These might be intentional or there may be an issue.")

conn.close()

print()
print("="*80)
print("FIX COMPLETE")
print("="*80)
print()
print("NOW TEST:")
print("1. Restart RateEdge")
print("2. Check Forward Swap Calculator")
print("3. Rates should be normal (3.6, not 363)")
print()
print("="*80)

input("Press Enter to exit...")
