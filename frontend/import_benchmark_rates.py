#!/usr/bin/env python3
"""
Central Bank & Benchmark Rates Importer for RateEdge
Imports AUD and NZD benchmark rates from BlueGamma Excel files

AUD RATES:
- RBA Cash Rate Target (Central Bank)
- BBSW 1M, 2M, 3M, 4M, 5M, 6M (Benchmark)

NZD RATES:
- OCR / RBNZ Official Cash Rate (Central Bank)
- BKBM 1M, 2M, 3M (Benchmark)
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

# Rate mapping: file pattern -> (currency, floating_rate, tenor)
RATE_MAPPING = {
    # AUD Central Bank
    'RBA': ('AUD', 'RBA', 'ON'),
    'RBA CASH': ('AUD', 'RBA', 'ON'),
    'RBA_CASH': ('AUD', 'RBA', 'ON'),
    
    # AUD BBSW Benchmarks
    'BBSW 1M': ('AUD', 'BBSW', '1M'),
    'BBSW 2M': ('AUD', 'BBSW', '2M'),
    'BBSW 3M': ('AUD', 'BBSW', '3M'),
    'BBSW 4M': ('AUD', 'BBSW', '4M'),
    'BBSW 5M': ('AUD', 'BBSW', '5M'),
    'BBSW 6M': ('AUD', 'BBSW', '6M'),
    'BBSW_1M': ('AUD', 'BBSW', '1M'),
    'BBSW_2M': ('AUD', 'BBSW', '2M'),
    'BBSW_3M': ('AUD', 'BBSW', '3M'),
    'BBSW_4M': ('AUD', 'BBSW', '4M'),
    'BBSW_5M': ('AUD', 'BBSW', '5M'),
    'BBSW_6M': ('AUD', 'BBSW', '6M'),
    
    # NZD Central Bank
    'OCR': ('NZD', 'RBNZ', 'ON'),
    'RBNZ': ('NZD', 'RBNZ', 'ON'),
    'RBNZ OFFICIAL': ('NZD', 'RBNZ', 'ON'),
    'RBNZ_OFFICIAL': ('NZD', 'RBNZ', 'ON'),
    
    # NZD BKBM Benchmarks
    'BKBM 1M': ('NZD', 'BKBM', '1M'),
    'BKBM 2M': ('NZD', 'BKBM', '2M'),
    'BKBM 3M': ('NZD', 'BKBM', '3M'),
    'BKBM_1M': ('NZD', 'BKBM', '1M'),
    'BKBM_2M': ('NZD', 'BKBM', '2M'),
    'BKBM_3M': ('NZD', 'BKBM', '3M'),
}

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

def import_rate_file(file_path, currency, floating_rate, tenor):
    """Import a single benchmark/central bank rate file"""
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
        
        # Add metadata
        df['Currency'] = currency
        df['Tenor'] = tenor
        df['Floating_Rate'] = floating_rate
        
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
        
        rate_name = f"{currency} {floating_rate} {tenor}"
        print(f"  ✓ {rate_name:20s}: {imported:4d} new, {duplicates:4d} dups")
        return imported
        
    except Exception as e:
        print(f"  ✗ Error importing {os.path.basename(file_path)}: {e}")
        return 0

def match_file_to_rate(filename):
    """Match a filename to a rate type"""
    filename_upper = filename.upper()
    
    # Try to match each pattern
    for pattern, (currency, floating_rate, tenor) in RATE_MAPPING.items():
        pattern_upper = pattern.upper()
        # Look for pattern with spaces or underscores
        if pattern_upper in filename_upper:
            return (currency, floating_rate, tenor)
    
    return None

def find_and_import_files():
    """Find and import all benchmark rate files"""
    if not os.path.exists(BLUEGAMMA_FOLDER):
        print(f"✗ BlueGamma folder not found: {BLUEGAMMA_FOLDER}")
        return
    
    print(f"\n{'='*80}")
    print(f"IMPORTING CENTRAL BANK & BENCHMARK RATES")
    print(f"{'='*80}")
    print(f"Source: {BLUEGAMMA_FOLDER}")
    print(f"Database: {DATABASE_PATH}")
    print()
    
    # Get all Excel files
    all_files = glob.glob(os.path.join(BLUEGAMMA_FOLDER, "*.xlsx"))
    
    # Filter for benchmark files (RBA, BBSW, OCR, RBNZ, BKBM)
    benchmark_files = []
    for f in all_files:
        filename = os.path.basename(f).upper()
        if any(keyword in filename for keyword in ['RBA', 'BBSW', 'OCR', 'RBNZ', 'BKBM']):
            # Exclude AONIA files (those are OIS)
            if 'AONIA' not in filename:
                benchmark_files.append(f)
    
    print(f"Found {len(benchmark_files)} benchmark rate files:")
    for f in benchmark_files:
        print(f"  - {os.path.basename(f)}")
    print()
    
    if not benchmark_files:
        print("✗ No benchmark rate files found!")
        print("\nLooking for files with: RBA, BBSW, OCR, RBNZ, BKBM")
        return
    
    print(f"{'='*80}")
    print("IMPORTING FILES")
    print(f"{'='*80}")
    
    total_imported = 0
    files_imported = 0
    
    for file_path in benchmark_files:
        filename = os.path.basename(file_path)
        rate_info = match_file_to_rate(filename)
        
        if rate_info:
            currency, floating_rate, tenor = rate_info
            imported = import_rate_file(file_path, currency, floating_rate, tenor)
            total_imported += imported
            if imported > 0:
                files_imported += 1
        else:
            print(f"  ? Could not determine rate type for: {filename}")
    
    print()
    print(f"{'='*80}")
    print(f"IMPORT COMPLETE")
    print(f"{'='*80}")
    print(f"Files processed: {len(benchmark_files)}")
    print(f"Files imported: {files_imported}")
    print(f"Total records imported: {total_imported}")
    print()

def show_statistics():
    """Show statistics of imported data"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Count by floating_rate
    print(f"{'='*80}")
    print(f"BENCHMARK RATES STATISTICS")
    print(f"{'='*80}")
    
    # AUD Central Bank
    cursor.execute("SELECT COUNT(*) FROM swap_rates WHERE currency='AUD' AND floating_rate='RBA'")
    rba_count = cursor.fetchone()[0]
    if rba_count > 0:
        cursor.execute("SELECT MIN(date), MAX(date) FROM swap_rates WHERE currency='AUD' AND floating_rate='RBA'")
        date_range = cursor.fetchone()
        print(f"\nAUD CENTRAL BANK (RBA Cash Rate):")
        print(f"  Records: {rba_count:,}")
        print(f"  Date range: {date_range[0]} to {date_range[1]}")
    
    # AUD BBSW
    cursor.execute("SELECT tenor, COUNT(*) FROM swap_rates WHERE currency='AUD' AND floating_rate='BBSW' GROUP BY tenor ORDER BY tenor")
    bbsw_data = cursor.fetchall()
    if bbsw_data:
        print(f"\nAUD BENCHMARK (BBSW):")
        for tenor, count in bbsw_data:
            print(f"  {tenor:3s}: {count:5,} records")
    
    # NZD Central Bank
    cursor.execute("SELECT COUNT(*) FROM swap_rates WHERE currency='NZD' AND floating_rate='RBNZ'")
    rbnz_count = cursor.fetchone()[0]
    if rbnz_count > 0:
        cursor.execute("SELECT MIN(date), MAX(date) FROM swap_rates WHERE currency='NZD' AND floating_rate='RBNZ'")
        date_range = cursor.fetchone()
        print(f"\nNZD CENTRAL BANK (RBNZ Official Cash Rate):")
        print(f"  Records: {rbnz_count:,}")
        print(f"  Date range: {date_range[0]} to {date_range[1]}")
    
    # NZD BKBM
    cursor.execute("SELECT tenor, COUNT(*) FROM swap_rates WHERE currency='NZD' AND floating_rate='BKBM' GROUP BY tenor ORDER BY tenor")
    bkbm_data = cursor.fetchall()
    if bkbm_data:
        print(f"\nNZD BENCHMARK (BKBM):")
        for tenor, count in bkbm_data:
            print(f"  {tenor:3s}: {count:5,} records")
    
    conn.close()
    print(f"{'='*80}")
    print()

def main():
    """Main execution"""
    print(f"\n{'='*80}")
    print(f"RATEEDGE - CENTRAL BANK & BENCHMARK RATES IMPORTER")
    print(f"{'='*80}")
    print()
    
    # Setup database
    setup_database()
    
    # Import files
    find_and_import_files()
    
    # Show statistics
    show_statistics()
    
    print("Import complete. Press Enter to exit...")
    input()

if __name__ == '__main__':
    main()
