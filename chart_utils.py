"""
Enhanced Chart Utilities
Professional chart styling and responsive layouts for laptop/desktop screens
"""
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import tkinter as tk
from tkinter import filedialog, messagebox
import numpy as np

# Professional color schemes
COLOR_SCHEMES = {
    'default': {
        'primary': '#2E86AB',
        'secondary': '#A23B72',
        'tertiary': '#F18F01',
        'quaternary': '#C73E1D',
        'positive': '#06A77D',
        'negative': '#D62828',
        'neutral': '#6C757D',
        'grid': '#E0E0E0'
    },
    'professional': {
        'primary': '#1f77b4',
        'secondary': '#ff7f0e',
        'tertiary': '#2ca02c',
        'quaternary': '#d62728',
        'positive': '#17a2b8',
        'negative': '#dc3545',
        'neutral': '#6c757d',
        'grid': '#dee2e6'
    },
    'dark': {
        'primary': '#3498db',
        'secondary': '#e74c3c',
        'tertiary': '#2ecc71',
        'quaternary': '#f39c12',
        'positive': '#1abc9c',
        'negative': '#e67e22',
        'neutral': '#95a5a6',
        'grid': '#2c3e50'
    }
}

class EnhancedChartFrame:
    """Enhanced chart frame with toolbar and responsive design"""
    
    def __init__(self, parent, title="Chart", height_ratio=0.6):
        """
        Create enhanced chart frame
        
        Args:
            parent: Parent widget
            title: Chart title
            height_ratio: Height as ratio of screen (0.4-0.8)
        """
        self.parent = parent
        self.title = title
        self.height_ratio = height_ratio
        
        # Detect screen size for responsive design
        screen_width = parent.winfo_screenwidth()
        screen_height = parent.winfo_screenheight()
        
        # Laptop detection (< 1920x1080)
        self.is_laptop = screen_width < 1920 or screen_height < 1080
        
        # Create frame
        self.frame = tk.Frame(parent)
        
        # Toolbar frame
        self.toolbar_frame = tk.Frame(self.frame)
        self.toolbar_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)
        
        # Chart frame
        self.chart_frame = tk.Frame(self.frame)
        self.chart_frame.pack(fill=tk.BOTH, expand=True)
        
        self.figure = None
        self.canvas = None
        self.toolbar = None
        
    def pack(self, **kwargs):
        """Pack the frame"""
        self.frame.pack(**kwargs)
    
    def get_figure_size(self, num_subplots=1):
        """
        Get optimal figure size based on screen size and number of subplots
        
        Args:
            num_subplots: Number of vertical subplots
            
        Returns:
            (width, height) tuple in inches
        """
        if self.is_laptop:
            # Laptop sizes - more compact
            base_width = 11
            base_height_per_plot = 2.5
        else:
            # Desktop sizes - more spacious
            base_width = 14
            base_height_per_plot = 3.5
        
        height = base_height_per_plot * num_subplots
        height = min(height, base_height_per_plot * 4)  # Max 4 plots worth of height
        
        return (base_width, height)
    
    def create_figure(self, num_subplots=1, sharex=False):
        """
        Create matplotlib figure with optimal size
        
        Args:
            num_subplots: Number of vertical subplots
            sharex: Share x-axis between subplots
            
        Returns:
            fig, axes (or single ax if num_subplots=1)
        """
        figsize = self.get_figure_size(num_subplots)
        
        if num_subplots == 1:
            fig, ax = plt.subplots(1, 1, figsize=figsize)
            axes = ax
        else:
            fig, axes = plt.subplots(num_subplots, 1, figsize=figsize, sharex=sharex)
        
        fig.patch.set_facecolor('white')
        
        # Adjust spacing for laptop
        if self.is_laptop:
            plt.tight_layout(rect=[0, 0.08, 1, 0.98], h_pad=1.5)
        else:
            plt.tight_layout(rect=[0, 0.05, 1, 0.98], h_pad=2.5)
        
        self.figure = fig
        return fig, axes
    
    def apply_professional_style(self, ax, title="", xlabel="", ylabel="", 
                                 color_scheme='default'):
        """
        Apply professional styling to axis
        
        Args:
            ax: Matplotlib axis
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label
            color_scheme: Color scheme to use
        """
        colors = COLOR_SCHEMES.get(color_scheme, COLOR_SCHEMES['default'])
        
        # Title and labels with responsive font sizes
        title_size = 12 if self.is_laptop else 14
        label_size = 10 if self.is_laptop else 12
        tick_size = 9 if self.is_laptop else 10
        
        if title:
            ax.set_title(title, fontsize=title_size, fontweight='bold', pad=10)
        if xlabel:
            ax.set_xlabel(xlabel, fontsize=label_size, fontweight='bold')
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=label_size, fontweight='bold')
        
        # Grid
        ax.grid(True, alpha=0.3, color=colors['grid'], linestyle='--', linewidth=0.8)
        ax.set_axisbelow(True)
        
        # Tick labels
        ax.tick_params(labelsize=tick_size)
        
        # Spines
        for spine in ax.spines.values():
            spine.set_edgecolor(colors['grid'])
            spine.set_linewidth(1.2)
    
    def add_zero_line(self, ax, color='black', alpha=0.3):
        """Add horizontal line at y=0"""
        ax.axhline(y=0, color=color, linestyle='--', alpha=alpha, linewidth=1.5)
    
    def add_stats_box(self, fig, stats_text, position='bottom'):
        """
        Add statistics box to figure
        
        Args:
            fig: Matplotlib figure
            stats_text: Text to display
            position: 'bottom' or 'top'
        """
        font_size = 9 if self.is_laptop else 10
        
        if position == 'bottom':
            y_pos = 0.02
        else:
            y_pos = 0.98
        
        fig.text(0.5, y_pos, stats_text, ha='center', fontsize=font_size,
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8, 
                         edgecolor='gray', linewidth=1.5))
    
    def show_chart(self, fig):
        """Display chart in frame with navigation toolbar"""
        # Clear previous chart
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        for widget in self.toolbar_frame.winfo_children():
            widget.destroy()
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(fig, self.chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Create toolbar with navigation tools
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.toolbar_frame)
        self.toolbar.update()
        
        # Add export button to toolbar
        export_btn = tk.Button(self.toolbar_frame, text="💾 Export Chart", 
                               command=self.export_chart,
                               bg='#3498db', fg='white', font=('Arial', 9, 'bold'),
                               padx=10, pady=3)
        export_btn.pack(side=tk.RIGHT, padx=5)
    
    def export_chart(self):
        """Export chart to file"""
        if self.figure is None:
            messagebox.showwarning("Warning", "No chart to export")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension='.png',
            filetypes=[
                ('PNG files', '*.png'),
                ('PDF files', '*.pdf'),
                ('SVG files', '*.svg'),
                ('All files', '*.*')
            ],
            initialfile=f"{self.title.replace(' ', '_')}.png"
        )
        
        if filename:
            try:
                self.figure.savefig(filename, dpi=300, bbox_inches='tight',
                                   facecolor='white', edgecolor='none')
                messagebox.showinfo("Success", f"Chart exported to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export chart:\n{e}")


