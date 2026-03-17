#!/usr/bin/env python3
"""
Check what format rates are stored in the database
This will help identify if old data is in decimal (0.036) vs new data in percentage (3.6)
"""

import sqlite3
import os

# EDIT THIS PATH TO YOUR DATABASE
DATABASE_PATH = r'C:\Users\willp\IRS_DATA_Manager\RateEdge_v7.2_FINAL\database\swap_rates.db'

if not os.path.exists(DATABASE_PATH):
    print(f"Database not found at: {DATABASE_PATH}")
    print("\nPlease edit CHECK_RATE_FORMAT.py and set DATABASE_PATH to your actual database location.")
    input("Press Enter to exit...")
    exit(1)

conn = sqlite3.connect(DATABASE_PATH)
cursor = conn.cursor()

print("="*80)
print("CHECKING RATE FORMAT IN DATABASE")
print("="*80)
print()

# Check AONIA rates (OIS - newly imported)
print("AONIA RATES (OIS - Recently Imported):")
cursor.execute("""
    SELECT date, tenor, rate 
    FROM swap_rates 
    WHERE floating_rate = 'AONIA' 
    ORDER BY date DESC, tenor 
    LIMIT 5
""")
aonia_rows = cursor.fetchall()
if aonia_rows:
    for date, tenor, rate in aonia_rows:
        print(f"  {date} {tenor:4s}: {rate:.4f}")
else:
    print("  No AONIA data found")

print()

# Check BBSW rates (Benchmark - newly imported)
print("BBSW RATES (Benchmark - Recently Imported):")
cursor.execute("""
    SELECT date, tenor, rate 
    FROM swap_rates 
    WHERE floating_rate = 'BBSW' 
    ORDER BY date DESC, tenor 
    LIMIT 5
""")
bbsw_rows = cursor.fetchall()
if bbsw_rows:
    for date, tenor, rate in bbsw_rows:
        print(f"  {date} {tenor:4s}: {rate:.4f}")
else:
    print("  No BBSW data found")

print()

# Check old swap rates (should be decimal format 0.036)
print("OLD SWAP RATES (3M tenor, various currencies):")
cursor.execute("""
    SELECT date, currency, floating_rate, rate 
    FROM swap_rates 
    WHERE tenor = '3M' 
    AND floating_rate NOT IN ('AONIA', 'BBSW', 'BKBM', 'RBA', 'RBNZ')
    ORDER BY date DESC 
    LIMIT 5
""")
old_rows = cursor.fetchall()
if old_rows:
    for date, currency, floating_rate, rate in old_rows:
        print(f"  {date} {currency} {floating_rate:10s}: {rate:.6f}")
else:
    print("  No old swap data found")

print()
print("="*80)
print("ANALYSIS:")
print("="*80)
print()

# Determine format
if aonia_rows:
    sample_rate = aonia_rows[0][2]
    if sample_rate > 1:
        print("AONIA rates are in PERCENTAGE format (e.g., 3.6000 = 3.6%)")
    else:
        print("AONIA rates are in DECIMAL format (e.g., 0.036 = 3.6%)")

if bbsw_rows:
    sample_rate = bbsw_rows[0][2]
    if sample_rate > 1:
        print("BBSW rates are in PERCENTAGE format (e.g., 3.6000 = 3.6%)")
    else:
        print("BBSW rates are in DECIMAL format (e.g., 0.036 = 3.6%)")

if old_rows:
    sample_rate = old_rows[0][3]
    if sample_rate > 1:
        print("OLD swap rates are in PERCENTAGE format (e.g., 3.6000 = 3.6%)")
    else:
        print("OLD swap rates are in DECIMAL format (e.g., 0.036 = 3.6%)")

print()
print("="*80)
print("RECOMMENDATION:")
print("="*80)
print()
print("If old data is DECIMAL and new data is PERCENTAGE:")
print("  → Need to divide new data by 100")
print("  → OR multiply old data by 100")
print()
print("The Forward Swap Calculator expects ALL rates in the same format.")
print()

conn.close()
input("Press Enter to exit...")
