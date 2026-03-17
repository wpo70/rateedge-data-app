"""
Simple stub for responsive_charts module
Provides basic chart styling without complex responsive features
"""
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt


class ChartStyler:
    """Simple chart styling helper"""
    
    @staticmethod
    def get_font_sizes(screen_width=1920):
        """Return font sizes based on screen width"""
        return {
            'title': 14,
            'label': 12,
            'tick': 10,
            'legend': 10
        }
    
    @staticmethod
    def get_color_palette():
        """Return color palette"""
        return {
            'primary': '#3498db',
            'secondary': '#e74c3c',
            'accent': '#2ecc71',
            'gray': '#95a5a6'
        }
    
    @staticmethod
    def style_title(ax, title, screen_width=1920):
        """Style chart title"""
        fonts = ChartStyler.get_font_sizes(screen_width)
        ax.set_title(title, fontsize=fonts['title'], fontweight='bold')
    
    @staticmethod
    def style_labels(ax, xlabel, ylabel, screen_width=1920):
        """Style axis labels"""
        fonts = ChartStyler.get_font_sizes(screen_width)
        if xlabel:
            ax.set_xlabel(xlabel, fontsize=fonts['label'])
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=fonts['label'])
    
    @staticmethod
    def style_chart(ax, screen_width=1920):
        """Style chart appearance"""
        ax.grid(True, alpha=0.3, linestyle='--')
        fonts = ChartStyler.get_font_sizes(screen_width)
        ax.tick_params(labelsize=fonts['tick'])
    
    @staticmethod
    def style_legend(ax, screen_width=1920, loc='best'):
        """Style legend"""
        fonts = ChartStyler.get_font_sizes(screen_width)
        ax.legend(fontsize=fonts['legend'], loc=loc)


class ResponsiveChartWindow:
    """Simple chart window wrapper"""
    
    def __init__(self, parent, title="Chart", figsize=(12, 8)):
        """Create chart window"""
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("1200x800")
        
        # Store figsize
        self.figsize = figsize
    
    def get_container(self):
        """Return container for chart"""
        return self.window


def create_butterfly_chart(parent, dates, butterfly1, butterfly2, 
                          short1, body1, long1, short2, body2, long2, 
                          currency='AUD'):
    """
    Create butterfly comparison chart
    Simple version without advanced responsive features
    """
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import numpy as np
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    fig.patch.set_facecolor('white')
    
    # Plot butterfly spreads
    ax1.plot(dates, butterfly1, 'b-', linewidth=2, 
            label=f'{short1}/{body1}/{long1}')
    ax1.plot(dates, butterfly2, 'r-', linewidth=2, 
            label=f'{short2}/{body2}/{long2}')
    
    ax1.set_title(f'{currency} Butterfly Spreads Comparison', 
                 fontsize=14, fontweight='bold')
    ax1.set_ylabel('Butterfly (bp)', fontsize=12)
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # Plot difference
    diff = np.array(butterfly2) - np.array(butterfly1)
    ax2.plot(dates, diff, 'g-', linewidth=2, label='Difference')
    ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    
    ax2.set_title('Butterfly Difference', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Date', fontsize=12)
    ax2.set_ylabel('Difference (bp)', fontsize=12)
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Create window
    window = tk.Toplevel(parent)
    window.title(f"{currency} Butterfly Analysis")
    window.geometry("1200x800")
    
    # Embed chart
    canvas = FigureCanvasTkAgg(fig, window)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    return window
