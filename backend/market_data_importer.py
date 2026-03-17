"""
Market Data Importer
Handles import of AONIA OIS and Benchmark rates from Excel files
"""

import pandas as pd
import sqlite3
import os
from datetime import datetime

class MarketDataImporter:
    """Import market data Excel files"""
    
    def __init__(self, database_path):
        self.database_path = database_path
        
    def import_file(self, file_path, data_type='auto'):
        """
        Import a single market data Excel file
        
        Args:
            file_path: Path to Excel file
            data_type: 'ois', 'benchmark', or 'auto' (detect from filename)
        
        Returns:
            dict with success, records_imported, duplicates, error
        """
        try:
            filename = os.path.basename(file_path)
            
            # Auto-detect data type from filename
            if data_type == 'auto':
                if 'AONIA' in filename.upper():
                    data_type = 'ois'
                elif any(x in filename.upper() for x in ['BBSW', 'BKBM', 'RBA', 'RBNZ', 'OCR', 'CASH']):
                    data_type = 'benchmark'
                else:
                    return {
                        'success': False,
                        'error': 'Cannot detect data type from filename. Use AONIA for OIS or BBSW/BKBM/RBA/RBNZ for benchmarks.'
                    }
            
            if data_type == 'ois':
                return self._import_ois(file_path, filename)
            else:
                return self._import_benchmark(file_path, filename)
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _import_ois(self, file_path, filename):
        """Import AONIA OIS data"""
        try:
            # Extract tenor from filename
            tenor = self._extract_tenor(filename)
            if not tenor:
                return {
                    'success': False,
                    'error': f'Cannot extract tenor from filename: {filename}'
                }
            
            # Read Excel
            df = pd.read_excel(file_path)
            
            # Check columns
            if 'Date' not in df.columns or 'Rate' not in df.columns:
                return {
                    'success': False,
                    'error': 'Excel file must have Date and Rate columns'
                }
            
            # Clean data
            df = df[['Date', 'Rate']].copy()
            df = df.dropna()
            
            # Convert date
            df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
            
            # CRITICAL: Convert percentage to decimal
            df['Rate'] = df['Rate'].apply(lambda x: x / 100 if x > 1 else x)
            
            # Add metadata
            df['Currency'] = 'AUD'
            df['Tenor'] = tenor
            df['Floating_Rate'] = 'AONIA'
            
            # Import to database
            return self._insert_data(df)
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _import_benchmark(self, file_path, filename):
        """Import benchmark data (BBSW, BKBM, RBA, RBNZ)"""
        try:
            # Detect what type of benchmark
            filename_upper = filename.upper()
            
            if 'RBA' in filename_upper or 'CASH RATE' in filename_upper:
                currency = 'AUD'
                tenor = '1D'
                floating_rate = 'RBA'
            elif 'RBNZ' in filename_upper or 'OCR' in filename_upper:
                currency = 'NZD'
                tenor = '1D'
                floating_rate = 'RBNZ'
            elif 'BBSW' in filename_upper:
                currency = 'AUD'
                tenor = self._extract_tenor(filename)
                floating_rate = 'BBSW'
            elif 'BKBM' in filename_upper:
                currency = 'NZD'
                tenor = self._extract_tenor(filename)
                floating_rate = 'BKBM'
            else:
                return {
                    'success': False,
                    'error': f'Cannot detect benchmark type from filename: {filename}'
                }
            
            # Read Excel
            df = pd.read_excel(file_path)
            
            # Check columns
            if 'Date' not in df.columns or 'Rate' not in df.columns:
                return {
                    'success': False,
                    'error': 'Excel file must have Date and Rate columns'
                }
            
            # Clean data
            df = df[['Date', 'Rate']].copy()
            df = df.dropna()
            
            # Convert date
            df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
            
            # CRITICAL: Convert percentage to decimal
            df['Rate'] = df['Rate'].apply(lambda x: x / 100 if x > 1 else x)
            
            # Add metadata
            df['Currency'] = currency
            df['Tenor'] = tenor
            df['Floating_Rate'] = floating_rate
            
            # Import to database
            return self._insert_data(df)
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _insert_data(self, df):
        """Insert dataframe into database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
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
        
        return {
            'success': True,
            'records_imported': imported,
            'duplicates': duplicates
        }
    
    def _extract_tenor(self, filename):
        """Extract tenor from filename"""
        # Tenors to look for
        tenors = ['1W', '2W', '3W', '1M', '2M', '3M', '4M', '5M', '6M', '9M', '12M', '18M', '24M',
                  '1Y', '2Y', '3Y', '4Y', '5Y', '6Y', '7Y', '8Y', '9Y', '10Y', '12Y', '15Y', '20Y', 
                  '25Y', '30Y', '35Y', '40Y']
        
        filename_upper = filename.upper()
        
        for tenor in tenors:
            if f' {tenor} ' in filename_upper or f'_{tenor}_' in filename_upper or f'-{tenor}-' in filename_upper:
                return tenor
        
        # Try without spaces
        for tenor in tenors:
            if tenor in filename_upper:
                return tenor
        
        return None
    
    def import_multiple_files(self, file_paths):
        """Import multiple files at once"""
        results = []
        total_imported = 0
        total_duplicates = 0
        errors = []
        
        for file_path in file_paths:
            result = self.import_file(file_path)
            results.append({
                'file': os.path.basename(file_path),
                'result': result
            })
            
            if result['success']:
                total_imported += result['records_imported']
                total_duplicates += result['duplicates']
            else:
                errors.append(f"{os.path.basename(file_path)}: {result['error']}")
        
        return {
            'success': len(errors) == 0,
            'total_files': len(file_paths),
            'total_imported': total_imported,
            'total_duplicates': total_duplicates,
            'errors': errors,
            'details': results
        }
