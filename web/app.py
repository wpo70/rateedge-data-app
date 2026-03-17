"""
RateEdge Web Application - COMPLETE VERSION
Exact replica of desktop app with ALL functionality
"""

from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import sys
from datetime import datetime, timedelta
import json
import sqlite3
import numpy as np

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from database_models import DatabaseManager, SwapRate
from market_data_importer import MarketDataImporter

# Initialize Flask app
app = Flask(__name__)

# ── ACCESS DENIED SPLASH ── remove this block to restore normal operation ──
@app.before_request
def splash():
    return open(os.path.join(app.root_path, 'templates', 'splash.html')).read(), 403
# ──────────────────────────────────────────────────────────────────────────────

app.config['SECRET_KEY'] = 'rateedge-secret-key-change-in-production'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database paths
# Database path - use the same database as desktop app
# Try multiple possible locations
possible_paths = [
    os.path.join(os.path.dirname(__file__), '..', 'database', 'swap_rates.db'),
    os.path.join(os.path.dirname(__file__), 'database', 'swap_rates.db'),
    r'C:\Users\willp\IRS_DATA_Manager\RateEdge_v7.2_FINAL\database\swap_rates.db',
]

db_path = None
for path in possible_paths:
    if os.path.exists(path):
        db_path = path
        print(f"Using database: {path}")
        break

if not db_path:
    db_path = possible_paths[0]  # Default to first option
    print(f"WARNING: Database not found, using default: {db_path}")
db_manager = DatabaseManager(f'sqlite:///{db_path}')
market_data_importer = MarketDataImporter(db_path)

# User database
users_db = {
    'admin': {
        'password': generate_password_hash('admin123'),
        'email': 'admin@rateedge.com',
        'role': 'admin'
    }
}

class User:
    def __init__(self, username):
        self.id = username
        self.username = username
        self.email = users_db[username]['email']
        self.role = users_db[username]['role']
    
    def is_authenticated(self):
        return True
    
    def is_active(self):
        return True
    
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return self.id

@login_manager.user_loader
def load_user(user_id):
    if user_id in users_db:
        return User(user_id)
    return None

# Helper functions
def get_db_connection():
    """Get direct SQLite connection for calculators"""
    return sqlite3.connect(db_path)

def tenor_to_years(tenor):
    """Convert tenor string to years"""
    if not tenor:
        return 0
    tenor = str(tenor).upper().strip()
    if tenor.endswith('Y'):
        return float(tenor[:-1])
    elif tenor.endswith('M'):
        return float(tenor[:-1]) / 12
    elif tenor.endswith('W'):
        return float(tenor[:-1]) / 52
    elif tenor.endswith('D') or tenor.endswith('BD'):
        return float(tenor.replace('BD', '').replace('D', '')) / 365
    return 0

# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in users_db and check_password_hash(users_db[username]['password'], password):
            user = User(username)
            login_user(user, remember=True)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ============================================================================
# DASHBOARD
# ============================================================================

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        session_db = db_manager.session
        total_records = session_db.query(SwapRate).count()
        latest_date = session_db.query(SwapRate.date).order_by(SwapRate.date.desc()).first()
        currencies = session_db.query(SwapRate.currency).distinct().count()
        
        return render_template('dashboard.html',
                             total_records=total_records,
                             latest_date=latest_date[0] if latest_date else 'No data',
                             currencies=currencies)
    except Exception as e:
        print(f"Dashboard error: {e}")
        return render_template('dashboard.html',
                             total_records=0,
                             latest_date='Error',
                             currencies=0)

# ============================================================================
# DATA VIEWING ROUTES
# ============================================================================

@app.route('/swap-rates')
@login_required
def swap_rates():
    return render_template('swap_rates.html')

@app.route('/benchmark')
@login_required
def benchmark():
    return render_template('benchmark.html')

@app.route('/ois')
@login_required
def ois():
    return render_template('ois.html')

