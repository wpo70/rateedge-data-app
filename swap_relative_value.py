"""
Swap Relative Value Analyzer
Analyze relationships between forward spreads and curve spreads
Example: 2y2y vs 4y2y compared to 2y-20y spread
Identify steepening/flattening opportunities with scatter plots
Uses CUBIC SPLINE interpolation when available, falls back to linear
"""
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import sqlite3
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
matplotlib.use('TkAgg')
import numpy as np
import os

# Try to import mplcursors for hover tooltips
try:
    import mplcursors
    MPLCURSORS_AVAILABLE = True
except ImportError:
    MPLCURSORS_AVAILABLE = False
    print("⚠️ mplcursors not available - using basic hover")

# Try to import scipy for cubic spline and stats
try:
    from scipy.interpolate import CubicSpline
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    print("⚠️ scipy not available - using linear interpolation and basic statistics")

class SwapRelativeValueAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("Swap Relative Value Analyzer")
        self.root.geometry("1600x950")
        
        self.db_path = os.path.join(os.path.dirname(__file__), 'database', 'swap_rates.db')
        
        # Available tenors for forward structures
        self.tenors = ['1Y', '2Y', '3Y', '4Y', '5Y', '6Y', '7Y', '8Y', '9Y', '10Y', 
                       '12Y', '15Y', '20Y', '25Y', '30Y']
        
        # Forward periods
        self.forward_periods = ['1m', '2m', '3m', '6m', '9m', '1y', '18m', '2y', '3y', 
                               '4y', '5y', '7y', '10y']
        
        self.setup_ui()
    
    def setup_ui(self):
        # Header
        header = tk.Frame(self.root, bg='#2c3e50', padx=20, pady=15)
        header.pack(fill=tk.X)
        
        tk.Label(header, text="📊 Swap Relative Value Analyzer", 
                bg='#2c3e50', fg='white', font=('Arial', 18, 'bold')).pack()
        
        tk.Label(header, text="Analyze forward spreads vs curve spreads | Identify steepening/flattening opportunities", 
                bg='#2c3e50', fg='#ecf0f1', font=('Arial', 11)).pack()
        
        # Main container with two panels
        container = tk.Frame(self.root)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Parameters
        left_panel = tk.Frame(container, width=400, bg='#ecf0f1')
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)
        
        # Right panel - Chart
        self.right_panel = tk.Frame(container, bg='white')
        self.right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.setup_left_panel(left_panel)
    
    def setup_left_panel(self, panel):
        # Title
        tk.Label(panel, text="Analysis Parameters", bg='#34495e', fg='white',
                font=('Arial', 12, 'bold'), pady=8).pack(fill=tk.X)
        
        # Scrollable frame for parameters
        canvas = tk.Canvas(panel, bg='#ecf0f1', highlightthickness=0)
        scrollbar = tk.Scrollbar(panel, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#ecf0f1')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Parameters
        params = scrollable_frame
        
        # Currency Mode Selection
        self.add_section(params, "Analysis Mode")
        mode_frame = tk.Frame(params, bg='#ecf0f1')
        mode_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.mode_var = tk.StringVar(value='single')
        tk.Radiobutton(mode_frame, text="Single Currency", variable=self.mode_var, 
                      value='single', bg='#ecf0f1', command=self.toggle_currency_mode).pack(anchor='w')
        tk.Radiobutton(mode_frame, text="Cross-Currency (Basis)", variable=self.mode_var, 
                      value='cross', bg='#ecf0f1', command=self.toggle_currency_mode).pack(anchor='w')
        
        # Currency Selection
        self.add_section(params, "Currency")
        
        # Single currency frame
        self.single_curr_frame = tk.Frame(params, bg='#ecf0f1')
        self.single_curr_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(self.single_curr_frame, text="Currency:", bg='#ecf0f1', 
                font=('Arial', 9)).pack(side=tk.LEFT, padx=5)
        self.currency_var = tk.StringVar(value='AUD')
        ttk.Combobox(self.single_curr_frame, textvariable=self.currency_var, 
                    values=['AUD', 'NZD', 'USD', 'JPY', 'EUR'], width=10, state='readonly').pack(side=tk.LEFT)
        
        tk.Label(self.single_curr_frame, text="Floating:", bg='#ecf0f1', 
                font=('Arial', 9)).pack(side=tk.LEFT, padx=(10, 5))
        self.floating_var = tk.StringVar(value='3M')
        ttk.Combobox(self.single_curr_frame, textvariable=self.floating_var,
                    values=['3M', '6M'], width=8, state='readonly').pack(side=tk.LEFT)
        
        # Cross-currency frame
        self.cross_curr_frame = tk.Frame(params, bg='#ecf0f1')
        # Don't pack yet - will be shown when cross mode selected
        
        tk.Label(self.cross_curr_frame, text="Currency 1:", bg='#ecf0f1', 
                font=('Arial', 9)).pack(side=tk.LEFT, padx=5)
        self.currency1_var = tk.StringVar(value='AUD')
        ttk.Combobox(self.cross_curr_frame, textvariable=self.currency1_var, 
                    values=['AUD', 'NZD', 'USD', 'JPY', 'EUR'], width=8, state='readonly').pack(side=tk.LEFT)
        
        tk.Label(self.cross_curr_frame, text="vs", bg='#ecf0f1', 
                font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=5)
        
        tk.Label(self.cross_curr_frame, text="Currency 2:", bg='#ecf0f1', 
                font=('Arial', 9)).pack(side=tk.LEFT, padx=5)
        self.currency2_var = tk.StringVar(value='NZD')
        ttk.Combobox(self.cross_curr_frame, textvariable=self.currency2_var, 
                    values=['AUD', 'NZD', 'USD', 'JPY', 'EUR'], width=8, state='readonly').pack(side=tk.LEFT)
        
        # Both use 3M for cross-currency
        self.cross_floating_var = tk.StringVar(value='3M')
        
        # Date range
        self.add_section(params, "Date Range")
        date_frame = tk.Frame(params, bg='#ecf0f1')
        date_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(date_frame, text="From:", bg='#ecf0f1', font=('Arial', 9)).pack(side=tk.LEFT, padx=5)
        self.start_date = DateEntry(date_frame, width=12, background='darkblue',
                                    foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.start_date.set_date(datetime.now() - timedelta(days=365))
        self.start_date.pack(side=tk.LEFT, padx=5)
        
        tk.Label(date_frame, text="To:", bg='#ecf0f1', font=('Arial', 9)).pack(side=tk.LEFT, padx=5)
        self.end_date = DateEntry(date_frame, width=12, background='darkblue',
                                  foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.end_date.set_date(datetime.now())
        self.end_date.pack(side=tk.LEFT, padx=5)
        
        # Forward Spread (X-Axis)
        self.add_section(params, "Forward Spread (X-Axis)")
        
        # First forward structure
        fwd1_frame = tk.Frame(params, bg='#ecf0f1')
        fwd1_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(fwd1_frame, text="Forward 1:", bg='#ecf0f1', 
                font=('Arial', 9, 'bold')).pack(anchor='w')
        
        fwd1_select = tk.Frame(fwd1_frame, bg='#ecf0f1')
        fwd1_select.pack(fill=tk.X, pady=2)
        
        self.fwd1_start_var = tk.StringVar(value='2y')
        self.fwd1_tenor_var = tk.StringVar(value='2Y')
        
        ttk.Combobox(fwd1_select, textvariable=self.fwd1_start_var,
                    values=self.forward_periods, width=8, state='readonly').pack(side=tk.LEFT, padx=2)
        tk.Label(fwd1_select, text="x", bg='#ecf0f1').pack(side=tk.LEFT)
        ttk.Combobox(fwd1_select, textvariable=self.fwd1_tenor_var,
                    values=self.tenors, width=8, state='readonly').pack(side=tk.LEFT, padx=2)
        
        # Second forward structure
        fwd2_frame = tk.Frame(params, bg='#ecf0f1')
        fwd2_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(fwd2_frame, text="Forward 2:", bg='#ecf0f1', 
                font=('Arial', 9, 'bold')).pack(anchor='w')
        
        fwd2_select = tk.Frame(fwd2_frame, bg='#ecf0f1')
        fwd2_select.pack(fill=tk.X, pady=2)
        
        self.fwd2_start_var = tk.StringVar(value='4y')
        self.fwd2_tenor_var = tk.StringVar(value='2Y')
        
        ttk.Combobox(fwd2_select, textvariable=self.fwd2_start_var,
                    values=self.forward_periods, width=8, state='readonly').pack(side=tk.LEFT, padx=2)
        tk.Label(fwd2_select, text="x", bg='#ecf0f1').pack(side=tk.LEFT)
        ttk.Combobox(fwd2_select, textvariable=self.fwd2_tenor_var,
                    values=self.tenors, width=8, state='readonly').pack(side=tk.LEFT, padx=2)
        
        tk.Label(fwd2_frame, text="Spread = Fwd1 - Fwd2", bg='#ecf0f1',
                font=('Arial', 8, 'italic'), fg='#7f8c8d').pack(anchor='w', pady=2)
        
        # Curve Spread (Y-Axis)
        self.add_section(params, "Curve Spread (Y-Axis)")
        
        curve_frame = tk.Frame(params, bg='#ecf0f1')
        curve_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(curve_frame, text="Tenor 1:", bg='#ecf0f1', 
                font=('Arial', 9, 'bold')).pack(anchor='w')
        
        tenor1_select = tk.Frame(curve_frame, bg='#ecf0f1')
        tenor1_select.pack(fill=tk.X, pady=2)
        
        self.curve_tenor1_var = tk.StringVar(value='2Y')
        ttk.Combobox(tenor1_select, textvariable=self.curve_tenor1_var,
                    values=self.tenors, width=12, state='readonly').pack(side=tk.LEFT, padx=2)
        
        tk.Label(curve_frame, text="Tenor 2:", bg='#ecf0f1', 
                font=('Arial', 9, 'bold')).pack(anchor='w', pady=(10, 0))
        
        tenor2_select = tk.Frame(curve_frame, bg='#ecf0f1')
        tenor2_select.pack(fill=tk.X, pady=2)
        
        self.curve_tenor2_var = tk.StringVar(value='10Y')
        ttk.Combobox(tenor2_select, textvariable=self.curve_tenor2_var,
                    values=self.tenors, width=12, state='readonly').pack(side=tk.LEFT, padx=2)
        
        tk.Label(curve_frame, text="Spread = Tenor2 - Tenor1", bg='#ecf0f1',
                font=('Arial', 8, 'italic'), fg='#7f8c8d').pack(anchor='w', pady=2)
        
        # Chart type
        self.add_section(params, "Chart Type")
        chart_frame = tk.Frame(params, bg='#ecf0f1')
        chart_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.chart_type_var = tk.StringVar(value='scatter')
        tk.Radiobutton(chart_frame, text="Scatter Plot", variable=self.chart_type_var,
                      value='scatter', bg='#ecf0f1', font=('Arial', 9)).pack(anchor='w')
        tk.Radiobutton(chart_frame, text="Time Series", variable=self.chart_type_var,
                      value='timeseries', bg='#ecf0f1', font=('Arial', 9)).pack(anchor='w')
        tk.Radiobutton(chart_frame, text="Both (Dual View)", variable=self.chart_type_var,
                      value='both', bg='#ecf0f1', font=('Arial', 9)).pack(anchor='w')
        
        # Buttons
        btn_frame = tk.Frame(params, bg='#ecf0f1')
        btn_frame.pack(fill=tk.X, padx=10, pady=20)
        
        tk.Button(btn_frame, text="🔄 Analyze", command=self.analyze,
                 bg='#27ae60', fg='white', font=('Arial', 11, 'bold'),
                 padx=20, pady=10, cursor='hand2').pack(fill=tk.X, pady=5)
        
        tk.Button(btn_frame, text="💾 Export Data", command=self.export_data,
                 bg='#3498db', fg='white', font=('Arial', 10, 'bold'),
                 padx=20, pady=8, cursor='hand2').pack(fill=tk.X, pady=5)
        
        # Status
        self.status_var = tk.StringVar(value="Ready - Configure parameters and click Analyze")
        tk.Label(params, textvariable=self.status_var, bg='#ecf0f1',
                font=('Arial', 9), fg='#7f8c8d', wraplength=350, justify='left').pack(pady=10, padx=10)
    
    def add_section(self, parent, title):
        """Add section header"""
        tk.Label(parent, text=title, bg='#3498db', fg='white',
                font=('Arial', 10, 'bold'), pady=5).pack(fill=tk.X, padx=5, pady=(10, 5))
    
    def toggle_currency_mode(self):
        """Toggle between single and cross-currency mode"""
        if self.mode_var.get() == 'single':
            self.cross_curr_frame.pack_forget()
            self.single_curr_frame.pack(fill=tk.X, padx=10, pady=5)
            self.status_var.set("Single currency mode - analyzing one currency")
        else:
            self.single_curr_frame.pack_forget()
            self.cross_curr_frame.pack(fill=tk.X, padx=10, pady=5)
            self.status_var.set("Cross-currency mode - analyzing currency basis (e.g., AUD vs NZD)")
    
    def period_to_years(self, period):
        """Convert period string to years"""
        period = period.lower().strip()
        if period.endswith('y'):
            return float(period[:-1])
        elif period.endswith('m'):
            return float(period[:-1]) / 12
        return 0
    
    def tenor_to_years(self, tenor):
        """Convert tenor string to years"""
        tenor = tenor.upper().strip()
        if tenor.endswith('Y'):
            return int(tenor[:-1])
        elif tenor.endswith('M'):
            return int(tenor[:-1]) / 12
        return 0
    
    def get_spot_curve(self, currency, floating_rate, date):
        """Get spot curve from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if currency == 'AUD':
                fixing = f'{floating_rate} BBSW'
            elif currency == 'NZD':
                fixing = f'{floating_rate} BKBM'
            else:
                fixing = floating_rate
            
            cursor.execute("""
                SELECT tenor, rate
                FROM swap_rates
                WHERE date = ? AND currency = ?
                AND (floating_rate = ? OR floating_rate LIKE ?)
                ORDER BY tenor
            """, (date, currency, fixing, f"{floating_rate}%"))
            
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                return None
            
            curve = {}
            for tenor, rate in rows:
                curve[tenor] = rate
            
            return curve
            
        except Exception as e:
            print(f"Error getting spot curve: {e}")
            return None
    
    def interpolate_rate(self, curve, years):
        """Cubic spline or linear interpolation"""
        points = [(self.tenor_to_years(t), r) for t, r in curve.items()]
        points.sort()
        
        if not points:
            return None
        
        for y, r in points:
            if abs(y - years) < 0.01:
                return r
        
        if len(points) < 2:
            return points[0][1] if points else None
        
        x_points = np.array([p[0] for p in points])
        y_points = np.array([p[1] for p in points])
        
        if years < x_points[0]:
            return y_points[0]
        elif years > x_points[-1]:
            return y_points[-1]
        
        # Use cubic spline if available
        if SCIPY_AVAILABLE and len(points) >= 3:
            try:
                cs = CubicSpline(x_points, y_points, bc_type='natural')
                return float(cs(years))
            except:
                pass  # Fall through to linear
        
        # Linear interpolation fallback
        for i in range(len(points) - 1):
            y1, r1 = points[i]
            y2, r2 = points[i + 1]
            if y1 <= years <= y2:
                t = (years - y1) / (y2 - y1)
                return r1 + t * (r2 - r1)
        return None
    
    def manual_linregress(self, x, y):
        """Manual linear regression when scipy not available"""
        x = np.array(x)
        y = np.array(y)
        n = len(x)
        
        x_mean = np.mean(x)
        y_mean = np.mean(y)
        
        # Calculate slope
        numerator = np.sum((x - x_mean) * (y - y_mean))
        denominator = np.sum((x - x_mean) ** 2)
        slope = numerator / denominator if denominator != 0 else 0
        
        # Calculate intercept
        intercept = y_mean - slope * x_mean
        
        # Calculate correlation coefficient
        x_std = np.std(x)
        y_std = np.std(y)
        if x_std > 0 and y_std > 0:
            r_value = numerator / (n * x_std * y_std)
        else:
            r_value = 0
        
        return slope, intercept, r_value
    
    def calculate_forward_rate(self, spot_curve, forward_years, tenor_years):
        """Calculate forward rate"""
        r1 = self.interpolate_rate(spot_curve, forward_years)
        r2 = self.interpolate_rate(spot_curve, forward_years + tenor_years)
        
        if r1 is None or r2 is None:
            return None
        
        t1 = forward_years
        t2 = forward_years + tenor_years
        
        try:
            forward_rate = ((1 + r2)**t2 / (1 + r1)**t1)**(1/(t2 - t1)) - 1
            return forward_rate
        except:
            return None
    
    def get_available_dates(self):
        """Get available dates in date range"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            currency = self.currency_var.get()
            floating_rate = self.floating_var.get()
            start_date = self.start_date.get_date().strftime('%Y-%m-%d')
            end_date = self.end_date.get_date().strftime('%Y-%m-%d')
            
            if currency == 'AUD':
                fixing = f'{floating_rate} BBSW'
            elif currency == 'NZD':
                fixing = f'{floating_rate} BKBM'
            else:
                fixing = floating_rate
            
            cursor.execute("""
                SELECT DISTINCT date
                FROM swap_rates
                WHERE currency = ? 
                AND (floating_rate = ? OR floating_rate LIKE ?)
                AND date BETWEEN ? AND ?
                ORDER BY date
            """, (currency, fixing, f"{floating_rate}%", start_date, end_date))
            
            dates = [row[0] for row in cursor.fetchall()]
            conn.close()
            return dates
            
        except Exception as e:
            print(f"Error getting dates: {e}")
            return []
    
    def analyze(self):
        """Perform relative value analysis"""
        self.status_var.set("Analyzing... Please wait")
        self.root.update()
        
        # Check mode
        mode = self.mode_var.get()
        
        if mode == 'single':
            self.analyze_single_currency()
        else:
            self.analyze_cross_currency()
    
    def analyze_single_currency(self):
        """Analyze single currency relative value"""
        # Get parameters
        currency = self.currency_var.get()
        floating_rate = self.floating_var.get()
        
        # Forward structures
        fwd1_start = self.period_to_years(self.fwd1_start_var.get())
        fwd1_tenor = self.tenor_to_years(self.fwd1_tenor_var.get())
        fwd2_start = self.period_to_years(self.fwd2_start_var.get())
        fwd2_tenor = self.tenor_to_years(self.fwd2_tenor_var.get())
        
        # Curve tenors
        curve_tenor1 = self.tenor_to_years(self.curve_tenor1_var.get())
        curve_tenor2 = self.tenor_to_years(self.curve_tenor2_var.get())
        
        # Get dates
        dates = self.get_available_dates()
        
        if not dates:
            messagebox.showerror("Error", "No data found for selected parameters")
            self.status_var.set("Error - No data")
            return
        
        # Calculate spreads for each date
        forward_spreads = []
        curve_spreads = []
        valid_dates = []
        
        for date in dates:
            curve = self.get_spot_curve(currency, floating_rate, date)
            if not curve:
                continue
            
            # Calculate forwards
            fwd1_rate = self.calculate_forward_rate(curve, fwd1_start, fwd1_tenor)
            fwd2_rate = self.calculate_forward_rate(curve, fwd2_start, fwd2_tenor)
            
            # Calculate spot rates for curve spread
            spot1 = self.interpolate_rate(curve, curve_tenor1)
            spot2 = self.interpolate_rate(curve, curve_tenor2)
            
            if all(x is not None for x in [fwd1_rate, fwd2_rate, spot1, spot2]):
                forward_spread = (fwd1_rate - fwd2_rate) * 10000  # In bp
                curve_spread = (spot2 - spot1) * 10000  # In bp
                
                forward_spreads.append(forward_spread)
                curve_spreads.append(curve_spread)
                valid_dates.append(date)
        
        if len(forward_spreads) < 2:
            messagebox.showerror("Error", "Insufficient data points for analysis")
            self.status_var.set("Error - Insufficient data")
            return
        
        # Store data for export
        self.analysis_data = {
            'dates': valid_dates,
            'forward_spreads': forward_spreads,
            'curve_spreads': curve_spreads,
            'parameters': {
                'mode': 'single',
                'currency': currency,
                'floating_rate': floating_rate,
                'fwd1': f"{self.fwd1_start_var.get()}x{self.fwd1_tenor_var.get()}",
                'fwd2': f"{self.fwd2_start_var.get()}x{self.fwd2_tenor_var.get()}",
                'curve_tenor1': self.curve_tenor1_var.get(),
                'curve_tenor2': self.curve_tenor2_var.get()
            }
        }
        
        # Plot
        chart_type = self.chart_type_var.get()
        if chart_type == 'scatter':
            self.plot_scatter(forward_spreads, curve_spreads, valid_dates)
        elif chart_type == 'timeseries':
            self.plot_timeseries(forward_spreads, curve_spreads, valid_dates)
        else:  # both
            self.plot_both(forward_spreads, curve_spreads, valid_dates)
        
        self.status_var.set(f"Analysis complete - {len(valid_dates)} data points")
    
    def analyze_cross_currency(self):
        """Analyze cross-currency basis"""
        # Get parameters
        currency1 = self.currency1_var.get()
        currency2 = self.currency2_var.get()
        floating_rate = self.cross_floating_var.get()
        
        if currency1 == currency2:
            messagebox.showerror("Error", "Please select two different currencies")
            self.status_var.set("Error - Same currency selected")
            return
        
        # Forward structures
        fwd1_start = self.period_to_years(self.fwd1_start_var.get())
        fwd1_tenor = self.tenor_to_years(self.fwd1_tenor_var.get())
        fwd2_start = self.period_to_years(self.fwd2_start_var.get())
        fwd2_tenor = self.tenor_to_years(self.fwd2_tenor_var.get())
        
        # Curve tenors
        curve_tenor1 = self.tenor_to_years(self.curve_tenor1_var.get())
        curve_tenor2 = self.tenor_to_years(self.curve_tenor2_var.get())
        
        # Get dates
        dates = self.get_available_dates()
        
        if not dates:
            messagebox.showerror("Error", "No data found for selected parameters")
            self.status_var.set("Error - No data")
            return
        
        # Calculate spreads for each date
        forward_basis = []
        curve_basis = []
        valid_dates = []
        
        for date in dates:
            # Get curves for both currencies
            curve1 = self.get_spot_curve(currency1, floating_rate, date)
            curve2 = self.get_spot_curve(currency2, floating_rate, date)
            
            if not curve1 or not curve2:
                continue
            
            # Calculate forwards for currency 1
            fwd1_rate_c1 = self.calculate_forward_rate(curve1, fwd1_start, fwd1_tenor)
            fwd2_rate_c1 = self.calculate_forward_rate(curve1, fwd2_start, fwd2_tenor)
            spot1_c1 = self.interpolate_rate(curve1, curve_tenor1)
            spot2_c1 = self.interpolate_rate(curve1, curve_tenor2)
            
            # Calculate forwards for currency 2
            fwd1_rate_c2 = self.calculate_forward_rate(curve2, fwd1_start, fwd1_tenor)
            fwd2_rate_c2 = self.calculate_forward_rate(curve2, fwd2_start, fwd2_tenor)
            spot1_c2 = self.interpolate_rate(curve2, curve_tenor1)
            spot2_c2 = self.interpolate_rate(curve2, curve_tenor2)
            
            if all(x is not None for x in [fwd1_rate_c1, fwd2_rate_c1, spot1_c1, spot2_c1,
                                          fwd1_rate_c2, fwd2_rate_c2, spot1_c2, spot2_c2]):
                # Calculate spreads
                forward_spread_c1 = (fwd1_rate_c1 - fwd2_rate_c1) * 10000
                forward_spread_c2 = (fwd1_rate_c2 - fwd2_rate_c2) * 10000
                curve_spread_c1 = (spot2_c1 - spot1_c1) * 10000
                curve_spread_c2 = (spot2_c2 - spot1_c2) * 10000
                
                # Calculate basis (difference between currencies)
                fwd_basis = forward_spread_c1 - forward_spread_c2
                crv_basis = curve_spread_c1 - curve_spread_c2
                
                forward_basis.append(fwd_basis)
                curve_basis.append(crv_basis)
                valid_dates.append(date)
        
        if len(forward_basis) < 2:
            messagebox.showerror("Error", "Insufficient data points for cross-currency analysis")
            self.status_var.set("Error - Insufficient data")
            return
        
        # Store data for export
        self.analysis_data = {
            'dates': valid_dates,
            'forward_spreads': forward_basis,
            'curve_spreads': curve_basis,
            'parameters': {
                'mode': 'cross',
                'currency1': currency1,
                'currency2': currency2,
                'floating_rate': floating_rate,
                'fwd1': f"{self.fwd1_start_var.get()}x{self.fwd1_tenor_var.get()}",
                'fwd2': f"{self.fwd2_start_var.get()}x{self.fwd2_tenor_var.get()}",
                'curve_tenor1': self.curve_tenor1_var.get(),
                'curve_tenor2': self.curve_tenor2_var.get()
            }
        }
        
        # Plot
        chart_type = self.chart_type_var.get()
        if chart_type == 'scatter':
            self.plot_scatter(forward_basis, curve_basis, valid_dates)
        elif chart_type == 'timeseries':
            self.plot_timeseries(forward_basis, curve_basis, valid_dates)
        else:  # both
            self.plot_both(forward_basis, curve_basis, valid_dates)
        
        self.status_var.set(f"Cross-currency analysis complete - {len(valid_dates)} data points")
    
        
        # Plot
        chart_type = self.chart_type_var.get()
        if chart_type == 'scatter':
            self.plot_scatter(forward_spreads, curve_spreads, valid_dates)
        elif chart_type == 'timeseries':
            self.plot_timeseries(forward_spreads, curve_spreads, valid_dates)
        else:  # both
            self.plot_both(forward_spreads, curve_spreads, valid_dates)
        
        self.status_var.set(f"Analysis complete - {len(valid_dates)} data points")
    
    def plot_scatter(self, fwd_spreads, curve_spreads, dates):
        """Plot scatter chart"""
        # Clear previous chart
        for widget in self.right_panel.winfo_children():
            widget.destroy()
        
        # Create figure
        fig = plt.Figure(figsize=(12, 8), dpi=100)
        ax = fig.add_subplot(111)
        
        # Scatter plot
        scatter = ax.scatter(fwd_spreads, curve_spreads, c=range(len(dates)), 
                           cmap='viridis', s=50, alpha=0.6, edgecolors='black', linewidth=0.5)
        
        # Linear regression
        if SCIPY_AVAILABLE:
            slope, intercept, r_value, p_value, std_err = stats.linregress(fwd_spreads, curve_spreads)
        else:
            slope, intercept, r_value = self.manual_linregress(fwd_spreads, curve_spreads)
        line_x = np.array([min(fwd_spreads), max(fwd_spreads)])
        line_y = slope * line_x + intercept
        ax.plot(line_x, line_y, 'r--', linewidth=2, label=f'Fit: y={slope:.3f}x+{intercept:.1f}\nR²={r_value**2:.3f}')
        
        # Labels
        params = self.analysis_data['parameters']
        
        if params.get('mode') == 'cross':
            # Cross-currency mode
            curr_label = f"{params['currency1']} vs {params['currency2']}"
            title = f"{curr_label} Basis Analysis\nScatter Plot: Forward Basis vs Curve Basis"
            xlabel = f"Forward Basis: {params['fwd1']} - {params['fwd2']} ({params['currency1']}-{params['currency2']}) (bp)"
            ylabel = f"Curve Basis: {params['curve_tenor2']} - {params['curve_tenor1']} ({params['currency1']}-{params['currency2']}) (bp)"
        else:
            # Single currency mode
            curr_label = f"{params['currency']} {params['floating_rate']}"
            title = f"{curr_label} Relative Value Analysis\nScatter Plot: Forward Spread vs Curve Spread"
            xlabel = f"Forward Spread: {params['fwd1']} - {params['fwd2']} (bp)"
            ylabel = f"Curve Spread: {params['curve_tenor2']} - {params['curve_tenor1']} (bp)"
        
        ax.set_xlabel(xlabel, fontsize=12, fontweight='bold')
        ax.set_ylabel(ylabel, fontsize=12, fontweight='bold')
        ax.set_title(title, fontsize=14, fontweight='bold')
        
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=10, loc='best')
        
        # Colorbar
        cbar = fig.colorbar(scatter, ax=ax, label='Time Progression (oldest → newest)')
        
        plt.tight_layout()
        
        # Add hover tooltips
        if MPLCURSORS_AVAILABLE:
            # Use mplcursors for nice hover tooltips
            cursor = mplcursors.cursor(scatter, hover=True)
            
            # Calculate statistics for context
            fwd_mean = np.mean(fwd_spreads)
            fwd_std = np.std(fwd_spreads)
            curve_mean = np.mean(curve_spreads)
            curve_std = np.std(curve_spreads)
            
            @cursor.connect("add")
            def on_add(sel):
                idx = sel.index
                fwd_val = fwd_spreads[idx]
                curve_val = curve_spreads[idx]
                
                # Calculate z-scores (standard deviations from mean)
                fwd_zscore = (fwd_val - fwd_mean) / fwd_std if fwd_std > 0 else 0
                curve_zscore = (curve_val - curve_mean) / curve_std if curve_std > 0 else 0
                
                # Format with rich information
                text = (
                    f"📅 Date: {dates[idx]}\n"
                    f"═══════════════════════\n"
                    f"Forward Spread: {fwd_val:.2f} bp\n"
                    f"  Deviation: {fwd_zscore:+.2f}σ\n"
                    f"  vs Mean: {fwd_val - fwd_mean:+.2f} bp\n"
                    f"─────────────────────\n"
                    f"Curve Spread: {curve_val:.2f} bp\n"
                    f"  Deviation: {curve_zscore:+.2f}σ\n"
                    f"  vs Mean: {curve_val - curve_mean:+.2f} bp"
                )
                
                sel.annotation.set_text(text)
                sel.annotation.set_fontsize(9)
                sel.annotation.get_bbox_patch().set(
                    fc="lightyellow", 
                    alpha=0.95, 
                    edgecolor="darkblue",
                    linewidth=2,
                    boxstyle="round,pad=0.8"
                )
        else:
            # Fallback: enhanced matplotlib annotation
            annot = ax.annotate("", xy=(0,0), xytext=(15,15), textcoords="offset points",
                              bbox=dict(boxstyle="round,pad=0.8", fc="lightyellow", alpha=0.95, 
                                       edgecolor="darkblue", linewidth=2),
                              arrowprops=dict(arrowstyle="->", color="darkblue", lw=2),
                              fontsize=9)
            annot.set_visible(False)
            
            # Calculate statistics
            fwd_mean = np.mean(fwd_spreads)
            fwd_std = np.std(fwd_spreads)
            curve_mean = np.mean(curve_spreads)
            curve_std = np.std(curve_spreads)
            
            def hover(event):
                if event.inaxes == ax:
                    cont, ind = scatter.contains(event)
                    if cont:
                        idx = ind["ind"][0]
                        fwd_val = fwd_spreads[idx]
                        curve_val = curve_spreads[idx]
                        fwd_zscore = (fwd_val - fwd_mean) / fwd_std if fwd_std > 0 else 0
                        curve_zscore = (curve_val - curve_mean) / curve_std if curve_std > 0 else 0
                        
                        annot.xy = (fwd_val, curve_val)
                        text = (
                            f"📅 {dates[idx]}\n"
                            f"Forward: {fwd_val:.2f} bp ({fwd_zscore:+.1f}σ)\n"
                            f"Curve: {curve_val:.2f} bp ({curve_zscore:+.1f}σ)"
                        )
                        annot.set_text(text)
                        annot.set_visible(True)
                        fig.canvas.draw_idle()
                    else:
                        if annot.get_visible():
                            annot.set_visible(False)
                            fig.canvas.draw_idle()
            
            fig.canvas.mpl_connect("motion_notify_event", hover)
        
        # Embed
        canvas = FigureCanvasTkAgg(fig, master=self.right_panel)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Stats label
        stats_text = (f"Correlation: {r_value:.3f} | R²: {r_value**2:.3f} | "
                     f"Data points: {len(dates)} | "
                     f"Period: {dates[0]} to {dates[-1]}")
        tk.Label(self.right_panel, text=stats_text, font=('Arial', 9), 
                fg='#7f8c8d', bg='white').pack(pady=5)
    
    def plot_timeseries(self, fwd_spreads, curve_spreads, dates):
        """Plot time series chart"""
        # Clear previous chart
        for widget in self.right_panel.winfo_children():
            widget.destroy()
        
        # Create figure
        fig = plt.Figure(figsize=(12, 8), dpi=100)
        ax1 = fig.add_subplot(111)
        
        # Convert dates
        date_objs = [datetime.strptime(d, '%Y-%m-%d') for d in dates]
        
        # Title
        params = self.analysis_data['parameters']
        
        if params.get('mode') == 'cross':
            curr_label = f"{params['currency1']} vs {params['currency2']}"
            title = f"{curr_label} Basis Analysis\nTime Series: {params['fwd1']}-{params['fwd2']} vs {params['curve_tenor2']}-{params['curve_tenor1']}"
            fwd_label = 'Forward Basis'
            curve_label = 'Curve Basis'
        else:
            curr_label = f"{params['currency']} {params['floating_rate']}"
            title = f"{curr_label} Relative Value Analysis\nTime Series: {params['fwd1']}-{params['fwd2']} vs {params['curve_tenor2']}-{params['curve_tenor1']}"
            fwd_label = 'Forward Spread'
            curve_label = 'Curve Spread'
        
        # Plot forward spread
        ax1.plot(date_objs, fwd_spreads, 'b-', linewidth=2, label=fwd_label, marker='o', markersize=3)
        ax1.set_xlabel('Date', fontsize=12, fontweight='bold')
        ax1.set_ylabel(f'{fwd_label} (bp)', fontsize=12, fontweight='bold', color='b')
        ax1.tick_params(axis='y', labelcolor='b')
        ax1.grid(True, alpha=0.3)
        
        # Plot curve spread on secondary axis
        ax2 = ax1.twinx()
        ax2.plot(date_objs, curve_spreads, 'r-', linewidth=2, label=curve_label, marker='s', markersize=3)
        ax2.set_ylabel(f'{curve_label} (bp)', fontsize=12, fontweight='bold', color='r')
        ax2.tick_params(axis='y', labelcolor='r')
        
        ax1.set_title(title, fontsize=14, fontweight='bold')
        
        # Legends
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='best', fontsize=10)
        
        # Rotate x-axis labels
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        plt.tight_layout()
        
        # Add hover tooltips for time series
        if MPLCURSORS_AVAILABLE:
            # Add cursor to both lines
            lines = ax1.get_lines() + ax2.get_lines()
            cursor = mplcursors.cursor(lines, hover=True)
            
            # Calculate stats
            fwd_mean = np.mean(fwd_spreads)
            curve_mean = np.mean(curve_spreads)
            
            @cursor.connect("add")
            def on_add(sel):
                idx = sel.index
                fwd_val = fwd_spreads[idx]
                curve_val = curve_spreads[idx]
                
                # Show both values always
                text = (
                    f"📅 {dates[idx]}\n"
                    f"═══════════════════\n"
                    f"{fwd_label}: {fwd_val:.2f} bp\n"
                    f"  (Mean: {fwd_mean:.2f}, Δ{fwd_val-fwd_mean:+.2f})\n"
                    f"─────────────────\n"
                    f"{curve_label}: {curve_val:.2f} bp\n"
                    f"  (Mean: {curve_mean:.2f}, Δ{curve_val-curve_mean:+.2f})"
                )
                
                sel.annotation.set_text(text)
                sel.annotation.set_fontsize(9)
                
                # Color based on which line was hovered
                if sel.artist in ax1.get_lines():
                    color = "lightblue"
                    edge = "blue"
                else:
                    color = "lightcoral"
                    edge = "red"
                
                sel.annotation.get_bbox_patch().set(
                    fc=color,
                    alpha=0.95,
                    edgecolor=edge,
                    linewidth=2,
                    boxstyle="round,pad=0.8"
                )
        else:
            # Enhanced fallback
            annot = ax1.annotate("", xy=(0,0), xytext=(15,15), textcoords="offset points",
                               bbox=dict(boxstyle="round,pad=0.8", fc="lightyellow", alpha=0.95, 
                                        edgecolor="darkgreen", linewidth=2),
                               arrowprops=dict(arrowstyle="->", color="darkgreen", lw=2),
                               fontsize=9)
            annot.set_visible(False)
            
            fwd_mean = np.mean(fwd_spreads)
            curve_mean = np.mean(curve_spreads)
            
            def hover(event):
                if event.inaxes in [ax1, ax2]:
                    if event.xdata is not None:
                        x_date = matplotlib.dates.num2date(event.xdata)
                        distances = [abs((d - x_date).total_seconds()) for d in date_objs]
                        idx = distances.index(min(distances))
                        
                        annot.xy = (date_objs[idx], fwd_spreads[idx] if event.inaxes == ax1 else curve_spreads[idx])
                        text = (
                            f"📅 {dates[idx]}\n"
                            f"{fwd_label}: {fwd_spreads[idx]:.2f} bp\n"
                            f"{curve_label}: {curve_spreads[idx]:.2f} bp"
                        )
                        annot.set_text(text)
                        annot.set_visible(True)
                        fig.canvas.draw_idle()
                else:
                    if annot.get_visible():
                        annot.set_visible(False)
                        fig.canvas.draw_idle()
            
            fig.canvas.mpl_connect("motion_notify_event", hover)
        
        # Embed
        canvas = FigureCanvasTkAgg(fig, master=self.right_panel)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Stats
        corr = np.corrcoef(fwd_spreads, curve_spreads)[0, 1]
        stats_text = (f"Correlation: {corr:.3f} | "
                     f"Fwd Spread Range: [{min(fwd_spreads):.1f}, {max(fwd_spreads):.1f}] bp | "
                     f"Curve Spread Range: [{min(curve_spreads):.1f}, {max(curve_spreads):.1f}] bp")
        tk.Label(self.right_panel, text=stats_text, font=('Arial', 9),
                fg='#7f8c8d', bg='white').pack(pady=5)
    
    def plot_both(self, fwd_spreads, curve_spreads, dates):
        """Plot both scatter and time series"""
        # Clear previous chart
        for widget in self.right_panel.winfo_children():
            widget.destroy()
        
        # Create figure with 2 subplots
        fig = plt.Figure(figsize=(12, 10), dpi=100)
        
        params = self.analysis_data['parameters']
        
        # Determine labels based on mode
        if params.get('mode') == 'cross':
            curr_label = f"{params['currency1']} vs {params['currency2']}"
            fwd_label = 'Forward Basis'
            curve_label = 'Curve Basis'
            xlabel = f"Forward Basis: {params['fwd1']} - {params['fwd2']} ({params['currency1']}-{params['currency2']}) (bp)"
            ylabel = f"Curve Basis: {params['curve_tenor2']} - {params['curve_tenor1']} ({params['currency1']}-{params['currency2']}) (bp)"
        else:
            curr_label = f"{params['currency']} {params['floating_rate']}"
            fwd_label = 'Forward Spread'
            curve_label = 'Curve Spread'
            xlabel = f"Forward Spread: {params['fwd1']} - {params['fwd2']} (bp)"
            ylabel = f"Curve Spread: {params['curve_tenor2']} - {params['curve_tenor1']} (bp)"
        
        # Scatter plot (top)
        ax1 = fig.add_subplot(211)
        scatter = ax1.scatter(fwd_spreads, curve_spreads, c=range(len(dates)), 
                            cmap='viridis', s=50, alpha=0.6, edgecolors='black', linewidth=0.5)
        
        if SCIPY_AVAILABLE:
            slope, intercept, r_value, _, _ = stats.linregress(fwd_spreads, curve_spreads)
        else:
            slope, intercept, r_value = self.manual_linregress(fwd_spreads, curve_spreads)
        line_x = np.array([min(fwd_spreads), max(fwd_spreads)])
        line_y = slope * line_x + intercept
        ax1.plot(line_x, line_y, 'r--', linewidth=2, label=f'R²={r_value**2:.3f}')
        
        ax1.set_xlabel(xlabel, fontsize=11, fontweight='bold')
        ax1.set_ylabel(ylabel, fontsize=11, fontweight='bold')
        ax1.set_title(f"{curr_label} - Scatter Plot (Correlation Analysis)", fontsize=12, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend(fontsize=9)
        
        # Time series (bottom)
        ax2 = fig.add_subplot(212)
        date_objs = [datetime.strptime(d, '%Y-%m-%d') for d in dates]
        
        ax2.plot(date_objs, fwd_spreads, 'b-', linewidth=2, label=fwd_label, marker='o', markersize=2)
        ax2.set_xlabel('Date', fontsize=11, fontweight='bold')
        ax2.set_ylabel(f'{fwd_label} (bp)', fontsize=11, fontweight='bold', color='b')
        ax2.tick_params(axis='y', labelcolor='b')
        ax2.grid(True, alpha=0.3)
        
        ax3 = ax2.twinx()
        ax3.plot(date_objs, curve_spreads, 'r-', linewidth=2, label=curve_label, marker='s', markersize=2)
        ax3.set_ylabel(f'{curve_label} (bp)', fontsize=11, fontweight='bold', color='r')
        ax3.tick_params(axis='y', labelcolor='r')
        
        ax2.set_title(f"{curr_label} - Time Series (Historical Evolution)", fontsize=12, fontweight='bold')
        
        lines1, labels1 = ax2.get_legend_handles_labels()
        lines2, labels2 = ax3.get_legend_handles_labels()
        ax2.legend(lines1 + lines2, labels1 + labels2, loc='best', fontsize=9)
        
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        fig.suptitle(f"{params.get('currency1', params.get('currency'))} Relative Value Analysis" if params.get('mode') != 'cross' else f"{params['currency1']} vs {params['currency2']} Basis Analysis",
                    fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        
        # Add hover tooltips to both subplots
        if MPLCURSORS_AVAILABLE:
            # Scatter plot hover
            cursor1 = mplcursors.cursor(scatter, hover=True)
            @cursor1.connect("add")
            def on_add_scatter(sel):
                idx = sel.index
                sel.annotation.set_text(
                    f"Date: {dates[idx]}\n"
                    f"Forward: {fwd_spreads[idx]:.2f} bp\n"
                    f"Curve: {curve_spreads[idx]:.2f} bp"
                )
                sel.annotation.get_bbox_patch().set(fc="white", alpha=0.9, edgecolor="black")
            
            # Time series hover
            lines = ax2.get_lines() + ax3.get_lines()
            cursor2 = mplcursors.cursor(lines, hover=True)
            @cursor2.connect("add")
            def on_add_ts(sel):
                idx = sel.index
                if sel.artist in ax2.get_lines():
                    sel.annotation.set_text(
                        f"Date: {dates[idx]}\n"
                        f"{fwd_label}: {fwd_spreads[idx]:.2f} bp"
                    )
                else:
                    sel.annotation.set_text(
                        f"Date: {dates[idx]}\n"
                        f"{curve_label}: {curve_spreads[idx]:.2f} bp"
                    )
                sel.annotation.get_bbox_patch().set(fc="white", alpha=0.9, edgecolor="black")
        else:
            # Fallback: basic hover for scatter
            annot1 = ax1.annotate("", xy=(0,0), xytext=(10,10), textcoords="offset points",
                                bbox=dict(boxstyle="round", fc="white", alpha=0.9, edgecolor="black"),
                                arrowprops=dict(arrowstyle="->"))
            annot1.set_visible(False)
            
            annot2 = ax2.annotate("", xy=(0,0), xytext=(10,10), textcoords="offset points",
                                bbox=dict(boxstyle="round", fc="white", alpha=0.9, edgecolor="black"))
            annot2.set_visible(False)
            
            def hover(event):
                # Scatter plot hover
                if event.inaxes == ax1:
                    cont, ind = scatter.contains(event)
                    if cont:
                        idx = ind["ind"][0]
                        annot1.xy = (fwd_spreads[idx], curve_spreads[idx])
                        annot1.set_text(
                            f"Date: {dates[idx]}\n"
                            f"Forward: {fwd_spreads[idx]:.2f} bp\n"
                            f"Curve: {curve_spreads[idx]:.2f} bp"
                        )
                        annot1.set_visible(True)
                        fig.canvas.draw_idle()
                    else:
                        if annot1.get_visible():
                            annot1.set_visible(False)
                            fig.canvas.draw_idle()
                
                # Time series hover
                elif event.inaxes in [ax2, ax3]:
                    if event.xdata is not None:
                        x_date = matplotlib.dates.num2date(event.xdata)
                        distances = [abs((d - x_date).total_seconds()) for d in date_objs]
                        idx = distances.index(min(distances))
                        
                        annot2.xy = (date_objs[idx], fwd_spreads[idx] if event.inaxes == ax2 else curve_spreads[idx])
                        annot2.set_text(
                            f"Date: {dates[idx]}\n"
                            f"{fwd_label}: {fwd_spreads[idx]:.2f} bp\n"
                            f"{curve_label}: {curve_spreads[idx]:.2f} bp"
                        )
                        annot2.set_visible(True)
                        fig.canvas.draw_idle()
                else:
                    if annot1.get_visible():
                        annot1.set_visible(False)
                        fig.canvas.draw_idle()
                    if annot2.get_visible():
                        annot2.set_visible(False)
                        fig.canvas.draw_idle()
            
            fig.canvas.mpl_connect("motion_notify_event", hover)
        
        # Embed
        canvas = FigureCanvasTkAgg(fig, master=self.right_panel)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def export_data(self):
        """Export analysis data to CSV"""
        if not hasattr(self, 'analysis_data'):
            messagebox.showwarning("Warning", "No analysis data to export. Run analysis first.")
            return
        
        from tkinter import filedialog
        import csv
        
        filename = filedialog.asksaveasfilename(
            defaultextension='.csv',
            filetypes=[('CSV files', '*.csv'), ('All files', '*.*')],
            initialfile=f"RelativeValue_{self.analysis_data['parameters']['currency']}.csv"
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    
                    # Header
                    params = self.analysis_data['parameters']
                    writer.writerow(['Swap Relative Value Analysis'])
                    writer.writerow(['Currency', params['currency']])
                    writer.writerow(['Floating Rate', params['floating_rate']])
                    writer.writerow(['Forward 1', params['fwd1']])
                    writer.writerow(['Forward 2', params['fwd2']])
                    writer.writerow(['Curve Tenor 1', params['curve_tenor1']])
                    writer.writerow(['Curve Tenor 2', params['curve_tenor2']])
                    writer.writerow([])
                    
                    # Data
                    writer.writerow(['Date', 'Forward Spread (bp)', 'Curve Spread (bp)'])
                    for date, fwd_spread, curve_spread in zip(
                        self.analysis_data['dates'],
                        self.analysis_data['forward_spreads'],
                        self.analysis_data['curve_spreads']
                    ):
                        writer.writerow([date, f"{fwd_spread:.3f}", f"{curve_spread:.3f}"])
                
                messagebox.showinfo("Success", f"Data exported to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export data:\n{e}")

def main():
    root = tk.Tk()
    app = SwapRelativeValueAnalyzer(root)
    root.mainloop()

if __name__ == '__main__':
    main()
