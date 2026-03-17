#!/usr/bin/env python3
"""
Complete OIS Data Importer for RateEdge - V2
Imports AONIA (AUD OIS) data from BlueGamma Excel files
More flexible file matching
"""

import os
import sys
import pandas as pd
import sqlite3
from datetime import datetime
import glob

# Configuration
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'database', 'swap_rates.db')
BLUEGAMMA_FOLDER = r'C:\Users\willp\IRS_DATA_Manager\BlueGamma'

# Tenor mapping - more flexible patterns
TENOR_PATTERNS = [
    # Pattern to match, database tenor
    ('1W', '1W'),
    ('2W', '2W'),
    ('3W', '3W'),
    ('1M', '1M'),
    ('2M', '2M'),
    ('3M', '3M'),
    ('4M', '4M'),
    ('5M', '5M'),
    ('6M', '6M'),
    ('9M', '9M'),
    ('12M', '1Y'),   # 12M = 1Y
    ('18M', '18M'),
    ('24M', '2Y'),   # 24M = 2Y
    ('3Y', '3Y'),
    ('4Y', '4Y'),
    ('5Y', '5Y'),
    ('6Y', '6Y'),
    ('7Y', '7Y'),
    ('8Y', '8Y'),
    ('9Y', '9Y'),
    ('10Y', '10Y'),
    ('12Y', '12Y'),
    ('15Y', '15Y'),
    ('20Y', '20Y'),
    ('25Y', '25Y'),
    ('30Y', '30Y'),
    ('35Y', '35Y'),
    ('40Y', '40Y'),
]

