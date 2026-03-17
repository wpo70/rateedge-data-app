"""
RateEdge - Fix Corrupted Rates Script
=====================================

This script fixes corrupted rates in the database where rates > 10% 
are actually meant to be rates that were incorrectly stored.

For AUD/NZD/CAD/GBP: Rates > 10% should be divided by 100
For EUR/JPY: Negative rates may be valid - only fixes extreme negatives

USAGE:
    python FIX_CORRUPTED_RATES.py --dry-run    # Preview changes
    python FIX_CORRUPTED_RATES.py --fix        # Apply fixes
    python FIX_CORRUPTED_RATES.py --delete     # Delete corrupted records instead

WARNING: BACKUP YOUR DATABASE FIRST!
"""

import sqlite3
import sys
import os
from datetime import datetime

# Path to database - adjust if needed
DB_PATH = 'database/swap_rates.db'

def backup_database():
    """Create a backup before making changes"""
    backup_path = f'database/swap_rates_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    import shutil
    shutil.copy(DB_PATH, backup_path)
    print(f"✅ Backup created: {backup_path}")
    return backup_path

def analyze_corruption(cursor):
    """Analyze and report on corruption"""
    print("\n" + "=" * 70)
    print("CORRUPTION ANALYSIS")
    print("=" * 70)
    
    cursor.execute("""
        SELECT 
            currency,
            COUNT(*) as total,
            SUM(CASE WHEN rate > 0.10 THEN 1 ELSE 0 END) as too_high,
            SUM(CASE WHEN rate < -0.50 THEN 1 ELSE 0 END) as very_negative
        FROM swap_rates 
        WHERE rate > 0.10 OR rate < -0.50
        GROUP BY currency
        ORDER BY total DESC
    """)
    
    print(f"\n{'Currency':<10} {'Total':<10} {'Too High (>10%)':<18} {'Very Negative (<-50%)'}")
    print("-" * 60)
    
    for row in cursor.fetchall():
        currency, total, too_high, very_neg = row
        print(f"{currency:<10} {total:<10} {too_high:<18} {very_neg}")

def fix_rates_divide_by_100(cursor, dry_run=True):
    """Fix rates by dividing by 100 for AUD/NZD/CAD/GBP"""
    
    # For AUD, NZD, CAD, GBP - rates > 10% should be divided by 100
    currencies = ['AUD', 'NZD', 'CAD', 'GBP']
    
    for currency in currencies:
        cursor.execute("""
            SELECT COUNT(*) FROM swap_rates 
            WHERE currency = ? AND rate > 0.10
        """, (currency,))
        count = cursor.fetchone()[0]
        
        if count > 0:
            print(f"\n{currency}: {count} records to fix (divide by 100)")
            
            if not dry_run:
                cursor.execute("""
                    UPDATE swap_rates 
                    SET rate = rate / 100
                    WHERE currency = ? AND rate > 0.10
                """, (currency,))
                print(f"   ✅ Fixed {cursor.rowcount} records")
            else:
                # Show sample
                cursor.execute("""
                    SELECT date, tenor, rate, rate/100 as fixed 
                    FROM swap_rates 
                    WHERE currency = ? AND rate > 0.10
                    ORDER BY date DESC LIMIT 5
                """, (currency,))
                print("   Sample fixes:")
                for row in cursor.fetchall():
                    date, tenor, rate, fixed = row
                    print(f"   {date} {tenor}: {rate:.6f} → {fixed:.6f} ({fixed*100:.4f}%)")

def fix_extreme_negatives(cursor, dry_run=True):
    """Fix extremely negative rates (< -50%) which are clearly wrong"""
    
    cursor.execute("""
        SELECT COUNT(*) FROM swap_rates WHERE rate < -0.50
    """)
    count = cursor.fetchone()[0]
    
    if count > 0:
        print(f"\n\nExtreme negatives (< -50%): {count} records")
        
        if not dry_run:
            # Delete these as they're clearly corrupt
            cursor.execute("DELETE FROM swap_rates WHERE rate < -0.50")
            print(f"   ✅ Deleted {cursor.rowcount} corrupt records")
        else:
            cursor.execute("""
                SELECT date, currency, tenor, rate 
                FROM swap_rates 
                WHERE rate < -0.50
                ORDER BY rate LIMIT 10
            """)
            print("   Sample (will be DELETED):")
            for row in cursor.fetchall():
                print(f"   {row[0]} {row[1]} {row[2]}: {row[3]:.6f}")

def delete_corrupted(cursor, dry_run=True):
    """Delete all corrupted records instead of fixing"""
    
    cursor.execute("""
        SELECT COUNT(*) FROM swap_rates 
        WHERE rate > 0.10 OR rate < -0.50
    """)
    count = cursor.fetchone()[0]
    
    print(f"\nWill DELETE {count} corrupted records")
    
    if not dry_run:
        cursor.execute("DELETE FROM swap_rates WHERE rate > 0.10 OR rate < -0.50")
        print(f"✅ Deleted {cursor.rowcount} records")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    mode = sys.argv[1]
    
    if mode not in ['--dry-run', '--fix', '--delete']:
        print("Usage: python FIX_CORRUPTED_RATES.py [--dry-run|--fix|--delete]")
        sys.exit(1)
    
    # Check database exists
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found: {DB_PATH}")
        print("   Make sure you're running from the RateEdge folder")
        sys.exit(1)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Analyze first
    analyze_corruption(cursor)
    
    dry_run = (mode == '--dry-run')
    
    if mode == '--delete':
        if not dry_run:
            backup_database()
        delete_corrupted(cursor, dry_run=False)
    else:
        if not dry_run:
            backup_database()
        
        # Fix by dividing by 100
        fix_rates_divide_by_100(cursor, dry_run)
        
        # Fix extreme negatives
        fix_extreme_negatives(cursor, dry_run)
    
    if not dry_run:
        conn.commit()
        print("\n" + "=" * 70)
        print("✅ ALL FIXES APPLIED")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("DRY RUN COMPLETE - No changes made")
        print("Run with --fix to apply changes")
        print("=" * 70)
    
    conn.close()

if __name__ == '__main__':
    main()
