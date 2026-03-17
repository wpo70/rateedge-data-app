"""
Simple Forward Swap Pricer
Full-featured swap pricing with proper date handling
Uses CUBIC SPLINE interpolation when available
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import os
import sqlite3
from dateutil.relativedelta import relativedelta

# Try to import cubic spline - fall back to linear if not available
try:
    from scipy.interpolate import CubicSpline
    import numpy as np
    CUBIC_AVAILABLE = True
except ImportError:
    CUBIC_AVAILABLE = False
    print("⚠️ scipy not available - using linear interpolation")


class SimpleForwardSwapPricer:
    def __init__(self, root):
        self.root = root
        self.root.title("Forward Swap Pricer - Simplified")
        self.root.geometry("450x700")
        
        # Database path
        self.db_path = os.path.join(os.path.dirname(__file__), 'database', 'swap_rates.db')
        
        self.setup_ui()
    
    def setup_ui(self):
        # Header
        header = tk.Frame(self.root, bg='#2c3e50', padx=20, pady=15)
        header.pack(fill=tk.X)
        
        tk.Label(header, text="⚙ Forward Swap Pricer", 
                bg='#2c3e50', fg='white', font=('Arial', 16, 'bold')).pack()
        
        interp_method = "Cubic Spline" if CUBIC_AVAILABLE else "Linear"
        tk.Label(header, text=f"Simple date-based pricing ({interp_method})", 
                bg='#2c3e50', fg='#ecf0f1', font=('Arial', 10)).pack()
        
        # Main frame
        main_frame = tk.Frame(self.root, padx=20, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Valuation Date
        row0 = tk.Frame(main_frame)
        row0.pack(fill=tk.X, pady=8)
        tk.Label(row0, text="Valuation Date:", width=20, anchor='w').pack(side=tk.LEFT)
        self.val_date = tk.Entry(row0, width=15)
        self.val_date.insert(0, datetime.now().strftime('%Y-%m-%d'))
        self.val_date.pack(side=tk.LEFT, padx=5)
        tk.Label(row0, text="(YYYY-MM-DD)", fg='gray', font=('Arial', 8)).pack(side=tk.LEFT)
        
        # Currency
        row1 = tk.Frame(main_frame)
        row1.pack(fill=tk.X, pady=8)
        tk.Label(row1, text="Currency:", width=20, anchor='w').pack(side=tk.LEFT)
        self.currency_var = tk.StringVar(value='AUD')
        ttk.Combobox(row1, textvariable=self.currency_var,
                    values=['AUD', 'USD', 'EUR', 'GBP', 'JPY', 'CAD', 'NZD'],
                    width=12, state='readonly').pack(side=tk.LEFT, padx=5)
        
        # Swap Start Date
        row2 = tk.Frame(main_frame)
        row2.pack(fill=tk.X, pady=8)
        tk.Label(row2, text="Swap Start Date:", width=20, anchor='w').pack(side=tk.LEFT)
        self.start_date = tk.Entry(row2, width=15)
        start = datetime.now() + timedelta(days=2)
        self.start_date.insert(0, start.strftime('%Y-%m-%d'))
        self.start_date.pack(side=tk.LEFT, padx=5)
        tk.Label(row2, text="Forward start", fg='gray', font=('Arial', 8)).pack(side=tk.LEFT)
        
        # Swap End Date
        row3 = tk.Frame(main_frame)
        row3.pack(fill=tk.X, pady=8)
        tk.Label(row3, text="Swap End Date:", width=20, anchor='w').pack(side=tk.LEFT)
        self.end_date = tk.Entry(row3, width=15)
        end = start + relativedelta(years=5)
        self.end_date.insert(0, end.strftime('%Y-%m-%d'))
        self.end_date.pack(side=tk.LEFT, padx=5)
        tk.Label(row3, text="Maturity", fg='gray', font=('Arial', 8)).pack(side=tk.LEFT)
        
        # Fixed Leg Frequency
        row4 = tk.Frame(main_frame)
        row4.pack(fill=tk.X, pady=8)
        tk.Label(row4, text="Fixed Leg Frequency:", width=20, anchor='w').pack(side=tk.LEFT)
        self.fixed_freq_var = tk.StringVar(value='6M')
        ttk.Combobox(row4, textvariable=self.fixed_freq_var,
                    values=['3M', '6M', '1Y'], width=12, state='readonly').pack(side=tk.LEFT, padx=5)
        
        # Floating Leg Frequency
        row5 = tk.Frame(main_frame)
        row5.pack(fill=tk.X, pady=8)
        tk.Label(row5, text="Floating Leg Frequency:", width=20, anchor='w').pack(side=tk.LEFT)
        self.float_freq_var = tk.StringVar(value='6M')
        ttk.Combobox(row5, textvariable=self.float_freq_var,
                    values=['3M', '6M', '1Y'], width=12, state='readonly').pack(side=tk.LEFT, padx=5)
        
        # Notional
        row6 = tk.Frame(main_frame)
        row6.pack(fill=tk.X, pady=8)
        tk.Label(row6, text="Notional:", width=20, anchor='w').pack(side=tk.LEFT)
        self.notional = tk.Entry(row6, width=15)
        self.notional.insert(0, "10,000,000")
        self.notional.pack(side=tk.LEFT, padx=5)
        
        # Price button
        tk.Button(main_frame, text="🔧 Price Swap", command=self.price_swap,
                 bg='#3498db', fg='white', font=('Arial', 12, 'bold'),
                 padx=40, pady=12).pack(pady=20)
        
        # Results
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.results_text = tk.Text(results_frame, height=15, wrap=tk.WORD,
                                   font=('Courier', 9), bg='#f5f5f5')
        self.results_text.pack(fill=tk.BOTH, expand=True)
    
    def price_swap(self):
        """Price the forward swap"""
        try:
            val_date = self.val_date.get()
            currency = self.currency_var.get()
            start_date = self.start_date.get()
            end_date = self.end_date.get()
            
            # Parse dates
            val_dt = datetime.strptime(val_date, '%Y-%m-%d')
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Calculate forward period and tenor
            forward_years = (start_dt - val_dt).days / 365.0
            tenor_years = (end_dt - start_dt).days / 365.0
            
            # Get zero curve from database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get latest rates
            cursor.execute("""
                SELECT tenor, rate 
                FROM swap_rates 
                WHERE currency = ? 
                AND date = (SELECT MAX(date) FROM swap_rates WHERE currency = ?)
                ORDER BY date DESC
            """, (currency, currency))
            
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                messagebox.showerror("Error", f"No data found for {currency}")
                return
            
            # Build curve
            tenor_map = {'6M': 0.5, '1Y': 1, '2Y': 2, '3Y': 3, '4Y': 4, '5Y': 5,
                        '6Y': 6, '7Y': 7, '8Y': 8, '9Y': 9, '10Y': 10,
                        '12Y': 12, '15Y': 15, '20Y': 20, '25Y': 25, '30Y': 30}
            
            curve = {}
            for tenor, rate in rows:
                if tenor in tenor_map:
                    curve[tenor_map[tenor]] = rate
            
            # Calculate forward rate
            t1 = forward_years
            t2 = forward_years + tenor_years
            
            # Interpolate
            r1 = self.interpolate(t1, curve)
            r2 = self.interpolate(t2, curve)
            
            if r1 is None or r2 is None:
                messagebox.showerror("Error", "Could not interpolate rates")
                return
            
            # Forward rate calculation
            forward_rate = (r2 * t2 - r1 * t1) / tenor_years
            
            # Display results
            self.results_text.delete(1.0, tk.END)
            
            # Determine which interpolation was used
            interp_method = "Cubic Spline" if (CUBIC_AVAILABLE and len(curve) >= 4) else "Linear"
            
            result = f"""Forward Swap Rate: {forward_rate:.5%}

