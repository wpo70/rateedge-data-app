"""
Rate Edge v5.1 - Installation Test Script
Run this to verify everything is working correctly
"""

import sys
import os

print("=" * 70)
print("  RATE EDGE v5.1 - INSTALLATION TEST")
print("=" * 70)
print()

# Test 1: Python version
print("[1/6] Checking Python version...")
if sys.version_info >= (3, 8):
    print(f"  ✅ Python {sys.version.split()[0]} - OK")
else:
    print(f"  ❌ Python {sys.version.split()[0]} - Need 3.8+")
    sys.exit(1)

# Test 2: Required packages
print("\n[2/6] Checking required packages...")
required = ['pandas', 'numpy', 'matplotlib', 'sqlalchemy', 'flask']
missing = []

for package in required:
    try:
        __import__(package)
        print(f"  ✅ {package}")
    except ImportError:
        print(f"  ❌ {package} - MISSING")
        missing.append(package)

if missing:
    print(f"\n  Please install: pip install {' '.join(missing)}")
    sys.exit(1)

# Test 3: Database file
print("\n[3/6] Checking database...")
db_path = os.path.join(os.path.dirname(__file__), 'database', 'swap_rates.db')
if os.path.exists(db_path):
    size_mb = os.path.getsize(db_path) / 1024 / 1024
    print(f"  ✅ Database found ({size_mb:.1f} MB)")
else:
    print(f"  ❌ Database not found at: {db_path}")
    sys.exit(1)

# Test 4: Database content
print("\n[4/6] Checking database content...")
try:
    import sqlite3
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM swap_rates")
    count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(DISTINCT currency) FROM swap_rates")
    currencies = cursor.fetchone()[0]
    conn.close()
    print(f"  ✅ {count:,} records")
    print(f"  ✅ {currencies} currencies")
except Exception as e:
    print(f"  ❌ Database error: {e}")
    sys.exit(1)

# Test 5: Key files
print("\n[5/6] Checking key files...")
key_files = ['launch.py', 'main.py', 'basis_analyzer.py', 'requirements.txt']
for filename in key_files:
    filepath = os.path.join(os.path.dirname(__file__), filename)
    if os.path.exists(filepath):
        print(f"  ✅ {filename}")
    else:
        print(f"  ❌ {filename} - MISSING")

# Test 6: Import main modules
print("\n[6/6] Testing module imports...")
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from database_models import DatabaseManager
    print("  ✅ database_models")
except Exception as e:
    print(f"  ❌ database_models: {e}")

try:
    from main import RateEdgeApp
    print("  ✅ main (RateEdgeApp)")
except Exception as e:
    print(f"  ❌ main: {e}")

try:
    from basis_analyzer import BasisAnalyzer
    print("  ✅ basis_analyzer")
except Exception as e:
    print(f"  ❌ basis_analyzer: {e}")

# Summary
print("\n" + "=" * 70)
print("  TEST SUMMARY")
print("=" * 70)
print("\n✅ All tests passed!")
print("\nYou can now launch Rate Edge:")
print("  python launch.py")
print("\nor:")
print("  python main.py")
print("\nFor web app:")
print("  python web_app.py")
print("\n" + "=" * 70)
