"""
IRS Butterfly Spread Analyzer
Compare butterfly structures over time
Example: 5y/6y/7y vs 7y/8y/9y
Butterfly = Middle - (Short + Long) / 2
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
from responsive_charts import ResponsiveChartWindow, ChartStyler, create_butterfly_chart

class ButterflyAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("IRS Butterfly Spread Analyzer")
        self.root.geometry("1400x950")
        
        self.db_path = os.path.join(os.path.dirname(__file__), 'database', 'swap_rates.db')
        
        # Available tenors
        self.tenors = ['6M', '9M', '1Y', '15M', '18M', '21M', '2Y', '30M', '3Y', 
                       '4Y', '5Y', '6Y', '7Y', '8Y', '9Y', '10Y', '12Y', '15Y', '20Y', '25Y', '30Y']
        
        # Store last chart data for enhanced view
        self.last_chart_data = None
        
        self.setup_ui()
    
    def setup_ui(self):
        # Header
        header = tk.Frame(self.root, bg='#2c3e50', padx=20, pady=15)
        header.pack(fill=tk.X)
        
        tk.Label(header, text="🦋 IRS Butterfly Spread Analyzer", 
                bg='#2c3e50', fg='white', font=('Arial', 18, 'bold')).pack()
        
        tk.Label(header, text="Compare butterfly structures over time + spot calculator", 
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
        self.start_date.insert(0, "2024-01-01")
        self.start_date.pack(side=tk.LEFT, padx=5)
        
        tk.Label(date_frame, text="To:", font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        self.end_date = tk.Entry(date_frame, width=12)
        self.end_date.insert(0, "2025-01-01")
        self.end_date.pack(side=tk.LEFT, padx=5)
        
        tk.Label(date_frame, text="Currency:", font=('Arial', 10)).pack(side=tk.LEFT, padx=15)
        self.currency = ttk.Combobox(date_frame, values=['AUD', 'NZD'], width=8, state='readonly')
        self.currency.set('AUD')
        self.currency.pack(side=tk.LEFT, padx=5)
        
        # Butterfly 1
        bf1_frame = tk.Frame(params)
        bf1_frame.pack(fill=tk.X, pady=8)
        
        tk.Label(bf1_frame, text="Butterfly 1:", font=('Arial', 11, 'bold'), fg='blue').pack(side=tk.LEFT, padx=5)
        
        tk.Label(bf1_frame, text="Short:", font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        self.bf1_short = ttk.Combobox(bf1_frame, values=self.tenors, width=6, state='readonly')
        self.bf1_short.set('5Y')
        self.bf1_short.pack(side=tk.LEFT, padx=2)
        
        tk.Label(bf1_frame, text="×", font=('Arial', 12, 'bold')).pack(side=tk.LEFT, padx=5)
        
        tk.Label(bf1_frame, text="Middle:", font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        self.bf1_middle = ttk.Combobox(bf1_frame, values=self.tenors, width=6, state='readonly')
        self.bf1_middle.set('6Y')
        self.bf1_middle.pack(side=tk.LEFT, padx=2)
        
        tk.Label(bf1_frame, text="×", font=('Arial', 12, 'bold')).pack(side=tk.LEFT, padx=5)
        
        tk.Label(bf1_frame, text="Long:", font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        self.bf1_long = ttk.Combobox(bf1_frame, values=self.tenors, width=6, state='readonly')
        self.bf1_long.set('7Y')
        self.bf1_long.pack(side=tk.LEFT, padx=2)
        
        tk.Label(bf1_frame, text="  (e.g., 5y × 6y × 7y)", fg='gray', font=('Arial', 9)).pack(side=tk.LEFT, padx=10)
        
        # Butterfly 2
        bf2_frame = tk.Frame(params)
        bf2_frame.pack(fill=tk.X, pady=8)
        
        tk.Label(bf2_frame, text="Butterfly 2:", font=('Arial', 11, 'bold'), fg='red').pack(side=tk.LEFT, padx=5)
        
        tk.Label(bf2_frame, text="Short:", font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        self.bf2_short = ttk.Combobox(bf2_frame, values=self.tenors, width=6, state='readonly')
        self.bf2_short.set('7Y')
        self.bf2_short.pack(side=tk.LEFT, padx=2)
        
        tk.Label(bf2_frame, text="×", font=('Arial', 12, 'bold')).pack(side=tk.LEFT, padx=5)
        
        tk.Label(bf2_frame, text="Middle:", font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        self.bf2_middle = ttk.Combobox(bf2_frame, values=self.tenors, width=6, state='readonly')
        self.bf2_middle.set('8Y')
        self.bf2_middle.pack(side=tk.LEFT, padx=2)
        
        tk.Label(bf2_frame, text="×", font=('Arial', 12, 'bold')).pack(side=tk.LEFT, padx=5)
        
        tk.Label(bf2_frame, text="Long:", font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        self.bf2_long = ttk.Combobox(bf2_frame, values=self.tenors, width=6, state='readonly')
        self.bf2_long.set('9Y')
        self.bf2_long.pack(side=tk.LEFT, padx=2)
        
        tk.Label(bf2_frame, text="  (e.g., 7y × 8y × 9y)", fg='gray', font=('Arial', 9)).pack(side=tk.LEFT, padx=10)
        
        # Info box
        info_frame = tk.Frame(params, bg='#fffacd', relief='solid', borderwidth=1)
        info_frame.pack(fill=tk.X, pady=10, padx=5)
        
        info_text = "💡 Butterfly = Middle - (Short + Long)/2    |    Measures curve curvature"
        tk.Label(info_frame, text=info_text, bg='#fffacd', font=('Arial', 9)).pack(pady=5)
        
        # Buttons frame
        button_frame = tk.Frame(params)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="🚀 Analyze Butterflies", command=self.run_analysis,
                 bg='#3498db', fg='white', font=('Arial', 12, 'bold'),
                 padx=30, pady=10).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="🔍 Open in Large Window", command=self.open_enhanced_view,
                 bg='#9b59b6', fg='white', font=('Arial', 12, 'bold'),
                 padx=20, pady=10).pack(side=tk.LEFT, padx=5)
        
        # Separator
        separator = tk.Frame(params, height=2, bg='#cccccc')
        separator.pack(fill=tk.X, pady=15)
        
        # Spot Calculator Section
        spot_label = tk.Label(params, text="💡 Spot Butterfly Calculator - Calculate for Specific Date", 
                             font=('Arial', 12, 'bold'), fg='#2c3e50')
        spot_label.pack(pady=(10, 5))
        
        spot_frame = tk.Frame(params)
        spot_frame.pack(fill=tk.X, pady=5)
        
        # Spot date input
        tk.Label(spot_frame, text="Date:", font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        self.spot_date = tk.Entry(spot_frame, width=12)
        self.spot_date.insert(0, "2021-10-25")
        self.spot_date.pack(side=tk.LEFT, padx=5)
        
        tk.Label(spot_frame, text="Currency:", font=('Arial', 10)).pack(side=tk.LEFT, padx=10)
        self.spot_currency = ttk.Combobox(spot_frame, values=['AUD', 'NZD'], width=8, state='readonly')
        self.spot_currency.set('AUD')
        self.spot_currency.pack(side=tk.LEFT, padx=5)
        
        # Spot butterfly structure
        spot_bf_frame = tk.Frame(params)
        spot_bf_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(spot_bf_frame, text="Butterfly:", font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        
        tk.Label(spot_bf_frame, text="Short:", font=('Arial', 9)).pack(side=tk.LEFT, padx=5)
        self.spot_short = ttk.Combobox(spot_bf_frame, values=self.tenors, width=6, state='readonly')
        self.spot_short.set('6Y')
        self.spot_short.pack(side=tk.LEFT, padx=2)
        
        tk.Label(spot_bf_frame, text="×", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=3)
        
        tk.Label(spot_bf_frame, text="Middle:", font=('Arial', 9)).pack(side=tk.LEFT, padx=5)
        self.spot_middle = ttk.Combobox(spot_bf_frame, values=self.tenors, width=6, state='readonly')
        self.spot_middle.set('7Y')
        self.spot_middle.pack(side=tk.LEFT, padx=2)
        
        tk.Label(spot_bf_frame, text="×", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=3)
        
        tk.Label(spot_bf_frame, text="Long:", font=('Arial', 9)).pack(side=tk.LEFT, padx=5)
        self.spot_long = ttk.Combobox(spot_bf_frame, values=self.tenors, width=6, state='readonly')
        self.spot_long.set('8Y')
        self.spot_long.pack(side=tk.LEFT, padx=2)
        
        # Spot calculate button
        tk.Button(spot_bf_frame, text="📊 Calculate", command=self.calculate_spot_butterfly,
                 bg='#27ae60', fg='white', font=('Arial', 10, 'bold'),
                 padx=20, pady=5).pack(side=tk.LEFT, padx=10)
        
        # Spot result display
        self.spot_result = tk.Label(params, text="", font=('Arial', 11), fg='#2c3e50',
                                   relief='solid', borderwidth=1, padx=10, pady=8)
        self.spot_result.pack(fill=tk.X, pady=5)
        
        # Status
        self.status = tk.Label(self.root, text="Ready - Configure butterflies above", 
                              font=('Arial', 10), fg='gray')
        self.status.pack()
        
        # Chart frame
        self.chart_frame = tk.Frame(self.root)
        self.chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def get_rates_for_date(self, date, currency):
        """Get all tenor rates for a specific date"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get rates within 7 days of target date
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
        
        # Convert to dict
        rates = {tenor: rate * 100 for tenor, rate in rows}  # Convert to percentage
        return rates
    
    def calculate_butterfly(self, short, middle, long, rates):
        """
        Calculate butterfly spread
        Butterfly = Middle - (Short + Long) / 2
        """
        if short not in rates or middle not in rates or long not in rates:
            return None
        
        butterfly = rates[middle] - (rates[short] + rates[long]) / 2
        return butterfly
    
    def calculate_spot_butterfly(self):
        """Calculate butterfly spread for a specific date"""
        try:
            # Get inputs
            date = self.spot_date.get()
            currency = self.spot_currency.get()
            short = self.spot_short.get()
            middle = self.spot_middle.get()
            long = self.spot_long.get()
            
            # Validate
            if not all([short, middle, long]):
                messagebox.showerror("Error", "Please select all butterfly tenors")
                return
            
            # Get rates for this date
            rates = self.get_rates_for_date(date, currency)
            
            if not rates:
                self.spot_result.config(
                    text=f"❌ No data found for {date}",
                    fg='red', bg='#ffcccc'
                )
                return
            
            # Check if all required tenors are available
            missing = []
            for tenor in [short, middle, long]:
                if tenor not in rates:
                    missing.append(tenor)
            
            if missing:
                self.spot_result.config(
                    text=f"❌ Missing tenor data: {', '.join(missing)}",
                    fg='red', bg='#ffcccc'
                )
                return
            
            # Calculate butterfly
            bf_value = self.calculate_butterfly(short, middle, long, rates)
            
            if bf_value is None:
                self.spot_result.config(
                    text="❌ Could not calculate butterfly",
                    fg='red', bg='#ffcccc'
                )
                return
            
            # Display result with component rates
            result_text = f"✅ {date} | {currency} | {short}/{middle}/{long}\n"
            result_text += f"Butterfly Spread: {bf_value:.5f} bp\n"
            result_text += f"Component Rates: {short}={rates[short]:.5f}%  "
            result_text += f"{middle}={rates[middle]:.5f}%  "
            result_text += f"{long}={rates[long]:.5f}%"
            
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
        """Run the butterfly analysis"""
        try:
            self.status.config(text="Running analysis...", fg='blue')
            self.root.update()
            
            # Get parameters
            start_date = self.start_date.get()
            end_date = self.end_date.get()
            currency = self.currency.get()
            
            # Butterfly 1
            bf1_short = self.bf1_short.get()
            bf1_middle = self.bf1_middle.get()
            bf1_long = self.bf1_long.get()
            
            # Butterfly 2
            bf2_short = self.bf2_short.get()
            bf2_middle = self.bf2_middle.get()
            bf2_long = self.bf2_long.get()
            
            # Validate
            if not all([bf1_short, bf1_middle, bf1_long, bf2_short, bf2_middle, bf2_long]):
                messagebox.showerror("Error", "Please select all butterfly tenors")
                return
            
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
                messagebox.showerror("Error", "No data found for selected date range")
                self.status.config(text="No data found", fg='red')
                return
            
            # Calculate butterflies for each date
            bf1_values = []
            bf2_values = []
            valid_dates = []
            
            for i, date in enumerate(dates):
                if i % 10 == 0:
                    self.status.config(text=f"Processing {i+1}/{len(dates)}: {date}", fg='blue')
                    self.root.update()
                
                # Get rates for this date
                rates = self.get_rates_for_date(date, currency)
                
                # Calculate both butterflies
                bf1 = self.calculate_butterfly(bf1_short, bf1_middle, bf1_long, rates)
                bf2 = self.calculate_butterfly(bf2_short, bf2_middle, bf2_long, rates)
                
                if bf1 is not None and bf2 is not None:
                    bf1_values.append(bf1)
                    bf2_values.append(bf2)
                    valid_dates.append(datetime.strptime(date, '%Y-%m-%d'))
            
            if not bf1_values:
                messagebox.showerror("Error", "Could not calculate butterflies.\n\nCheck that all tenors have data.")
                self.status.config(text="Calculation failed", fg='red')
                return
            
            # Plot results
            self.plot_results(valid_dates, bf1_values, bf2_values,
                            bf1_short, bf1_middle, bf1_long,
                            bf2_short, bf2_middle, bf2_long,
                            currency)
            
            self.status.config(text=f"✅ Analysis complete! Analyzed {len(valid_dates)} dates", fg='green')
            
        except Exception as e:
            messagebox.showerror("Error", f"Analysis failed:\n{str(e)}")
            self.status.config(text=f"Error: {str(e)}", fg='red')
            import traceback
            traceback.print_exc()
    
    def plot_results(self, dates, bf1_values, bf2_values, 
                     bf1_s, bf1_m, bf1_l, bf2_s, bf2_m, bf2_l, currency):
        """Plot the butterfly analysis results with responsive layout"""
        # Store data for export
        self.last_chart_data = {
            'Date': [d.strftime('%Y-%m-%d') for d in dates],
            f'{bf1_s}/{bf1_m}/{bf1_l} Butterfly': bf1_values,
            f'{bf2_s}/{bf2_m}/{bf2_l} Butterfly': bf2_values,
            'Difference (BF2-BF1)': [bf2 - bf1 for bf1, bf2 in zip(bf1_values, bf2_values)]
        }
        
        # Clear previous chart
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        
        # Get screen dimensions for adaptive sizing
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Adaptive figure sizing
        if screen_width <= 1366:  # Laptop
            fig_width = 11
            fig_height = 8
        elif screen_width <= 1920:  # Standard desktop
            fig_width = 13
            fig_height = 9
        else:  # Large desktop
            fig_width = 14
            fig_height = 10
        
        fonts = ChartStyler.get_font_sizes(screen_width)
        colors = ChartStyler.get_color_palette()
        
        # Create figure with 3 subplots
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(fig_width, fig_height), dpi=100)
        fig.patch.set_facecolor('white')
        plt.subplots_adjust(hspace=0.35, top=0.95, bottom=0.08)
        
        # Convert to numpy arrays
        bf1_values = np.array(bf1_values)
        bf2_values = np.array(bf2_values)
        
        # Plot 1: Both butterflies
        line1 = ax1.plot(dates, bf1_values, color=colors[0], linewidth=2.5, 
                marker='o', markersize=4, label=f'{bf1_s}/{bf1_m}/{bf1_l}', alpha=0.8)[0]
        line2 = ax1.plot(dates, bf2_values, color=colors[1], linewidth=2.5, 
                marker='s', markersize=4, label=f'{bf2_s}/{bf2_m}/{bf2_l}', alpha=0.8)[0]
        ax1.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.4)
        
        ChartStyler.style_title(ax1, f'{currency} Butterfly Spreads Comparison', screen_width=screen_width)
        ChartStyler.style_labels(ax1, '', 'Butterfly (bp)', screen_width)
        ChartStyler.style_chart(ax1, screen_width)
        ChartStyler.style_legend(ax1, screen_width, loc='best')
        
        # Add hover tooltips
        cursor1 = mplcursors.cursor([line1, line2], hover=True)
        @cursor1.connect("add")
        def on_add1(sel):
            date_idx = int(sel.index)
            if sel.artist == line1:
                sel.annotation.set(text=f'{dates[date_idx].strftime("%Y-%m-%d")}\n{bf1_s}/{bf1_m}/{bf1_l}\n{bf1_values[date_idx]:.5f} bp')
            else:
                sel.annotation.set(text=f'{dates[date_idx].strftime("%Y-%m-%d")}\n{bf2_s}/{bf2_m}/{bf2_l}\n{bf2_values[date_idx]:.5f} bp')
            sel.annotation.get_bbox_patch().set(fc="yellow", alpha=0.9)
        
        # Plot 2: Difference (BF2 - BF1)
        diff = bf2_values - bf1_values
        line3 = ax2.plot(dates, diff, color=colors[2], linewidth=2.5, 
                marker='D', markersize=4, label='Butterfly 2 - Butterfly 1', alpha=0.8)[0]
        ax2.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.4)
        
        ChartStyler.style_title(ax2, 'Butterfly Difference', screen_width=screen_width)
        ChartStyler.style_labels(ax2, '', 'Difference (bp)', screen_width)
        ChartStyler.style_chart(ax2, screen_width)
        ChartStyler.style_legend(ax2, screen_width)
        
        # Add hover tooltips for diff
        cursor2 = mplcursors.cursor(line3, hover=True)
        @cursor2.connect("add")
        def on_add2(sel):
            date_idx = int(sel.index)
            sel.annotation.set(text=f'{dates[date_idx].strftime("%Y-%m-%d")}\nDiff: {diff[date_idx]:.5f} bp')
            sel.annotation.get_bbox_patch().set(fc="lightblue", alpha=0.9)
        
        # Plot 3: Statistical summary
        ax3.axis('off')
        
        # Calculate statistics
        stats_text = []
        stats_text.append(f"{'Metric':<25} {bf1_s}/{bf1_m}/{bf1_l}  {bf2_s}/{bf2_m}/{bf2_l}  Difference")
        stats_text.append("-" * 70)
        stats_text.append(f"{'Current':<25} {bf1_values[-1]:>7.3f}  {bf2_values[-1]:>7.3f}  {diff[-1]:>7.3f}")
        stats_text.append(f"{'Average':<25} {np.mean(bf1_values):>7.3f}  {np.mean(bf2_values):>7.3f}  {np.mean(diff):>7.3f}")
        stats_text.append(f"{'Std Dev':<25} {np.std(bf1_values):>7.3f}  {np.std(bf2_values):>7.3f}  {np.std(diff):>7.3f}")
        stats_text.append(f"{'Min':<25} {np.min(bf1_values):>7.3f}  {np.min(bf2_values):>7.3f}  {np.min(diff):>7.3f}")
        stats_text.append(f"{'Max':<25} {np.max(bf1_values):>7.3f}  {np.max(bf2_values):>7.3f}  {np.max(diff):>7.3f}")
        stats_text.append(f"{'Range':<25} {np.ptp(bf1_values):>7.3f}  {np.ptp(bf2_values):>7.3f}  {np.ptp(diff):>7.3f}")
        
        ax3.text(0.5, 0.5, '\n'.join(stats_text), 
                transform=ax3.transAxes,
                fontsize=fonts['tick'], 
                verticalalignment='center',
                horizontalalignment='center',
                family='monospace',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
        
        # Add timestamp
        timestamp = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        fig.text(0.99, 0.01, timestamp, ha='right', fontsize=fonts['tick']-1, alpha=0.5)
        
        # Embed in tkinter with canvas
        canvas = FigureCanvasTkAgg(fig, self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add button to open in full screen
        btn_frame = tk.Frame(self.chart_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(btn_frame, text="🖥️ Open in Fullscreen", 
                 command=lambda: self.open_fullscreen_chart(dates, bf1_values, bf2_values, 
                                                            bf1_s, bf1_m, bf1_l, bf2_s, bf2_m, bf2_l, currency),
                 bg='#3498db', fg='white', font=('Arial', 10, 'bold'),
                 padx=15, pady=6).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="💾 Save Chart", 
                 command=lambda: self.save_current_chart(fig),
                 bg='#27ae60', fg='white', font=('Arial', 10, 'bold'),
                 padx=15, pady=6).pack(side=tk.LEFT, padx=5)
    
    def open_fullscreen_chart(self, dates, bf1_values, bf2_values, 
                             bf1_s, bf1_m, bf1_l, bf2_s, bf2_m, bf2_l, currency):
        """Open chart in responsive fullscreen window"""
        chart_window = ResponsiveChartWindow(
            self.root, 
            f"Butterfly Spreads - {currency}",
            self.last_chart_data
        )
        chart_window.add_header(
            f"{currency} Butterfly Spreads Analysis",
            f"{bf1_s}/{bf1_m}/{bf1_l} vs {bf2_s}/{bf2_m}/{bf2_l}"
        )
        chart_window.add_controls()
        
        # Create the same chart but optimized for the window size
        self.plot_in_window(chart_window, dates, bf1_values, bf2_values,
                           bf1_s, bf1_m, bf1_l, bf2_s, bf2_m, bf2_l, currency)
    
    def plot_in_window(self, chart_window, dates, bf1_values, bf2_values,
                      bf1_s, bf1_m, bf1_l, bf2_s, bf2_m, bf2_l, currency):
        """Plot in the responsive window"""
        screen_width = chart_window.window.winfo_screenwidth()
        fonts = ChartStyler.get_font_sizes(screen_width)
        colors = ChartStyler.get_color_palette()
        
        fig = chart_window.create_figure()
        gs = fig.add_gridspec(3, 1, hspace=0.3)
        
        # Plot butterfly comparison
        ax1 = fig.add_subplot(gs[0, 0])
        ax1.plot(dates, bf1_values, color=colors[0], linewidth=2.5,
                marker='o', markersize=5, label=f'{bf1_s}/{bf1_m}/{bf1_l}', alpha=0.8)
        ax1.plot(dates, bf2_values, color=colors[1], linewidth=2.5,
                marker='s', markersize=5, label=f'{bf2_s}/{bf2_m}/{bf2_l}', alpha=0.8)
        ax1.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.4)
        
        ChartStyler.style_title(ax1, f'{currency} Butterfly Spreads Comparison', screen_width=screen_width)
        ChartStyler.style_labels(ax1, '', 'Butterfly (bp)', screen_width)
        ChartStyler.style_chart(ax1, screen_width)
        ChartStyler.style_legend(ax1, screen_width)
        
        # Plot difference
        diff = np.array(bf2_values) - np.array(bf1_values)
        ax2 = fig.add_subplot(gs[1, 0])
        ax2.plot(dates, diff, color=colors[2], linewidth=2.5,
                marker='D', markersize=5, label='Difference', alpha=0.8)
        ax2.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.4)
        
        ChartStyler.style_title(ax2, 'Butterfly Difference', screen_width=screen_width)
        ChartStyler.style_labels(ax2, 'Date', 'Difference (bp)', screen_width)
        ChartStyler.style_chart(ax2, screen_width)
        ChartStyler.style_legend(ax2, screen_width)
        
        chart_window.embed_figure(fig)
    
    def save_current_chart(self, fig):
        """Save the current chart"""
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            defaultextension='.png',
            filetypes=[('PNG files', '*.png'), ('PDF files', '*.pdf'), ('All files', '*.*')],
            initialfile="butterfly_chart.png"
        )
        if filename:
            fig.savefig(filename, dpi=300, bbox_inches='tight')
            messagebox.showinfo("Success", f"Chart saved to:\n{filename}")
        ax2.axhline(y=0, color='black', linestyle='--', alpha=0.3)
        ax2.fill_between(dates, diff, 0, alpha=0.2, color='green')
        ax2.set_title('Relative Value: Difference Between Butterflies', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Difference (bp)', fontsize=12)
        ax2.legend(fontsize=11)
        ax2.grid(True, alpha=0.3)
        
        # Add hover tooltips for chart 2
        cursor2 = mplcursors.cursor(line3, hover=True)
        @cursor2.connect("add")
        def on_add2(sel):
            date_idx = int(sel.index)
            sel.annotation.set(text=f'{dates[date_idx].strftime("%Y-%m-%d")}\nDifference: {diff[date_idx]:.5f}bp')
            sel.annotation.get_bbox_patch().set(fc="yellow", alpha=0.9)
        
        # Plot 3: Ratio (BF2 / BF1) - only if no zeros
        if np.all(bf1_values != 0):
            ratio = bf2_values / bf1_values
            line4 = ax3.plot(dates, ratio, 'purple', linewidth=2, label='Butterfly 2 / Butterfly 1')[0]
            ax3.axhline(y=1, color='black', linestyle='--', alpha=0.3, label='Equal (ratio=1)')
            ax3.set_title('Butterfly Ratio', fontsize=14, fontweight='bold')
            ax3.set_ylabel('Ratio', fontsize=12)
            ax3.set_xlabel('Date', fontsize=12)
            ax3.legend(fontsize=11)
            ax3.grid(True, alpha=0.3)
            
            # Add hover tooltips for chart 3
            cursor3 = mplcursors.cursor(line4, hover=True)
            @cursor3.connect("add")
            def on_add3(sel):
                date_idx = int(sel.index)
                sel.annotation.set(text=f'{dates[date_idx].strftime("%Y-%m-%d")}\nRatio: {ratio[date_idx]:.5f}')
                sel.annotation.get_bbox_patch().set(fc="yellow", alpha=0.9)
        else:
            # Show difference again if ratio not possible
            line5 = ax3.plot(dates, diff, 'g-', linewidth=2)[0]
            ax3.axhline(y=0, color='black', linestyle='--', alpha=0.3)
            ax3.set_title('Difference (alternative view)', fontsize=14, fontweight='bold')
            ax3.set_ylabel('Difference (bp)', fontsize=12)
            ax3.set_xlabel('Date', fontsize=12)
            ax3.grid(True, alpha=0.3)
            
            # Add hover tooltips
            cursor3 = mplcursors.cursor(line5, hover=True)
            @cursor3.connect("add")
            def on_add3_alt(sel):
                date_idx = int(sel.index)
                sel.annotation.set(text=f'{dates[date_idx].strftime("%Y-%m-%d")}\nDifference: {diff[date_idx]:.5f}bp')
                sel.annotation.get_bbox_patch().set(fc="yellow", alpha=0.9)
        
        # Add statistics box
        stats_text = f"Butterfly 1 ({bf1_s}/{bf1_m}/{bf1_l}): Avg={np.mean(bf1_values):.2f}bp, "
        stats_text += f"Min={np.min(bf1_values):.2f}bp, Max={np.max(bf1_values):.2f}bp\n"
        stats_text += f"Butterfly 2 ({bf2_s}/{bf2_m}/{bf2_l}): Avg={np.mean(bf2_values):.2f}bp, "
        stats_text += f"Min={np.min(bf2_values):.2f}bp, Max={np.max(bf2_values):.2f}bp\n"
        stats_text += f"Difference: Avg={np.mean(diff):.2f}bp, Min={np.min(diff):.2f}bp, Max={np.max(diff):.2f}bp"
        
        fig.text(0.5, 0.01, stats_text, ha='center', fontsize=10,
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout(rect=[0, 0.05, 1, 1])
        
        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

if __name__ == '__main__':
    root = tk.Tk()
    app = ButterflyAnalyzer(root)
    root.mainloop()
