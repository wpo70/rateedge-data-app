"""
Rate Edge - Data Upload Handler
Handles daily rate uploads for BBSW fixings, swap curves, and OIS rates
"""

import pandas as pd
from datetime import datetime
import os
from typing import Dict, List, Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RateUploadHandler:
    """Handles uploading and validating rate data"""
    
    VALID_CURRENCIES = ['AUD', 'CAD', 'EUR', 'GBP', 'JPY', 'NZD', 'USD']
    
    VALID_BENCHMARK_TYPES = [
        'BBSW', 'CDOR', 'EURIBOR', 'SONIA', 'TONAR', 'BKBM', 'SOFR',
        '1M', '2M', '3M', '6M', '12M'  # Standard tenors
    ]
    
    VALID_SWAP_TENORS = [
        '1Y', '2Y', '3Y', '4Y', '5Y', '6Y', '7Y', '8Y', '9Y', '10Y',
        '12Y', '15Y', '20Y', '25Y', '30Y', '40Y', '50Y'
    ]
    
    def __init__(self, database_manager):
        """Initialize with database manager"""
        self.db = database_manager
        self.upload_log = []
    
    def validate_date(self, date_str: str) -> Optional[datetime]:
        """Validate and parse date string"""
        try:
            # Try multiple date formats
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y%m%d']:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            return None
        except Exception as e:
            logger.error(f"Error parsing date {date_str}: {e}")
            return None
    
    def validate_rate(self, rate_value) -> Optional[float]:
        """Validate rate value"""
        try:
            rate = float(rate_value)
            # Rates should be reasonable (between -5% and 50%)
            if -5.0 <= rate <= 50.0:
                return rate
            return None
        except (ValueError, TypeError):
            return None
    
    def parse_benchmark_rates_csv(self, file_path: str) -> Tuple[List[Dict], List[str]]:
        """
        Parse CSV file with benchmark rates (BBSW, CDOR, etc.)
        
        Expected format:
        Date, Currency, Rate_Type, Rate
        2025-11-04, AUD, BBSW_3M, 4.35
        2025-11-04, AUD, BBSW_6M, 4.40
        """
        errors = []
        valid_records = []
        
        try:
            df = pd.read_csv(file_path)
            
            # Check required columns
            required_cols = ['Date', 'Currency', 'Rate_Type', 'Rate']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                errors.append(f"Missing required columns: {', '.join(missing_cols)}")
                return valid_records, errors
            
            # Validate each row
            for idx, row in df.iterrows():
                row_errors = []
                
                # Validate date
                parsed_date = self.validate_date(str(row['Date']))
                if not parsed_date:
                    row_errors.append(f"Row {idx+2}: Invalid date '{row['Date']}'")
                    continue
                
                # Validate currency
                currency = str(row['Currency']).upper().strip()
                if currency not in self.VALID_CURRENCIES:
                    row_errors.append(f"Row {idx+2}: Invalid currency '{currency}'")
                
                # Validate rate type
                rate_type = str(row['Rate_Type']).upper().strip()
                
                # Validate rate value
                rate_value = self.validate_rate(row['Rate'])
                if rate_value is None:
                    row_errors.append(f"Row {idx+2}: Invalid rate '{row['Rate']}'")
                
                if row_errors:
                    errors.extend(row_errors)
                else:
                    valid_records.append({
                        'date': parsed_date.strftime('%Y-%m-%d'),
                        'currency': currency,
                        'rate_type': rate_type,
                        'rate': rate_value
                    })
            
            logger.info(f"Parsed {len(valid_records)} valid benchmark rate records")
            
        except Exception as e:
            errors.append(f"Error reading CSV file: {str(e)}")
        
        return valid_records, errors
    
    def parse_swap_rates_csv(self, file_path: str) -> Tuple[List[Dict], List[str]]:
        """
        Parse CSV file with swap rates
        
        Expected format:
        Date, Currency, Tenor, Rate
        2025-11-04, AUD, 2Y, 4.25
        2025-11-04, AUD, 5Y, 4.35
        """
        errors = []
        valid_records = []
        
        try:
            df = pd.read_csv(file_path)
            
            # Check required columns
            required_cols = ['Date', 'Currency', 'Tenor', 'Rate']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                errors.append(f"Missing required columns: {', '.join(missing_cols)}")
                return valid_records, errors
            
            # Validate each row
            for idx, row in df.iterrows():
                row_errors = []
                
                # Validate date
                parsed_date = self.validate_date(str(row['Date']))
                if not parsed_date:
                    row_errors.append(f"Row {idx+2}: Invalid date '{row['Date']}'")
                    continue
                
                # Validate currency
                currency = str(row['Currency']).upper().strip()
                if currency not in self.VALID_CURRENCIES:
                    row_errors.append(f"Row {idx+2}: Invalid currency '{currency}'")
                
                # Validate tenor
                tenor = str(row['Tenor']).upper().strip()
                
                # Validate rate value
                rate_value = self.validate_rate(row['Rate'])
                if rate_value is None:
                    row_errors.append(f"Row {idx+2}: Invalid rate '{row['Rate']}'")
                
                if row_errors:
                    errors.extend(row_errors)
                else:
                    valid_records.append({
                        'date': parsed_date.strftime('%Y-%m-%d'),
                        'currency': currency,
                        'tenor': tenor,
                        'rate': rate_value
                    })
            
            logger.info(f"Parsed {len(valid_records)} valid swap rate records")
            
        except Exception as e:
            errors.append(f"Error reading CSV file: {str(e)}")
        
        return valid_records, errors
    
    def parse_ois_rates_csv(self, file_path: str) -> Tuple[List[Dict], List[str]]:
        """
        Parse CSV file with OIS rates
        
        Expected format:
        Date, Currency, Tenor, Rate
        2025-11-04, AUD, 1M, 4.10
        2025-11-04, AUD, 3M, 4.15
        """
        # OIS rates have same format as swap rates
        return self.parse_swap_rates_csv(file_path)
    
    def upload_benchmark_rates(self, records: List[Dict]) -> Tuple[int, int, List[str]]:
        """
        Upload benchmark rates to database
        Returns: (success_count, duplicate_count, errors)
        """
        success_count = 0
        duplicate_count = 0
        errors = []
        
        for record in records:
            try:
                # Check if record already exists
                existing = self.db.get_benchmark_rates(
                    currency=record['currency'],
                    rate_type=record['rate_type'],
                    start_date=record['date'],
                    end_date=record['date']
                )
                
                if existing:
                    duplicate_count += 1
                    logger.debug(f"Duplicate: {record['date']} {record['currency']} {record['rate_type']}")
                else:
                    # Insert new record
                    self.db.add_benchmark_rate(
                        date=record['date'],
                        currency=record['currency'],
                        rate_type=record['rate_type'],
                        rate=record['rate']
                    )
                    success_count += 1
                    logger.info(f"Added: {record['date']} {record['currency']} {record['rate_type']} = {record['rate']}")
            
            except Exception as e:
                error_msg = f"Error inserting {record['date']} {record['currency']} {record['rate_type']}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        return success_count, duplicate_count, errors
    
    def upload_swap_rates(self, records: List[Dict]) -> Tuple[int, int, List[str]]:
        """
        Upload swap rates to database
        Returns: (success_count, duplicate_count, errors)
        """
        success_count = 0
        duplicate_count = 0
        errors = []
        
        for record in records:
            try:
                # Check if record already exists
                existing = self.db.get_swap_rates(
                    currency=record['currency'],
                    tenor=record['tenor'],
                    start_date=record['date'],
                    end_date=record['date']
                )
                
                if existing:
                    duplicate_count += 1
                    logger.debug(f"Duplicate: {record['date']} {record['currency']} {record['tenor']}")
                else:
                    # Insert new record
                    self.db.add_swap_rate(
                        date=record['date'],
                        currency=record['currency'],
                        tenor=record['tenor'],
                        rate=record['rate']
                    )
                    success_count += 1
                    logger.info(f"Added: {record['date']} {record['currency']} {record['tenor']} = {record['rate']}")
            
            except Exception as e:
                error_msg = f"Error inserting {record['date']} {record['currency']} {record['tenor']}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        return success_count, duplicate_count, errors
    
    def upload_ois_rates(self, records: List[Dict]) -> Tuple[int, int, List[str]]:
        """
        Upload OIS rates to database
        Returns: (success_count, duplicate_count, errors)
        """
        success_count = 0
        duplicate_count = 0
        errors = []
        
        for record in records:
            try:
                # Check if record already exists
                existing = self.db.get_ois_rates(
                    currency=record['currency'],
                    rate_type=record['tenor'],  # OIS uses rate_type field
                    start_date=record['date'],
                    end_date=record['date']
                )
                
                if existing:
                    duplicate_count += 1
                    logger.debug(f"Duplicate: {record['date']} {record['currency']} {record['tenor']}")
                else:
                    # Insert new record
                    self.db.add_ois_rate(
                        date=record['date'],
                        currency=record['currency'],
                        rate_type=record['tenor'],
                        rate=record['rate']
                    )
                    success_count += 1
                    logger.info(f"Added: {record['date']} {record['currency']} {record['tenor']} = {record['rate']}")
            
            except Exception as e:
                error_msg = f"Error inserting {record['date']} {record['currency']} {record['tenor']}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        return success_count, duplicate_count, errors
    
    def generate_template_csv(self, rate_type: str, output_path: str):
        """Generate a template CSV file for uploads"""
        
        if rate_type == 'benchmark':
            template_data = {
                'Date': ['2025-11-04', '2025-11-04', '2025-11-04'],
                'Currency': ['AUD', 'AUD', 'AUD'],
                'Rate_Type': ['BBSW_1M', 'BBSW_3M', 'BBSW_6M'],
                'Rate': [4.30, 4.35, 4.40]
            }
        elif rate_type == 'swap':
            template_data = {
                'Date': ['2025-11-04', '2025-11-04', '2025-11-04'],
                'Currency': ['AUD', 'AUD', 'AUD'],
                'Tenor': ['2Y', '5Y', '10Y'],
                'Rate': [4.25, 4.35, 4.45]
            }
        elif rate_type == 'ois':
            template_data = {
                'Date': ['2025-11-04', '2025-11-04', '2025-11-04'],
                'Currency': ['AUD', 'AUD', 'AUD'],
                'Tenor': ['1M', '3M', '6M'],
                'Rate': [4.10, 4.15, 4.20]
            }
        else:
            raise ValueError(f"Invalid rate type: {rate_type}")
        
        df = pd.DataFrame(template_data)
        df.to_csv(output_path, index=False)
        logger.info(f"Generated template: {output_path}")
        
        return output_path
