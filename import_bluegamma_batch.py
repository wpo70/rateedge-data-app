"""
BlueGamma Batch Import Script
Automatically imports all BlueGamma files to RateEdge database
Extracts metadata from filenames and appends new data only
"""
import pandas as pd
import sqlite3
import os
import sys
import glob
from datetime import datetime
import re

class BlueGammaImporter:
    def __init__(self, db_path):
        self.db_path = db_path
        self.imported_count = 0
        self.skipped_count = 0
        self.error_count = 0
        self.total_records = 0
        
    def extract_metadata_from_filename(self, filename):
        """
        Extract currency, tenor, and floating rate from BlueGamma filename
        
        Examples:
        2025-11-13_AONIA_5Y_Historical_Swap_Rates_-_BlueGamma.xlsx
        2025-11-13_3M_BBSW_10Y_Historical_Swap_Rates_-_BlueGamma.xlsx
        2025-11-13_BBSW_3M_10950-Day_History_-_BlueGamma.xlsx
        2025-11-13_OCR_15Y_Historical_Swap_Rates_-_BlueGamma.xlsx
        """
        filename = os.path.basename(filename)
        parts = filename.upper().replace('.XLSX', '').split('_')
        
        currency = None
        tenor = None
        floating_rate = None
        
        # Determine currency
        if 'AONIA' in filename.upper() or 'BBSW' in filename.upper() or 'RBA' in filename.upper():
            currency = 'AUD'
        elif 'OCR' in filename.upper() or 'BKBM' in filename.upper() or 'RBNZ' in filename.upper():
            currency = 'NZD'
        
        # Determine floating rate and tenor
        if 'AONIA' in filename.upper() and '10950-DAY' in filename.upper():
            floating_rate = 'AONIA'
            tenor = '1D'
        elif 'AONIA' in filename.upper():
            floating_rate = 'AONIA'
            # Extract tenor
            for part in parts:
                if re.match(r'^\d+[WDMY]$', part):
                    tenor = part
                    break
        
        elif 'RBA' in filename.upper():
            floating_rate = 'RBA'
            tenor = 'ON'
        
        elif 'RBNZ' in filename.upper():
            floating_rate = 'RBNZ'
            tenor = 'ON'
        
        elif 'BBSW' in filename.upper() and '10950-DAY' in filename.upper():
            # Example: 2025-11-13_BBSW_3M_10950-Day_History
            for part in parts:
                if re.match(r'^\d+M$', part):
                    floating_rate = part
                    tenor = part  # For benchmark rates, tenor = floating_rate
                    break
        
        elif '3M_BBSW' in filename.upper() or '3M' in parts and 'BBSW' in parts:
            floating_rate = '3M'
            # Extract tenor
            for part in parts:
                if re.match(r'^\d+[MY]$', part) and part != '3M':
                    tenor = part
                    break
        
        elif '6M_BBSW' in filename.upper() or '6M' in parts and 'BBSW' in parts:
            floating_rate = '6M'
            # Extract tenor
            for part in parts:
                if re.match(r'^\d+[MY]$', part) and part != '6M':
                    tenor = part
                    break
        
        elif 'BKBM' in filename.upper() and '10950-DAY' in filename.upper():
            for part in parts:
                if re.match(r'^\d+M$', part):
                    floating_rate = part
                    tenor = part
                    break
        
        elif 'BKBM' in filename.upper():
            floating_rate = '3M'
            # Extract tenor
            for part in parts:
                if re.match(r'^\d+[MY]$', part):
                    tenor = part
                    break
        
        elif 'OCR' in filename.upper() and '10950-DAY' in filename.upper():
            floating_rate = 'OCR'
            tenor = '1D'
        
        elif 'OCR' in filename.upper():
            floating_rate = 'OCR'
            # Extract tenor
            for part in parts:
                if re.match(r'^\d+[WDMY]$', part):
                    tenor = part
                    break
        
        return currency, tenor, floating_rate
    
    def get_latest_date(self, currency, tenor, floating_rate):
        """Get the latest date already in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT MAX(date) FROM swap_rates
                WHERE currency = ? AND tenor = ? AND floating_rate = ?
            """, (currency, tenor, floating_rate))
            
            result = cursor.fetchone()[0]
            conn.close()
            return result
        except:
            return None
    
    def import_file(self, filepath):
        """Import a single BlueGamma file"""
        filename = os.path.basename(filepath)
        print(f"\n{'='*70}")
        print(f"Processing: {filename}")
        print(f"{'='*70}")
        
        # Extract metadata
        currency, tenor, floating_rate = self.extract_metadata_from_filename(filename)
        
        if not currency or not tenor or not floating_rate:
            print(f"❌ Could not extract metadata")
            print(f"   Currency: {currency}, Tenor: {tenor}, Floating: {floating_rate}")
            self.error_count += 1
            return
        
        print(f"Currency: {currency}")
        print(f"Tenor: {tenor}")
        print(f"Floating Rate: {floating_rate}")
        
        # Read file
        try:
            df = pd.read_excel(filepath)
            print(f"✅ Read file: {len(df)} rows")
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            self.error_count += 1
            return
        
        # Check structure
        if len(df.columns) < 2:
            print(f"❌ File must have at least 2 columns (Date, Rate)")
            self.error_count += 1
            return
        
        # Get latest date in database
        latest_date = self.get_latest_date(currency, tenor, floating_rate)
        
        if latest_date:
            print(f"Latest in DB: {latest_date}")
            # Filter to only new data
            df['Date'] = pd.to_datetime(df.iloc[:, 0])
            df_new = df[df['Date'] > pd.to_datetime(latest_date)]
            print(f"New records: {len(df_new)}")
        else:
            print(f"No existing data - importing all")
            df_new = df.copy()
            df_new['Date'] = pd.to_datetime(df.iloc[:, 0])
        
        if len(df_new) == 0:
            print(f"ℹ️  No new data to import")
            self.skipped_count += 1
            return
        
        # Import to database
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            imported = 0
            for _, row in df_new.iterrows():
                date = row['Date'].strftime('%Y-%m-%d')
                rate = float(row.iloc[1])
                
                cursor.execute("""
                    INSERT OR REPLACE INTO swap_rates
                    (date, currency, tenor, floating_rate, rate)
                    VALUES (?, ?, ?, ?, ?)
                """, (date, currency, tenor, floating_rate, rate))
                imported += 1
            
            conn.commit()
            conn.close()
            
            print(f"✅ Imported {imported} records")
            self.imported_count += 1
            self.total_records += imported
            
        except Exception as e:
            print(f"❌ Error importing: {e}")
            self.error_count += 1
            import traceback
            traceback.print_exc()
    
    def import_directory(self, directory):
        """Import all BlueGamma files from directory"""
        print("\n" + "="*70)
        print("BLUEGAMMA BATCH IMPORT")
        print("="*70)
        print(f"Directory: {directory}")
        print(f"Database: {self.db_path}")
        print()
        
        # Find all xlsx files
        pattern = os.path.join(directory, "*.xlsx")
        files = glob.glob(pattern)
        
        if len(files) == 0:
            print(f"❌ No .xlsx files found in {directory}")
            return
        
        print(f"Found {len(files)} Excel files\n")
        
        # Process each file
        for filepath in sorted(files):
            self.import_file(filepath)
        
        # Summary
        print("\n" + "="*70)
        print("IMPORT COMPLETE")
        print("="*70)
        print(f"✅ Successfully imported: {self.imported_count} files")
        print(f"ℹ️  Skipped (no new data): {self.skipped_count} files")
        print(f"❌ Errors: {self.error_count} files")
        print(f"📊 Total new records: {self.total_records}")
        print("="*70)


def main():
    if len(sys.argv) < 2:
        print("Usage: python import_bluegamma_batch.py <directory_with_xlsx_files>")
        print("\nOr place this script in RateEdge_v7.1 folder and run:")
        print("  python import_bluegamma_batch.py /path/to/bluegamma/files")
        sys.exit(1)
    
    # Get directory
    source_dir = sys.argv[1]
    
    if not os.path.exists(source_dir):
        print(f"❌ Directory not found: {source_dir}")
        sys.exit(1)
    
    # Get database path
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'swap_rates.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        print("Make sure this script is in the RateEdge_v7.1 folder!")
        sys.exit(1)
    
    # Run import
    importer = BlueGammaImporter(db_path)
    importer.import_directory(source_dir)


if __name__ == '__main__':
    main()
