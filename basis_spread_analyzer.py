"""
Basis Spread Analyzer
Calculate and analyze floating rate basis spreads
AUD 3M BBSW vs 6M BBSW basis
Spread = 6M Rate - 3M Rate (in basis points)
Market convention: "6M flat + X bp" where X is the basis
"""
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import mplcursors
import numpy as np
import os

class BasisSpreadAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("Basis Spread Analyzer - AUD 3M vs 6M BBSW")
        self.root.geometry("1400x900")
        
        self.db_path = os.path.join(os.path.dirname(__file__), 'database', 'swap_rates.db')
        
        # Available tenors (where we have both 3M and 6M data)
        self.tenors = ['4Y', '5Y', '6Y', '7Y', '9Y', '10Y', '12Y', '15Y', '20Y', '25Y', '30Y']
        
        self.setup_ui()
    
    def setup_ui(self):
        # Header
        header = tk.Frame(self.root, bg='#2c3e50', padx=20, pady=15)
        header.pack(fill=tk.X)
        
        tk.Label(header, text="📊 AUD Basis Spread Analyzer", 
                bg='#2c3e50', fg='white', font=('Arial', 18, 'bold')).pack()
        
        tk.Label(header, text="3M BBSW vs 6M BBSW Basis (6M - 3M)", 
                bg='#2c3e50', fg='#ecf0f1', font=('Arial', 11)).pack()
        
        # Parameters frame
        params = tk.Frame(self.root, padx=20, pady=15)
        params.pack(fill=tk.X)
        
        # Analysis type
        type_frame = tk.Frame(params)
        type_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(type_frame, text="Analysis:", font=('Arial', 11, 'bold')).pack(side=tk.LEFT, padx=5)
        
        self.analysis_type = tk.StringVar(value='single')
        tk.Radiobutton(type_frame, text="Single Tenor", variable=self.analysis_type, 
                      value='single', font=('Arial', 10)).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(type_frame, text="All Tenors", variable=self.analysis_type, 
                      value='all', font=('Arial', 10)).pack(side=tk.LEFT, padx=10)
        
        # Date range
        date_frame = tk.Frame(params)
        date_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(date_frame, text="Period:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        tk.Label(date_frame, text="From:", font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        self.start_date = tk.Entry(date_frame, width=12)
        self.start_date.insert(0, "2025-01-01")
        self.start_date.pack(side=tk.LEFT, padx=5)
        
        tk.Label(date_frame, text="To:", font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        self.end_date = tk.Entry(date_frame, width=12)
        self.end_date.insert(0, "2025-10-22")
        self.end_date.pack(side=tk.LEFT, padx=5)
        
        # Tenor selection
        tenor_frame = tk.Frame(params)
        tenor_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(tenor_frame, text="Tenor:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        self.selected_tenor = ttk.Combobox(tenor_frame, values=self.tenors, width=10, state='readonly')
        self.selected_tenor.set('5Y')
        self.selected_tenor.pack(side=tk.LEFT, padx=5)
        
        tk.Label(tenor_frame, text="(for Single Tenor analysis)", fg='gray', font=('Arial', 9)).pack(side=tk.LEFT, padx=10)
        
        # Info box
        info_frame = tk.Frame(params, bg='#e3f2fd', relief='solid', borderwidth=1)
        info_frame.pack(fill=tk.X, pady=10, padx=5)
        
        info_text = "💡 Basis Spread = 6M Rate - 3M Rate (in bp)  |  Positive = 6M pays more  |  Market: '6M flat + X bp'"
        tk.Label(info_frame, text=info_text, bg='#e3f2fd', font=('Arial', 9)).pack(pady=5)
        
        # Button
        tk.Button(params, text="🚀 Analyze Basis Spreads", command=self.run_analysis,
                 bg='#3498db', fg='white', font=('Arial', 12, 'bold'),
                 padx=30, pady=10).pack(pady=10)
        
        # Spot Calculator Section
        separator = tk.Frame(params, height=2, bg='#cccccc')
        separator.pack(fill=tk.X, pady=15)
        
        spot_label = tk.Label(params, text="💡 Spot Basis Calculator - Calculate for Specific Date", 
                             font=('Arial', 12, 'bold'), fg='#2c3e50')
        spot_label.pack(pady=(10, 5))
        
        spot_frame = tk.Frame(params)
        spot_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(spot_frame, text="Date:", font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        self.spot_date = tk.Entry(spot_frame, width=12)
        self.spot_date.insert(0, "2025-10-22")
        self.spot_date.pack(side=tk.LEFT, padx=5)
        
        tk.Label(spot_frame, text="Tenor:", font=('Arial', 10)).pack(side=tk.LEFT, padx=10)
        self.spot_tenor = ttk.Combobox(spot_frame, values=self.tenors, width=10, state='readonly')
        self.spot_tenor.set('5Y')
        self.spot_tenor.pack(side=tk.LEFT, padx=5)
        
        tk.Button(spot_frame, text="📊 Calculate", command=self.calculate_spot_basis,
                 bg='#27ae60', fg='white', font=('Arial', 10, 'bold'),
                 padx=20, pady=5).pack(side=tk.LEFT, padx=10)
        
        # Spot result
        self.spot_result = tk.Label(params, text="", font=('Arial', 11), fg='#2c3e50',
                                   relief='solid', borderwidth=1, padx=10, pady=8)
        self.spot_result.pack(fill=tk.X, pady=5)
        
        # Status
        self.status = tk.Label(self.root, text="Ready - Select analysis type and date range", 
                              font=('Arial', 10), fg='gray')
        self.status.pack()
        
        # Chart frame
        self.chart_frame = tk.Frame(self.root)
        self.chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def get_rate(self, date, tenor, floating_rate):
        """Get rate for specific date, tenor, and floating rate"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Handle both old format (3M, 6M) and new format (3M BBSW, 6M BBSW, 3M BKBM, 6M BKBM)
        # Extract just the period (3M or 6M) for LIKE query
        period = floating_rate.split()[0] if ' ' in floating_rate else floating_rate
        
        cursor.execute("""
            SELECT rate 
            FROM swap_rates 
            WHERE date = ? 
            AND tenor = ? 
            AND (floating_rate = ? OR floating_rate LIKE ?)
            AND currency = 'AUD'
            LIMIT 1
        """, (date, tenor, floating_rate, f"{period}%"))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
    
    def get_dates_with_both_rates(self, start_date, end_date):
        """Get dates where we have both 3M and 6M rates"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT s1.date 
            FROM swap_rates s1
            INNER JOIN swap_rates s2 
                ON s1.date = s2.date 
                AND s1.tenor = s2.tenor
            WHERE s1.currency = 'AUD'
            AND s1.floating_rate = '3M'
            AND s2.floating_rate = '6M'
            AND s1.date >= ?
            AND s1.date <= ?
            ORDER BY s1.date
        """, (start_date, end_date))
        
        dates = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return dates
    
    def calculate_spot_basis(self):
        """Calculate basis spread for a specific date and tenor"""
        try:
            date = self.spot_date.get()
            tenor = self.spot_tenor.get()
            
            if not tenor:
                messagebox.showerror("Error", "Please select a tenor")
                return
            
            # Get both rates
            rate_3m = self.get_rate(date, tenor, '3M')
            rate_6m = self.get_rate(date, tenor, '6M')
            
            if rate_3m is None or rate_6m is None:
                missing = []
                if rate_3m is None:
                    missing.append("3M")
                if rate_6m is None:
                    missing.append("6M")
                
                self.spot_result.config(
                    text=f"❌ Missing data for {date} {tenor}: {', '.join(missing)}",
                    fg='red', bg='#ffcccc'
                )
                return
            
            # Calculate basis spread in basis points
            basis_bp = (rate_6m - rate_3m) * 10000
            
            # Display result
            result_text = f"✅ {date} | AUD {tenor} | Basis Spread\n"
            result_text += f"6M Rate: {rate_6m*100:.5f}%  |  3M Rate: {rate_3m*100:.5f}%\n"
            result_text += f"Basis (6M - 3M): {basis_bp:+.5f} bp\n"
            result_text += f"Market Quote: 6M flat + {basis_bp:+.3f} bp"
            
            if basis_bp > 0:
                color_fg = '#155724'
                color_bg = '#d4edda'
                result_text += "  (3M pays MORE)"
            elif basis_bp < 0:
                color_fg = '#721c24'
                color_bg = '#f8d7da'
                result_text += "  (6M pays MORE)"
            else:
                color_fg = '#383d41'
                color_bg = '#e2e3e5'
                result_text += "  (No basis)"
            
            self.spot_result.config(
                text=result_text,
                fg=color_fg, bg=color_bg
            )
            
        except Exception as e:
            self.spot_result.config(
                text=f"❌ Error: {str(e)}",
                fg='red', bg='#ffcccc'
            )
            import traceback
            traceback.print_exc()
    
    def run_analysis(self):
        """Run the basis spread analysis"""
        try:
            self.status.config(text="Running analysis...", fg='blue')
            self.root.update()
            
            start_date = self.start_date.get()
            end_date = self.end_date.get()
            analysis_type = self.analysis_type.get()
            
            # Get dates where we have both rates
            dates = self.get_dates_with_both_rates(start_date, end_date)
            
            if not dates:
                messagebox.showerror("Error", "No overlapping data found for 3M and 6M in this date range")
                self.status.config(text="No data found", fg='red')
                return
            
            if analysis_type == 'single':
                tenor = self.selected_tenor.get()
                if not tenor:
                    messagebox.showerror("Error", "Please select a tenor")
                    return
                self.analyze_single_tenor(dates, tenor)
            else:
                self.analyze_all_tenors(dates)
            
            self.status.config(text=f"✅ Analysis complete! Analyzed {len(dates)} dates", fg='green')
            
        except Exception as e:
            messagebox.showerror("Error", f"Analysis failed:\n{str(e)}")
            self.status.config(text=f"Error: {str(e)}", fg='red')
            import traceback
            traceback.print_exc()
    
    def analyze_single_tenor(self, dates, tenor):
        """Analyze basis spread for a single tenor over time"""
        basis_spreads = []
        rates_3m = []
        rates_6m = []
        valid_dates = []
        
        for date in dates:
            rate_3m = self.get_rate(date, tenor, '3M')
            rate_6m = self.get_rate(date, tenor, '6M')
            
            if rate_3m is not None and rate_6m is not None:
                basis_bp = (rate_6m - rate_3m) * 10000
                basis_spreads.append(basis_bp)
                rates_3m.append(rate_3m * 100)  # Convert to percentage
                rates_6m.append(rate_6m * 100)
                valid_dates.append(datetime.strptime(date, '%Y-%m-%d'))
        
        if not basis_spreads:
            messagebox.showerror("Error", f"No data found for {tenor}")
            return
        
        self.plot_single_tenor(valid_dates, basis_spreads, rates_3m, rates_6m, tenor)
    
    def analyze_all_tenors(self, dates):
        """Analyze basis spreads for all tenors"""
        # Get most recent date
        latest_date = dates[-1]
        
        tenors_list = []
        basis_spreads = []
        
        for tenor in self.tenors:
            rate_3m = self.get_rate(latest_date, tenor, '3M')
            rate_6m = self.get_rate(latest_date, tenor, '6M')
            
            if rate_3m is not None and rate_6m is not None:
                basis_bp = (rate_6m - rate_3m) * 10000
                tenors_list.append(tenor)
                basis_spreads.append(basis_bp)
        
        if not basis_spreads:
            messagebox.showerror("Error", "No data found for any tenor")
            return
        
        self.plot_all_tenors(tenors_list, basis_spreads, latest_date)
    
    def plot_single_tenor(self, dates, basis_spreads, rates_3m, rates_6m, tenor):
        """Plot basis spread for single tenor over time"""
        # Clear previous chart
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        
        # Create figure with 2 subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8))
        fig.patch.set_facecolor('white')
        
        # Plot 1: Both rates
        line1 = ax1.plot(dates, rates_3m, 'b-', linewidth=2, label='3M BBSW', marker='o', markersize=3)[0]
        line2 = ax1.plot(dates, rates_6m, 'r-', linewidth=2, label='6M BBSW', marker='s', markersize=3)[0]
        ax1.set_title(f'AUD {tenor} - 3M vs 6M BBSW Rates', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Rate (%)', fontsize=12)
        ax1.legend(fontsize=11)
        ax1.grid(True, alpha=0.3)
        
        # Add hover tooltips for chart 1
        cursor1 = mplcursors.cursor([line1, line2], hover=True)
        @cursor1.connect("add")
        def on_add1(sel):
            idx = int(sel.index)
            if sel.artist == line1:
                sel.annotation.set(text=f'{dates[idx].strftime("%Y-%m-%d")}\n3M: {rates_3m[idx]:.5f}%')
            else:
                sel.annotation.set(text=f'{dates[idx].strftime("%Y-%m-%d")}\n6M: {rates_6m[idx]:.5f}%')
            sel.annotation.get_bbox_patch().set(fc="yellow", alpha=0.9)
        
        # Plot 2: Basis spread
        basis_array = np.array(basis_spreads)
        colors = ['green' if x >= 0 else 'red' for x in basis_array]
        
        line3 = ax2.plot(dates, basis_array, 'purple', linewidth=2, label='Basis (6M - 3M)', marker='D', markersize=3)[0]
        ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5, linewidth=1)
        ax2.fill_between(dates, basis_array, 0, alpha=0.2, color='purple')
        ax2.set_title(f'AUD {tenor} - Basis Spread (6M - 3M)', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Date', fontsize=12)
        ax2.set_ylabel('Basis Spread (bp) - Market: 6M flat + X bp', fontsize=12)
        ax2.legend(fontsize=11)
        ax2.grid(True, alpha=0.3)
        
        # Add hover tooltips for chart 2
        cursor2 = mplcursors.cursor(line3, hover=True)
        @cursor2.connect("add")
        def on_add2(sel):
            idx = int(sel.index)
            sel.annotation.set(text=f'{dates[idx].strftime("%Y-%m-%d")}\nBasis: {basis_array[idx]:+.5f}bp')
            sel.annotation.get_bbox_patch().set(fc="yellow", alpha=0.9)
        
        # Add statistics
        stats_text = f"3M Avg: {np.mean(rates_3m):.3f}%, 6M Avg: {np.mean(rates_6m):.3f}%\n"
        stats_text += f"Basis: Avg={np.mean(basis_array):+.2f}bp, Min={np.min(basis_array):+.2f}bp, Max={np.max(basis_array):+.2f}bp"
        
        fig.text(0.5, 0.01, stats_text, ha='center', fontsize=10,
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout(rect=[0, 0.05, 1, 1])
        
        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def plot_all_tenors(self, tenors, basis_spreads, date):
        """Plot basis spreads across all tenors for latest date"""
        # Clear previous chart
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        
        # Create figure
        fig, ax = plt.subplots(figsize=(14, 8))
        fig.patch.set_facecolor('white')
        
        # Create bar chart
        colors = ['green' if x >= 0 else 'red' for x in basis_spreads]
        bars = ax.bar(tenors, basis_spreads, color=colors, alpha=0.7, edgecolor='black')
        
        ax.axhline(y=0, color='black', linestyle='--', linewidth=1)
        ax.set_title(f'AUD Basis Spreads (6M - 3M) as of {date}\nMarket: 6M flat + X bp', fontsize=14, fontweight='bold')
        ax.set_xlabel('Tenor', fontsize=12)
        ax.set_ylabel('Basis Spread (bp)', fontsize=12)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for bar, value in zip(bars, basis_spreads):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{value:+.2f}',
                   ha='center', va='bottom' if value >= 0 else 'top',
                   fontsize=9, fontweight='bold')
        
        # Add statistics
        stats_text = f"Average Basis: {np.mean(basis_spreads):+.2f}bp  |  "
        stats_text += f"Min: {np.min(basis_spreads):+.2f}bp  |  Max: {np.max(basis_spreads):+.2f}bp"
        
        fig.text(0.5, 0.02, stats_text, ha='center', fontsize=11,
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout(rect=[0, 0.05, 1, 1])
        
        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

if __name__ == '__main__':
    root = tk.Tk()
    app = BasisSpreadAnalyzer(root)
    root.mainloop()
