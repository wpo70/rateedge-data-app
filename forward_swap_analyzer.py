"""
Historical Forward Swap Analysis Tool
Prices forward swaps over time and compares structures
Example: 5y fwd 5y vs 5y fwd 10y from 2024-01 to 2025-01
Uses CUBIC SPLINE interpolation
"""
import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import mplcursors
import numpy as np

# Try to import cubic spline
try:
    from scipy.interpolate import CubicSpline
    CUBIC_AVAILABLE = True
except ImportError:
    CUBIC_AVAILABLE = False
    print("⚠️ scipy not available - using linear interpolation")

class ForwardSwapAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("Historical Forward Swap Analysis")
        self.root.geometry("1400x900")
        
        # Database path
        self.db_path = os.path.join(os.path.dirname(__file__), 'database', 'swap_rates.db')
        
        self.setup_ui()
    
    def setup_ui(self):
        # Top frame for inputs
        input_frame = tk.Frame(self.root, bg='#2c3e50', padx=20, pady=15)
        input_frame.pack(fill=tk.X)
        
        tk.Label(input_frame, text="📊 Historical Forward Swap Analysis", 
                bg='#2c3e50', fg='white', font=('Arial', 16, 'bold')).pack()
        
        tk.Label(input_frame, text="Compare forward swap structures over time", 
                bg='#2c3e50', fg='#ecf0f1', font=('Arial', 11)).pack()
        
        # Parameters frame
        params_frame = tk.Frame(self.root, padx=20, pady=15)
        params_frame.pack(fill=tk.X)
        
        # Row 1: Date range and currency
        row1 = tk.Frame(params_frame)
        row1.pack(fill=tk.X, pady=5)
        
        tk.Label(row1, text="Analysis Period:", font=('Arial', 11, 'bold')).pack(side=tk.LEFT, padx=5)
        tk.Label(row1, text="From:", font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        self.start_date = tk.Entry(row1, width=12)
        self.start_date.insert(0, "2024-01-01")
        self.start_date.pack(side=tk.LEFT, padx=5)
        
        tk.Label(row1, text="To:", font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        self.end_date = tk.Entry(row1, width=12)
        self.end_date.insert(0, "2025-01-01")
        self.end_date.pack(side=tk.LEFT, padx=5)
        
        tk.Label(row1, text="Currency:", font=('Arial', 10)).pack(side=tk.LEFT, padx=15)
        self.currency = ttk.Combobox(row1, values=['AUD', 'NZD'], width=8, state='readonly')
        self.currency.set('AUD')
        self.currency.pack(side=tk.LEFT, padx=5)
        
        # Row 2: Swap 1 parameters (simplified)
        row2 = tk.Frame(params_frame)
        row2.pack(fill=tk.X, pady=8)
        
        tk.Label(row2, text="Structure 1:", font=('Arial', 11, 'bold'), fg='blue').pack(side=tk.LEFT, padx=5)
        self.fwd1_start = tk.Entry(row2, width=4)
        self.fwd1_start.insert(0, "5")
        self.fwd1_start.pack(side=tk.LEFT, padx=2)
        tk.Label(row2, text="y forward ×", font=('Arial', 10)).pack(side=tk.LEFT, padx=2)
        
        self.swap1_tenor = tk.Entry(row2, width=4)
        self.swap1_tenor.insert(0, "5")
        self.swap1_tenor.pack(side=tk.LEFT, padx=2)
        tk.Label(row2, text="y tenor", font=('Arial', 10)).pack(side=tk.LEFT, padx=2)
        
        tk.Label(row2, text="(e.g., 5y forward starting 5y swap)", fg='gray', font=('Arial', 9)).pack(side=tk.LEFT, padx=10)
        
        # Row 3: Swap 2 parameters (simplified)
        row3 = tk.Frame(params_frame)
        row3.pack(fill=tk.X, pady=8)
        
        tk.Label(row3, text="Structure 2:", font=('Arial', 11, 'bold'), fg='red').pack(side=tk.LEFT, padx=5)
        self.fwd2_start = tk.Entry(row3, width=4)
        self.fwd2_start.insert(0, "5")
        self.fwd2_start.pack(side=tk.LEFT, padx=2)
        tk.Label(row3, text="y forward ×", font=('Arial', 10)).pack(side=tk.LEFT, padx=2)
        
        self.swap2_tenor = tk.Entry(row3, width=4)
        self.swap2_tenor.insert(0, "10")
        self.swap2_tenor.pack(side=tk.LEFT, padx=2)
        tk.Label(row3, text="y tenor", font=('Arial', 10)).pack(side=tk.LEFT, padx=2)
        
        tk.Label(row3, text="(e.g., 5y forward starting 10y swap)", fg='gray', font=('Arial', 9)).pack(side=tk.LEFT, padx=10)
        
        # Button
        tk.Button(params_frame, text="🚀 Run Analysis", command=self.run_analysis,
                 bg='#3498db', fg='white', font=('Arial', 12, 'bold'),
                 padx=30, pady=10).pack(pady=15)
        
        # Status
        self.status = tk.Label(self.root, text="Ready - Enter dates and structures above", font=('Arial', 10), fg='gray')
        self.status.pack()
        
        # Chart frame
        self.chart_frame = tk.Frame(self.root)
        self.chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def get_zero_curve(self, date, currency):
        """Get zero curve for a specific date"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get rates for this date (within 7 days)
        cursor.execute("""
            SELECT tenor, rate 
            FROM swap_rates 
            WHERE currency = ? 
            AND date >= ? 
            AND date <= ?
            ORDER BY date DESC
        """, (currency, 
              (datetime.strptime(date, '%Y-%m-%d') - timedelta(days=7)).strftime('%Y-%m-%d'),
              date))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return None
        
        # Convert to zero curve format
        tenor_map = {'6M': 0.5, '1Y': 1, '2Y': 2, '3Y': 3, '4Y': 4, '5Y': 5,
                     '6Y': 6, '7Y': 7, '8Y': 8, '9Y': 9, '10Y': 10,
                     '12Y': 12, '15Y': 15, '20Y': 20, '25Y': 25, '30Y': 30}
        
        zero_curve = {}
        for tenor, rate in rows:
            if tenor in tenor_map:
                zero_curve[int(tenor_map[tenor] * 12)] = rate  # Convert to months
        
        return zero_curve
    
    def calculate_forward_rate(self, forward_years, tenor_years, curve):
        """
        Calculate forward swap rate
        Simplified: (T2_rate * T2 - T1_rate * T1) / (T2 - T1)
        """
        t1_years = forward_years
        t2_years = forward_years + tenor_years
        
        # Interpolate rates
        t1_rate = self.interpolate_rate(t1_years, curve)
        t2_rate = self.interpolate_rate(t2_years, curve)
        
        if t1_rate is None or t2_rate is None:
            return None
        
        # Forward rate calculation
        forward_rate = (t2_rate * t2_years - t1_rate * t1_years) / tenor_years
        
        return forward_rate
    
    def interpolate_rate(self, years, curve):
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
    
    def run_analysis(self):
        """Run the historical analysis"""
        try:
            self.status.config(text="Running analysis...", fg='blue')
            self.root.update()
            
            # Get parameters
            start_date = self.start_date.get()
            end_date = self.end_date.get()
            currency = self.currency.get()
            
            fwd1_start = float(self.fwd1_start.get())
            swap1_tenor = float(self.swap1_tenor.get())
            
            fwd2_start = float(self.fwd2_start.get())
            swap2_tenor = float(self.swap2_tenor.get())
            
            # Get all dates in range
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT date 
                FROM swap_rates 
                WHERE currency = ? 
                AND date >= ? 
                AND date <= ?
                ORDER BY date
            """, (currency, start_date, end_date))
            
            dates = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            if not dates:
                messagebox.showerror("Error", "No data found for selected date range and currency")
                self.status.config(text="No data found", fg='red')
                return
            
            # Price swaps for each date
            results1 = []
            results2 = []
            valid_dates = []
            
            for i, date in enumerate(dates):
                if i % 10 == 0:  # Update every 10th date
                    self.status.config(text=f"Processing {i+1}/{len(dates)}: {date}", fg='blue')
                    self.root.update()
                
                # Get zero curve
                zero_curve = self.get_zero_curve(date, currency)
                if not zero_curve or len(zero_curve) < 5:
                    continue
                
                # Calculate forward rates (simplified)
                rate1 = self.calculate_forward_rate(fwd1_start, swap1_tenor, zero_curve)
                rate2 = self.calculate_forward_rate(fwd2_start, swap2_tenor, zero_curve)
                
                if rate1 is not None and rate2 is not None:
                    results1.append(rate1 * 100)  # Convert to percentage
                    results2.append(rate2 * 100)
                    valid_dates.append(datetime.strptime(date, '%Y-%m-%d'))
            
            if not results1:
                messagebox.showerror("Error", "Could not price any swaps. Check your parameters.")
                self.status.config(text="Pricing failed", fg='red')
                return
            
            # Plot results
            self.plot_results(valid_dates, results1, results2, 
                            fwd1_start, swap1_tenor, fwd2_start, swap2_tenor, currency)
            
            self.status.config(text=f"✅ Analysis complete! Priced {len(valid_dates)} dates", fg='green')
            
        except Exception as e:
            messagebox.showerror("Error", f"Analysis failed:\n{str(e)}")
            self.status.config(text=f"Error: {str(e)}", fg='red')
            import traceback
            traceback.print_exc()
    
    def plot_results(self, dates, results1, results2, fwd1, tenor1, fwd2, tenor2, currency):
        """Plot the analysis results"""
        # Clear previous chart
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        
        # Create figure
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8))
        fig.patch.set_facecolor('white')
        
        # Plot 1: Both swap rates over time
        line1 = ax1.plot(dates, results1, 'b-', linewidth=2, label=f'{fwd1}y fwd {tenor1}y')[0]
        line2 = ax1.plot(dates, results2, 'r-', linewidth=2, label=f'{fwd2}y fwd {tenor2}y')[0]
        ax1.set_title(f'{currency} Forward Swap Rates Comparison', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Par Rate (%)', fontsize=12)
        ax1.legend(fontsize=11)
        ax1.grid(True, alpha=0.3)
        
        # Add hover tooltips for chart 1
        cursor1 = mplcursors.cursor([line1, line2], hover=True)
        @cursor1.connect("add")
        def on_add1(sel):
            date_idx = int(sel.index)
            if sel.artist == line1:
                sel.annotation.set(text=f'{dates[date_idx].strftime("%Y-%m-%d")}\n{fwd1}y fwd {tenor1}y\n{results1[date_idx]:.5f}%')
            else:
                sel.annotation.set(text=f'{dates[date_idx].strftime("%Y-%m-%d")}\n{fwd2}y fwd {tenor2}y\n{results2[date_idx]:.5f}%')
            sel.annotation.get_bbox_patch().set(fc="yellow", alpha=0.9)
        
        # Plot 2: Spread (difference) over time
        spread = np.array(results2) - np.array(results1)
        line3 = ax2.plot(dates, spread, 'g-', linewidth=2, label='Spread (Swap2 - Swap1)')[0]
        ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        ax2.set_title('Spread Between Structures', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Date', fontsize=12)
        ax2.set_ylabel('Spread (bp)', fontsize=12)
        ax2.legend(fontsize=11)
        ax2.grid(True, alpha=0.3)
        
        # Add hover tooltips for chart 2
        cursor2 = mplcursors.cursor(line3, hover=True)
        @cursor2.connect("add")
        def on_add2(sel):
            date_idx = int(sel.index)
            sel.annotation.set(text=f'{dates[date_idx].strftime("%Y-%m-%d")}\nSpread: {spread[date_idx]:.5f}bp')
            sel.annotation.get_bbox_patch().set(fc="yellow", alpha=0.9)
        
        # Add statistics
        stats_text = f"Swap 1: Avg={np.mean(results1):.2f}%, Min={np.min(results1):.2f}%, Max={np.max(results1):.2f}%\n"
        stats_text += f"Swap 2: Avg={np.mean(results2):.2f}%, Min={np.min(results2):.2f}%, Max={np.max(results2):.2f}%\n"
        stats_text += f"Spread: Avg={np.mean(spread):.2f}bp, Min={np.min(spread):.2f}bp, Max={np.max(spread):.2f}bp"
        
        fig.text(0.5, 0.01, stats_text, ha='center', fontsize=10, 
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout(rect=[0, 0.05, 1, 1])
        
        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

if __name__ == '__main__':
    root = tk.Tk()
    app = ForwardSwapAnalyzer(root)
    root.mainloop()