def create_professional_line_chart(ax, x_data, y_data, label, color, 
                                   linewidth=2, marker=None, alpha=1.0):
    """
    Create professional line chart
    
    Args:
        ax: Matplotlib axis
        x_data: X-axis data
        y_data: Y-axis data
        label: Line label
        color: Line color
        linewidth: Line width
        marker: Optional marker style
        alpha: Line transparency
        
    Returns:
        Line object
    """
    line = ax.plot(x_data, y_data, color=color, linewidth=linewidth,
                   label=label, marker=marker, alpha=alpha,
                   markersize=4 if marker else 0,
                   markeredgecolor='white', markeredgewidth=0.5)[0]
    return line


def create_filled_area(ax, x_data, y_data, baseline=0, color='green', alpha=0.2):
    """
    Create filled area under/over line
    
    Args:
        ax: Matplotlib axis
        x_data: X-axis data
        y_data: Y-axis data
        baseline: Baseline value
        color: Fill color
        alpha: Fill transparency
    """
    ax.fill_between(x_data, y_data, baseline, alpha=alpha, color=color)


def add_hover_tooltips(line, dates, values, label=""):
    """
    Add interactive hover tooltips to line
    
    Args:
        line: Line object
        dates: Date array
        values: Value array
        label: Optional label prefix
    """
    try:
        import mplcursors
        cursor = mplcursors.cursor(line, hover=True)
        
        @cursor.connect("add")
        def on_add(sel):
            idx = int(sel.index)
            date_str = dates[idx].strftime("%Y-%m-%d") if hasattr(dates[idx], 'strftime') else str(dates[idx])
            value_str = f"{values[idx]:.5f}"
            
            text = f"{date_str}"
            if label:
                text += f"\n{label}"
            text += f"\n{value_str}"
            
            sel.annotation.set(text=text)
            sel.annotation.get_bbox_patch().set(fc="yellow", alpha=0.95, 
                                               edgecolor='gray', linewidth=1.5)
    except ImportError:
        # mplcursors not available
        pass


def format_chart_for_laptop():
    """Set matplotlib defaults for laptop screens"""
    plt.rcParams['figure.dpi'] = 100
    plt.rcParams['font.size'] = 9
    plt.rcParams['axes.labelsize'] = 10
    plt.rcParams['axes.titlesize'] = 12
    plt.rcParams['xtick.labelsize'] = 9
    plt.rcParams['ytick.labelsize'] = 9
    plt.rcParams['legend.fontsize'] = 9


def format_chart_for_desktop():
    """Set matplotlib defaults for desktop screens"""
    plt.rcParams['figure.dpi'] = 100
    plt.rcParams['font.size'] = 10
    plt.rcParams['axes.labelsize'] = 12
    plt.rcParams['axes.titlesize'] = 14
    plt.rcParams['xtick.labelsize'] = 10
    plt.rcParams['ytick.labelsize'] = 10
    plt.rcParams['legend.fontsize'] = 11


def detect_and_configure_display(root):
    """
    Detect screen size and configure matplotlib accordingly
    
    Args:
        root: Tkinter root window
        
    Returns:
        bool: True if laptop, False if desktop
    """
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    
    is_laptop = screen_width < 1920 or screen_height < 1080
    
    if is_laptop:
        format_chart_for_laptop()
    else:
        format_chart_for_desktop()
    
    return is_laptop
