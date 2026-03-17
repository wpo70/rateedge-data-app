"""
Basis Butterfly Analyzer - 6M vs 3M
Analyze butterfly spreads on the basis curve
Butterfly = 2 × Middle_Basis - Wing1_Basis - Wing2_Basis
Where Basis = 6M Rate - 3M Rate (in bp)
"""
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import sqlite3
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import mplcursors
import numpy as np
import os

class BasisButterflyAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("Basis Butterfly Analyzer - AUD 3M vs 6M")
        self.root.geometry("1400x900")
        
        self.db_path = os.path.join(os.path.dirname(__file__), 'database', 'swap_rates.db')
        
        # Available tenors for butterflies
        self.tenors = ['4Y', '5Y', '6Y', '7Y', '9Y', '10Y', '12Y', '15Y', '20Y', '25Y', '30Y']
        
        self.setup_ui()
    
    def setup_ui(self):
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tab 1: Time Series Comparison
        self.time_series_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.time_series_tab, text="Time Series Comparison")
        self.setup_time_series_tab()
        
        # Tab 2: Spot Calculator
        self.spot_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.spot_tab, text="Spot Calculator")
        self.setup_spot_tab()
    
    def setup_time_series_tab(self):
        """Setup time series comparison tab"""
        # Header
        header = tk.Frame(self.time_series_tab, bg='#2c3e50', padx=20, pady=15)
        header.pack(fill=tk.X)
        
        tk.Label(header, text="🦋 Basis Butterfly Time Series", 
                bg='#2c3e50', fg='white', font=('Arial', 18, 'bold')).pack()
        
        tk.Label(header, text="Compare two basis butterflies over time", 
                bg='#2c3e50', fg='#ecf0f1', font=('Arial', 11)).pack()
        
        # Parameters frame
        params = tk.Frame(self.time_series_tab, padx=20, pady=15)
        params.pack(fill=tk.X)
        
        # Butterfly 1
        bf1_frame = tk.LabelFrame(params, text="Butterfly 1", font=('Arial', 11, 'bold'), padx=15, pady=10)
        bf1_frame.grid(row=0, column=0, padx=10, pady=5, sticky='ew')
        
        tk.Label(bf1_frame, text="Wing 1:", font=('Arial', 10)).grid(row=0, column=0, padx=5, pady=5)
        self.bf1_wing1 = ttk.Combobox(bf1_frame, values=self.tenors, width=8, state='readonly')
        self.bf1_wing1.set('5Y')
        self.bf1_wing1.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(bf1_frame, text="Body:", font=('Arial', 10)).grid(row=0, column=2, padx=5, pady=5)
        self.bf1_body = ttk.Combobox(bf1_frame, values=self.tenors, width=8, state='readonly')
        self.bf1_body.set('7Y')
        self.bf1_body.grid(row=0, column=3, padx=5, pady=5)
        
        tk.Label(bf1_frame, text="Wing 2:", font=('Arial', 10)).grid(row=0, column=4, padx=5, pady=5)
        self.bf1_wing2 = ttk.Combobox(bf1_frame, values=self.tenors, width=8, state='readonly')
        self.bf1_wing2.set('10Y')
        self.bf1_wing2.grid(row=0, column=5, padx=5, pady=5)
        
        # Butterfly 2
        bf2_frame = tk.LabelFrame(params, text="Butterfly 2", font=('Arial', 11, 'bold'), padx=15, pady=10)
        bf2_frame.grid(row=1, column=0, padx=10, pady=5, sticky='ew')
        
        tk.Label(bf2_frame, text="Wing 1:", font=('Arial', 10)).grid(row=0, column=0, padx=5, pady=5)
        self.bf2_wing1 = ttk.Combobox(bf2_frame, values=self.tenors, width=8, state='readonly')
        self.bf2_wing1.set('7Y')
        self.bf2_wing1.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(bf2_frame, text="Body:", font=('Arial', 10)).grid(row=0, column=2, padx=5, pady=5)
        self.bf2_body = ttk.Combobox(bf2_frame, values=self.tenors, width=8, state='readonly')
        self.bf2_body.set('10Y')
        self.bf2_body.grid(row=0, column=3, padx=5, pady=5)
        
        tk.Label(bf2_frame, text="Wing 2:", font=('Arial', 10)).grid(row=0, column=4, padx=5, pady=5)
        self.bf2_wing2 = ttk.Combobox(bf2_frame, values=self.tenors, width=8, state='readonly')
        self.bf2_wing2.set('15Y')
        self.bf2_wing2.grid(row=0, column=5, padx=5, pady=5)
        
        # Date range
        date_frame = tk.LabelFrame(params, text="Date Range", font=('Arial', 11, 'bold'), padx=15, pady=10)
        date_frame.grid(row=2, column=0, padx=10, pady=5, sticky='ew')
        
        tk.Label(date_frame, text="From:", font=('Arial', 10)).grid(row=0, column=0, padx=5, pady=5)
        self.ts_start_date = DateEntry(date_frame, width=12, background='darkblue',
                                       foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.ts_start_date.set_date(datetime.now() - timedelta(days=365))
        self.ts_start_date.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(date_frame, text="To:", font=('Arial', 10)).grid(row=0, column=2, padx=5, pady=5)
        self.ts_end_date = DateEntry(date_frame, width=12, background='darkblue',
                                     foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.ts_end_date.set_date(datetime.now())
        self.ts_end_date.grid(row=0, column=3, padx=5, pady=5)
        
        # Analyze button
        analyze_btn = tk.Button(date_frame, text="Analyze", command=self.analyze_time_series,
                               font=('Arial', 11, 'bold'), bg='#3498db', fg='white',
                               padx=20, pady=8, cursor='hand2')
        analyze_btn.grid(row=0, column=4, padx=20, pady=5)
        
        # Info label
        info_label = tk.Label(params, 
                             text="💡 Basis Butterfly = 2 × Body_Basis - Wing1_Basis - Wing2_Basis (in bp)",
                             font=('Arial', 9), fg='#555')
        info_label.grid(row=3, column=0, pady=10)
        
        # Chart frame
        self.ts_chart_frame = tk.Frame(self.time_series_tab)
        self.ts_chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def setup_spot_tab(self):
        """Setup spot calculator tab"""
        # Header
        header = tk.Frame(self.spot_tab, bg='#2c3e50', padx=20, pady=15)
        header.pack(fill=tk.X)
        
        tk.Label(header, text="📅 Basis Butterfly Spot Calculator", 
                bg='#2c3e50', fg='white', font=('Arial', 18, 'bold')).pack()
        
        tk.Label(header, text="Calculate butterfly for a specific date", 
                bg='#2c3e50', fg='#ecf0f1', font=('Arial', 11)).pack()
        
        # Parameters frame
        params = tk.Frame(self.spot_tab, padx=20, pady=15)
        params.pack()
        
        # Date
        date_frame = tk.Frame(params)
        date_frame.pack(pady=10)
        
        tk.Label(date_frame, text="Date:", font=('Arial', 11, 'bold')).pack(side=tk.LEFT, padx=5)
        self.spot_date = DateEntry(date_frame, width=15, background='darkblue',
                                   foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.spot_date.set_date(datetime.now())
        self.spot_date.pack(side=tk.LEFT, padx=5)
        
        # Butterfly structure
        bf_frame = tk.LabelFrame(params, text="Butterfly Structure", font=('Arial', 11, 'bold'), padx=15, pady=10)
        bf_frame.pack(pady=10)
        
        tk.Label(bf_frame, text="Wing 1:", font=('Arial', 10)).grid(row=0, column=0, padx=5, pady=5)
        self.spot_wing1 = ttk.Combobox(bf_frame, values=self.tenors, width=8, state='readonly')
        self.spot_wing1.set('5Y')
        self.spot_wing1.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(bf_frame, text="Body:", font=('Arial', 10)).grid(row=0, column=2, padx=5, pady=5)
        self.spot_body = ttk.Combobox(bf_frame, values=self.tenors, width=8, state='readonly')
        self.spot_body.set('7Y')
        self.spot_body.grid(row=0, column=3, padx=5, pady=5)
        
        tk.Label(bf_frame, text="Wing 2:", font=('Arial', 10)).grid(row=0, column=4, padx=5, pady=5)
        self.spot_wing2 = ttk.Combobox(bf_frame, values=self.tenors, width=8, state='readonly')
        self.spot_wing2.set('10Y')
        self.spot_wing2.grid(row=0, column=5, padx=5, pady=5)
        
        # Calculate button
        calc_btn = tk.Button(params, text="Calculate", command=self.calculate_spot,
                            font=('Arial', 12, 'bold'), bg='#27ae60', fg='white',
                            padx=30, pady=10, cursor='hand2')
        calc_btn.pack(pady=20)
        
        # Result display
        self.spot_result = tk.Label(params, text="", font=('Arial', 11), 
                                   wraplength=800, justify=tk.LEFT,
                                   bg='#f0f0f0', padx=20, pady=20, relief='solid', borderwidth=1)
        self.spot_result.pack(pady=20, fill=tk.X)
    
    def get_basis(self, date, tenor):
        """Get basis spread (6M - 3M) for a specific date and tenor"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get 3M rate (handles both "3M" and "3M BBSW"/"3M BKBM")
            cursor.execute("""
                SELECT rate FROM swap_rates
                WHERE date = ? AND currency = 'AUD' AND tenor = ? 
                AND (floating_rate = '3M' OR floating_rate LIKE '3M %')
                LIMIT 1
            """, (date, tenor))
            r3m = cursor.fetchone()
            
            # Get 6M rate (handles both "6M" and "6M BBSW"/"6M BKBM")
            cursor.execute("""
                SELECT rate FROM swap_rates
                WHERE date = ? AND currency = 'AUD' AND tenor = ? 
                AND (floating_rate = '6M' OR floating_rate LIKE '6M %')
                LIMIT 1
            """, (date, tenor))
            r6m = cursor.fetchone()
            
            conn.close()
            
            if r3m and r6m:
                # Basis = 6M - 3M (in basis points)
                return (r6m[0] - r3m[0]) * 10000
            return None
            
        except Exception as e:
            print(f"Error getting basis: {e}")
            return None
    
    def calculate_butterfly(self, date, wing1, body, wing2):
        """Calculate basis butterfly value"""
        basis_wing1 = self.get_basis(date, wing1)
        basis_body = self.get_basis(date, body)
        basis_wing2 = self.get_basis(date, wing2)
        
        if basis_wing1 is not None and basis_body is not None and basis_wing2 is not None:
            # Butterfly = 2 × Body - Wing1 - Wing2
            butterfly = 2 * basis_body - basis_wing1 - basis_wing2
            return butterfly, basis_wing1, basis_body, basis_wing2
        
        return None, None, None, None
    
    def analyze_time_series(self):
        """Analyze butterfly time series"""
        # Get parameters
        start_date = self.ts_start_date.get_date().strftime('%Y-%m-%d')
        end_date = self.ts_end_date.get_date().strftime('%Y-%m-%d')
        
        bf1_w1 = self.bf1_wing1.get()
        bf1_b = self.bf1_body.get()
        bf1_w2 = self.bf1_wing2.get()
        
        bf2_w1 = self.bf2_wing1.get()
        bf2_b = self.bf2_body.get()
        bf2_w2 = self.bf2_wing2.get()
        
        # Get all dates in range
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT DISTINCT date FROM swap_rates
                WHERE date BETWEEN ? AND ? AND currency = 'AUD'
                ORDER BY date
            """, (start_date, end_date))
            
            dates = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            if not dates:
                messagebox.showerror("Error", "No data found in date range")
                return
            
            # Calculate butterflies for each date
            bf1_values = []
            bf2_values = []
            valid_dates = []
            
            for date in dates:
                bf1, _, _, _ = self.calculate_butterfly(date, bf1_w1, bf1_b, bf1_w2)
                bf2, _, _, _ = self.calculate_butterfly(date, bf2_w1, bf2_b, bf2_w2)
                
                if bf1 is not None and bf2 is not None:
                    bf1_values.append(bf1)
                    bf2_values.append(bf2)
                    valid_dates.append(datetime.strptime(date, '%Y-%m-%d'))
            
            if not bf1_values:
                messagebox.showerror("Error", "No complete data found")
                return
            
            # Plot
            self.plot_time_series(valid_dates, bf1_values, bf2_values,
                                 f"{bf1_w1}/{bf1_b}/{bf1_w2}",
                                 f"{bf2_w1}/{bf2_b}/{bf2_w2}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Analysis failed:\n{e}")
            import traceback
            traceback.print_exc()
    
    def plot_time_series(self, dates, bf1_values, bf2_values, bf1_label, bf2_label):
        """Plot butterfly time series"""
        # Clear previous chart
        for widget in self.ts_chart_frame.winfo_children():
            widget.destroy()
        
        # Create figure
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10))
        fig.suptitle('AUD Basis Butterfly Analysis', fontsize=16, fontweight='bold')
        
        # Chart 1: Both butterflies
        line1 = ax1.plot(dates, bf1_values, 'b-', linewidth=2, label=bf1_label, marker='o', markersize=3)[0]
        line2 = ax1.plot(dates, bf2_values, 'r-', linewidth=2, label=bf2_label, marker='s', markersize=3)[0]
        ax1.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        ax1.set_title('Basis Butterflies Comparison', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Butterfly Value (bp)', fontsize=12)
        ax1.legend(fontsize=11)
        ax1.grid(True, alpha=0.3)
        
        # Chart 2: Spread
        spread = np.array(bf1_values) - np.array(bf2_values)
        line3 = ax2.plot(dates, spread, 'g-', linewidth=2, label=f'{bf1_label} - {bf2_label}', marker='D', markersize=3)[0]
        ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        ax2.set_title('Butterfly Spread', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Spread (bp)', fontsize=12)
        ax2.legend(fontsize=11)
        ax2.grid(True, alpha=0.3)
        
        # Chart 3: Distribution
        ax3.hist([bf1_values, bf2_values], bins=30, label=[bf1_label, bf2_label],
                color=['blue', 'red'], alpha=0.6, edgecolor='black')
        ax3.set_title('Distribution', fontsize=14, fontweight='bold')
        ax3.set_xlabel('Butterfly Value (bp)', fontsize=12)
        ax3.set_ylabel('Frequency', fontsize=12)
        ax3.legend(fontsize=11)
        ax3.grid(True, alpha=0.3, axis='y')
        
        # Add tooltips
        cursor1 = mplcursors.cursor([line1, line2], hover=True)
        @cursor1.connect("add")
        def on_add1(sel):
            idx = int(sel.index)
            date_str = dates[idx].strftime("%Y-%m-%d")
            if sel.artist == line1:
                sel.annotation.set(text=f'{date_str}\n{bf1_label}: {bf1_values[idx]:.5f}bp')
            else:
                sel.annotation.set(text=f'{date_str}\n{bf2_label}: {bf2_values[idx]:.5f}bp')
            sel.annotation.get_bbox_patch().set(fc="yellow", alpha=0.9)
        
        cursor2 = mplcursors.cursor(line3, hover=True)
        @cursor2.connect("add")
        def on_add2(sel):
            idx = int(sel.index)
            sel.annotation.set(text=f'{dates[idx].strftime("%Y-%m-%d")}\nSpread: {spread[idx]:.5f}bp')
            sel.annotation.get_bbox_patch().set(fc="lightgreen", alpha=0.9)
        
        plt.tight_layout()
        
        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, self.ts_chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def calculate_spot(self):
        """Calculate butterfly for specific date"""
        date = self.spot_date.get_date().strftime('%Y-%m-%d')
        wing1 = self.spot_wing1.get()
        body = self.spot_body.get()
        wing2 = self.spot_wing2.get()
        
        butterfly, basis_w1, basis_body, basis_w2 = self.calculate_butterfly(date, wing1, body, wing2)
        
        if butterfly is None:
            self.spot_result.config(
                text=f"❌ Incomplete data for {date}\n\nNeed both 3M and 6M rates for {wing1}, {body}, and {wing2}",
                fg='red', bg='#ffcccc'
            )
            return
        
        # Display result
        result_text = f"✅ {date} | AUD Basis Butterfly\n\n"
        result_text += f"Structure: {wing1}/{body}/{wing2}\n\n"
        result_text += f"Component Basis Spreads (6M - 3M):\n"
        result_text += f"  {wing1}: {basis_w1:+.5f} bp\n"
        result_text += f"  {body}: {basis_body:+.5f} bp\n"
        result_text += f"  {wing2}: {basis_w2:+.5f} bp\n\n"
        result_text += f"Butterfly Value:\n"
        result_text += f"  2 × {basis_body:.5f} - {basis_w1:.5f} - {basis_w2:.5f}\n"
        result_text += f"  = {butterfly:+.5f} bp"
        
        if butterfly > 0:
            color_fg = '#155724'
            color_bg = '#d4edda'
            result_text += "\n\n📈 Positive butterfly (body basis is rich)"
        elif butterfly < 0:
            color_fg = '#721c24'
            color_bg = '#f8d7da'
            result_text += "\n\n📉 Negative butterfly (body basis is cheap)"
        else:
            color_fg = '#383d41'
            color_bg = '#e2e3e5'
            result_text += "\n\n➖ Flat butterfly"
        
        self.spot_result.config(text=result_text, fg=color_fg, bg=color_bg)

def main():
    root = tk.Tk()
    app = BasisButterflyAnalyzer(root)
    root.mainloop()

if __name__ == '__main__':
    main()