def setup_database():
    """Ensure database and table exist"""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS swap_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            currency TEXT NOT NULL,
            tenor TEXT NOT NULL,
            rate REAL NOT NULL,
            floating_rate TEXT NOT NULL,
            fixed_frequency TEXT,
            day_count TEXT,
            business_day_convention TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(date, currency, tenor, floating_rate)
        )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON swap_rates(date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_currency ON swap_rates(currency)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tenor ON swap_rates(tenor)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_floating_rate ON swap_rates(floating_rate)')
    
    conn.commit()
    conn.close()
    print(f"✓ Database setup complete: {DATABASE_PATH}")

def import_aonia_file(file_path, tenor):
    """Import a single AONIA file"""
    try:
        # Read Excel file
        df = pd.read_excel(file_path)
        
        # Check for required columns
        if 'Date' not in df.columns or 'Rate' not in df.columns:
            print(f"  ✗ Missing required columns in {os.path.basename(file_path)}")
            return 0
        
        # Clean data
        df = df[['Date', 'Rate']].copy()
        df = df.dropna()
        
        # Convert date to string format
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
        
        # CRITICAL: Convert percentage to decimal if needed
        # BlueGamma exports rates as percentages (3.6000 = 3.6%)
        # Database expects decimals (0.036 = 3.6%)
        df['Rate'] = df['Rate'].apply(lambda x: x / 100 if x > 1 else x)
        
        # Add currency and tenor
        df['Currency'] = 'AUD'
        df['Tenor'] = tenor
        df['Floating_Rate'] = 'AONIA'
        
        # Connect to database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Import data
        imported = 0
        duplicates = 0
        
        for _, row in df.iterrows():
            try:
                cursor.execute('''
                    INSERT INTO swap_rates (date, currency, tenor, rate, floating_rate)
                    VALUES (?, ?, ?, ?, ?)
                ''', (row['Date'], row['Currency'], row['Tenor'], row['Rate'], row['Floating_Rate']))
                imported += 1
            except sqlite3.IntegrityError:
                duplicates += 1
        
        conn.commit()
        conn.close()
        
        print(f"  ✓ {tenor:4s}: {imported:4d} new, {duplicates:4d} existing (kept) - {os.path.basename(file_path)}")
        return imported
        
    except Exception as e:
        print(f"  ✗ Error importing {os.path.basename(file_path)}: {e}")
        return 0

def find_files_in_folder():
    """Find all AONIA Excel files in the folder"""
    if not os.path.exists(BLUEGAMMA_FOLDER):
        print(f"✗ Folder not found: {BLUEGAMMA_FOLDER}")
        return []
    
    # Get all Excel files
    all_files = glob.glob(os.path.join(BLUEGAMMA_FOLDER, "*.xlsx"))
    
    print(f"\nFound {len(all_files)} Excel files in folder")
    
    # Filter for AONIA files
    aonia_files = []
    for f in all_files:
        filename = os.path.basename(f).upper()
        if 'AONIA' in filename:
            aonia_files.append(f)
    
    print(f"Found {len(aonia_files)} AONIA files:")
    for f in aonia_files:
        print(f"  - {os.path.basename(f)}")
    
    return aonia_files

def match_file_to_tenor(filename):
    """Match a filename to a tenor"""
    filename_upper = filename.upper()
    
    # Try to match each pattern
    for pattern, tenor in TENOR_PATTERNS:
        # Look for pattern with spaces or underscores
        # Files are like: "2025-11-14 AONIA 1W Historical Swap Rates"
        if f' {pattern} ' in filename_upper or f'_{pattern}_' in filename_upper or f'_{pattern}.' in filename_upper or f' {pattern}.' in filename_upper:
            return tenor
    
    return None

def import_all_files():
    """Find and import all AONIA files"""
    print(f"\n{'='*80}")
    print(f"IMPORTING AONIA (AUD OIS) DATA - V2")
    print(f"{'='*80}")
    print(f"Source: {BLUEGAMMA_FOLDER}")
    print(f"Database: {DATABASE_PATH}")
    
    files = find_files_in_folder()
    
    if not files:
        print("\n✗ No AONIA files found!")
        print("\nMake sure files are in the BlueGamma folder and have 'AONIA' in the name.")
        return
    
    print(f"\n{'='*80}")
    print("IMPORTING FILES")
    print(f"{'='*80}")
    
    total_imported = 0
    files_imported = 0
    
    for file_path in files:
        filename = os.path.basename(file_path)
        tenor = match_file_to_tenor(filename)
        
        if tenor:
            imported = import_aonia_file(file_path, tenor)
            total_imported += imported
            if imported > 0:
                files_imported += 1
        else:
            print(f"  ? Could not determine tenor for: {filename}")
    
    print()
    print(f"{'='*80}")
    print(f"IMPORT COMPLETE")
    print(f"{'='*80}")
    print(f"Files processed: {len(files)}")
    print(f"Files imported: {files_imported}")
    print(f"Total records imported: {total_imported}")
    print()

def show_statistics():
    """Show statistics of imported data"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Count AONIA records
    cursor.execute("SELECT COUNT(*) FROM swap_rates WHERE floating_rate = 'AONIA'")
    total = cursor.fetchone()[0]
    
    if total == 0:
        print("No AONIA data in database.")
        conn.close()
        return
    
    # Count by tenor
    cursor.execute("""
        SELECT tenor, COUNT(*) 
        FROM swap_rates 
        WHERE floating_rate = 'AONIA' 
        GROUP BY tenor 
        ORDER BY 
            CASE 
                WHEN tenor LIKE '%W' THEN 1
                WHEN tenor LIKE '%M' THEN 2
                WHEN tenor LIKE '%Y' THEN 3
            END,
            CAST(REPLACE(REPLACE(REPLACE(tenor, 'W', ''), 'M', ''), 'Y', '') AS INTEGER)
    """)
    tenor_counts = cursor.fetchall()
    
    # Date range
    cursor.execute("""
        SELECT MIN(date), MAX(date) 
        FROM swap_rates 
        WHERE floating_rate = 'AONIA'
    """)
    date_range = cursor.fetchone()
    
    conn.close()
    
    print(f"{'='*80}")
    print(f"AONIA DATA STATISTICS")
    print(f"{'='*80}")
    print(f"Total records: {total:,}")
    print(f"Date range: {date_range[0]} to {date_range[1]}")
    print()
    print("Records by tenor:")
    
    # Split into short and long
    short_term = []
    long_term = []
    
    for tenor, count in tenor_counts:
        if tenor in ['1W', '2W', '3W', '1M', '2M', '3M', '4M', '5M', '6M', '9M', '1Y', '18M', '2Y']:
            short_term.append((tenor, count))
        else:
            long_term.append((tenor, count))
    
    if short_term:
        print("  Short Term (0-2Y):")
        for tenor, count in short_term:
            print(f"    {tenor:4s}: {count:5,} records")
    
    if long_term:
        print("\n  Medium/Long Term (3Y+):")
        for tenor, count in long_term:
            print(f"    {tenor:4s}: {count:5,} records")
    
    print(f"{'='*80}")
    print()

def main():
    """Main execution"""
    print(f"\n{'='*80}")
    print(f"RATEEDGE - AONIA (AUD OIS) DATA IMPORTER V2")
    print(f"{'='*80}")
    print()
    
    # Setup database
    setup_database()
    
    # Import files
    import_all_files()
    
    # Show statistics
    show_statistics()
    
    print("Import complete. Press Enter to exit...")
    input()

if __name__ == '__main__':
    main()
