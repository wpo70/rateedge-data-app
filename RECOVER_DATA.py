#!/usr/bin/env python3
"""
EMERGENCY DATA RECOVERY
This script will find your old database and copy all data to the new location
"""

import os
import sqlite3
import shutil
from datetime import datetime

print("="*80)
print("RATEEDGE DATA RECOVERY TOOL")
print("="*80)
print()

# Possible locations for old database
possible_locations = [
    r'C:\Users\willp\IRS_DATA_Manager\latest RateEdge 13112025\RateEdge_v7.1\database\swap_rates.db',
    r'C:\Users\willp\IRS_DATA_Manager\RateEdge_v7.1\database\swap_rates.db',
    r'C:\Users\willp\IRS_DATA_Manager\RateEdge_v7.0\database\swap_rates.db',
]

# Current location (where script is)
current_db = os.path.join(os.path.dirname(__file__), 'database', 'swap_rates.db')

print(f"Current database location: {current_db}")
print()

# Check current database size
if os.path.exists(current_db):
    size = os.path.getsize(current_db) / (1024 * 1024)  # MB
    print(f"Current database size: {size:.2f} MB")
    
    conn = sqlite3.connect(current_db)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM swap_rates")
    count = cursor.fetchone()[0]
    conn.close()
    print(f"Current database records: {count:,}")
else:
    print("Current database does not exist yet")
print()

# Find old database
print("Searching for old database with your 7.5 years of data...")
print()

old_db = None
for location in possible_locations:
    if os.path.exists(location):
        size = os.path.getsize(location) / (1024 * 1024)  # MB
        
        conn = sqlite3.connect(location)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM swap_rates")
            count = cursor.fetchone()[0]
            conn.close()
            
            print(f"✓ FOUND: {location}")
            print(f"  Size: {size:.2f} MB")
            print(f"  Records: {count:,}")
            
            if count > 1000:  # Assume this is the good one
                old_db = location
                print(f"  → This looks like your main database!")
                break
        except:
            conn.close()
            print(f"  - {location} (not a valid database)")

print()

if not old_db:
    print("Could not automatically find your old database.")
    print()
    print("Please manually enter the full path to your old database file:")
    print("Example: C:\\Users\\willp\\IRS_DATA_Manager\\RateEdge_v7.1\\database\\swap_rates.db")
    old_db = input("Path: ").strip()
    
    if not os.path.exists(old_db):
        print(f"✗ File not found: {old_db}")
        print()
        print("Please find your swap_rates.db file manually and run this script again.")
        input("Press Enter to exit...")
        exit(1)

print("="*80)
print("RECOVERY OPTIONS")
print("="*80)
print()
print("1. REPLACE current database with old database")
print("   (Recommended if current database is empty or has only test data)")
print()
print("2. MERGE old database INTO current database")
print("   (Use if you want to keep both)")
print()
print("3. Just show me the path to my old database")
print()

choice = input("Enter choice (1, 2, or 3): ").strip()

if choice == "1":
    # Backup current if it exists
    if os.path.exists(current_db):
        backup = current_db + f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(current_db, backup)
        print(f"✓ Backed up current database to: {backup}")
    
    # Copy old to current
    os.makedirs(os.path.dirname(current_db), exist_ok=True)
    shutil.copy2(old_db, current_db)
    print(f"✓ Copied old database to: {current_db}")
    
    # Verify
    conn = sqlite3.connect(current_db)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM swap_rates")
    count = cursor.fetchone()[0]
    conn.close()
    
    print(f"✓ Verified: {count:,} records in current database")
    print()
    print("="*80)
    print("RECOVERY COMPLETE")
    print("="*80)
    print()
    print("Your 7.5 years of data has been restored!")
    print("You can now run RateEdge normally.")

elif choice == "2":
    print()
    print("Merging databases...")
    
    # Connect to both
    old_conn = sqlite3.connect(old_db)
    new_conn = sqlite3.connect(current_db)
    
    # Get all data from old
    old_cursor = old_conn.cursor()
    old_cursor.execute("SELECT date, currency, tenor, rate, floating_rate FROM swap_rates")
    rows = old_cursor.fetchall()
    
    # Insert into new
    new_cursor = new_conn.cursor()
    imported = 0
    duplicates = 0
    
    for row in rows:
        try:
            new_cursor.execute(
                "INSERT INTO swap_rates (date, currency, tenor, rate, floating_rate) VALUES (?, ?, ?, ?, ?)",
                row
            )
            imported += 1
        except sqlite3.IntegrityError:
            duplicates += 1
    
    new_conn.commit()
    
    old_conn.close()
    new_conn.close()
    
    print(f"✓ Imported: {imported:,} records")
    print(f"✓ Duplicates skipped: {duplicates:,}")
    print()
    print("="*80)
    print("MERGE COMPLETE")
    print("="*80)

elif choice == "3":
    print()
    print("="*80)
    print(f"Your old database is located at:")
    print(f"{old_db}")
    print("="*80)
    print()
    print("To fix this, either:")
    print("1. Copy this file to your new RateEdge location, OR")
    print("2. Run this script again and choose option 1 or 2")

else:
    print("Invalid choice")

print()
input("Press Enter to exit...")
