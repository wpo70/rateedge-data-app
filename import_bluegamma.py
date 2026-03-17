"""
BlueGamma Batch Import Script - ULTIMATE FIX
- Handles BOTH spaces AND underscores in filenames
- Normalizes tenors (12M → 1Y, 24M → 2Y)
- Converts basis points to percentage (divides by 100)
- Handles NaT dates
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
        
    def normalize_tenor(self, tenor):
        """Normalize tenor labels: 12M → 1Y, 24M → 2Y, etc."""
        if not tenor:
            return None
            
        tenor_upper = tenor.upper()
        
        # Convert months to years where appropriate
        if tenor_upper == '12M':
            return '1Y'
        elif tenor_upper == '24M':
            return '2Y'
        elif tenor_upper == '18M':
            return '18M'  # Keep as is
        elif tenor_upper == '30M':
            return '30M'  # Keep as is
        else:
            return tenor_upper
    
    def extract_metadata_from_filename(self, filename):
        """Extract currency, tenor, and floating rate - handles SPACES and UNDERSCORES"""
        filename = os.path.basename(filename)
        filename_upper = filename.upper()
        
        # Replace underscores with spaces for easier parsing
        filename_normalized = filename_upper.replace('_', ' ')
        
        currency = None
        tenor = None
        floating_rate = None
        
        # Determine currency
        if 'AONIA' in filename_upper or 'BBSW' in filename_upper or 'RBA' in filename_upper:
            currency = 'AUD'
        elif 'OCR' in filename_upper or 'BKBM' in filename_upper or 'RBNZ' in filename_upper:
            currency = 'NZD'
        
        # Extract tenor - look for patterns like "5Y", "10Y", "3M", "1W", "12M", "18M", etc.
        tenor_match = re.search(r'\b(\d+[WDMY])\b', filename_upper)
        if tenor_match:
            tenor = self.normalize_tenor(tenor_match.group(1))
        
        # Determine floating rate - using normalized filename (spaces instead of underscores)
        if 'AONIA' in filename_normalized and '10950 DAY' in filename_normalized:
            floating_rate = 'AONIA'
            tenor = '1D'
        elif 'AONIA' in filename_normalized:
            floating_rate = 'AONIA'
        
        elif 'RBA' in filename_normalized:
            floating_rate = 'RBA'
            tenor = 'ON'
        
        elif 'RBNZ' in filename_normalized:
            floating_rate = 'RBNZ'
            tenor = 'ON'
        
        elif 'OCR' in filename_normalized and '10950 DAY' in filename_normalized:
            floating_rate = 'OCR'
            tenor = '1D'
        elif 'OCR' in filename_normalized:
            floating_rate = 'OCR'
        
        elif '3M BBSW' in filename_normalized or 'BBSW 3M' in filename_normalized:
            floating_rate = '3M'
        
        elif '6M BBSW' in filename_normalized or 'BBSW 6M' in filename_normalized:
            floating_rate = '6M'
        
        elif 'BBSW' in filename_normalized and '10950 DAY' in filename_normalized:
            # Benchmark: "2025-11-13 BBSW 3M 10950-Day History"
            bbsw_match = re.search(r'BBSW (\d+M)', filename_normalized)
            if bbsw_match:
                floating_rate = bbsw_match.group(1)
                tenor = floating_rate
        
        elif 'BKBM' in filename_normalized and '10950 DAY' in filename_normalized:
            # Benchmark: "2025-11-13 BKBM 3M 10950-Day History"
            bkbm_match = re.search(r'BKBM (\d+M)', filename_normalized)
            if bkbm_match:
                floating_rate = bkbm_match.group(1)
                tenor = floating_rate
        
        elif 'BKBM' in filename_normalized or '3M BKBM' in filename_normalized:
            floating_rate = '3M'
        
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
        
        # Convert dates and remove invalid ones
        df['Date'] = pd.to_datetime(df.iloc[:, 0], errors='coerce')
        
        # Remove rows with NaT (invalid) dates
        df_valid = df[df['Date'].notna()].copy()
        
        if len(df_valid) == 0:
            print(f"⚠️  No valid dates in file - skipping")
            self.skipped_count += 1
            return
        
        if len(df_valid) < len(df):
            print(f"⚠️  Removed {len(df) - len(df_valid)} rows with invalid dates")
        
        # Get latest date in database
        latest_date = self.get_latest_date(currency, tenor, floating_rate)
        
        if latest_date:
            print(f"Latest in DB: {latest_date}")
            df_new = df_valid[df_valid['Date'] > pd.to_datetime(latest_date)]
            print(f"New records: {len(df_new)}")
        else:
            print(f"No existing data - importing all valid rows")
            df_new = df_valid
        
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
                # Skip if date or rate is invalid
                if pd.isna(row['Date']) or pd.isna(row.iloc[1]):
                    continue
                
                date = row['Date'].strftime('%Y-%m-%d')
                raw_rate = float(row.iloc[1])
                
                # Convert from basis points to percentage
                # If rate > 50, it's likely in basis points (e.g., 426.32 bps = 4.2632%)
                if raw_rate > 50:
                    rate = raw_rate / 100.0
                else:
                    rate = raw_rate
                
                cursor.execute("""
                    INSERT OR REPLACE INTO swap_rates
                    (date, currency, tenor, floating_rate, rate)
                    VALUES (?, ?, ?, ?, ?)
                """, (date, currency, tenor, floating_rate, rate))
                imported += 1
            
            conn.commit()
            conn.close()
            
            if imported > 0:
                print(f"✅ Imported {imported} records")
                self.imported_count += 1
                self.total_records += imported
            else:
                print(f"ℹ️  No valid records to import")
                self.skipped_count += 1
            
        except Exception as e:
            print(f"❌ Error importing: {e}")
            self.error_count += 1
            import traceback
            traceback.print_exc()
    
    def import_directory(self, directory):
        """Import all BlueGamma files from directory"""
        print("\n" + "="*70)
        print("BLUEGAMMA BATCH IMPORT - ULTIMATE FIX")
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
    print("="*70)
    print("BLUEGAMMA BATCH IMPORTER - ULTIMATE FIX")
    print("="*70)
    print()
    
    # Get source directory
    if len(sys.argv) > 1:
        source_dir = sys.argv[1]
    else:
        source_dir = input("Enter path to folder with BlueGamma .xlsx files: ").strip('"')
    
    if not os.path.exists(source_dir):
        print(f"❌ Directory not found: {source_dir}")
        sys.exit(1)
    
    # Get database path
    if len(sys.argv) > 2:
        db_path = sys.argv[2]
    else:
        db_path = input("Enter path to swap_rates.db: ").strip('"')
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        sys.exit(1)
    
    # Run import
    importer = BlueGammaImporter(db_path)
    importer.import_directory(source_dir)
    
    print("\n\nPress Enter to exit...")
    input()


if __name__ == '__main__':
    main()
