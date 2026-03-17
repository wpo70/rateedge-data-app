"""
AUD Basis Analyzer - 3M vs 6M BBSW Spreads
Calculate and visualize the basis between 3M and 6M floating rate curves
Formula: Basis (bp) = 3M Rate - 6M Rate (expressed in basis points)
"""
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import mplcursors
import numpy as np
import os

class BasisAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("AUD Basis Analyzer - 3M vs 6M BBSW")
        self.root.geometry("1400x950")
        
        self.db_path = os.path.join(os.path.dirname(__file__), 'database', 'swap_rates.db')
        
        # Available tenors (should match between curves)
        self.tenors = ['4Y', '5Y', '6Y', '7Y', '9Y', '10Y', '12Y', '15Y', '20Y', '25Y', '30Y']
        
        self.setup_ui()
    
    def setup_ui(self):
        # Header
        header = tk.Frame(self.root, bg='#2c3e50', padx=20, pady=15)
        header.pack(fill=tk.X)
        
        tk.Label(header, text="📊 AUD Basis Analyzer", 
                bg='#2c3e50', fg='white', font=('Arial', 18, 'bold')).pack()
        
        tk.Label(header, text="3M vs 6M BBSW Floating Rate Basis Analysis", 
                bg='#2c3e50', fg='#ecf0f1', font=('Arial', 11)).pack()
        
        # Parameters frame
        params = tk.Frame(self.root, padx=20, pady=15)
        params.pack(fill=tk.X)
        
        # Date range
        date_frame = tk.Frame(params)
        date_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(date_frame, text="Analysis Period:", font=('Arial', 11, 'bold')).pack(side=tk.LEFT, padx=5)
        tk.Label(date_frame, text="From:", font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        self.start_date = tk.Entry(date_frame, width=12)
        self.start_date.insert(0, "2025-01-01")
        self.start_date.pack(side=tk.LEFT, padx=5)
        
        tk.Label(date_frame, text="To:", font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        self.end_date = tk.Entry(date_frame, width=12)
        self.end_date.insert(0, "2025-10-31")
        self.end_date.pack(side=tk.LEFT, padx=5)
        
        # Tenor selection
        tenor_frame = tk.Frame(params)
        tenor_frame.pack(fill=tk.X, pady=8)
        
        tk.Label(tenor_frame, text="Select Tenors to Analyze:", 
                font=('Arial', 11, 'bold')).pack(side=tk.LEFT, padx=5)
        
        # Checkboxes for multiple tenor selection
        self.tenor_vars = {}
        tenor_box = tk.Frame(tenor_frame)
        tenor_box.pack(side=tk.LEFT, padx=10)
        
        for i, tenor in enumerate(self.tenors):
            var = tk.BooleanVar(value=False)
            self.tenor_vars[tenor] = var
            cb = tk.Checkbutton(tenor_box, text=tenor, variable=var, font=('Arial', 10))
            cb.grid(row=i//6, column=i%6, sticky='w', padx=5)
        
        # Select all / none buttons
        btn_frame = tk.Frame(params)
        btn_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(btn_frame, text="Select Key Tenors (5Y,7Y,10Y)", 
                 command=self.select_key_tenors, bg='#3498db', fg='white',
                 font=('Arial', 9)).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="Select All", command=self.select_all_tenors,
                 bg='#2ecc71', fg='white', font=('Arial', 9)).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="Clear All", command=self.clear_all_tenors,
                 bg='#e74c3c', fg='white', font=('Arial', 9)).pack(side=tk.LEFT, padx=5)
        
        # Info box
        info_frame = tk.Frame(params, bg='#fffacd', relief='solid', borderwidth=1)
        info_frame.pack(fill=tk.X, pady=10, padx=5)
        
        info_text = "💡 Basis (bp) = 3M Rate - 6M Rate  |  Positive = 3M trades wider than 6M"
        tk.Label(info_frame, text=info_text, bg='#fffacd', font=('Arial', 9)).pack(pady=5)
        
        # Button
        tk.Button(params, text="🚀 Calculate Basis", command=self.run_analysis,
                 bg='#3498db', fg='white', font=('Arial', 12, 'bold'),
                 padx=30, pady=10).pack(pady=10)
        
        # Separator
        separator = tk.Frame(params, height=2, bg='#cccccc')
        separator.pack(fill=tk.X, pady=15)
        
        # Spot Calculator Section
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
        self.spot_tenor = ttk.Combobox(spot_frame, values=self.tenors, width=6, state='readonly')
        self.spot_tenor.set('5Y')
        self.spot_tenor.pack(side=tk.LEFT, padx=5)
        
        tk.Button(spot_frame, text="📊 Calculate Basis", command=self.calculate_spot_basis,
                 bg='#27ae60', fg='white', font=('Arial', 10, 'bold'),
                 padx=20, pady=5).pack(side=tk.LEFT, padx=10)
        
        # Spot result display
        self.spot_result = tk.Label(params, text="", font=('Arial', 11), fg='#2c3e50',
                                   relief='solid', borderwidth=1, padx=10, pady=8)
        self.spot_result.pack(fill=tk.X, pady=5)
        
        # Status
        self.status = tk.Label(self.root, text="Ready - Select tenors and date range above", 
                              font=('Arial', 10), fg='gray')
        self.status.pack()
        
        # Chart frame
        self.chart_frame = tk.Frame(self.root)
        self.chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def select_key_tenors(self):
        """Select commonly used tenors"""
        for tenor, var in self.tenor_vars.items():
            if tenor in ['5Y', '7Y', '10Y']:
                var.set(True)
            else:
                var.set(False)
    
    def select_all_tenors(self):
        """Select all tenors"""
        for var in self.tenor_vars.values():
            var.set(True)
    
    def clear_all_tenors(self):
        """Clear all tenor selections"""
        for var in self.tenor_vars.values():
            var.set(False)
    
    def get_rates_for_date_and_floating(self, date, floating_rate):
        """Get all tenor rates for a specific date and floating rate"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT tenor, rate 
            FROM swap_rates 
            WHERE currency = 'AUD' 
            AND floating_rate = ?
            AND date = ?
            ORDER BY tenor
        """, (floating_rate, date))
        
        rows = cursor.fetchall()
        conn.close()
        
        # Convert to dict and percentage
        rates = {tenor: rate * 100 for tenor, rate in rows}
        return rates
    
    def calculate_basis_for_date(self, date, tenor):
        """Calculate basis for a specific date and tenor"""
        # Get 3M rate
        rates_3m = self.get_rates_for_date_and_floating(date, '3M')
        # Get 6M rate
        rates_6m = self.get_rates_for_date_and_floating(date, '6M')
        
        if tenor not in rates_3m or tenor not in rates_6m:
            return None
        
        # Basis = 3M - 6M (in basis points)
        basis = (rates_3m[tenor] - rates_6m[tenor]) * 100
        return basis, rates_3m[tenor], rates_6m[tenor]
    
    def calculate_spot_basis(self):
        """Calculate basis for a specific date"""
        try:
            date = self.spot_date.get()
            tenor = self.spot_tenor.get()
            
            if not tenor:
                messagebox.showerror("Error", "Please select a tenor")
                return
            
            result = self.calculate_basis_for_date(date, tenor)
            
            if result is None:
                self.spot_result.config(
                    text=f"❌ No data found for {date} - {tenor}",
                    fg='red', bg='#ffcccc'
                )
                return
            
            basis, rate_3m, rate_6m = result
            
            # Display result
            result_text = f"✅ {date} | AUD {tenor}\n"
            result_text += f"6M BBSW Rate: {rate_6m:.5f}%\n"
            result_text += f"3M BBSW Rate: {rate_3m:.5f}%\n"
            result_text += f"Basis (3M - 6M): {basis:+.5f} bp"
            
            if basis > 0:
                result_text += " (3M trades wider)"
            elif basis < 0:
                result_text += " (6M trades wider)"
            else:
                result_text += " (No spread)"
            
            self.spot_result.config(
                text=result_text,
                fg='#155724', bg='#d4edda'
            )
            
        except Exception as e:
            self.spot_result.config(
                text=f"❌ Error: {str(e)}",
                fg='red', bg='#ffcccc'
            )
            import traceback
            traceback.print_exc()
    
    def run_analysis(self):
        """Run the basis analysis"""
        try:
            self.status.config(text="Running analysis...", fg='blue')
            self.root.update()
            
            # Get parameters
            start_date = self.start_date.get()
            end_date = self.end_date.get()
            
            # Get selected tenors
            selected_tenors = [tenor for tenor, var in self.tenor_vars.items() if var.get()]
            
            if not selected_tenors:
                messagebox.showerror("Error", "Please select at least one tenor")
                self.status.config(text="No tenors selected", fg='red')
                return
            
            # Get all dates in range that have both 3M and 6M data
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Find dates where we have BOTH 3M and 6M data
            cursor.execute("""
                SELECT DISTINCT s1.date 
                FROM swap_rates s1
                INNER JOIN swap_rates s2 
                    ON s1.date = s2.date 
                    AND s1.tenor = s2.tenor 
                    AND s1.currency = s2.currency
                WHERE s1.currency = 'AUD'
                AND s1.floating_rate = '3M'
                AND s2.floating_rate = '6M'
                AND s1.date >= ? 
                AND s1.date <= ?
                ORDER BY s1.date
            """, (start_date, end_date))
            
            dates = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            if not dates:
                messagebox.showerror("Error", "No overlapping data found for 3M and 6M in selected date range")
                self.status.config(text="No data found", fg='red')
                return
            
            # Calculate basis for each tenor and date
            basis_data = {tenor: [] for tenor in selected_tenors}
            valid_dates = []
            
            for i, date in enumerate(dates):
                if i % 10 == 0:
                    self.status.config(text=f"Processing {i+1}/{len(dates)}: {date}", fg='blue')
                    self.root.update()
                
                has_data = False
                for tenor in selected_tenors:
                    result = self.calculate_basis_for_date(date, tenor)
                    if result is not None:
                        basis, _, _ = result
                        basis_data[tenor].append(basis)
                        has_data = True
                    else:
                        basis_data[tenor].append(np.nan)
                
                if has_data:
                    valid_dates.append(datetime.strptime(date, '%Y-%m-%d'))
            
            if not valid_dates:
                messagebox.showerror("Error", "Could not calculate basis for any dates")
                self.status.config(text="Calculation failed", fg='red')
                return
            
            # Plot results
            self.plot_results(valid_dates, basis_data, selected_tenors)
            
            self.status.config(text=f"✅ Analysis complete! Analyzed {len(valid_dates)} dates", fg='green')
            
        except Exception as e:
            messagebox.showerror("Error", f"Analysis failed:\n{str(e)}")
            self.status.config(text=f"Error: {str(e)}", fg='red')
            import traceback
            traceback.print_exc()
    
    def plot_results(self, dates, basis_data, tenors):
        """Plot the basis analysis results"""
        # Clear previous chart
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        
        # Create figure
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        fig.patch.set_facecolor('white')
        
        # Color palette
        colors = plt.cm.tab10(np.linspace(0, 1, len(tenors)))
        
        lines1 = []
        lines2 = []
        
        # Plot 1: All basis curves
        for i, tenor in enumerate(tenors):
            data = [x for x in basis_data[tenor] if not np.isnan(x)]
            if data:
                line = ax1.plot(dates[:len(basis_data[tenor])], basis_data[tenor], 
                               linewidth=2, label=tenor, color=colors[i])[0]
                lines1.append(line)
        
        ax1.axhline(y=0, color='black', linestyle='--', alpha=0.5, label='Zero basis')
        ax1.set_title('AUD 3M vs 6M BBSW Basis by Tenor', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Basis (bp)', fontsize=12)
        ax1.legend(fontsize=10, loc='best', ncol=2)
        ax1.grid(True, alpha=0.3)
        
        # Add hover for plot 1
        cursor1 = mplcursors.cursor(lines1, hover=True)
        @cursor1.connect("add")
        def on_add1(sel):
            date_idx = int(sel.index)
            tenor_idx = lines1.index(sel.artist)
            tenor = tenors[tenor_idx]
            basis_val = basis_data[tenor][date_idx]
            if not np.isnan(basis_val):
                sel.annotation.set(text=f'{dates[date_idx].strftime("%Y-%m-%d")}\n{tenor}\n{basis_val:+.5f}bp')
                sel.annotation.get_bbox_patch().set(fc="yellow", alpha=0.9)
        
        # Plot 2: Average basis and range
        avg_basis = []
        max_basis = []
        min_basis = []
        
        for i in range(len(dates)):
            values = [basis_data[tenor][i] for tenor in tenors if i < len(basis_data[tenor]) and not np.isnan(basis_data[tenor][i])]
            if values:
                avg_basis.append(np.mean(values))
                max_basis.append(np.max(values))
                min_basis.append(np.min(values))
            else:
                avg_basis.append(np.nan)
                max_basis.append(np.nan)
                min_basis.append(np.nan)
        
        line2 = ax2.plot(dates, avg_basis, 'b-', linewidth=3, label='Average Basis')[0]
        ax2.fill_between(dates, min_basis, max_basis, alpha=0.3, color='blue', label='Range (min-max)')
        ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        ax2.set_title('Average Basis Across All Selected Tenors', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Date', fontsize=12)
        ax2.set_ylabel('Average Basis (bp)', fontsize=12)
        ax2.legend(fontsize=11)
        ax2.grid(True, alpha=0.3)
        
        # Add hover for plot 2
        cursor2 = mplcursors.cursor(line2, hover=True)
        @cursor2.connect("add")
        def on_add2(sel):
            date_idx = int(sel.index)
            if not np.isnan(avg_basis[date_idx]):
                sel.annotation.set(text=f'{dates[date_idx].strftime("%Y-%m-%d")}\nAvg: {avg_basis[date_idx]:+.5f}bp')
                sel.annotation.get_bbox_patch().set(fc="yellow", alpha=0.9)
        
        # Calculate and display statistics
        stats_text = f"Period: {dates[0].strftime('%Y-%m-%d')} to {dates[-1].strftime('%Y-%m-%d')} | "
        stats_text += f"Avg Basis: {np.nanmean(avg_basis):+.2f}bp | "
        stats_text += f"Min: {np.nanmin(min_basis):+.2f}bp | "
        stats_text += f"Max: {np.nanmax(max_basis):+.2f}bp"
        
        fig.text(0.5, 0.01, stats_text, ha='center', fontsize=10,
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout(rect=[0, 0.03, 1, 1])
        
        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

if __name__ == '__main__':
    root = tk.Tk()
    app = BasisAnalyzer(root)
    root.mainloop()