Structure:
  Start: {start_date} ({forward_years:.2f}y forward)
    End: {end_date}

Calculation:
  T1 ({forward_years:.2f}y): {r1:.5%}
  T2 ({forward_years + tenor_years:.2f}y): {r2:.5%}
  
  Forward = (r2·t2 - r1·t1) / tenor
          = ({r2:.5%}·{t2:.2f} - {r1:.5%}·{t1:.2f}) / {tenor_years:.2f}
          = {forward_rate:.5%}

Interpolation: {interp_method}
For production use, see Analytics → Historical Forward Swap Analyzer"""
            
            self.results_text.insert(1.0, result)
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid date format. Use YYYY-MM-DD\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Pricing failed:\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    def interpolate(self, years, curve):
        """Cubic spline interpolation (or linear fallback)"""
        if years in curve:
            return curve[years]
        
        keys = sorted(curve.keys())
        
        if not keys:
            return None
        
        if years < keys[0]:
            return curve[keys[0]]
        if years > keys[-1]:
            return curve[keys[-1]]
        
        # Try cubic spline if available and enough points
        if CUBIC_AVAILABLE and len(keys) >= 4:
            try:
                x = np.array(keys)
                y = np.array([curve[k] for k in keys])
                cs = CubicSpline(x, y, bc_type='natural')
                return float(cs(years))
            except:
                pass  # Fall back to linear
        
        # Linear interpolation fallback
        for i in range(len(keys) - 1):
            if keys[i] <= years <= keys[i+1]:
                x0, x1 = keys[i], keys[i+1]
                y0, y1 = curve[x0], curve[x1]
                return y0 + (y1 - y0) * (years - x0) / (x1 - x0)
        
        return curve[keys[-1]]


def main():
    root = tk.Tk()
    app = SimpleForwardSwapPricer(root)
    root.mainloop()


if __name__ == '__main__':
    main()