@app.route('/import')
@login_required
def import_data():
    return render_template('import.html')

# ============================================================================
# CALCULATOR ROUTES
# ============================================================================

@app.route('/calculators/basis-analyzer')
@login_required
def basis_analyzer():
    return render_template('calculators/basis_analyzer.html')

@app.route('/calculators/forward-basis-matrix')
@login_required
def forward_basis_matrix():
    return render_template('calculators/forward_basis_matrix.html')

@app.route('/calculators/forward-swap-matrix')
@login_required
def forward_swap_matrix():
    return render_template('calculators/forward_swap_matrix.html')

@app.route('/calculators/butterfly-analyzer')
@login_required
def butterfly_analyzer():
    return render_template('calculators/butterfly_analyzer.html')

@app.route('/calculators/basis-spread')
@login_required
def basis_spread():
    return render_template('calculators/basis_spread.html')

@app.route('/calculators/relative-value')
@login_required
def relative_value():
    return render_template('calculators/relative_value.html')

# ============================================================================
# API ROUTES - DATA
# ============================================================================

@app.route('/api/swap-rates')
@login_required
def api_swap_rates():
    try:
        currency = request.args.get('currency', 'All')
        tenor = request.args.get('tenor', 'All')
        floating_rate = request.args.get('floating_rate', 'All')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = int(request.args.get('limit', 1000))
        
        session_db = db_manager.session
        query = session_db.query(SwapRate)
        
        if currency != 'All':
            query = query.filter(SwapRate.currency == currency)
        if tenor != 'All':
            query = query.filter(SwapRate.tenor == tenor)
        if floating_rate != 'All':
            query = query.filter(SwapRate.floating_rate == floating_rate)
        if start_date:
            query = query.filter(SwapRate.date >= start_date)
        if end_date:
            query = query.filter(SwapRate.date <= end_date)
        
        rates = query.order_by(SwapRate.date.desc()).limit(limit).all()
        
        data = [{
            'date': r.date.isoformat() if hasattr(r.date, 'isoformat') else str(r.date),
            'currency': r.currency,
            'tenor': r.tenor,
            'rate': r.rate,
            'floating_rate': r.floating_rate
        } for r in rates]
        
        return jsonify(data)
    except Exception as e:
        print(f"API error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/benchmark-rates')
@login_required
def api_benchmark_rates():
    """Get benchmark rates from benchmark_rates table"""
    try:
        currency = request.args.get('currency', 'All')
        rate_type = request.args.get('rate_type', 'All')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = int(request.args.get('limit', 10000))
        
        # Use direct SQL query to benchmark_rates table
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT date, currency, rate_type, rate FROM benchmark_rates WHERE 1=1"
        params = []
        
        if currency != 'All':
            query += " AND currency = ?"
            params.append(currency)
        if rate_type != 'All':
            query += " AND rate_type = ?"
            params.append(rate_type)
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        
        query += " ORDER BY date DESC"
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        data = [{
            'date': row[0],
            'currency': row[1],
            'rate_type': row[2],
            'rate': row[3]
        } for row in rows]
        
        return jsonify(data)
    except Exception as e:
        print(f"Benchmark API error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/benchmark-rate-types')
@login_required
def api_benchmark_rate_types():
    """Get available benchmark rate types for a currency"""
    try:
        currency = request.args.get('currency', 'AUD')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT rate_type FROM benchmark_rates 
            WHERE currency = ? ORDER BY rate_type
        """, (currency,))
        
        rate_types = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return jsonify(rate_types)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ois-rates')
@login_required
def api_ois_rates():
    """Get OIS rates from ois_rates table"""
    try:
        currency = request.args.get('currency', 'All')
        rate_type = request.args.get('rate_type', 'All')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = int(request.args.get('limit', 10000))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check table structure
        cursor.execute("PRAGMA table_info(ois_rates)")
        columns = cursor.fetchall()
        col_names = [col[1] for col in columns]
        print(f"OIS table columns: {col_names}")
        
        # Query ois_rates table - get all columns
        query = "SELECT * FROM ois_rates WHERE 1=1"
        params = []
        
        if currency != 'All':
            query += " AND currency = ?"
            params.append(currency)
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        
        query += " ORDER BY date DESC"
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        print(f"OIS API: Found {len(rows)} rows")
        if rows:
            print(f"OIS first row: {rows[0]}")
        
        conn.close()
        
        # Build response based on actual columns
        data = []
        for row in rows:
            row_dict = dict(zip(col_names, row))
            # Use 'tenor' as rate_type if it exists, otherwise use 'rate_type'
            rt = row_dict.get('tenor', row_dict.get('rate_type', ''))
            data.append({
                'date': row_dict.get('date', ''),
                'currency': row_dict.get('currency', ''),
                'rate_type': rt,
                'rate': row_dict.get('rate', 0)
            })
        
        if data:
            sample_types = list(set([d['rate_type'] for d in data[:100]]))
            print(f"OIS sample rate_types: {sample_types}")
        
        return jsonify(data)
    except Exception as e:
        print(f"OIS API error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/ois-rate-types')
@login_required
def api_ois_rate_types():
    """Get available OIS rate types for a currency"""
    try:
        currency = request.args.get('currency', 'AUD')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT rate_type FROM ois_rates 
            WHERE currency = ? ORDER BY rate_type
        """, (currency,))
        
        rate_types = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return jsonify(rate_types)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/import', methods=['POST'])
@login_required
def api_import():
    if 'files[]' not in request.files:
        return jsonify({'success': False, 'error': 'No files uploaded'})
    
    files = request.files.getlist('files[]')
    results = []
    total_imported = 0
    total_duplicates = 0
    
    for file in files:
        if file.filename:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            result = market_data_importer.import_file(filepath)
            
            if result['success']:
                total_imported += result['records_imported']
                total_duplicates += result['duplicates']
            
            results.append({
                'filename': filename,
                'result': result
            })
            
            try:
                os.remove(filepath)
            except:
                pass
    
    return jsonify({
        'success': True,
        'total_imported': total_imported,
        'total_duplicates': total_duplicates,
        'results': results
    })

# ============================================================================
# API ROUTES - CALCULATORS
# ============================================================================

@app.route('/api/calculate/basis', methods=['POST'])
@login_required
def api_calculate_basis():
    """Calculate basis spread (3M vs 6M)"""
    try:
        data = request.json
        date = data.get('date')
        tenor = data.get('tenor')
        currency = data.get('currency', 'AUD')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get 3M rate
        cursor.execute("""
            SELECT rate FROM swap_rates 
            WHERE date = ? AND currency = ? AND tenor = ? 
            AND (floating_rate LIKE '%3M%' OR floating_rate = '3M')
        """, (date, currency, tenor))
        rate_3m_row = cursor.fetchone()
        
        # Get 6M rate
        cursor.execute("""
            SELECT rate FROM swap_rates 
            WHERE date = ? AND currency = ? AND tenor = ? 
            AND (floating_rate LIKE '%6M%' OR floating_rate = '6M')
        """, (date, currency, tenor))
        rate_6m_row = cursor.fetchone()
        
        conn.close()
        
        if not rate_3m_row or not rate_6m_row:
            return jsonify({'error': f'Data not found for {date} {currency} {tenor}'}), 404
        
        rate_3m = rate_3m_row[0]
        rate_6m = rate_6m_row[0]
        
        # Basis = 3M - 6M (in basis points)
        basis = (rate_3m - rate_6m) * 10000
        
        return jsonify({
            'success': True,
            'date': date,
            'tenor': tenor,
            'currency': currency,
            'rate_3m': rate_3m * 100,
            'rate_6m': rate_6m * 100,
            'basis_bp': round(basis, 2)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/calculate/butterfly', methods=['POST'])
@login_required
def api_calculate_butterfly():
    """Calculate butterfly spread"""
    try:
        data = request.json
        date = data.get('date')
        currency = data.get('currency', 'AUD')
        short_tenor = data.get('short_tenor')
        mid_tenor = data.get('mid_tenor')
        long_tenor = data.get('long_tenor')
        floating_rate = data.get('floating_rate', 'AONIA')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get rates
        rates = {}
        for tenor in [short_tenor, mid_tenor, long_tenor]:
            cursor.execute("""
                SELECT rate FROM swap_rates 
                WHERE date = ? AND currency = ? AND tenor = ? 
                AND floating_rate LIKE ?
            """, (date, currency, tenor, f'%{floating_rate}%'))
            row = cursor.fetchone()
            if row:
                rates[tenor] = row[0]
        
        conn.close()
        
        if len(rates) != 3:
            return jsonify({'error': 'Could not find all required rates'}), 404
        
        # Butterfly = Mid - (Short + Long) / 2
        butterfly = (rates[mid_tenor] - (rates[short_tenor] + rates[long_tenor]) / 2) * 10000
        
        return jsonify({
            'success': True,
            'date': date,
            'currency': currency,
            'short_rate': rates[short_tenor] * 100,
            'mid_rate': rates[mid_tenor] * 100,
            'long_rate': rates[long_tenor] * 100,
            'butterfly_bp': round(butterfly, 2)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/calculate/forward-rate', methods=['POST'])
@login_required
def api_calculate_forward_rate():
    """Calculate forward swap rate"""
    try:
        data = request.json
        date = data.get('date')
        currency = data.get('currency', 'AUD')
        forward_start = data.get('forward_start')  # in years
        swap_tenor = data.get('swap_tenor')  # in years
        floating_rate = data.get('floating_rate', 'AONIA')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get spot curve
        cursor.execute("""
            SELECT tenor, rate FROM swap_rates 
            WHERE date = ? AND currency = ? AND floating_rate LIKE ?
        """, (date, currency, f'%{floating_rate}%'))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return jsonify({'error': 'No curve data found'}), 404
        
        # Build curve
        curve = {tenor_to_years(r[0]): r[1] for r in rows}
        
        # Simple linear interpolation for forward rate
        # Forward rate = ((1 + r2)^t2 / (1 + r1)^t1)^(1/(t2-t1)) - 1
        t1 = float(forward_start)
        t2 = t1 + float(swap_tenor)
        
        # Get or interpolate rates
        def get_rate(years):
            if years in curve:
                return curve[years]
            # Linear interpolation
            years_list = sorted(curve.keys())
            for i in range(len(years_list) - 1):
                if years_list[i] <= years <= years_list[i+1]:
                    w = (years - years_list[i]) / (years_list[i+1] - years_list[i])
                    return curve[years_list[i]] * (1 - w) + curve[years_list[i+1]] * w
            return None
        
        r1 = get_rate(t1) if t1 > 0 else 0
        r2 = get_rate(t2)
        
        if r2 is None:
            return jsonify({'error': f'Cannot interpolate rate for {t2}Y'}), 404
        
        # Calculate forward rate
        if t1 == 0:
            forward_rate = r2
        else:
            df1 = 1 / ((1 + r1) ** t1)
            df2 = 1 / ((1 + r2) ** t2)
            forward_rate = (df1 / df2 - 1) / (t2 - t1)
        
        return jsonify({
            'success': True,
            'date': date,
            'currency': currency,
            'forward_start': forward_start,
            'swap_tenor': swap_tenor,
            'forward_rate': round(forward_rate * 100, 4)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/curve-data')
@login_required
def api_curve_data():
    """Get curve data for charting"""
    try:
        date = request.args.get('date')
        currency = request.args.get('currency', 'AUD')
        floating_rate = request.args.get('floating_rate', 'AONIA')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT tenor, rate FROM swap_rates 
            WHERE date = ? AND currency = ? AND floating_rate LIKE ?
        """, (date, currency, f'%{floating_rate}%'))
        
        rows = cursor.fetchall()
        conn.close()
        
        data = []
        for tenor, rate in rows:
            years = tenor_to_years(tenor)
            if years > 0:
                data.append({
                    'tenor': tenor,
                    'years': years,
                    'rate': rate * 100
                })
        
        data.sort(key=lambda x: x['years'])
        
        return jsonify(data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/available-dates')
@login_required
def api_available_dates():
    """Get available dates for a currency"""
    try:
        currency = request.args.get('currency', 'AUD')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT date FROM swap_rates 
            WHERE currency = ? 
            ORDER BY date DESC LIMIT 100
        """, (currency,))
        
        dates = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return jsonify(dates)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/basis-history')
@login_required
def api_basis_history():
    """Get basis history for charting"""
    try:
        currency = request.args.get('currency', 'AUD')
        tenor = request.args.get('tenor', '5Y')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get 3M rates
        query_3m = """
            SELECT date, rate FROM swap_rates 
            WHERE currency = ? AND tenor = ? 
            AND (floating_rate LIKE '%3M%' OR floating_rate = '3M')
        """
        params = [currency, tenor]
        if start_date:
            query_3m += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query_3m += " AND date <= ?"
            params.append(end_date)
        query_3m += " ORDER BY date"
        
        cursor.execute(query_3m, params)
        rates_3m = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Get 6M rates
        query_6m = query_3m.replace('%3M%', '%6M%').replace("= '3M'", "= '6M'")
        params[0] = currency  # Reset currency
        cursor.execute(query_6m, params)
        rates_6m = {row[0]: row[1] for row in cursor.fetchall()}
        
        conn.close()
        
        # Calculate basis for each date
        data = []
        for date in sorted(set(rates_3m.keys()) & set(rates_6m.keys())):
            basis = (rates_3m[date] - rates_6m[date]) * 10000
            data.append({
                'date': date,
                'basis': round(basis, 2),
                'rate_3m': rates_3m[date] * 100,
                'rate_6m': rates_6m[date] * 100
            })
        
        return jsonify(data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/butterfly-history')
@login_required
def api_butterfly_history():
    """Get butterfly history for charting"""
    try:
        currency = request.args.get('currency', 'AUD')
        short_tenor = request.args.get('short_tenor', '5Y')
        mid_tenor = request.args.get('mid_tenor', '7Y')
        long_tenor = request.args.get('long_tenor', '10Y')
        floating_rate = request.args.get('floating_rate', 'AONIA')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get rates for all three tenors
        def get_tenor_rates(tenor):
            query = """
                SELECT date, rate FROM swap_rates 
                WHERE currency = ? AND tenor = ? AND floating_rate LIKE ?
            """
            params = [currency, tenor, f'%{floating_rate}%']
            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND date <= ?"
                params.append(end_date)
            query += " ORDER BY date"
            cursor.execute(query, params)
            return {row[0]: row[1] for row in cursor.fetchall()}
        
        short_rates = get_tenor_rates(short_tenor)
        mid_rates = get_tenor_rates(mid_tenor)
        long_rates = get_tenor_rates(long_tenor)
        
        conn.close()
        
        # Calculate butterfly for each date
        common_dates = sorted(set(short_rates.keys()) & set(mid_rates.keys()) & set(long_rates.keys()))
        
        data = []
        for date in common_dates:
            butterfly = (mid_rates[date] - (short_rates[date] + long_rates[date]) / 2) * 10000
            data.append({
                'date': date,
                'butterfly': round(butterfly, 2),
                'short_rate': short_rates[date] * 100,
                'mid_rate': mid_rates[date] * 100,
                'long_rate': long_rates[date] * 100
            })
        
        return jsonify(data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
