#!/usr/bin/env python3
"""
Delete Incorrectly Imported Data
This removes AONIA, BBSW, BKBM, RBA, RBNZ data that was imported in percentage format
Then you can re-import with the fixed scripts that convert to decimal
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
print("DELETE INCORRECTLY IMPORTED DATA")
print("="*80)
print()

# Check what will be deleted
print("CHECKING what will be deleted...")
print()

floating_rates_to_delete = ['AONIA', 'BBSW', 'BKBM', 'RBA', 'RBNZ']

for floating_rate in floating_rates_to_delete:
    cursor.execute("SELECT COUNT(*) FROM swap_rates WHERE floating_rate = ?", (floating_rate,))
    count = cursor.fetchone()[0]
    if count > 0:
        cursor.execute("SELECT MIN(date), MAX(date) FROM swap_rates WHERE floating_rate = ?", (floating_rate,))
        date_range = cursor.fetchone()
        print(f"  {floating_rate:10s}: {count:6,} records ({date_range[0]} to {date_range[1]})")

print()
print("="*80)
print("WARNING")
print("="*80)
print()
print("This will DELETE all data for:")
for fr in floating_rates_to_delete:
    print(f"  - {fr}")
print()
print("You will need to RE-IMPORT this data using the fixed import scripts")
print("that convert percentage format to decimal format.")
print()
print("="*80)

response = input("Type 'DELETE' to proceed, or anything else to cancel: ")

if response.strip().upper() != 'DELETE':
    print("\nCancelled. No data was deleted.")
    conn.close()
    input("Press Enter to exit...")
    exit(0)

print()
print("Deleting data...")
print()

total_deleted = 0

for floating_rate in floating_rates_to_delete:
    cursor.execute("DELETE FROM swap_rates WHERE floating_rate = ?", (floating_rate,))
    deleted = cursor.rowcount
    if deleted > 0:
        print(f"  ✓ Deleted {deleted:,} {floating_rate} records")
        total_deleted += deleted

conn.commit()
conn.close()

print()
print("="*80)
print("DELETION COMPLETE")
print("="*80)
print(f"Total records deleted: {total_deleted:,}")
print()
print("NOW YOU CAN:")
print("1. Run import_ois_complete_v2.py to re-import AONIA data")
print("2. Run import_benchmark_rates.py to re-import BBSW/BKBM/RBA/RBNZ data")
print()
print("The fixed import scripts will automatically convert percentage to decimal.")
print()
print("="*80)

input("Press Enter to exit...")
