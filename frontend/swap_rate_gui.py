"""
Desktop GUI Application for IRS Swap Rate Management
Provides user-friendly interface for data import, viewing, and analysis
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from database_models import DatabaseManager
from excel_importer import ExcelImporter
from analytics import SwapRateAnalytics
from alerts import AlertManager, AlertConditions
from report_generator import SwapRateReportGenerator
import pandas as pd

# Matplotlib for charting
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure


class SwapRateApp:
    """Main application class"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("RateEdge - Professional Interest Rate Analytics")
        self.root.geometry("1400x900")
        
        # Set window icon
        try:
            from PIL import Image, ImageTk
            icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'assets', 'icon.png')
            if os.path.exists(icon_path):
                icon_img = Image.open(icon_path)
                icon_photo = ImageTk.PhotoImage(icon_img)
                self.root.iconphoto(True, icon_photo)
        except Exception as e:
            print(f"Could not set window icon: {e}")
        
        # RateEdge Brand Colors
        self.colors = {
            'primary': '#1e3a5f',        # Navy (Rate)
            'primary_light': '#2563eb',  # Blue
            'accent': '#dc2626',         # Red (Edge)
            'accent_hover': '#ef4444',   # Red Light
            'success': '#27ae60',        # Green
            'warning': '#f39c12',        # Orange
            'danger': '#dc2626',         # Red
            'bg_main': '#f1f5f9',        # Gray 100
            'bg_card': '#ffffff',        # White for cards
            'text_dark': '#1e3a5f',      # Navy text
            'text_light': '#64748b',     # Gray 500
            'border': '#e2e8f0'          # Gray 200
        }
        
        # Font configuration
        self.fonts = {
            'title': ('Segoe UI', 18, 'bold'),
            'heading': ('Segoe UI', 12, 'bold'),
            'normal': ('Segoe UI', 10),
            'small': ('Segoe UI', 9),
            'mono': ('Consolas', 10)
        }
        
        # Theme management
        self.current_theme = 'light'  # 'light' or 'dark'
        self.themes = {
            'light': {
                'primary': '#1e3a5f',       # Navy
                'primary_light': '#2563eb', # Blue
                'accent': '#dc2626',        # Red
                'accent_hover': '#ef4444',  # Red Light
                'success': '#27ae60',
                'warning': '#f39c12',
                'danger': '#dc2626',
                'bg_main': '#f1f5f9',       # Gray 100
                'bg_card': '#ffffff',
                'text_dark': '#1e3a5f',
                'text_light': '#64748b',
                'border': '#e2e8f0',
                'table_alt': '#f8f9fa',
                'table_hover': '#e8f4f8',
                'header_bg': '#1e3a5f'      # Navy header
            },
            'dark': {
                'primary': '#f1f5f9',       # Light text
                'primary_light': '#3b82f6', # Blue Light
                'accent': '#ef4444',        # Red Light
                'accent_hover': '#dc2626',
                'success': '#27ae60',
                'warning': '#f39c12',
                'danger': '#ef4444',
                'bg_main': '#0f172a',       # Slate Dark
                'bg_card': '#1e293b',
                'text_dark': '#f1f5f9',
                'text_light': '#94a3b8',
                'border': '#334155',
                'table_alt': '#1e293b',
                'table_hover': '#1e3a5f',
                'header_bg': '#0f172a'      # Slate header
            }
        }
        
        # View mode
        self.view_mode = 'standard'  # 'standard' or 'pivot'
        self.benchmark_view_mode = 'standard'
        self.ois_view_mode = 'standard'
        self.ois_short_view_mode = 'standard'  # for short term OIS
        self.ois_medium_view_mode = 'standard'  # for medium term OIS
        
        # Update colors to current theme
        self.colors = self.themes[self.current_theme]
        
        # Configure root window background
        self.root.configure(bg=self.colors['bg_main'])
        
        # Initialize database
        db_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'swap_rates.db')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_manager = DatabaseManager(f'sqlite:///{db_path}')
        self.excel_importer = ExcelImporter(self.db_manager)
        
        # Initialize market data importer
        self.db_path = db_path
        try:
            from market_data_importer import MarketDataImporter
            self.market_data_importer = MarketDataImporter(db_path)
        except ImportError:
            self.market_data_importer = None
            print("Warning: Market data importer not available")
        
        # Initialize analytics and reporting modules
        self.analytics = SwapRateAnalytics(self.db_manager)
        self.alert_manager = AlertManager(self.db_manager)
        self.report_generator = SwapRateReportGenerator(self.db_manager, self.analytics)
        
        # Alert checking configuration
        self.alert_check_interval = 300000  # 5 minutes in milliseconds
        self.alert_after_id = None
        
        # Configure custom styles
        self.setup_styles()
        
        # Setup UI
        self.setup_ui()
        
        # Load initial data (with delay to ensure UI is ready)
        self.root.after(100, self.refresh_everything)
        
        # Check alerts on startup (delayed to ensure UI is ready)
        self.root.after(2000, self.check_alerts_background)
    
    def refresh_everything(self):
        """Refresh all UI components including dashboard"""
        # Update filter dropdowns
        self.update_tenor_list()
        self.update_floating_rate_list()
        self.update_benchmark_rate_type_list()
        self.update_ois_rate_type_list()
        
        # Refresh the data table
        self.refresh_data()
        
        # Refresh benchmark data
        self.refresh_benchmark_data()
        
        # Refresh OIS data
        self.refresh_ois_data()
        
        # Force dashboard update
        self.update_dashboard()
    
    def update_dashboard(self):
        """Update dashboard metrics - REMOVED, dashboard deleted"""
        pass  # Dashboard removed, this method does nothing now
    
    def toggle_theme(self):
        """Toggle between light and dark themes"""
        self.current_theme = 'dark' if self.current_theme == 'light' else 'light'
        self.colors = self.themes[self.current_theme]
        
        # Update root background
        self.root.configure(bg=self.colors['bg_main'])
        
        # Reapply styles
        self.setup_styles()
        
        # Update heading colors based on current view mode
        self.update_heading_colors()
        
        # Refresh data to apply new colors
        self.refresh_data()
        
        # Show message
        theme_name = "Dark" if self.current_theme == 'dark' else "Light"
        self.status_var.set(f"Switched to {theme_name} Mode")
    
    def toggle_view_mode(self):
        """Toggle between standard and pivot view"""
        self.view_mode = 'pivot' if self.view_mode == 'standard' else 'standard'
        
        # Update heading colors based on view mode
        self.update_heading_colors()
        
        # Get current filters from UI
        filters = self.get_current_filters()
        
        # Refresh with current filters
        self.refresh_data(filters)
        
        view_name = "Table" if self.view_mode == 'pivot' else "Standard"
        self.status_var.set(f"Switched to {view_name} View")
    
    def update_heading_colors(self):
        """Update Treeview heading colors based on view mode"""
        style = ttk.Style()
        
        # In pivot view, use orange for tenor headers
        if self.view_mode == 'pivot':
            style.configure('Treeview.Heading',
                           background=self.colors['warning'],  # Orange
                           foreground='white',
                           font=self.fonts['heading'],
                           borderwidth=1,
                           relief='raised')
            style.map('Treeview.Heading',
                     background=[('active', '#e67e22')],  # Darker orange on hover
                     foreground=[('active', 'white')])
        else:
            # Standard view - use primary color
            style.configure('Treeview.Heading',
                           background=self.colors['primary'],
                           foreground='white',
                           font=self.fonts['heading'],
                           borderwidth=1,
                           relief='raised')
            style.map('Treeview.Heading',
                     background=[('active', self.colors['primary_light'])],
                     foreground=[('active', 'white')])
    
    def get_current_filters(self):
        """Get current filter values from UI"""
        filters = {}
        
        # Currency filter
        if self.currency_var.get() != "All":
            filters['currency'] = self.currency_var.get()
        
        # Tenor filter (only for standard view, NOT for pivot!)
        # In pivot view, tenors are columns, so we want ALL tenors
        if self.view_mode == 'standard' and self.tenor_var.get() != "All":
            filters['tenor'] = self.tenor_var.get()
        
        # Date filters
        if self.start_date_var.get():
            try:
                filters['start_date'] = datetime.strptime(
                    self.start_date_var.get(), '%Y-%m-%d'
                ).date()
            except ValueError:
                pass  # Ignore invalid dates
        
        if self.end_date_var.get():
            try:
                filters['end_date'] = datetime.strptime(
                    self.end_date_var.get(), '%Y-%m-%d'
                ).date()
            except ValueError:
                pass  # Ignore invalid dates
        
        return filters
    
    def get_dashboard_metrics(self):
        """Calculate dashboard metrics"""
        session = self.db_manager.Session()
        try:
            from database_models import SwapRate
            from sqlalchemy import func
            
            # Total records
            total = session.query(SwapRate).count()
            
            # Currencies
            currencies = session.query(SwapRate.currency).distinct().all()
            curr_list = ", ".join([c[0] for c in currencies]) if currencies else "None"
            
            # Latest date
            latest = session.query(SwapRate.date).order_by(SwapRate.date.desc()).first()
            latest_date = latest[0].strftime('%Y-%m-%d') if latest else "N/A"
            
            # Date range
            oldest = session.query(SwapRate.date).order_by(SwapRate.date.asc()).first()
            oldest_date = oldest[0].strftime('%Y-%m-%d') if oldest else "N/A"
            
            # Average 5Y rate
            avg_5y = session.query(SwapRate).filter(
                SwapRate.tenor == '5Y'
            ).with_entities(func.avg(SwapRate.rate)).scalar()
            avg_5y_pct = avg_5y if avg_5y else None
            
            return {
                'total_records': total,
                'currencies': curr_list,
                'latest_date': latest_date,
                'oldest_date': oldest_date,
                'avg_rate_5y': avg_5y_pct
            }
        finally:
            session.close()
    
    def setup_styles(self):
        """Configure custom ttk styles for modern look"""
        style = ttk.Style()
        
        # Use 'clam' theme as base (more customizable than default)
        style.theme_use('clam')
        
        # Configure main frame background
        style.configure('Main.TFrame', background=self.colors['bg_main'])
        style.configure('Card.TFrame', background=self.colors['bg_card'], 
                       relief='solid', borderwidth=1)
        
        # Configure labels
        style.configure('Title.TLabel', 
                       background=self.colors['bg_main'],
                       foreground=self.colors['primary'],
                       font=self.fonts['title'])
        
        style.configure('Heading.TLabel',
                       background=self.colors['bg_card'],
                       foreground=self.colors['primary'],
                       font=self.fonts['heading'])
        
        style.configure('TLabel',
                       background=self.colors['bg_card'],
                       foreground=self.colors['text_dark'],
                       font=self.fonts['normal'])
        
        # Configure buttons with modern look
        style.configure('Accent.TButton',
                       background=self.colors['accent'],
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       font=self.fonts['normal'],
                       padding=(15, 8))
        
        style.map('Accent.TButton',
                 background=[('active', self.colors['accent_hover']),
                           ('pressed', self.colors['accent_hover'])])
        
        # Success button (green)
        style.configure('Success.TButton',
                       background=self.colors['success'],
                       foreground='white',
                       borderwidth=0,
                       font=self.fonts['normal'],
                       padding=(12, 6))
        
        style.map('Success.TButton',
                 background=[('active', '#229954')])
        
        # Danger button (red)
        style.configure('Danger.TButton',
                       background=self.colors['danger'],
                       foreground='white',
                       borderwidth=0,
                       font=self.fonts['normal'],
                       padding=(12, 6))
        
        # Configure comboboxes
        style.configure('TCombobox',
                       fieldbackground='white',
                       background=self.colors['accent'],
                       foreground=self.colors['text_dark'],
                       arrowcolor=self.colors['accent'],
                       font=self.fonts['normal'],
                       padding=5)
        
        # Configure entry widgets
        style.configure('TEntry',
                       fieldbackground='white',
                       foreground=self.colors['text_dark'],
                       font=self.fonts['normal'],
                       padding=5)
        
        # Configure LabelFrame
        style.configure('TLabelframe',
                       background=self.colors['bg_card'],
                       foreground=self.colors['primary'],
                       borderwidth=2,
                       relief='solid',
                       font=self.fonts['heading'])
        
        style.configure('TLabelframe.Label',
                       background=self.colors['bg_card'],
                       foreground=self.colors['primary'],
                       font=self.fonts['heading'])
        
        # Configure Treeview (table)
        style.configure('Treeview',
                       background=self.colors['bg_card'],
                       foreground=self.colors['text_dark'],
                       fieldbackground=self.colors['bg_card'],
                       font=self.fonts['normal'],
                       rowheight=28)
        
        style.configure('Treeview.Heading',
                       background=self.colors['primary'],
                       foreground='white',
                       font=self.fonts['heading'],
                       borderwidth=1,
                       relief='raised')
        
        style.map('Treeview.Heading',
                 background=[('active', self.colors['primary_light'])],
                 foreground=[('active', 'white')])
        
        style.map('Treeview',
                 background=[('selected', self.colors['accent'])],
                 foreground=[('selected', 'white')])
    
    def setup_ui(self):
        """Create the user interface"""
        
        # Create menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Import Excel", command=self.import_excel)
        file_menu.add_command(label="Import Market Data Files", command=self.import_market_data)
        file_menu.add_separator()
        file_menu.add_command(label="Export to Excel", command=self.export_to_excel)
        file_menu.add_command(label="Export to CSV", command=self.export_to_csv)
        file_menu.add_command(label="Export to JSON", command=self.export_to_json)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Data menu
        data_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Data", menu=data_menu)
        data_menu.add_command(label="Add Rate Manually", command=self.add_rate_dialog)
        data_menu.add_command(label="Delete Selected", command=self.delete_selected)
        data_menu.add_command(label="Refresh", command=self.refresh_data)
        
        # Charts menu
        charts_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Charts", menu=charts_menu)
        charts_menu.add_command(label="Compare Tenors", command=self.show_tenor_comparison_chart)
        charts_menu.add_command(label="Yield Curve", command=self.show_yield_curve)
        charts_menu.add_command(label="Spread Chart", command=self.show_spread_analysis)
        charts_menu.add_command(label="Volatility Chart", command=self.show_volatility_analysis)
        
        # Analytics menu
        analytics_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Analytics", menu=analytics_menu)
        analytics_menu.add_command(label="Statistics Summary", command=self.show_statistics_dialog)
        analytics_menu.add_command(label="Spread Analysis", command=self.show_spread_analysis)
        analytics_menu.add_command(label="Volatility Analysis", command=self.show_volatility_analysis)
        analytics_menu.add_command(label="Rate Changes", command=self.show_rate_changes)
        analytics_menu.add_command(label="Correlation Matrix", command=self.show_correlation_matrix)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="💱 Simple Forward Swap Pricer", command=self.launch_simple_pricer)
        tools_menu.add_command(label="📊 Historical Forward Swap Analyzer", command=self.launch_historical_analyzer)
        tools_menu.add_command(label="📈 Forward Swap Matrix Generator", command=self.launch_forward_matrix)
        tools_menu.add_command(label="📊 Forward Basis Matrix (6M vs 3M)", command=self.launch_forward_basis_matrix)
        tools_menu.add_separator()
        tools_menu.add_command(label="📊 Swap Relative Value Analyzer", command=self.launch_relative_value)
        tools_menu.add_separator()
        tools_menu.add_command(label="🦋 IRS Butterfly Spread Analyzer", command=self.launch_butterfly_analyzer)
        tools_menu.add_command(label="📈 AUD Basis Analyzer (3M vs 6M)", command=self.launch_basis_analyzer)
        tools_menu.add_command(label="🦋 Basis Butterfly Analyzer (3M vs 6M)", command=self.launch_basis_butterfly_analyzer)
        tools_menu.add_separator()
        tools_menu.add_command(label="Manage Alerts", command=self.show_alerts_manager)
        tools_menu.add_command(label="Check Alerts Now", command=self.check_alerts_manual)
        tools_menu.add_separator()
        tools_menu.add_command(label="Find Missing Dates", command=self.show_missing_dates)
        tools_menu.add_command(label="Detect Outliers", command=self.show_outliers)
        tools_menu.add_command(label="Data Quality Report", command=self.show_data_quality)
        
        # Reports menu
        reports_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Reports", menu=reports_menu)
        reports_menu.add_command(label="Generate Market Report (PDF)", command=self.generate_pdf_report)
        reports_menu.add_command(label="Custom Report", command=self.generate_custom_report)
        
        # View menu (NEW)
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Toggle Dark Mode", command=self.toggle_theme)
        view_menu.add_command(label="Toggle Table View", command=self.toggle_view_mode)
        view_menu.add_separator()
        view_menu.add_command(label="Refresh Dashboard", command=self.refresh_data)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Feature Guide", command=self.show_feature_guide)
        
        # Main container with modern styling
        main_container = ttk.Frame(self.root, padding="20", style='Main.TFrame')
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_container.columnconfigure(0, weight=1)
        main_container.rowconfigure(2, weight=1)  # Table row expands
        
        # Professional Header with RateEdge Branding
        header_bg = self.colors.get('header_bg', '#1e3a5f')
        header_frame = tk.Frame(main_container, bg=header_bg, height=90)
        header_frame.grid(row=0, column=0, pady=(0, 10), sticky=(tk.W, tk.E))
        header_frame.grid_propagate(False)  # Maintain fixed height
        
        
        # Title and subtitle container - CENTERED WITH LOGO
        # Center container with logo and title
        center_container = tk.Frame(header_frame, bg=header_bg)
        center_container.pack(expand=True, fill=tk.BOTH)
        
        # Inner frame to hold logo and text (centered)
        inner_container = tk.Frame(center_container, bg=header_bg)
        inner_container.pack(anchor=tk.CENTER)
        
        # Try to load and display logo (use dark version for dark theme)
        try:
            from PIL import Image, ImageTk
            if self.current_theme == 'dark':
                logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'assets', 'logo_dark.png')
            else:
                logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'assets', 'logo_dark.png')
            if os.path.exists(logo_path):
                logo_img = Image.open(logo_path)
                # Resize logo to fit header (maintain aspect ratio)
                logo_img = logo_img.resize((200, 75), Image.Resampling.LANCZOS)
                logo_photo = ImageTk.PhotoImage(logo_img)
                logo_label = tk.Label(inner_container, image=logo_photo, bg=header_bg)
                logo_label.image = logo_photo  # Keep a reference
                logo_label.pack(side=tk.LEFT, padx=(0, 20), pady=0)
        except Exception as e:
            print(f"Could not load logo: {e}")
        
        # Title container
        title_container = tk.Frame(inner_container, bg=header_bg)
        title_container.pack(side=tk.LEFT, fill=tk.Y)
        
        # Main title - RateEdge styling
        title_frame = tk.Frame(title_container, bg=header_bg)
        title_frame.pack(anchor=tk.W)
        
        # "Rate" in white
        rate_label = tk.Label(title_frame, 
                              text="Rate", 
                              font=('Segoe UI', 20, 'bold'),
                              bg=header_bg,
                              fg='white')
        rate_label.pack(side=tk.LEFT)
        
        # "Edge" in red
        edge_label = tk.Label(title_frame, 
                              text="Edge", 
                              font=('Segoe UI', 20, 'bold'),
                              bg=header_bg,
                              fg='#dc2626')
        edge_label.pack(side=tk.LEFT)
        
        # Subtitle line 1
        subtitle1_label = tk.Label(title_container,
                                  text="Professional Edition",
                                  font=('Segoe UI', 10),
                                  bg=header_bg,
                                  fg='#e2e8f0')
        subtitle1_label.pack(anchor=tk.W)
        
        # Subtitle line 2
        subtitle2_label = tk.Label(title_container,
                                  text="Multi-Currency Interest Rate Swap Analytics",
                                  font=('Segoe UI', 9),
                                  bg=header_bg,
                                  fg='#94a3b8')
        subtitle2_label.pack(anchor=tk.W)
        
        # View control buttons in header (right side)
        button_frame = tk.Frame(header_frame, bg=header_bg)
        button_frame.pack(side=tk.RIGHT, padx=15, pady=5)
        
        # Theme toggle button
        theme_text = "🌙 Dark Mode" if self.current_theme == 'light' else "☀️ Light Mode"
        theme_btn = tk.Button(button_frame, text=theme_text, command=self.toggle_theme,
                             font=('Segoe UI', 10), 
                             bg='#2563eb', fg='white', relief=tk.FLAT,
                             padx=15, pady=8, cursor='hand2',
                             activebackground='#3b82f6', activeforeground='white')
        theme_btn.pack(side=tk.TOP, pady=5)
        
        # View toggle button  
        view_text = "📊 Table View" if self.view_mode == 'standard' else "📊 Standard View"
        view_btn = tk.Button(button_frame, text=view_text, command=self.toggle_view_mode,
                            font=('Segoe UI', 10),
                            bg='#2563eb', fg='white', relief=tk.FLAT,
                            padx=15, pady=8, cursor='hand2',
                            activebackground='#3b82f6', activeforeground='white')
        view_btn.pack(side=tk.TOP, pady=5)
        
        # NO DASHBOARD - REMOVED TO FIX BUGS
        # Dashboard was causing display issues, removed entirely
        
        # Filter section with card styling
        filter_card = ttk.Frame(main_container, style='Card.TFrame', relief='solid', borderwidth=1)
        filter_card.grid(row=1, column=0, pady=(0, 15), sticky=(tk.W, tk.E))
        
        filter_frame = ttk.LabelFrame(filter_card, text="  Filters & Quick Actions  ", 
                                     padding="15", style='TLabelframe')
        filter_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Currency filter
        ttk.Label(filter_frame, text="Currency:", font=self.fonts['normal']).grid(row=0, column=0, padx=(0, 8), sticky=tk.W)
        self.currency_var = tk.StringVar(value="All")
        currency_combo = ttk.Combobox(filter_frame, textvariable=self.currency_var,
                                     values=["All", "AUD", "CAD", "EUR", "GBP", "JPY", "NZD", "USD"], width=12, state='readonly',
                                     font=self.fonts['normal'])
        currency_combo.grid(row=0, column=1, padx=(0, 20))
        currency_combo.bind('<<ComboboxSelected>>', lambda e: self.update_floating_rate_list(self.currency_var.get()))
        
        # Tenor filter
        ttk.Label(filter_frame, text="Tenor:", font=self.fonts['normal']).grid(row=0, column=2, padx=(0, 8), sticky=tk.W)
        self.tenor_var = tk.StringVar(value="All")
        self.tenor_combo = ttk.Combobox(filter_frame, textvariable=self.tenor_var,
                                       width=12, state='readonly', font=self.fonts['normal'])
        self.tenor_combo.grid(row=0, column=3, padx=(0, 20))
        self.update_tenor_list()
        
        # Floating Rate filter
        ttk.Label(filter_frame, text="Floating:", font=self.fonts['normal']).grid(row=0, column=4, padx=(0, 8), sticky=tk.W)
        self.floating_rate_var = tk.StringVar(value="All")
        self.floating_rate_combo = ttk.Combobox(filter_frame, textvariable=self.floating_rate_var,
                                               width=12, state='readonly', font=self.fonts['normal'])
        self.floating_rate_combo.grid(row=0, column=5, padx=(0, 20))
        self.floating_rate_combo['values'] = ['All']  # Will be populated based on currency
        
        # Date range filter
        ttk.Label(filter_frame, text="From:", font=self.fonts['normal']).grid(row=0, column=6, padx=(0, 8), sticky=tk.W)
        self.start_date_var = tk.StringVar()
        start_date_entry = ttk.Entry(filter_frame, textvariable=self.start_date_var, width=13,
                                     font=self.fonts['normal'])
        start_date_entry.grid(row=0, column=7, padx=(0, 15))
        
        ttk.Label(filter_frame, text="To:", font=self.fonts['normal']).grid(row=0, column=8, padx=(0, 8), sticky=tk.W)
        self.end_date_var = tk.StringVar()
        end_date_entry = ttk.Entry(filter_frame, textvariable=self.end_date_var, width=13,
                                    font=self.fonts['normal'])
        end_date_entry.grid(row=0, column=9, padx=(0, 20))
        
        # Filter button
        filter_btn = ttk.Button(filter_frame, text="Apply Filters", command=self.apply_filters,
                               style='Accent.TButton')
        filter_btn.grid(row=0, column=10, padx=(10, 5))
        
        # Clear filters button
        clear_btn = ttk.Button(filter_frame, text="Clear", command=self.clear_filters,
                              style='TButton')
        clear_btn.grid(row=0, column=11, padx=5)
        
        # Separator
        ttk.Separator(filter_frame, orient='horizontal').grid(row=1, column=0, columnspan=12, 
                                                              sticky=(tk.W, tk.E), pady=(15, 10))
        
        # Quick date range buttons (row 2)
        ttk.Label(filter_frame, text="Quick Dates:", font=self.fonts['normal']).grid(row=2, column=0, 
                                                                                      padx=(0, 8), sticky=tk.W)
        ttk.Button(filter_frame, text="Last 30 Days", 
                  command=lambda: self.set_date_range(30), width=13).grid(row=2, column=1, padx=3, pady=5)
        ttk.Button(filter_frame, text="Last 90 Days", 
                  command=lambda: self.set_date_range(90), width=13).grid(row=2, column=2, padx=3, pady=5)
        ttk.Button(filter_frame, text="Last Year", 
                  command=lambda: self.set_date_range(365), width=13).grid(row=2, column=3, padx=3, pady=5)
        ttk.Button(filter_frame, text="All Time", 
                  command=self.set_all_time_range, width=13).grid(row=2, column=4, padx=3, pady=5)
        
        # Date format hint
        ttk.Label(filter_frame, text="Date format: YYYY-MM-DD (e.g., 2024-01-15)", 
                 font=self.fonts['small'], foreground=self.colors['text_light']).grid(row=2, column=5, 
                                                                                       columnspan=5, 
                                                                                       sticky=tk.W, padx=(15, 0))
        
        # Separator before tenor range filters
        ttk.Separator(filter_frame, orient='horizontal').grid(row=3, column=0, columnspan=10, 
                                                              sticky=(tk.W, tk.E), pady=(10, 10))
        
        # Tenor Range Quick Filters (row 4)
        ttk.Label(filter_frame, text="Tenor Range:", font=self.fonts['normal']).grid(row=4, column=0, 
                                                                                      padx=(0, 8), sticky=tk.W)
        ttk.Button(filter_frame, text="0-2Y (Short)", 
                  command=lambda: self.apply_tenor_range_filter(0, 2), width=13).grid(row=4, column=1, padx=3, pady=5)
        ttk.Button(filter_frame, text="2Y+ (Long)", 
                  command=lambda: self.apply_tenor_range_filter(2, None), width=13).grid(row=4, column=2, padx=3, pady=5)
        ttk.Button(filter_frame, text="All Tenors", 
                  command=self.clear_tenor_range_filter, width=13).grid(row=4, column=3, padx=3, pady=5)
        
        # Info label for tenor range filter
        self.tenor_range_label = ttk.Label(filter_frame, text="", 
                                          font=self.fonts['small'], 
                                          foreground=self.colors['accent'])
        self.tenor_range_label.grid(row=4, column=4, columnspan=6, sticky=tk.W, padx=(15, 0))
        
        # Create Notebook for tabs
        notebook = ttk.Notebook(main_container, style='TNotebook')
        notebook.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        
        # TAB 1: SWAP RATES
        swap_tab = ttk.Frame(notebook, style='Card.TFrame')
        notebook.add(swap_tab, text='📊 Swap Rates')
        
        # Data table section with card styling
        table_card = ttk.Frame(swap_tab, style='Card.TFrame', relief='solid', borderwidth=1)
        table_card.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        table_frame = ttk.Frame(table_card, style='Card.TFrame')
        table_frame.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        
        # Create Treeview with enhanced styling
        columns = ('Date', 'Currency', 'Tenor', 'Rate', 'Updated')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', 
                                height=22, style='Treeview')
        
        # Define headings with better text
        self.tree.heading('Date', text='📅 Date')
        self.tree.heading('Currency', text='💱 Currency')
        self.tree.heading('Tenor', text='⏱ Tenor')
        self.tree.heading('Rate', text='📊 Rate (%)')
        self.tree.heading('Updated', text='🔄 Last Updated')
        
        # Define column widths (wider for better readability)
        self.tree.column('Date', width=130, anchor='center')
        self.tree.column('Currency', width=110, anchor='center')
        self.tree.column('Tenor', width=100, anchor='center')
        self.tree.column('Rate', width=130, anchor='center')
        self.tree.column('Updated', width=200, anchor='center')
        
        # Add scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        hsb.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Add hover effects
        self.tree.tag_configure('hover', background=self.colors['table_hover'])
        self.current_hover_item = None
        
        def on_mouse_motion(event):
            """Handle mouse motion for hover effects"""
            item = self.tree.identify_row(event.y)
            if item != self.current_hover_item:
                # Remove hover from previous item
                if self.current_hover_item:
                    # Restore original tag
                    tags = list(self.tree.item(self.current_hover_item, 'tags'))
                    if 'hover' in tags:
                        tags.remove('hover')
                    self.tree.item(self.current_hover_item, tags=tags)
                
                # Add hover to new item
                if item:
                    tags = list(self.tree.item(item, 'tags'))
                    if 'hover' not in tags:
                        tags.append('hover')
                    self.tree.item(item, tags=tags)
                
                self.current_hover_item = item
        
        def on_mouse_leave(event):
            """Handle mouse leaving the tree"""
            if self.current_hover_item:
                tags = list(self.tree.item(self.current_hover_item, 'tags'))
                if 'hover' in tags:
                    tags.remove('hover')
                self.tree.item(self.current_hover_item, tags=tags)
                self.current_hover_item = None
        
        self.tree.bind('<Motion>', on_mouse_motion)
        self.tree.bind('<Leave>', on_mouse_leave)
        
        # TAB 2: CENTRAL BANK & BENCHMARK RATES
        benchmark_tab = ttk.Frame(notebook, style='Card.TFrame')
        notebook.add(benchmark_tab, text='🏦 Central Bank & Benchmark Rates')
        
        # Benchmark filters
        bm_filter_card = ttk.Frame(benchmark_tab, style='Card.TFrame', relief='solid', borderwidth=1)
        bm_filter_card.pack(fill=tk.X, padx=5, pady=5)
        
        bm_filter_frame = ttk.LabelFrame(bm_filter_card, text="  Benchmark Rate Filters  ", padding="15", style='TLabelframe')
        bm_filter_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        ttk.Label(bm_filter_frame, text="Currency:", font=self.fonts['normal']).grid(row=0, column=0, padx=(0, 8), sticky=tk.W)
        self.benchmark_currency_var = tk.StringVar(value="All")
        bm_curr_combo = ttk.Combobox(bm_filter_frame, textvariable=self.benchmark_currency_var,
                                     values=["All", "AUD", "CAD", "NZD"], width=12, state='readonly', font=self.fonts['normal'])
        bm_curr_combo.grid(row=0, column=1, padx=(0, 20))
        bm_curr_combo.bind('<<ComboboxSelected>>', lambda e: (self.update_benchmark_rate_type_list(), self.refresh_current_benchmark_view()))
        
        ttk.Label(bm_filter_frame, text="Rate Type:", font=self.fonts['normal']).grid(row=0, column=2, padx=(0, 8), sticky=tk.W)
        self.benchmark_rate_type_var = tk.StringVar(value="All")
        self.benchmark_rate_type_combo = ttk.Combobox(bm_filter_frame, textvariable=self.benchmark_rate_type_var,
                                                      width=20, state='readonly', font=self.fonts['normal'])
        self.benchmark_rate_type_combo.grid(row=0, column=3, padx=(0, 20))
        
        ttk.Label(bm_filter_frame, text="From:", font=self.fonts['normal']).grid(row=0, column=4, padx=(0, 8), sticky=tk.W)
        self.benchmark_start_date_var = tk.StringVar()
        ttk.Entry(bm_filter_frame, textvariable=self.benchmark_start_date_var, width=13, font=self.fonts['normal']).grid(row=0, column=5, padx=(0, 15))
        
        ttk.Label(bm_filter_frame, text="To:", font=self.fonts['normal']).grid(row=0, column=6, padx=(0, 8), sticky=tk.W)
        self.benchmark_end_date_var = tk.StringVar()
        ttk.Entry(bm_filter_frame, textvariable=self.benchmark_end_date_var, width=13, font=self.fonts['normal']).grid(row=0, column=7, padx=(0, 20))
        
        ttk.Button(bm_filter_frame, text="Apply Filters", command=self.apply_benchmark_filters, style='Accent.TButton').grid(row=0, column=8, padx=(10, 5))
        ttk.Button(bm_filter_frame, text="Clear", command=self.clear_benchmark_filters, style='TButton').grid(row=0, column=9, padx=5)
        ttk.Button(bm_filter_frame, text="📥 Import Benchmark Data", command=self.import_benchmark_data, style='Accent.TButton').grid(row=0, column=10, padx=(20, 5))
        ttk.Button(bm_filter_frame, text="📊 Table View", command=self.toggle_benchmark_view, style='Accent.TButton').grid(row=0, column=11, padx=5)
        
        # Benchmark table
        bm_table_card = ttk.Frame(benchmark_tab, style='Card.TFrame', relief='solid', borderwidth=1)
        bm_table_card.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        bm_table_frame = ttk.Frame(bm_table_card, style='Card.TFrame')
        bm_table_frame.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
        bm_table_frame.columnconfigure(0, weight=1)
        bm_table_frame.rowconfigure(0, weight=1)
        
        bm_columns = ('Date', 'Currency', 'Rate Type', 'Rate')
        self.benchmark_tree = ttk.Treeview(bm_table_frame, columns=bm_columns, show='headings', height=22, style='Treeview')
        
        self.benchmark_tree.heading('Date', text='📅 Date')
        self.benchmark_tree.heading('Currency', text='💱 Currency')
        self.benchmark_tree.heading('Rate Type', text='📊 Rate Type')
        self.benchmark_tree.heading('Rate', text='📈 Rate (%)')
        
        self.benchmark_tree.column('Date', width=130, anchor='center')
        self.benchmark_tree.column('Currency', width=110, anchor='center')
        self.benchmark_tree.column('Rate Type', width=250, anchor='center')
        self.benchmark_tree.column('Rate', width=150, anchor='center')
        
        bm_vsb = ttk.Scrollbar(bm_table_frame, orient="vertical", command=self.benchmark_tree.yview)
        bm_hsb = ttk.Scrollbar(bm_table_frame, orient="horizontal", command=self.benchmark_tree.xview)
        self.benchmark_tree.configure(yscrollcommand=bm_vsb.set, xscrollcommand=bm_hsb.set)
        
        self.benchmark_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        bm_vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        bm_hsb.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        self.benchmark_tree.tag_configure('evenrow', background=self.colors['bg_card'], foreground=self.colors['text_dark'])
        self.benchmark_tree.tag_configure('oddrow', background=self.colors['table_alt'], foreground=self.colors['text_dark'])
        
        # TAB 3: OIS RATES
        ois_tab = ttk.Frame(notebook, style='Card.TFrame')
        notebook.add(ois_tab, text='📊 OIS Rates')
        
        # OIS filters (shared across all sub-tabs)
        ois_filter_card = ttk.Frame(ois_tab, style='Card.TFrame', relief='solid', borderwidth=1)
        ois_filter_card.pack(fill=tk.X, padx=5, pady=5)
        
        ois_filter_frame = ttk.LabelFrame(ois_filter_card, text="  OIS Rate Filters  ", padding="15", style='TLabelframe')
        ois_filter_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        ttk.Label(ois_filter_frame, text="Currency:", font=self.fonts['normal']).grid(row=0, column=0, padx=(0, 8), sticky=tk.W)
        self.ois_currency_var = tk.StringVar(value="All")
        ois_curr_combo = ttk.Combobox(ois_filter_frame, textvariable=self.ois_currency_var,
                                      values=["All", "AUD", "CAD", "EUR", "GBP", "JPY", "NZD", "USD"], width=12, state='readonly', font=self.fonts['normal'])
        ois_curr_combo.grid(row=0, column=1, padx=(0, 20))
        ois_curr_combo.bind('<<ComboboxSelected>>', lambda e: self.update_ois_rate_type_list())
        
        ttk.Label(ois_filter_frame, text="Rate Type:", font=self.fonts['normal']).grid(row=0, column=2, padx=(0, 8), sticky=tk.W)
        self.ois_rate_type_var = tk.StringVar(value="All")
        self.ois_rate_type_combo = ttk.Combobox(ois_filter_frame, textvariable=self.ois_rate_type_var,
                                                width=20, state='readonly', font=self.fonts['normal'])
        self.ois_rate_type_combo.grid(row=0, column=3, padx=(0, 20))
        
        ttk.Label(ois_filter_frame, text="From:", font=self.fonts['normal']).grid(row=0, column=4, padx=(0, 8), sticky=tk.W)
        self.ois_start_date_var = tk.StringVar()
        ttk.Entry(ois_filter_frame, textvariable=self.ois_start_date_var, width=13, font=self.fonts['normal']).grid(row=0, column=5, padx=(0, 15))
        
        ttk.Label(ois_filter_frame, text="To:", font=self.fonts['normal']).grid(row=0, column=6, padx=(0, 8), sticky=tk.W)
        self.ois_end_date_var = tk.StringVar()
        ttk.Entry(ois_filter_frame, textvariable=self.ois_end_date_var, width=13, font=self.fonts['normal']).grid(row=0, column=7, padx=(0, 20))
        
        ttk.Button(ois_filter_frame, text="Apply Filters", command=self.apply_ois_filters, style='Accent.TButton').grid(row=0, column=8, padx=(10, 5))
        ttk.Button(ois_filter_frame, text="Clear", command=self.clear_ois_filters, style='TButton').grid(row=0, column=9, padx=5)
        ttk.Button(ois_filter_frame, text="📥 Import OIS Data", command=self.import_ois_data, style='Accent.TButton').grid(row=0, column=10, padx=(20, 0))
        
        # Create notebook for OIS sub-tabs
        ois_notebook = ttk.Notebook(ois_tab, style='TNotebook')
        ois_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # SUB-TAB 1: SHORT TERM OIS (0-2Y)
        ois_short_tab = ttk.Frame(ois_notebook, style='Card.TFrame')
        ois_notebook.add(ois_short_tab, text='Short Term (0-2Y)')
        
        # Short term controls
        ois_short_controls = ttk.Frame(ois_short_tab, style='Card.TFrame')
        ois_short_controls.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(ois_short_controls, text="📊 Table View", command=self.toggle_ois_short_view, style='Accent.TButton').pack(side=tk.RIGHT, padx=5)
        
        # Short term table
        ois_short_card = ttk.Frame(ois_short_tab, style='Card.TFrame', relief='solid', borderwidth=1)
        ois_short_card.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ois_short_frame = ttk.Frame(ois_short_card, style='Card.TFrame')
        ois_short_frame.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
        ois_short_frame.columnconfigure(0, weight=1)
        ois_short_frame.rowconfigure(0, weight=1)
        
        ois_columns = ('Date', 'Currency', 'Rate Type', 'Rate')
        self.ois_tree_short = ttk.Treeview(ois_short_frame, columns=ois_columns, show='headings', height=22, style='Treeview')
        
        self.ois_tree_short.heading('Date', text='📅 Date')
        self.ois_tree_short.heading('Currency', text='💱 Currency')
        self.ois_tree_short.heading('Rate Type', text='📊 Rate Type')
        self.ois_tree_short.heading('Rate', text='📈 Rate (%)')
        
        self.ois_tree_short.column('Date', width=130, anchor='center')
        self.ois_tree_short.column('Currency', width=110, anchor='center')
        self.ois_tree_short.column('Rate Type', width=250, anchor='center')
        self.ois_tree_short.column('Rate', width=150, anchor='center')
        
        ois_short_vsb = ttk.Scrollbar(ois_short_frame, orient="vertical", command=self.ois_tree_short.yview)
        ois_short_hsb = ttk.Scrollbar(ois_short_frame, orient="horizontal", command=self.ois_tree_short.xview)
        self.ois_tree_short.configure(yscrollcommand=ois_short_vsb.set, xscrollcommand=ois_short_hsb.set)
        
        self.ois_tree_short.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        ois_short_vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        ois_short_hsb.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        self.ois_tree_short.tag_configure('evenrow', background=self.colors['bg_card'], foreground=self.colors['text_dark'])
        self.ois_tree_short.tag_configure('oddrow', background=self.colors['table_alt'], foreground=self.colors['text_dark'])
        
        # SUB-TAB 2: MEDIUM TERM OIS (3Y+)
        ois_medium_tab = ttk.Frame(ois_notebook, style='Card.TFrame')
        ois_notebook.add(ois_medium_tab, text='Medium Term (3Y+)')
        
        # Medium term controls
        ois_medium_controls = ttk.Frame(ois_medium_tab, style='Card.TFrame')
        ois_medium_controls.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(ois_medium_controls, text="📊 Table View", command=self.toggle_ois_medium_view, style='Accent.TButton').pack(side=tk.RIGHT, padx=5)
        
        # Medium term table
        ois_medium_card = ttk.Frame(ois_medium_tab, style='Card.TFrame', relief='solid', borderwidth=1)
        ois_medium_card.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ois_medium_frame = ttk.Frame(ois_medium_card, style='Card.TFrame')
        ois_medium_frame.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
        ois_medium_frame.columnconfigure(0, weight=1)
        ois_medium_frame.rowconfigure(0, weight=1)
        
        self.ois_tree_medium = ttk.Treeview(ois_medium_frame, columns=ois_columns, show='headings', height=22, style='Treeview')
        
        self.ois_tree_medium.heading('Date', text='📅 Date')
        self.ois_tree_medium.heading('Currency', text='💱 Currency')
        self.ois_tree_medium.heading('Rate Type', text='📊 Rate Type')
        self.ois_tree_medium.heading('Rate', text='📈 Rate (%)')
        
        self.ois_tree_medium.column('Date', width=130, anchor='center')
        self.ois_tree_medium.column('Currency', width=110, anchor='center')
        self.ois_tree_medium.column('Rate Type', width=250, anchor='center')
        self.ois_tree_medium.column('Rate', width=150, anchor='center')
        
        ois_medium_vsb = ttk.Scrollbar(ois_medium_frame, orient="vertical", command=self.ois_tree_medium.yview)
        ois_medium_hsb = ttk.Scrollbar(ois_medium_frame, orient="horizontal", command=self.ois_tree_medium.xview)
        self.ois_tree_medium.configure(yscrollcommand=ois_medium_vsb.set, xscrollcommand=ois_medium_hsb.set)
        
        self.ois_tree_medium.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        ois_medium_vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        ois_medium_hsb.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        self.ois_tree_medium.tag_configure('evenrow', background=self.colors['bg_card'], foreground=self.colors['text_dark'])
        self.ois_tree_medium.tag_configure('oddrow', background=self.colors['table_alt'], foreground=self.colors['text_dark'])
        
        # SUB-TAB 3: CENTRAL BANK MEETING OIS
        ois_cb_tab = ttk.Frame(ois_notebook, style='Card.TFrame')
        ois_notebook.add(ois_cb_tab, text='Central Bank Meeting OIS')
        
        cb_label = ttk.Label(ois_cb_tab, text="Central Bank Meeting OIS\n\nComing Soon", 
                            font=self.fonts['heading'], foreground=self.colors['text_light'])
        cb_label.pack(expand=True, pady=100)
        
        # Keep old ois_tree for backward compatibility
        self.ois_tree = self.ois_tree_short
        
        # TAB 4: SWAPTION VOL HISTORY
        swaption_tab = ttk.Frame(notebook, style='Card.TFrame')
        notebook.add(swaption_tab, text='📈 Swaption Vol History')
        
        swaption_label = ttk.Label(swaption_tab, text="Swaption Volatility History\n\nComing Soon - Upload your swaption vol data", 
                                   font=self.fonts['heading'], foreground=self.colors['text_light'])
        swaption_label.pack(expand=True, pady=100)
        
        # TAB 5: CAP AND FLOOR HISTORY
        capfloor_tab = ttk.Frame(notebook, style='Card.TFrame')
        notebook.add(capfloor_tab, text='📊 Cap & Floor History')
        
        capfloor_label = ttk.Label(capfloor_tab, text="Cap and Floor Volatility History\n\nComing Soon - Upload your cap/floor data", 
                                   font=self.fonts['heading'], foreground=self.colors['text_light'])
        capfloor_label.pack(expand=True, pady=100)
        
        # Status bar with modern design
        status_card = ttk.Frame(main_container, style='Card.TFrame', relief='solid', borderwidth=1)
        status_card.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        status_frame = ttk.Frame(status_card, style='Card.TFrame')
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Main status message
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(status_frame, textvariable=self.status_var,
                                font=self.fonts['normal'],
                                foreground=self.colors['text_dark'])
        status_label.pack(side=tk.LEFT, padx=10)
        
        # Separator
        ttk.Separator(status_frame, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Data count indicator
        self.data_count_var = tk.StringVar(value="0 records")
        data_count_label = ttk.Label(status_frame, textvariable=self.data_count_var,
                                     font=self.fonts['normal'],
                                     foreground=self.colors['accent'])
        data_count_label.pack(side=tk.LEFT, padx=10)
        
        # Separator
        ttk.Separator(status_frame, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Alert indicator
        self.alert_indicator = ttk.Label(status_frame, text="● Alerts: 0 active",
                                        foreground=self.colors['success'],
                                        font=self.fonts['normal'])
        self.alert_indicator.pack(side=tk.LEFT, padx=10)
        
        # Separator
        ttk.Separator(status_frame, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Last update time
        self.last_update_var = tk.StringVar(value="Not yet updated")
        update_label = ttk.Label(status_frame, textvariable=self.last_update_var,
                                font=self.fonts['small'],
                                foreground=self.colors['text_light'])
        update_label.pack(side=tk.LEFT, padx=10)
        
        # Quick action buttons with modern styling
        button_card = ttk.Frame(main_container, style='Card.TFrame', relief='solid', borderwidth=1)
        button_card.grid(row=4, column=0, pady=(0, 0))
        
        button_frame = ttk.Frame(button_card, style='Card.TFrame')
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Import/Export section
        io_frame = ttk.Frame(button_frame, style='Card.TFrame')
        io_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(io_frame, text="Data:", font=self.fonts['heading']).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(io_frame, text="📥 Import Swaps", 
                  command=self.import_swaps_dialog, style='Accent.TButton').pack(side=tk.LEFT, padx=3)
        ttk.Button(io_frame, text="📤 Export Excel", 
                  command=self.export_to_excel, style='TButton').pack(side=tk.LEFT, padx=3)
        ttk.Button(io_frame, text="➕ Add Rate", 
                  command=self.add_rate_dialog, style='Success.TButton').pack(side=tk.LEFT, padx=3)
        
        # Separator
        ttk.Separator(button_frame, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=15)
        
        # Charts section
        charts_frame = ttk.Frame(button_frame, style='Card.TFrame')
        charts_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(charts_frame, text="Quick Charts:", font=self.fonts['heading']).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(charts_frame, text="📊 Compare Tenors", 
                  command=self.show_tenor_comparison_chart, style='TButton').pack(side=tk.LEFT, padx=3)
        ttk.Button(charts_frame, text="📈 Yield Curve", 
                  command=self.show_yield_curve, style='TButton').pack(side=tk.LEFT, padx=3)
        
        # Separator
        ttk.Separator(button_frame, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=15)
        
        # Analytics section
        analytics_frame = ttk.Frame(button_frame, style='Card.TFrame')
        analytics_frame.pack(side=tk.LEFT)
        
        ttk.Label(analytics_frame, text="Quick Analytics:", font=self.fonts['heading']).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(analytics_frame, text="📋 Statistics", 
                  command=self.show_statistics_dialog, style='TButton').pack(side=tk.LEFT, padx=3)
        ttk.Button(analytics_frame, text="📄 PDF Report", 
                  command=self.generate_pdf_report, style='TButton').pack(side=tk.LEFT, padx=3)
    
    def update_tenor_list(self):
        """Update the tenor dropdown with available tenors"""
        tenors = self.db_manager.get_available_tenors()
        self.tenor_combo['values'] = ["All"] + tenors
    
    def update_floating_rate_list(self, currency=None):
        """Update the floating rate dropdown based on selected currency"""
        if currency and currency != "All":
            floating_rates = self.db_manager.get_available_floating_rates(currency)
            self.floating_rate_combo['values'] = ["All"] + floating_rates
        else:
            # Get all floating rates if no currency selected
            floating_rates = self.db_manager.get_available_floating_rates()
            self.floating_rate_combo['values'] = ["All"] + floating_rates
    
    def refresh_data(self, filters=None):
        """Refresh the data table"""
        # Check view mode
        if self.view_mode == 'pivot':
            self.refresh_pivot_view(filters)
        else:
            self.refresh_standard_view(filters)
    
    def refresh_standard_view(self, filters=None):
        """Refresh standard view (original table format)"""
        # Clear existing data
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Ensure standard columns
        columns = ('Date', 'Currency', 'Tenor', 'Rate', 'Updated')
        if self.tree['columns'] != columns:
            self.tree.configure(columns=columns)
            self.tree.column('#0', width=0, stretch=tk.NO)
            
            # Reset headings
            self.tree.heading('Date', text='📅 Date')
            self.tree.heading('Currency', text='💱 Currency')
            self.tree.heading('Tenor', text='⏱ Tenor')
            self.tree.heading('Rate', text='📊 Rate (%)')
            self.tree.heading('Updated', text='🔄 Last Updated')
            
            # Reset column widths
            self.tree.column('Date', width=130, anchor='center')
            self.tree.column('Currency', width=110, anchor='center')
            self.tree.column('Tenor', width=100, anchor='center')
            self.tree.column('Rate', width=130, anchor='center')
            self.tree.column('Updated', width=200, anchor='center')
        
        # Get data from database
        if filters:
            rates = self.db_manager.get_rates(**filters)
        else:
            rates = self.db_manager.get_rates()
        
        # Populate table with alternating colors
        # Display rates as percentage (rate * 100)
        for i, rate in enumerate(rates):
            tags = ('evenrow',) if i % 2 == 0 else ('oddrow',)
            self.tree.insert('', tk.END, values=(
                rate.date.strftime('%Y-%m-%d'),
                rate.currency,
                rate.tenor,
                f"{rate.rate * 100:.4f}",
                rate.updated_at.strftime('%Y-%m-%d %H:%M:%S') if rate.updated_at else ''
            ), tags=tags)
        
        # Configure row colors for alternating rows
        self.tree.tag_configure('oddrow', background=self.colors['bg_card'], foreground=self.colors['text_dark'])
        self.tree.tag_configure('evenrow', background=self.colors['table_alt'], foreground=self.colors['text_dark'])
        
        # Update status indicators
        self.status_var.set(f"Showing {len(rates)} records")
        self.data_count_var.set(f"{len(rates)} records")
        self.last_update_var.set(f"Updated: {datetime.now().strftime('%H:%M:%S')}")
        self.update_tenor_list()
        
        # Update dashboard metrics
        self.update_dashboard()
    
    def refresh_pivot_view(self, filters=None):
        """Refresh pivot view (tenors as columns) - SIMPLIFIED VERSION"""
        # Clear existing data
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Define tenor columns - ALL consecutive tenors including 3M
        tenor_columns = ['3M', '6M', '9M', '1Y', '2Y', '3Y', '4Y', '5Y', '6Y', '7Y', '8Y', '9Y', 
                        '10Y', '12Y', '15Y', '20Y', '30Y']
        columns = ['Date', 'Currency'] + tenor_columns
        
        # Reconfigure tree for pivot view
        self.tree.configure(columns=columns)
        self.tree.column('#0', width=0, stretch=tk.NO)
        
        # Set headings
        self.tree.heading('Date', text='📅 Date')
        self.tree.heading('Currency', text='💱 Curr')
        for tenor in tenor_columns:
            self.tree.heading(tenor, text=tenor)
        
        # Set column widths
        self.tree.column('Date', width=100, anchor='center')
        self.tree.column('Currency', width=60, anchor='center')
        for tenor in tenor_columns:
            self.tree.column(tenor, width=70, anchor='center')
        
        # SIMPLIFIED: Direct SQL query like the working standalone version
        import sqlite3
        import os
        
        try:
            # Get database path
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'swap_rates.db')
            
            # Connect directly
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Simple query - get ALL data (or filtered)
            sql = "SELECT date, currency, tenor, rate, floating_rate FROM swap_rates"
            params = []
            
            where_clauses = []
            if filters:
                if 'currency' in filters:
                    where_clauses.append("currency = ?")
                    params.append(filters['currency'])
                if 'floating_rate' in filters:
                    where_clauses.append("floating_rate = ?")
                    params.append(filters['floating_rate'])
                if 'start_date' in filters:
                    where_clauses.append("date >= ?")
                    params.append(filters['start_date'].strftime('%Y-%m-%d'))
                if 'end_date' in filters:
                    where_clauses.append("date <= ?")
                    params.append(filters['end_date'].strftime('%Y-%m-%d'))
            
            if where_clauses:
                sql += " WHERE " + " AND ".join(where_clauses)
            
            sql += " ORDER BY date DESC, currency, tenor"
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            # ALSO FETCH BENCHMARK RATES (RBA, RBNZ cash rates)
            # These are the actual central bank benchmark rates
            benchmark_sql = """
                SELECT date, currency, tenor, rate FROM swap_rates 
                WHERE floating_rate IN ('RBA', 'RBNZ')
                AND tenor IN ('1M','2M','3M','4M','5M','6M','1D','ON')
            """
            
            benchmark_params = []
            benchmark_where = []
            
            if filters:
                if 'currency' in filters:
                    benchmark_where.append("currency = ?")
                    benchmark_params.append(filters['currency'])
                if 'start_date' in filters:
                    benchmark_where.append("date >= ?")
                    benchmark_params.append(filters['start_date'].strftime('%Y-%m-%d'))
                if 'end_date' in filters:
                    benchmark_where.append("date <= ?")
                    benchmark_params.append(filters['end_date'].strftime('%Y-%m-%d'))
            
            if benchmark_where:
                # Modify the WHERE clause to include both original condition and filters
                benchmark_sql = benchmark_sql.replace(
                    "WHERE", 
                    "WHERE (" 
                ) + ") AND " + " AND ".join(benchmark_where)
            
            benchmark_sql += " ORDER BY date DESC, currency"
            
            cursor.execute(benchmark_sql, benchmark_params)
            benchmark_rows = cursor.fetchall()
            
            if not rows and not benchmark_rows:
                self.status_var.set("No data found")
                messagebox.showwarning("No Data", "No data matches your filters.")
                conn.close()
                return
            
            # Organize by date and currency
            data_dict = {}
            
            # Helper function to normalize dates (strip time if present)
            def normalize_date(date_str):
                """Convert date string to YYYY-MM-DD format (no time)"""
                if isinstance(date_str, str):
                    # If it has a timestamp, take only the date part
                    return date_str.split(' ')[0]
                return str(date_str)
            
            # First, add swap rates
            for date, currency, tenor, rate, floating_rate in rows:
                date_norm = normalize_date(date)
                key = (date_norm, currency)
                if key not in data_dict:
                    data_dict[key] = {}
                data_dict[key][tenor] = rate
            
            # Second, add benchmark rates (RBA, RBNZ)
            for date, currency, tenor, rate in benchmark_rows:
                date_norm = normalize_date(date)
                key = (date_norm, currency)
                if key not in data_dict:
                    data_dict[key] = {}
                # Add with the actual tenor
                data_dict[key][tenor] = rate
            
            # Sort by date (most recent first)
            sorted_keys = sorted(data_dict.keys(), reverse=True)
            
            # Insert into tree
            for i, (date, currency) in enumerate(sorted_keys):
                values = [date, currency]
                
                # Add tenor values - display as percentage (rate * 100)
                for tenor in tenor_columns:
                    if tenor in data_dict[(date, currency)]:
                        values.append(f"{data_dict[(date, currency)][tenor] * 100:.4f}")
                    else:
                        values.append("")
                
                # Alternate row colors
                tags = ('evenrow',) if i % 2 == 0 else ('oddrow',)
                self.tree.insert('', tk.END, values=values, tags=tags)
            
            # Configure row colors
            self.tree.tag_configure('oddrow', background=self.colors['bg_card'], foreground=self.colors['text_dark'])
            self.tree.tag_configure('evenrow', background=self.colors['table_alt'], foreground=self.colors['text_dark'])
            
            # Update status
            total_rates = len(rows) + len(benchmark_rows)
            self.status_var.set(f"Showing {len(sorted_keys)} dates ({total_rates} rates)")
            self.data_count_var.set(f"{total_rates} rates")
            self.last_update_var.set(f"Updated: {datetime.now().strftime('%H:%M:%S')}")
            
            conn.close()
            
        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            messagebox.showerror("Table View Error", 
                               f"Error:\n\n{str(e)}\n\nDetails:\n{error_msg}")
            print(error_msg)
    
    def apply_filters(self):
        """Apply filters to the data view"""
        filters = {}
        
        # Currency filter
        if self.currency_var.get() != "All":
            filters['currency'] = self.currency_var.get()
        
        # Tenor filter
        if self.tenor_var.get() != "All":
            filters['tenor'] = self.tenor_var.get()
        
        # Floating rate filter
        if self.floating_rate_var.get() != "All":
            filters['floating_rate'] = self.floating_rate_var.get()
        
        # Date filters
        if self.start_date_var.get():
            try:
                filters['start_date'] = datetime.strptime(
                    self.start_date_var.get(), '%Y-%m-%d'
                ).date()
            except ValueError:
                messagebox.showerror("Error", "Invalid start date format. Use YYYY-MM-DD\n\nExample: 2024-01-15")
                return
        
        if self.end_date_var.get():
            try:
                filters['end_date'] = datetime.strptime(
                    self.end_date_var.get(), '%Y-%m-%d'
                ).date()
            except ValueError:
                messagebox.showerror("Error", "Invalid end date format. Use YYYY-MM-DD\n\nExample: 2025-10-20")
                return
        
        # Check if date range makes sense
        if 'start_date' in filters and 'end_date' in filters:
            if filters['start_date'] > filters['end_date']:
                messagebox.showerror("Error", "Start date must be before end date")
                return
        
        # Apply filters and check results
        self.refresh_data(filters)
        
        # Get count from status bar
        status_text = self.status_var.get()
        if "Showing 0 records" in status_text:
            # Show helpful message
            dates = self.db_manager.get_available_dates(filters.get('currency'))
            if dates:
                msg = f"No data found for the selected filters.\n\n"
                msg += f"Available date range:\n"
                msg += f"From: {dates[-1]}\n"
                msg += f"To: {dates[0]}\n\n"
                msg += "Try:\n"
                msg += "1. Use 'Quick' buttons for common date ranges\n"
                msg += "2. Click 'Clear' to reset all filters\n"
                msg += "3. Check your date format (YYYY-MM-DD)"
                messagebox.showwarning("No Results", msg)
            else:
                messagebox.showwarning("No Data", "No data available in database.\n\nImport Excel data first.")
    
    def clear_filters(self):
        """Clear all filters"""
        self.currency_var.set("All")
        self.tenor_var.set("All")
        self.floating_rate_var.set("All")
        self.start_date_var.set("")
        self.end_date_var.set("")
        self.refresh_data()
    
    def set_date_range(self, days):
        """Set date range to last N days"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        self.start_date_var.set(start_date.strftime('%Y-%m-%d'))
        self.end_date_var.set(end_date.strftime('%Y-%m-%d'))
        
        # Auto-apply filters
        self.apply_filters()
    
    def set_all_time_range(self):
        """Set date range to show all data"""
        # Get earliest and latest dates from database
        dates = self.db_manager.get_available_dates()
        if dates:
            self.start_date_var.set(dates[-1].strftime('%Y-%m-%d'))  # Oldest
            self.end_date_var.set(dates[0].strftime('%Y-%m-%d'))  # Newest
            self.apply_filters()
        else:
            messagebox.showinfo("No Data", "No data available in database")
    
    def import_excel(self):
        """Import data from Excel file"""
        file_path = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        # Import dialog
        import_dialog = tk.Toplevel(self.root)
        import_dialog.title("Import Options")
        import_dialog.geometry("400x200")
        
        ttk.Label(import_dialog, text="Select import format:").pack(pady=10)
        
        format_var = tk.StringVar(value="long")
        ttk.Radiobutton(import_dialog, text="Long Format (Date, Currency, Tenor, Rate)", 
                       variable=format_var, value="long").pack(anchor=tk.W, padx=20)
        ttk.Radiobutton(import_dialog, text="Wide Format (Date, then tenor columns)", 
                       variable=format_var, value="wide").pack(anchor=tk.W, padx=20)
        
        ttk.Label(import_dialog, text="Currency (for wide format):").pack(pady=5)
        currency_var = tk.StringVar(value="AUD")
        ttk.Combobox(import_dialog, textvariable=currency_var, 
                    values=["AUD", "NZD", "USD", "EUR", "GBP", "JPY"], state='readonly').pack()
        
        def do_import():
            import_dialog.destroy()
            self.status_var.set("Importing data...")
            self.root.update()
            
            try:
                result = self.excel_importer.import_from_excel(file_path)
                
                if result['success']:
                    messagebox.showinfo(
                        "Import Successful",
                        f"Imported {result['records_imported']} records\n"
                        f"Errors: {result.get('total_errors', 0)}"
                    )
                    self.refresh_data()
                else:
                    # Build error message
                    error_msg = result.get('error', '')
                    if not error_msg and result.get('errors'):
                        # Show first few errors
                        error_msg = f"Failed to import. {result.get('total_errors', 0)} errors:\n\n"
                        for err in result['errors'][:5]:
                            error_msg += f"• {err}\n"
                        if result.get('total_errors', 0) > 5:
                            error_msg += f"\n... and {result['total_errors'] - 5} more errors"
                    elif not error_msg:
                        error_msg = "Unknown error - No records imported"
                    
                    messagebox.showerror("Import Failed", error_msg)
            except Exception as e:
                messagebox.showerror("Import Error", f"{type(e).__name__}: {str(e)}\n\nTry the debug_import.py script for details")
            
            self.status_var.set("Ready")
        
        ttk.Button(import_dialog, text="Import", command=do_import).pack(pady=20)
    
    def import_market_data(self):
        """Import OIS and Benchmark data files (AONIA, BBSW, BKBM, RBA, RBNZ)"""
        if not self.market_data_importer:
            messagebox.showerror("Error", "Market data importer not available.\n\nMake sure market_data_importer.py is in the backend folder.")
            return
        
        # Select files
        file_paths = filedialog.askopenfilenames(
            title="Select Market Data Excel Files",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        
        if not file_paths:
            return
        
        # Import dialog
        import_dialog = tk.Toplevel(self.root)
        import_dialog.title("Importing Market Data")
        import_dialog.geometry("600x400")
        
        # Progress text
        progress_text = tk.Text(import_dialog, height=20, width=70)
        progress_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(import_dialog, command=progress_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        progress_text.config(yscrollcommand=scrollbar.set)
        
        def do_import():
            progress_text.insert(tk.END, f"Importing {len(file_paths)} files...\n\n")
            progress_text.see(tk.END)
            import_dialog.update()
            
            # Import each file
            total_imported = 0
            total_duplicates = 0
            errors = []
            
            for i, file_path in enumerate(file_paths, 1):
                filename = os.path.basename(file_path)
                progress_text.insert(tk.END, f"[{i}/{len(file_paths)}] {filename}\n")
                progress_text.see(tk.END)
                import_dialog.update()
                
                result = self.market_data_importer.import_file(file_path)
                
                if result['success']:
                    progress_text.insert(tk.END, 
                        f"  ✓ {result['records_imported']} new, {result['duplicates']} existing\n\n")
                    total_imported += result['records_imported']
                    total_duplicates += result['duplicates']
                else:
                    progress_text.insert(tk.END, f"  ✗ Error: {result['error']}\n\n")
                    errors.append(f"{filename}: {result['error']}")
                
                progress_text.see(tk.END)
                import_dialog.update()
            
            # Summary
            progress_text.insert(tk.END, "="*60 + "\n")
            progress_text.insert(tk.END, "IMPORT COMPLETE\n")
            progress_text.insert(tk.END, "="*60 + "\n")
            progress_text.insert(tk.END, f"Total records imported: {total_imported:,}\n")
            progress_text.insert(tk.END, f"Duplicates skipped: {total_duplicates:,}\n")
            
            if errors:
                progress_text.insert(tk.END, f"Errors: {len(errors)}\n\n")
                for error in errors:
                    progress_text.insert(tk.END, f"  • {error}\n")
            else:
                progress_text.insert(tk.END, "No errors!\n")
            
            progress_text.see(tk.END)
            
            # Refresh data
            if total_imported > 0:
                self.refresh_data()
            
            self.status_var.set(f"Imported {total_imported:,} records from {len(file_paths)} files")
        
        # Start import button
        ttk.Button(import_dialog, text="Start Import", command=do_import, 
                  style='Accent.TButton').pack(pady=10)
    
    def import_swaps_dialog(self):
        """Import swap data with currency and floating rate selection"""
        if not self.market_data_importer:
            messagebox.showerror("Error", "Market data importer not available.\n\nMake sure market_data_importer.py is in the backend folder.")
            return
        
        # Create dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Import Swap Data")
        dialog.geometry("500x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Title
        ttk.Label(dialog, text="Import Swap Data", font=('Segoe UI', 14, 'bold')).pack(pady=15)
        
        # Options frame
        options_frame = ttk.LabelFrame(dialog, text="Filter by Data Type", padding=20)
        options_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Currency selection
        ttk.Label(options_frame, text="Currency:", font=('Segoe UI', 10)).grid(row=0, column=0, sticky=tk.W, pady=10)
        currency_var = tk.StringVar(value="All")
        currency_combo = ttk.Combobox(options_frame, textvariable=currency_var, 
                                      values=["All", "AUD", "NZD", "USD", "EUR", "GBP", "JPY", "CAD"],
                                      state='readonly', width=15)
        currency_combo.grid(row=0, column=1, padx=10, pady=10, sticky=tk.W)
        
        # Floating rate selection
        ttk.Label(options_frame, text="Floating Rate:", font=('Segoe UI', 10)).grid(row=1, column=0, sticky=tk.W, pady=10)
        floating_var = tk.StringVar(value="All")
        floating_combo = ttk.Combobox(options_frame, textvariable=floating_var,
                                      values=["All", "AONIA", "BBSW", "BKBM", "RBA", "RBNZ", "SOFR", "SONIA", "ESTR", "CORRA", "OCR"],
                                      state='readonly', width=15)
        floating_combo.grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)
        
        # Info text
        info_text = ttk.Label(options_frame, 
                             text="Select 'All' to import any swap data files.\nOr choose specific currency/rate type to filter files.",
                             font=('Segoe UI', 9), foreground='gray')
        info_text.grid(row=2, column=0, columnspan=2, pady=15)
        
        # Button frame
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        def select_and_import():
            dialog.destroy()
            
            # Build filter hint for dialog title
            filter_parts = []
            if currency_var.get() != "All":
                filter_parts.append(currency_var.get())
            if floating_var.get() != "All":
                filter_parts.append(floating_var.get())
            
            if filter_parts:
                title = f"Select {' '.join(filter_parts)} Swap Data Files"
            else:
                title = "Select Swap Data Files"
            
            # Select files
            file_paths = filedialog.askopenfilenames(
                title=title,
                filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
            )
            
            if not file_paths:
                return
            
            # Import files
            self._run_import_dialog(file_paths, "Swap Data")
        
        ttk.Button(button_frame, text="Select Files & Import", command=select_and_import,
                  style='Accent.TButton').pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy,
                  style='TButton').pack(side=tk.RIGHT)
    
    def import_ois_data(self):
        """Import OIS data files (AONIA, SOFR, SONIA, etc.)"""
        if not self.market_data_importer:
            messagebox.showerror("Error", "Market data importer not available.\n\nMake sure market_data_importer.py is in the backend folder.")
            return
        
        # Select files
        file_paths = filedialog.askopenfilenames(
            title="Select OIS Data Excel Files (AONIA, SOFR, SONIA, ESTR, etc.)",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        
        if not file_paths:
            return
        
        self._run_import_dialog(file_paths, "OIS Data")
    
    def import_benchmark_data(self):
        """Import Benchmark data files (BBSW, BKBM, RBA, RBNZ)"""
        if not self.market_data_importer:
            messagebox.showerror("Error", "Market data importer not available.\n\nMake sure market_data_importer.py is in the backend folder.")
            return
        
        # Select files
        file_paths = filedialog.askopenfilenames(
            title="Select Benchmark Data Excel Files (BBSW, BKBM, RBA, RBNZ, etc.)",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        
        if not file_paths:
            return
        
        self._run_import_dialog(file_paths, "Benchmark Data")
    
    def _run_import_dialog(self, file_paths, data_type_label):
        """Common import dialog for OIS and Benchmark data"""
        # Import dialog
        import_dialog = tk.Toplevel(self.root)
        import_dialog.title(f"Importing {data_type_label}")
        import_dialog.geometry("700x450")
        
        # Title
        title_label = ttk.Label(import_dialog, text=f"Importing {data_type_label}", 
                               font=('Segoe UI', 14, 'bold'))
        title_label.pack(pady=10)
        
        # Progress text
        progress_frame = ttk.Frame(import_dialog)
        progress_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        progress_text = tk.Text(progress_frame, height=20, width=80, font=('Consolas', 9))
        progress_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(progress_frame, command=progress_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        progress_text.config(yscrollcommand=scrollbar.set)
        
        # Close button (initially disabled)
        close_button = ttk.Button(import_dialog, text="Close", command=import_dialog.destroy, 
                                  style='TButton', state='disabled')
        close_button.pack(pady=10)
        
        def do_import():
            progress_text.insert(tk.END, f"Selected {len(file_paths)} file(s) for import\n")
            progress_text.insert(tk.END, "="*70 + "\n\n")
            progress_text.see(tk.END)
            import_dialog.update()
            
            # Import each file
            total_imported = 0
            total_duplicates = 0
            errors = []
            
            for i, file_path in enumerate(file_paths, 1):
                filename = os.path.basename(file_path)
                progress_text.insert(tk.END, f"[{i}/{len(file_paths)}] {filename}\n")
                progress_text.see(tk.END)
                import_dialog.update()
                
                result = self.market_data_importer.import_file(file_path)
                
                if result['success']:
                    progress_text.insert(tk.END, 
                        f"  ✓ Imported {result['records_imported']} new records, {result['duplicates']} duplicates skipped\n\n")
                    total_imported += result['records_imported']
                    total_duplicates += result['duplicates']
                else:
                    progress_text.insert(tk.END, f"  ✗ Error: {result['error']}\n\n")
                    errors.append(f"{filename}: {result['error']}")
                
                progress_text.see(tk.END)
                import_dialog.update()
            
            # Summary
            progress_text.insert(tk.END, "\n" + "="*70 + "\n")
            progress_text.insert(tk.END, "IMPORT COMPLETE\n")
            progress_text.insert(tk.END, "="*70 + "\n\n")
            progress_text.insert(tk.END, f"Files processed:      {len(file_paths)}\n")
            progress_text.insert(tk.END, f"Records imported:     {total_imported:,}\n")
            progress_text.insert(tk.END, f"Duplicates skipped:   {total_duplicates:,}\n")
            progress_text.insert(tk.END, f"Errors:               {len(errors)}\n")
            
            if errors:
                progress_text.insert(tk.END, "\nERROR DETAILS:\n")
                for error in errors:
                    progress_text.insert(tk.END, f"  • {error}\n")
            else:
                progress_text.insert(tk.END, "\n✓ All files imported successfully!\n")
            
            progress_text.see(tk.END)
            
            # Enable close button
            close_button.config(state='normal')
            
            # Refresh data
            if total_imported > 0:
                self.refresh_data()
            
            self.status_var.set(f"Imported {total_imported:,} records from {len(file_paths)} files")
        
        # Start import automatically
        import_dialog.after(100, do_import)
    
    def export_to_excel(self):
        """Export current view to Excel"""
        file_path = filedialog.asksaveasfilename(
            title="Save Excel File",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            # Get current filters
            filters = {}
            if self.currency_var.get() != "All":
                filters['currency'] = self.currency_var.get()
            if self.tenor_var.get() != "All":
                filters['tenor'] = self.tenor_var.get()
            
            # Get data
            rates = self.db_manager.get_rates(**filters)
            
            # Convert to DataFrame
            data = [{
                'Date': rate.date,
                'Currency': rate.currency,
                'Tenor': rate.tenor,
                'Rate': rate.rate  # Convert to percentage
            } for rate in rates]
            
            df = pd.DataFrame(data)
            df.to_excel(file_path, index=False, engine='openpyxl')
            
            messagebox.showinfo("Export Successful", 
                              f"Exported {len(data)} records to {file_path}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))
    
    def add_rate_dialog(self):
        """Dialog for manually adding a rate"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Swap Rate")
        dialog.geometry("350x250")
        
        # Date
        ttk.Label(dialog, text="Date (YYYY-MM-DD):").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        date_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        ttk.Entry(dialog, textvariable=date_var, width=20).grid(row=0, column=1, padx=10, pady=10)
        
        # Currency
        ttk.Label(dialog, text="Currency:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        currency_var = tk.StringVar(value="AUD")
        ttk.Combobox(dialog, textvariable=currency_var, 
                    values=["AUD", "NZD"], width=18, state='readonly').grid(row=1, column=1, padx=10, pady=10)
        
        # Tenor
        ttk.Label(dialog, text="Tenor:").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        tenor_var = tk.StringVar(value="1Y")
        tenors = ["1Y", "2Y", "3Y", "4Y", "5Y", "7Y", "10Y", "15Y", "20Y", "30Y"]
        ttk.Combobox(dialog, textvariable=tenor_var, 
                    values=tenors, width=18).grid(row=2, column=1, padx=10, pady=10)
        
        # Rate
        ttk.Label(dialog, text="Rate (%):").grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)
        rate_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=rate_var, width=20).grid(row=3, column=1, padx=10, pady=10)
        
        def save_rate():
            try:
                date_obj = datetime.strptime(date_var.get(), '%Y-%m-%d').date()
                rate_val = float(rate_var.get()) / 100  # Convert percentage to decimal
                
                success = self.db_manager.add_rate(
                    date_obj, currency_var.get(), tenor_var.get(), rate_val
                )
                
                if success:
                    messagebox.showinfo("Success", "Rate added successfully")
                    dialog.destroy()
                    self.refresh_data()
                else:
                    messagebox.showerror("Error", "Failed to add rate")
            except ValueError as e:
                messagebox.showerror("Invalid Input", str(e))
        
        ttk.Button(dialog, text="Save", command=save_rate).grid(row=4, column=0, columnspan=2, pady=20)
    
    def delete_selected(self):
        """Delete selected rows"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select rows to delete")
            return
        
        if messagebox.askyesno("Confirm Delete", 
                              f"Delete {len(selected)} selected record(s)?"):
            # Note: This is simplified - you'd need to implement actual deletion
            messagebox.showinfo("Info", "Delete functionality to be implemented")
    
    def view_latest_rates(self):
        """Show latest rates for all tenors"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Latest Swap Rates")
        dialog.geometry("600x400")
        
        # Currency selection
        frame = ttk.Frame(dialog, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Select Currency:").pack(pady=5)
        currency_var = tk.StringVar(value="AUD")
        ttk.Combobox(frame, textvariable=currency_var, 
                    values=["AUD", "NZD"], state='readonly').pack(pady=5)
        
        # Table
        columns = ('Tenor', 'Rate', 'Date')
        tree = ttk.Treeview(frame, columns=columns, show='headings', height=15)
        tree.heading('Tenor', text='Tenor')
        tree.heading('Rate', text='Rate (%)')
        tree.heading('Date', text='Date')
        tree.pack(pady=10, fill=tk.BOTH, expand=True)
        
        def load_latest():
            for item in tree.get_children():
                tree.delete(item)
            
            rates = self.db_manager.get_latest_rates(currency_var.get())
            for rate in rates:
                tree.insert('', tk.END, values=(
                    rate.tenor,
                    f"{rate.rate * 100:.4f}",
                    rate.date.strftime('%Y-%m-%d')
                ))
        
        ttk.Button(frame, text="Load", command=load_latest).pack(pady=5)
        load_latest()  # Load initially
    
    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "About RateEdge",
            "RateEdge\n\n"
            "Professional Edition v8.0\n\n"
            "Comprehensive multi-currency interest rate swap analytics\n"
            "Import, analyze, and manage swap data across major currencies\n\n"
            "Features:\n"
            "• Swap rates, benchmark rates, and OIS rates\n"
            "• Advanced analytics and charting\n"
            "• Missing data detection and interpolation\n"
            "• Forward rate calculations\n\n"
            "© 2025 Rate Edge (Aust)"
        )
    
    def show_tenor_comparison_chart(self):
        """Show interactive chart comparing up to 3 tenors"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Compare Tenors - Historical Chart")
        dialog.geometry("1000x700")
        
        # Control frame
        control_frame = ttk.Frame(dialog, padding="10")
        control_frame.pack(fill=tk.X)
        
        # Currency selection
        ttk.Label(control_frame, text="Currency:").grid(row=0, column=0, padx=5, pady=5)
        currency_var = tk.StringVar(value="AUD")
        ttk.Combobox(control_frame, textvariable=currency_var, 
                    values=["AUD", "NZD"], state='readonly', width=10).grid(row=0, column=1, padx=5)
        
        # Get available tenors
        tenors = self.db_manager.get_available_tenors()
        
        # Tenor selections (up to 3)
        tenor_vars = []
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c']  # Blue, Orange, Green
        
        # Add empty option to allow blank selections
        tenor_options = [""] + tenors  # Empty string first for blank option
        
        # Default selections (pick spread across curve if available)
        default_tenors = []
        if len(tenors) >= 3:
            # Try to pick short, medium, long
            default_tenors = [tenors[0], tenors[len(tenors)//2], tenors[-1]]
        elif len(tenors) == 2:
            default_tenors = [tenors[0], tenors[1], ""]
        elif len(tenors) == 1:
            default_tenors = [tenors[0], "", ""]
        else:
            default_tenors = ["", "", ""]
        
        for i in range(3):
            ttk.Label(control_frame, text=f"Tenor {i+1}:").grid(row=0, column=2+i*2, padx=5, pady=5)
            var = tk.StringVar(value=default_tenors[i])
            combo = ttk.Combobox(control_frame, textvariable=var, 
                               values=tenor_options, width=10)
            combo.grid(row=0, column=3+i*2, padx=5)
            tenor_vars.append(var)
        
        # Date range
        ttk.Label(control_frame, text="From:").grid(row=1, column=0, padx=5, pady=5)
        start_date_var = tk.StringVar()
        ttk.Entry(control_frame, textvariable=start_date_var, width=12).grid(row=1, column=1, padx=5)
        
        ttk.Label(control_frame, text="To:").grid(row=1, column=2, padx=5, pady=5)
        end_date_var = tk.StringVar()
        ttk.Entry(control_frame, textvariable=end_date_var, width=12).grid(row=1, column=3, padx=5)
        
        # Chart frame
        chart_frame = ttk.Frame(dialog)
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create matplotlib figure
        fig = Figure(figsize=(10, 6), dpi=100)
        ax = fig.add_subplot(111)
        
        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill=tk.BOTH, expand=True)
        
        # Add toolbar
        toolbar = NavigationToolbar2Tk(canvas, chart_frame)
        toolbar.update()
        
        def plot_data():
            """Plot the selected tenors"""
            ax.clear()
            
            currency = currency_var.get()
            
            # Check if at least one tenor is selected
            selected_tenors = [tv.get() for tv in tenor_vars if tv.get().strip()]
            if not selected_tenors:
                ax.text(0.5, 0.5, 'Please select at least one tenor', 
                       ha='center', va='center', transform=ax.transAxes, fontsize=14, color='red')
                canvas.draw()
                return
            
            # Get date range
            start_date = None
            end_date = None
            if start_date_var.get():
                try:
                    start_date = datetime.strptime(start_date_var.get(), '%Y-%m-%d').date()
                except ValueError:
                    messagebox.showerror("Error", "Invalid start date. Use YYYY-MM-DD")
                    return
            
            if end_date_var.get():
                try:
                    end_date = datetime.strptime(end_date_var.get(), '%Y-%m-%d').date()
                except ValueError:
                    messagebox.showerror("Error", "Invalid end date. Use YYYY-MM-DD")
                    return
            
            # Plot each selected tenor
            plotted = 0
            for i, tenor_var in enumerate(tenor_vars):
                tenor = tenor_var.get().strip().upper()  # Normalize to uppercase
                if not tenor:
                    continue
                
                # Get data for this tenor
                rates = self.db_manager.get_rates(
                    currency=currency,
                    tenor=tenor,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if not rates:
                    continue
                
                # Extract dates and rates
                dates = [rate.date for rate in rates]
                values = [rate.rate for rate in rates]  # Convert to percentage
                
                # Plot
                ax.plot(dates, values, label=f"{tenor}", 
                       color=colors[i], linewidth=2, marker='o', markersize=3)
                plotted += 1
            
            if plotted == 0:
                # Show more helpful error message
                error_msg = 'No data to display\n\n'
                error_msg += f'Currency: {currency}\n'
                error_msg += f'Selected tenors: {", ".join(selected_tenors)}\n'
                if start_date:
                    error_msg += f'Date range: {start_date} to {end_date or "latest"}\n'
                error_msg += '\nCheck:\n'
                error_msg += '• Data is imported\n'
                error_msg += '• Tenor names match (case-insensitive)\n'
                error_msg += '• Date range includes data'
                
                ax.text(0.5, 0.5, error_msg, 
                       ha='center', va='center', transform=ax.transAxes, 
                       fontsize=10, family='monospace')
            else:
                ax.set_xlabel('Date', fontsize=12)
                ax.set_ylabel('Swap Rate (%)', fontsize=12)
                ax.set_title(f'{currency} Swap Rates Comparison', fontsize=14, fontweight='bold')
                ax.legend(loc='best', fontsize=10)
                ax.grid(True, alpha=0.3)
                
                # Format x-axis dates
                fig.autofmt_xdate()
            
            canvas.draw()
        
        # Plot button
        ttk.Button(control_frame, text="Plot", command=plot_data).grid(row=1, column=4, padx=10)
        
        # Auto-plot on open with default selections
        if tenors:
            dialog.after(100, plot_data)
    
    def show_yield_curve(self):
        """Show yield curve for a specific date"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Yield Curve")
        dialog.geometry("1000x700")
        
        # Control frame
        control_frame = ttk.Frame(dialog, padding="10")
        control_frame.pack(fill=tk.X)
        
        # Currency selection
        ttk.Label(control_frame, text="Currency:").grid(row=0, column=0, padx=5, pady=5)
        currency_var = tk.StringVar(value="AUD")
        ttk.Combobox(control_frame, textvariable=currency_var, 
                    values=["AUD", "NZD"], state='readonly', width=10).grid(row=0, column=1, padx=5)
        
        # Date selection
        ttk.Label(control_frame, text="Date:").grid(row=0, column=2, padx=5, pady=5)
        date_var = tk.StringVar()
        date_entry = ttk.Entry(control_frame, textvariable=date_var, width=12)
        date_entry.grid(row=0, column=3, padx=5)
        
        ttk.Label(control_frame, text="(or leave blank for latest)", 
                 font=('Arial', 9, 'italic')).grid(row=0, column=4, padx=5)
        
        # Helper button to get latest date
        def use_latest_date():
            dates = self.db_manager.get_available_dates(currency_var.get())
            if dates:
                date_var.set(dates[0].strftime('%Y-%m-%d'))
                messagebox.showinfo("Latest Date", f"Latest date: {dates[0]}")
            else:
                messagebox.showwarning("No Data", "No data available for this currency")
        
        ttk.Button(control_frame, text="Get Latest", 
                  command=use_latest_date).grid(row=0, column=5, padx=5)
        
        # Chart frame
        chart_frame = ttk.Frame(dialog)
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create matplotlib figure
        fig = Figure(figsize=(10, 6), dpi=100)
        ax = fig.add_subplot(111)
        
        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill=tk.BOTH, expand=True)
        
        # Add toolbar
        toolbar = NavigationToolbar2Tk(canvas, chart_frame)
        toolbar.update()
        
        def plot_yield_curve():
            """Plot the yield curve"""
            ax.clear()
            
            currency = currency_var.get()
            
            # Get date
            if date_var.get().strip():
                try:
                    target_date = datetime.strptime(date_var.get(), '%Y-%m-%d').date()
                except ValueError:
                    messagebox.showerror("Error", "Invalid date. Use YYYY-MM-DD")
                    return
            else:
                # Use latest date
                dates = self.db_manager.get_available_dates(currency)
                if not dates:
                    messagebox.showerror("Error", "No data available")
                    return
                target_date = dates[0]
            
            # Get rates for this date
            rates = self.db_manager.get_rates(
                currency=currency,
                start_date=target_date,
                end_date=target_date
            )
            
            # If no data for exact date, find nearest date
            if not rates:
                dates = self.db_manager.get_available_dates(currency)
                if not dates:
                    ax.text(0.5, 0.5, f'No data available for {currency}', 
                           ha='center', va='center', transform=ax.transAxes, fontsize=14)
                    canvas.draw()
                    return
                
                # Find nearest date
                nearest_date = min(dates, key=lambda d: abs((d - target_date).days))
                
                # Get rates for nearest date
                rates = self.db_manager.get_rates(
                    currency=currency,
                    start_date=nearest_date,
                    end_date=nearest_date
                )
                
                if not rates:
                    ax.text(0.5, 0.5, f'No data available', 
                           ha='center', va='center', transform=ax.transAxes, fontsize=14)
                    canvas.draw()
                    return
                
                # Update target_date to show what we're actually plotting
                target_date = nearest_date
                messagebox.showinfo("Date Adjusted", 
                                  f"No data for requested date.\nShowing nearest available date: {nearest_date}")
            
            # Convert tenors to months for x-axis
            from database_models import tenor_sort_key
            
            tenor_months = []
            rate_values = []
            tenor_labels = []
            
            for rate in rates:
                months = tenor_sort_key(rate.tenor)
                tenor_months.append(months)
                rate_values.append(rate.rate)
                tenor_labels.append(rate.tenor)
            
            # Sort by tenor
            sorted_data = sorted(zip(tenor_months, rate_values, tenor_labels))
            tenor_months, rate_values, tenor_labels = zip(*sorted_data)
            
            # Plot
            ax.plot(tenor_months, rate_values, marker='o', linewidth=2, 
                   markersize=8, color='#1f77b4')
            
            # Set x-axis labels to actual tenors
            ax.set_xticks(tenor_months)
            ax.set_xticklabels(tenor_labels, rotation=45)
            
            ax.set_xlabel('Tenor', fontsize=12)
            ax.set_ylabel('Swap Rate (%)', fontsize=12)
            ax.set_title(f'{currency} Yield Curve - {target_date}', 
                        fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)
            
            canvas.draw()
        
        # Plot button
        ttk.Button(control_frame, text="Plot", command=plot_yield_curve).grid(row=0, column=5, padx=10)
        
        # Auto-plot on open
        dialog.after(100, plot_yield_curve)
    
    def on_closing(self):
        """Handle application closing"""
        self.db_manager.close()
        self.root.destroy()



    # ==================== ANALYTICS METHODS ====================
    
    def show_statistics_dialog(self):
        """Show comprehensive statistics for a tenor"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Statistics Summary")
        dialog.geometry("600x700")
        
        control_frame = ttk.Frame(dialog, padding="10")
        control_frame.pack(fill=tk.X)
        
        ttk.Label(control_frame, text="Currency:").grid(row=0, column=0, padx=5)
        currency_var = tk.StringVar(value="AUD")
        ttk.Combobox(control_frame, textvariable=currency_var,
                    values=["AUD", "NZD"], state='readonly', width=10).grid(row=0, column=1, padx=5)
        
        ttk.Label(control_frame, text="Tenor:").grid(row=0, column=2, padx=5)
        tenors = self.db_manager.get_available_tenors()
        tenor_var = tk.StringVar(value=tenors[0] if tenors else "")
        ttk.Combobox(control_frame, textvariable=tenor_var,
                    values=tenors, state='readonly', width=10).grid(row=0, column=3, padx=5)
        
        # Text widget for results
        text_frame = ttk.Frame(dialog)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=('Courier', 10))
        scrollbar = ttk.Scrollbar(text_frame, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        def calculate_stats():
            currency = currency_var.get()
            tenor = tenor_var.get()
            
            if not tenor:
                return
            
            stats = self.analytics.get_rate_statistics(currency, tenor)
            
            if not stats:
                text_widget.delete(1.0, tk.END)
                text_widget.insert(tk.END, "No data available for this selection.")
                return
            
            text_widget.delete(1.0, tk.END)
            text_widget.insert(tk.END, f"═══════════════════════════════════════\n")
            text_widget.insert(tk.END, f"  STATISTICS SUMMARY: {currency} {tenor}\n")
            text_widget.insert(tk.END, f"═══════════════════════════════════════\n\n")
            
            text_widget.insert(tk.END, f"CURRENT DATA:\n")
            text_widget.insert(tk.END, f"  Current Rate:    {stats['current']:.4f}%\n")
            text_widget.insert(tk.END, f"  Last Updated:    {stats['last_date']}\n")
            text_widget.insert(tk.END, f"  Data Points:     {stats['count']}\n\n")
            
            text_widget.insert(tk.END, f"CENTRAL TENDENCY:\n")
            text_widget.insert(tk.END, f"  Mean:            {stats['mean']:.4f}%\n")
            text_widget.insert(tk.END, f"  Median:          {stats['median']:.4f}%\n\n")
            
            text_widget.insert(tk.END, f"DISPERSION:\n")
            text_widget.insert(tk.END, f"  Std Deviation:   {stats['std_dev']:.4f}%\n")
            text_widget.insert(tk.END, f"  Minimum:         {stats['min']:.4f}%\n")
            text_widget.insert(tk.END, f"  Maximum:         {stats['max']:.4f}%\n")
            text_widget.insert(tk.END, f"  Range:           {stats['range']:.4f}%\n\n")
            
            text_widget.insert(tk.END, f"PERCENTILES:\n")
            text_widget.insert(tk.END, f"  25th:            {stats['percentile_25']:.4f}%\n")
            text_widget.insert(tk.END, f"  75th:            {stats['percentile_75']:.4f}%\n\n")
            
            if 'change_1d' in stats:
                text_widget.insert(tk.END, f"RATE CHANGES:\n")
                text_widget.insert(tk.END, f"  1 Day:           {stats['change_1d']:+.4f}%\n")
                text_widget.insert(tk.END, f"  1 Week:          {stats['change_1w']:+.4f}%\n")
                text_widget.insert(tk.END, f"  1 Month:         {stats['change_1m']:+.4f}%\n")
                text_widget.insert(tk.END, f"  3 Months:        {stats['change_3m']:+.4f}%\n")
        
        ttk.Button(control_frame, text="Calculate", command=calculate_stats).grid(row=0, column=4, padx=10)
        calculate_stats()  # Auto-calculate on open
    
    def show_spread_analysis(self):
        """Analyze spread between two tenors"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Spread Analysis")
        dialog.geometry("1000x700")
        
        control_frame = ttk.Frame(dialog, padding="10")
        control_frame.pack(fill=tk.X)
        
        ttk.Label(control_frame, text="Currency:").grid(row=0, column=0, padx=5)
        currency_var = tk.StringVar(value="AUD")
        ttk.Combobox(control_frame, textvariable=currency_var,
                    values=["AUD", "NZD"], state='readonly').grid(row=0, column=1, padx=5)
        
        tenors = self.db_manager.get_available_tenors()
        
        ttk.Label(control_frame, text="Tenor 1:").grid(row=0, column=2, padx=5)
        tenor1_var = tk.StringVar(value=tenors[0] if len(tenors) > 0 else "")
        ttk.Combobox(control_frame, textvariable=tenor1_var,
                    values=tenors, state='readonly').grid(row=0, column=3, padx=5)
        
        ttk.Label(control_frame, text="Tenor 2:").grid(row=0, column=4, padx=5)
        tenor2_var = tk.StringVar(value=tenors[-1] if len(tenors) > 0 else "")
        ttk.Combobox(control_frame, textvariable=tenor2_var,
                    values=tenors, state='readonly').grid(row=0, column=5, padx=5)
        
        # Chart frame
        chart_frame = ttk.Frame(dialog)
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        fig = Figure(figsize=(10, 6), dpi=100)
        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill=tk.BOTH, expand=True)
        
        toolbar = NavigationToolbar2Tk(canvas, chart_frame)
        toolbar.update()
        
        def plot_spread():
            currency = currency_var.get()
            tenor1 = tenor1_var.get()
            tenor2 = tenor2_var.get()
            
            if not tenor1 or not tenor2:
                return
            
            spread_data = self.analytics.calculate_spread(currency, tenor1, tenor2)
            
            if not spread_data or spread_data['data'].empty:
                messagebox.showwarning("No Data", "No overlapping data for these tenors")
                return
            
            df = spread_data['data']
            stats = spread_data['stats']
            
            fig.clear()
            ax = fig.add_subplot(111)
            
            ax.plot(df['date'], df['spread'], linewidth=2, color=self.colors['primary'])
            ax.axhline(y=stats['mean_spread'], color=self.colors['danger'], 
                      linestyle='--', label=f"Mean: {stats['mean_spread']:.2f}%")
            
            ax.set_xlabel('Date', fontsize=11)
            ax.set_ylabel('Spread (%)', fontsize=11)
            ax.set_title(f'{currency} Spread: {tenor2} - {tenor1}', fontsize=13, fontweight='bold')
            ax.legend()
            ax.grid(True, alpha=0.3)
            fig.autofmt_xdate()
            
            canvas.draw()
        
        ttk.Button(control_frame, text="Plot", command=plot_spread).grid(row=0, column=6, padx=10)
        plot_spread()
    
    def show_volatility_analysis(self):
        """Show volatility analysis"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Volatility Analysis")
        dialog.geometry("1000x700")
        
        control_frame = ttk.Frame(dialog, padding="10")
        control_frame.pack(fill=tk.X)
        
        ttk.Label(control_frame, text="Currency:").grid(row=0, column=0, padx=5)
        currency_var = tk.StringVar(value="AUD")
        ttk.Combobox(control_frame, textvariable=currency_var,
                    values=["AUD", "NZD"], state='readonly').grid(row=0, column=1, padx=5)
        
        tenors = self.db_manager.get_available_tenors()
        ttk.Label(control_frame, text="Tenor:").grid(row=0, column=2, padx=5)
        tenor_var = tk.StringVar(value=tenors[0] if tenors else "")
        ttk.Combobox(control_frame, textvariable=tenor_var,
                    values=tenors, state='readonly').grid(row=0, column=3, padx=5)
        
        ttk.Label(control_frame, text="Window:").grid(row=0, column=4, padx=5)
        window_var = tk.StringVar(value="30")
        ttk.Combobox(control_frame, textvariable=window_var,
                    values=["10", "20", "30", "60", "90"], state='readonly', width=8).grid(row=0, column=5, padx=5)
        
        chart_frame = ttk.Frame(dialog)
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        fig = Figure(figsize=(10, 6), dpi=100)
        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill=tk.BOTH, expand=True)
        
        toolbar = NavigationToolbar2Tk(canvas, chart_frame)
        toolbar.update()
        
        def plot_volatility():
            currency = currency_var.get()
            tenor = tenor_var.get()
            window = int(window_var.get())
            
            vol_df = self.analytics.calculate_volatility(currency, tenor, window=window)
            
            if vol_df is None or vol_df.empty:
                messagebox.showwarning("No Data", "Insufficient data for volatility calculation")
                return
            
            fig.clear()
            ax = fig.add_subplot(111)
            
            ax.plot(vol_df['date'], vol_df['volatility_annualized'], 
                   linewidth=2, color=self.colors['danger'])
            ax.set_xlabel('Date', fontsize=11)
            ax.set_ylabel('Annualized Volatility (%)', fontsize=11)
            ax.set_title(f'{currency} {tenor} Rolling Volatility ({window}-day window)', 
                        fontsize=13, fontweight='bold')
            ax.grid(True, alpha=0.3)
            fig.autofmt_xdate()
            
            canvas.draw()
        
        ttk.Button(control_frame, text="Plot", command=plot_volatility).grid(row=0, column=6, padx=10)
    
    def show_rate_changes(self):
        """Show rate changes over different periods"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Rate Changes Analysis")
        dialog.geometry("700x600")
        
        control_frame = ttk.Frame(dialog, padding="10")
        control_frame.pack(fill=tk.X)
        
        ttk.Label(control_frame, text="Currency:").grid(row=0, column=0, padx=5)
        currency_var = tk.StringVar(value="AUD")
        ttk.Combobox(control_frame, textvariable=currency_var,
                    values=["AUD", "NZD"], state='readonly').grid(row=0, column=1, padx=5)
        
        tenors = self.db_manager.get_available_tenors()
        ttk.Label(control_frame, text="Tenor:").grid(row=0, column=2, padx=5)
        tenor_var = tk.StringVar(value=tenors[0] if tenors else "")
        ttk.Combobox(control_frame, textvariable=tenor_var,
                    values=tenors, state='readonly').grid(row=0, column=3, padx=5)
        
        # Table frame
        table_frame = ttk.Frame(dialog)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ('Period', 'Change (bps)', 'Change (%)', 'From', 'To')
        tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        def calculate_changes():
            for item in tree.get_children():
                tree.delete(item)
            
            currency = currency_var.get()
            tenor = tenor_var.get()
            
            changes = self.analytics.calculate_rate_changes(currency, tenor)
            
            if not changes:
                messagebox.showinfo("No Data", "Insufficient data for rate change calculation")
                return
            
            for period, data in changes.items():
                tree.insert('', tk.END, values=(
                    period,
                    f"{data['absolute_change']*100:.2f}",
                    f"{data['percent_change']:.2f}",
                    f"{data['from_rate']:.4f}%",
                    f"{data['to_rate']:.4f}%"
                ))
        
        ttk.Button(control_frame, text="Calculate", command=calculate_changes).grid(row=0, column=4, padx=10)
        calculate_changes()
    
    def show_correlation_matrix(self):
        """Show correlation between multiple tenors"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Correlation Analysis")
        dialog.geometry("600x400")
        
        messagebox.showinfo("Feature", 
                          "Correlation matrix shows how tenors move together.\n\n"
                          "Values close to 1.0 indicate strong positive correlation.\n"
                          "Values close to -1.0 indicate strong negative correlation.\n\n"
                          "This feature is available via the API or can be added to GUI.")
    
    # ==================== ALERT METHODS ====================
    
    def show_alerts_manager(self):
        """Alert management interface"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Alert Manager")
        dialog.geometry("900x600")
        
        # Button frame
        button_frame = ttk.Frame(dialog, padding="10")
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Add Alert", 
                  command=lambda: self.add_alert_dialog(tree)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete Selected", 
                  command=lambda: self.delete_alert(tree)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Enable Selected", 
                  command=lambda: self.toggle_alert(tree, True)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Disable Selected", 
                  command=lambda: self.toggle_alert(tree, False)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Refresh", 
                  command=lambda: self.refresh_alerts(tree)).pack(side=tk.LEFT, padx=5)
        
        # Alert list
        list_frame = ttk.Frame(dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ('ID', 'Name', 'Currency', 'Tenor', 'Condition', 'Threshold', 'Enabled', 'Triggers')
        tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        for col in columns:
            tree.heading(col, text=col)
            if col == 'Name':
                tree.column(col, width=150)
            elif col in ['ID', 'Triggers']:
                tree.column(col, width=50)
            else:
                tree.column(col, width=80)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.refresh_alerts(tree)
    
    def add_alert_dialog(self, tree):
        """Dialog to add new alert"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Alert")
        dialog.geometry("400x350")
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Alert Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        name_var = tk.StringVar()
        ttk.Entry(frame, textvariable=name_var, width=30).grid(row=0, column=1, pady=5)
        
        ttk.Label(frame, text="Currency:").grid(row=1, column=0, sticky=tk.W, pady=5)
        currency_var = tk.StringVar(value="AUD")
        ttk.Combobox(frame, textvariable=currency_var, values=["AUD", "NZD"], 
                    state='readonly', width=28).grid(row=1, column=1, pady=5)
        
        tenors = self.db_manager.get_available_tenors()
        ttk.Label(frame, text="Tenor:").grid(row=2, column=0, sticky=tk.W, pady=5)
        tenor_var = tk.StringVar(value=tenors[0] if tenors else "")
        ttk.Combobox(frame, textvariable=tenor_var, values=tenors, 
                    width=28).grid(row=2, column=1, pady=5)
        
        ttk.Label(frame, text="Condition:").grid(row=3, column=0, sticky=tk.W, pady=5)
        condition_var = tk.StringVar(value="above")
        conditions = [
            ("Above threshold", "above"),
            ("Below threshold", "below"),
            ("Crosses above", "crosses_above"),
            ("Crosses below", "crosses_below"),
            ("Changes by amount", "change")
        ]
        condition_combo = ttk.Combobox(frame, textvariable=condition_var,
                                      values=[c[1] for c in conditions],
                                      width=28, state='readonly')
        condition_combo.grid(row=3, column=1, pady=5)
        
        ttk.Label(frame, text="Threshold (%):").grid(row=4, column=0, sticky=tk.W, pady=5)
        threshold_var = tk.StringVar(value="4.5")
        ttk.Entry(frame, textvariable=threshold_var, width=30).grid(row=4, column=1, pady=5)
        
        ttk.Label(frame, text="Enabled:").grid(row=5, column=0, sticky=tk.W, pady=5)
        enabled_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, variable=enabled_var).grid(row=5, column=1, sticky=tk.W, pady=5)
        
        def save_alert():
            alert_config = {
                'name': name_var.get() or f"{currency_var.get()} {tenor_var.get()} Alert",
                'currency': currency_var.get(),
                'tenor': tenor_var.get(),
                'condition': condition_var.get(),
                'threshold': float(threshold_var.get()),
                'enabled': enabled_var.get()
            }
            
            self.alert_manager.add_alert(alert_config)
            messagebox.showinfo("Success", "Alert created successfully")
            dialog.destroy()
            self.refresh_alerts(tree)
        
        ttk.Button(frame, text="Save Alert", command=save_alert).grid(row=6, column=0, columnspan=2, pady=20)
    
    def delete_alert(self, tree):
        """Delete selected alert"""
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an alert to delete")
            return
        
        item = tree.item(selected[0])
        alert_id = int(item['values'][0])
        
        if messagebox.askyesno("Confirm", "Delete this alert?"):
            self.alert_manager.remove_alert(alert_id)
            self.refresh_alerts(tree)
    
    def toggle_alert(self, tree, enable):
        """Enable or disable alert"""
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an alert")
            return
        
        item = tree.item(selected[0])
        alert_id = int(item['values'][0])
        
        if enable:
            self.alert_manager.enable_alert(alert_id)
        else:
            self.alert_manager.disable_alert(alert_id)
        
        self.refresh_alerts(tree)
    
    def refresh_alerts(self, tree):
        """Refresh alert list"""
        for item in tree.get_children():
            tree.delete(item)
        
        alerts = self.alert_manager.get_alerts()
        
        for alert in alerts:
            tree.insert('', tk.END, values=(
                alert['id'],
                alert.get('name', 'Unnamed'),
                alert['currency'],
                alert['tenor'],
                alert['condition'],
                f"{alert['threshold']:.2f}",
                'Yes' if alert.get('enabled', False) else 'No',
                alert.get('trigger_count', 0)
            ))
        
        # Update main window indicator
        enabled_count = len([a for a in alerts if a.get('enabled', False)])
        self.alert_indicator.config(text=f"● Alerts: {enabled_count} active")
    
    def check_alerts_manual(self):
        """Manually check all alerts"""
        triggered = self.alert_manager.check_alerts()
        
        if triggered:
            msg = f"🔔 {len(triggered)} Alert(s) Triggered!\n\n"
            for t in triggered:
                msg += f"• {t['message']}\n"
            messagebox.showwarning("Alerts Triggered", msg)
        else:
            messagebox.showinfo("Alerts", "No alerts triggered. All rates within thresholds.")
    
    def check_alerts_background(self):
        """Background alert checking"""
        try:
            triggered = self.alert_manager.check_alerts()
            
            if triggered:
                # Update indicator color
                self.alert_indicator.config(foreground=self.colors['danger'])
                # Could add popup notification here
            else:
                self.alert_indicator.config(foreground=self.colors['success'])
        except Exception as e:
            print(f"Error checking alerts: {e}")
        
        # Schedule next check
        self.alert_after_id = self.root.after(self.alert_check_interval, self.check_alerts_background)
    
    # ==================== DATA VALIDATION METHODS ====================
    
    def show_missing_dates(self):
        """Enhanced missing dates finder with interpolation"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Missing Data Finder & Filler")
        dialog.geometry("900x700")
        
        # Control frame
        control_frame = ttk.LabelFrame(dialog, text="  Analysis Options  ", padding="15")
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Currency selection
        ttk.Label(control_frame, text="Currency:").grid(row=0, column=0, padx=5, sticky=tk.W)
        currency_var = tk.StringVar(value="All")
        currency_combo = ttk.Combobox(control_frame, textvariable=currency_var,
                    values=["All", "AUD", "CAD", "EUR", "GBP", "JPY", "NZD", "USD"], state='readonly', width=12)
        currency_combo.grid(row=0, column=1, padx=5)
        
        # Tenor selection
        tenors = self.db_manager.get_available_tenors()
        ttk.Label(control_frame, text="Tenor:").grid(row=0, column=2, padx=5, sticky=tk.W)
        tenor_var = tk.StringVar(value="All")
        tenor_combo = ttk.Combobox(control_frame, textvariable=tenor_var,
                    values=["All"] + tenors, state='readonly', width=12)
        tenor_combo.grid(row=0, column=3, padx=5)
        
        # Check All button
        ttk.Button(control_frame, text="🔍 Check All", command=lambda: find_missing(check_all=True), 
                  style='Accent.TButton').grid(row=0, column=4, padx=10)
        
        # Find Missing button
        ttk.Button(control_frame, text="Find Missing", command=lambda: find_missing(check_all=False), 
                  style='TButton').grid(row=0, column=5, padx=5)
        
        # Results frame
        results_frame = ttk.LabelFrame(dialog, text="  Missing Data Points  ", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Results tree
        columns = ('Currency', 'Tenor', 'Floating Rate', 'Missing Dates', 'Date Range')
        tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=15)
        
        tree.heading('Currency', text='Currency')
        tree.heading('Tenor', text='Tenor')
        tree.heading('Floating Rate', text='Floating Rate')
        tree.heading('Missing Dates', text='Missing Dates')
        tree.heading('Date Range', text='Date Range')
        
        tree.column('Currency', width=80, anchor='center')
        tree.column('Tenor', width=80, anchor='center')
        tree.column('Floating Rate', width=120, anchor='center')
        tree.column('Missing Dates', width=100, anchor='center')
        tree.column('Date Range', width=200, anchor='center')
        
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Status label
        status_var = tk.StringVar(value="Ready - Select options and click 'Find Missing'")
        status_label = ttk.Label(dialog, textvariable=status_var, font=self.fonts['small'])
        status_label.pack(pady=5)
        
        # Action buttons frame
        action_frame = ttk.Frame(dialog, padding="10")
        action_frame.pack(fill=tk.X)
        
        ttk.Button(action_frame, text="📊 Generate Report", command=lambda: generate_report(), 
                  style='TButton').pack(side=tk.LEFT, padx=5)
        
        ttk.Button(action_frame, text="✨ Fill Missing Data (Cubic Spline)", command=lambda: fill_missing_data(), 
                  style='Success.TButton').pack(side=tk.LEFT, padx=5)
        
        ttk.Button(action_frame, text="Close", command=dialog.destroy, 
                  style='TButton').pack(side=tk.RIGHT, padx=5)
        
        # Store missing data info
        missing_data = []
        
        def find_missing(check_all=False):
            """Find missing dates"""
            nonlocal missing_data
            missing_data = []
            
            for item in tree.get_children():
                tree.delete(item)
            
            status_var.set("Searching for missing dates...")
            dialog.update()
            
            import sqlite3
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'swap_rates.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get combinations to check
            if check_all or currency_var.get() == "All":
                currencies = ["AUD", "CAD", "EUR", "GBP", "JPY", "NZD", "USD"]
            else:
                currencies = [currency_var.get()]
            
            if check_all or tenor_var.get() == "All":
                cursor.execute("SELECT DISTINCT tenor FROM swap_rates ORDER BY tenor")
                tenors_to_check = [row[0] for row in cursor.fetchall()]
            else:
                tenors_to_check = [tenor_var.get()]
            
            total_missing = 0
            
            for curr in currencies:
                for ten in tenors_to_check:
                    # Get data for this combination
                    cursor.execute("""
                        SELECT date, floating_rate FROM swap_rates 
                        WHERE currency = ? AND tenor = ? 
                        ORDER BY date
                    """, (curr, ten))
                    
                    rows = cursor.fetchall()
                    if len(rows) < 2:
                        continue
                    
                    # Get floating rate
                    floating_rate = rows[0][1] if rows else "N/A"
                    
                    # Convert to dates
                    dates = [datetime.strptime(row[0], '%Y-%m-%d').date() for row in rows]
                    
                    # Find missing business days
                    from datetime import timedelta
                    missing = []
                    for i in range(len(dates) - 1):
                        current = dates[i]
                        next_date = dates[i + 1]
                        
                        # Check each day in between
                        check_date = current + timedelta(days=1)
                        while check_date < next_date:
                            # Skip weekends
                            if check_date.weekday() < 5:  # Monday = 0, Friday = 4
                                missing.append(check_date)
                            check_date += timedelta(days=1)
                    
                    if missing:
                        total_missing += len(missing)
                        date_range = f"{dates[0]} to {dates[-1]}"
                        
                        tree.insert('', tk.END, values=(
                            curr, ten, floating_rate, len(missing), date_range
                        ))
                        
                        missing_data.append({
                            'currency': curr,
                            'tenor': ten,
                            'floating_rate': floating_rate,
                            'missing_dates': missing,
                            'existing_dates': dates
                        })
            
            conn.close()
            
            if total_missing == 0:
                status_var.set("✓ No missing dates found - data is complete!")
                messagebox.showinfo("Complete Data", "No missing business days found!")
            else:
                status_var.set(f"Found {total_missing} missing data points across {len(missing_data)} series")
        
        def generate_report():
            """Generate missing data report"""
            if not missing_data:
                messagebox.showwarning("No Data", "Please run 'Find Missing' first")
                return
            
            from tkinter import filedialog
            filepath = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="Save Missing Data Report"
            )
            
            if not filepath:
                return
            
            with open(filepath, 'w') as f:
                f.write("=" * 80 + "\n")
                f.write("MISSING DATA REPORT\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 80 + "\n\n")
                
                total = 0
                for item in missing_data:
                    f.write(f"\nCurrency: {item['currency']}\n")
                    f.write(f"Tenor: {item['tenor']}\n")
                    f.write(f"Floating Rate: {item['floating_rate']}\n")
                    f.write(f"Missing Dates: {len(item['missing_dates'])}\n")
                    f.write(f"Date Range: {item['existing_dates'][0]} to {item['existing_dates'][-1]}\n")
                    f.write(f"\nMissing Business Days:\n")
                    for date in item['missing_dates'][:20]:  # First 20
                        f.write(f"  - {date}\n")
                    if len(item['missing_dates']) > 20:
                        f.write(f"  ... and {len(item['missing_dates']) - 20} more\n")
                    f.write("-" * 80 + "\n")
                    total += len(item['missing_dates'])
                
                f.write(f"\nTOTAL MISSING DATA POINTS: {total}\n")
            
            messagebox.showinfo("Report Saved", f"Report saved to:\n{filepath}")
        
        def fill_missing_data():
            """Fill missing data using cubic spline interpolation"""
            if not missing_data:
                messagebox.showwarning("No Data", "Please run 'Find Missing' first")
                return
            
            if not messagebox.askyesno("Confirm Fill", 
                f"This will fill {sum(len(item['missing_dates']) for item in missing_data)} missing data points using cubic spline interpolation.\n\nContinue?"):
                return
            
            try:
                from scipy.interpolate import CubicSpline
            except ImportError:
                messagebox.showerror("Missing Library", 
                    "scipy is required for cubic spline interpolation.\n\nInstall with: pip install scipy")
                return
            
            status_var.set("Filling missing data...")
            dialog.update()
            
            import sqlite3
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'swap_rates.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            filled_count = 0
            
            for item in missing_data:
                # Get existing data
                cursor.execute("""
                    SELECT date, rate FROM swap_rates 
                    WHERE currency = ? AND tenor = ? AND floating_rate = ?
                    ORDER BY date
                """, (item['currency'], item['tenor'], item['floating_rate']))
                
                rows = cursor.fetchall()
                dates = [datetime.strptime(row[0], '%Y-%m-%d').date() for row in rows]
                rates = [row[1] for row in rows]
                
                # Convert dates to numerical values (days since first date)
                date_nums = [(d - dates[0]).days for d in dates]
                
                # Create cubic spline
                cs = CubicSpline(date_nums, rates, bc_type='natural')
                
                # Fill missing dates
                for missing_date in item['missing_dates']:
                    missing_num = (missing_date - dates[0]).days
                    interpolated_rate = float(cs(missing_num))
                    
                    # Insert into database
                    cursor.execute("""
                        INSERT OR REPLACE INTO swap_rates (date, currency, tenor, floating_rate, rate, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                    """, (missing_date.strftime('%Y-%m-%d'), item['currency'], item['tenor'], 
                          item['floating_rate'], interpolated_rate))
                    
                    filled_count += 1
            
            conn.commit()
            conn.close()
            
            status_var.set(f"✓ Filled {filled_count} missing data points using cubic spline")
            messagebox.showinfo("Success", f"Filled {filled_count} missing data points!\n\nRefresh your data to see the changes.")
            
            # Refresh the main view
            self.refresh_data()
    
    def show_outliers(self):
        """Detect outliers in data"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Outlier Detection")
        dialog.geometry("700x500")
        
        control_frame = ttk.Frame(dialog, padding="10")
        control_frame.pack(fill=tk.X)
        
        ttk.Label(control_frame, text="Currency:").grid(row=0, column=0, padx=5)
        currency_var = tk.StringVar(value="AUD")
        ttk.Combobox(control_frame, textvariable=currency_var,
                    values=["AUD", "NZD"], state='readonly').grid(row=0, column=1, padx=5)
        
        tenors = self.db_manager.get_available_tenors()
        ttk.Label(control_frame, text="Tenor:").grid(row=0, column=2, padx=5)
        tenor_var = tk.StringVar(value=tenors[0] if tenors else "")
        ttk.Combobox(control_frame, textvariable=tenor_var,
                    values=tenors, state='readonly').grid(row=0, column=3, padx=5)
        
        ttk.Label(control_frame, text="Threshold (σ):").grid(row=0, column=4, padx=5)
        threshold_var = tk.StringVar(value="3")
        ttk.Combobox(control_frame, textvariable=threshold_var,
                    values=["2", "2.5", "3", "3.5"], width=8).grid(row=0, column=5, padx=5)
        
        list_frame = ttk.Frame(dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ('Date', 'Rate', 'Z-Score', 'Deviation')
        tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        for col in columns:
            tree.heading(col, text=col)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        def detect_outliers():
            for item in tree.get_children():
                tree.delete(item)
            
            currency = currency_var.get()
            tenor = tenor_var.get()
            threshold = float(threshold_var.get())
            
            result = self.analytics.detect_outliers(currency, tenor, threshold)
            
            if not result:
                messagebox.showinfo("No Data", "No data available")
                return
            
            if result['count'] == 0:
                messagebox.showinfo("Clean Data", "No outliers detected!")
                return
            
            for outlier in result['outliers']:
                tree.insert('', tk.END, values=(
                    outlier['date'].strftime('%Y-%m-%d'),
                    f"{outlier['rate']:.4f}%",
                    f"{outlier['z_score']:.2f}",
                    f"{outlier['deviation_from_mean']:+.4f}%"
                ))
            
            messagebox.showinfo("Outliers", f"Found {result['count']} outliers")
        
        ttk.Button(control_frame, text="Detect", command=detect_outliers).grid(row=0, column=6, padx=10)
    
    def show_data_quality(self):
        """Show overall data quality report"""
        messagebox.showinfo("Data Quality", 
                          "Data Quality Dashboard:\n\n"
                          "• Use 'Find Missing Dates' to check for gaps\n"
                          "• Use 'Detect Outliers' to find unusual values\n"
                          "• Check Statistics Summary for data ranges\n\n"
                          "A comprehensive report can be generated via PDF Reports.")
    
    # ==================== REPORT METHODS ====================
    
    def generate_pdf_report(self):
        """Generate comprehensive PDF report"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Generate PDF Report")
        dialog.geometry("400x200")
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Currency:").grid(row=0, column=0, sticky=tk.W, pady=10)
        currency_var = tk.StringVar(value="AUD")
        ttk.Combobox(frame, textvariable=currency_var,
                    values=["AUD", "NZD"], state='readonly', width=20).grid(row=0, column=1, pady=10)
        
        ttk.Label(frame, text="Report will include:\n"
                             "• Latest rates table\n"
                             "• Yield curve\n"
                             "• Historical charts\n"
                             "• Statistics",
                 justify=tk.LEFT).grid(row=1, column=0, columnspan=2, pady=10)
        
        def generate():
            currency = currency_var.get()
            
            file_path = filedialog.asksaveasfilename(
                title="Save PDF Report",
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")]
            )
            
            if not file_path:
                return
            
            try:
                dialog.destroy()
                messagebox.showinfo("Generating", "Generating report... This may take a moment.")
                
                self.report_generator.generate_market_report(currency, file_path)
                
                messagebox.showinfo("Success", f"Report generated successfully!\n\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to generate report:\n{str(e)}")
        
        ttk.Button(frame, text="Generate Report", command=generate).grid(row=2, column=0, columnspan=2, pady=20)
    
    def generate_custom_report(self):
        """Generate custom PDF report"""
        messagebox.showinfo("Custom Report", 
                          "Custom report builder allows you to:\n\n"
                          "• Select specific tenors\n"
                          "• Choose date range\n"
                          "• Include/exclude sections\n\n"
                          "Use 'Generate Market Report' for a standard report,\n"
                          "or contact support for custom report templates.")
    
    # ==================== ADDITIONAL CHART METHODS ====================
    
    def show_spread_chart(self):
        """Show spread chart between two tenors"""
        self.show_spread_analysis()  # Reuse the spread analysis
    
    def show_volatility_chart(self):
        """Show volatility chart"""
        self.show_volatility_analysis()  # Reuse volatility analysis
    
    def show_feature_guide(self):
        """Show feature guide"""
        guide = """IRS SWAP RATE MANAGER - FEATURE GUIDE

ANALYTICS:
• Statistics Summary: Comprehensive stats for any tenor
• Spread Analysis: Compare two tenors over time
• Volatility Analysis: Rolling volatility calculations
• Rate Changes: Track changes over multiple periods
• Correlation Matrix: See how tenors move together

ALERTS:
• Create alerts for rate thresholds
• Get notified when rates cross levels
• Monitor large rate movements
• Auto-check every 5 minutes

CHARTS:
• Compare up to 3 tenors side-by-side
• View yield curves for any date
• Analyze spreads visually
• Track volatility trends

DATA VALIDATION:
• Find missing dates in your data
• Detect outlier values
• Check data quality

REPORTS:
• Generate professional PDF reports
• Include charts and statistics
• Export for presentations

Visit the menu items to explore each feature!
"""
        messagebox.showinfo("Feature Guide", guide)
    
    # ============================================================================
    # PHASE 2 FEATURES - Advanced Functionality
    # ============================================================================
    
    def show_swap_pricer(self):
        """Open Forward Swap Pricer tool"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Forward Swap Pricer")
        dialog.geometry("1200x900")
        dialog.configure(bg=self.colors['bg_main'])
        
        # Main container
        main_frame = ttk.Frame(dialog, style='Main.TFrame', padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_frame = ttk.Frame(main_frame, style='Main.TFrame')
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(title_frame, text="💹 Forward-Starting Swap Pricer",
                 style='Title.TLabel').pack(side=tk.LEFT)
        
        ttk.Label(title_frame, text="Professional swap valuation with OIS discounting",
                 font=self.fonts['small'], foreground=self.colors['text_light']).pack(
            side=tk.LEFT, padx=(15, 0))
        
        # Input section
        input_card = ttk.Frame(main_frame, style='Card.TFrame', relief='solid', borderwidth=1)
        input_card.pack(fill=tk.X, pady=(0, 15))
        
        input_frame = ttk.LabelFrame(input_card, text="  Swap Parameters  ", 
                                     padding=20, style='TLabelframe')
        input_frame.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
        
        # Create parameter inputs in a grid
        params = [
            ("Valuation Date (YYYY-MM-DD):", datetime.now().strftime('%Y-%m-%d')),
            ("Start (months from valuation):", "6"),
            ("Maturity (years from start):", "5"),
            ("Fixed Rate (%):", "4.50"),
            ("Notional (AUD):", "10000000"),
            ("Fixed Payments Per Year:", "2"),
            ("Float Payments Per Year:", "4"),
            ("Float Tenor (months):", "3"),
            ("Fixed Spread (basis points):", "0"),
            ("Float Margin (basis points):", "0"),
            ("Convexity Adj Float (bp):", "0"),
            ("Convexity Adj Fixed (bp):", "0"),
        ]
        
        entry_vars = {}
        for i, (label, default) in enumerate(params):
            row = i // 2
            col = (i % 2) * 3
            
            ttk.Label(input_frame, text=label, font=self.fonts['normal']).grid(
                row=row, column=col, padx=(15 if col == 0 else 40, 8), pady=8, sticky=tk.W)
            
            var = tk.StringVar(value=default)
            entry_vars[label] = var
            ttk.Entry(input_frame, textvariable=var, width=18, 
                     font=self.fonts['normal']).grid(
                row=row, column=col+1, padx=(0, 15), pady=8, sticky=tk.W)
        
        # OIS toggle
        use_ois_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(input_frame, text="Use OIS Discounting (separate discount curve)",
                       variable=use_ois_var, style='TCheckbutton').grid(
            row=len(params)//2, column=0, columnspan=2, pady=15, padx=15, sticky=tk.W)
        
        # Curve source info
        curve_info_frame = ttk.Frame(input_frame, style='Card.TFrame')
        curve_info_frame.grid(row=len(params)//2 + 1, column=0, columnspan=6, 
                             pady=10, padx=15, sticky=(tk.W, tk.E))
        
        ttk.Label(curve_info_frame, 
                 text="📊 Zero Curve Source: Using rates from database for projection curve",
                 font=self.fonts['small'], foreground=self.colors['text_light']).pack(
            side=tk.LEFT)
        
        # Calculate button
        def calculate_swap():
            try:
                # Import swap pricer with better path handling
                import sys
                import os
                
                # Get the correct path to backend
                current_dir = os.path.dirname(os.path.abspath(__file__))
                backend_dir = os.path.join(current_dir, '..', 'backend')
                backend_dir = os.path.abspath(backend_dir)
                
                if backend_dir not in sys.path:
                    sys.path.insert(0, backend_dir)
                
                try:
                    from swap_pricer import SwapPricer
                except ImportError as ie:
                    messagebox.showerror("Import Error", 
                                       f"Cannot import swap pricer module.\n\n"
                                       f"Looking in: {backend_dir}\n"
                                       f"Error: {str(ie)}\n\n"
                                       f"Please ensure swap_pricer.py exists in backend folder.")
                    return
                
                from datetime import datetime
                
                # Parse inputs with validation
                try:
                    val_date = datetime.strptime(entry_vars["Valuation Date (YYYY-MM-DD):"].get(), 
                                                '%Y-%m-%d').date()
                except ValueError:
                    messagebox.showerror("Input Error", "Invalid valuation date. Use format: YYYY-MM-DD")
                    return
                
                try:
                    start_months = int(entry_vars["Start (months from valuation):"].get())
                    maturity_years = float(entry_vars["Maturity (years from start):"].get())
                    fixed_rate = float(entry_vars["Fixed Rate (%):"].get()) / 100
                    notional = float(entry_vars["Notional (AUD):"].get().replace(',', ''))
                    fixed_freq = int(entry_vars["Fixed Payments Per Year:"].get())
                    float_freq = int(entry_vars["Float Payments Per Year:"].get())
                    float_tenor = int(entry_vars["Float Tenor (months):"].get())
                    fixed_spread_bp = float(entry_vars["Fixed Spread (basis points):"].get())
                    float_margin_bp = float(entry_vars["Float Margin (basis points):"].get())
                    conv_float_bp = float(entry_vars["Convexity Adj Float (bp):"].get())
                    conv_fixed_bp = float(entry_vars["Convexity Adj Fixed (bp):"].get())
                except ValueError as ve:
                    messagebox.showerror("Input Error", f"Invalid numeric input:\n{str(ve)}")
                    return
                
                # Get curve data from database
                projection_curve = self.build_zero_curve_from_database(val_date)
                
                if not projection_curve:
                    messagebox.showerror("Error", 
                                       "No curve data available. Please import swap rates first.\n\n"
                                       "The pricer needs rates within 7 days of the valuation date.")
                    return
                
                # Initialize pricer
                pricer = SwapPricer(valuation_date=val_date)
                
                # Price the swap
                result = pricer.price_forward_swap(
                    start_months=start_months,
                    maturity_years=maturity_years,
                    fixed_rate=fixed_rate,
                    notional=notional,
                    projection_curve=projection_curve,
                    discount_curve=projection_curve if use_ois_var.get() else None,
                    fixed_freq=fixed_freq,
                    float_freq=float_freq,
                    float_tenor_months=float_tenor,
                    use_ois_discounting=use_ois_var.get(),
                    fixed_spread_bp=fixed_spread_bp,
                    float_margin_bp=float_margin_bp,
                    convexity_adj_float_bp=conv_float_bp,
                    convexity_adj_fixed_bp=conv_fixed_bp
                )
                
                # Display results
                display_swap_results(result, notional, val_date)
                
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                messagebox.showerror("Calculation Error", 
                                   f"Error calculating swap:\n\n{str(e)}\n\n"
                                   f"Please check your inputs and try again.\n\n"
                                   f"Details:\n{error_details[-500:]}")
        
        ttk.Button(input_frame, text="💹 Calculate Swap Value", 
                  command=calculate_swap, style='Accent.TButton').grid(
            row=len(params)//2, column=3, columnspan=3, pady=15, padx=15, sticky=tk.E)
        
        # Results section
        results_card = ttk.Frame(main_frame, style='Card.TFrame', relief='solid', borderwidth=1)
        results_card.pack(fill=tk.BOTH, expand=True)
        
        results_frame = ttk.LabelFrame(results_card, text="  Swap Valuation Results  ",
                                       padding=20, style='TLabelframe')
        results_frame.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
        
        # Results display
        results_text = tk.Text(results_frame, height=25, font=self.fonts['mono'],
                              bg=self.colors['bg_card'], fg=self.colors['text_dark'],
                              wrap=tk.NONE)
        results_scrollbar = ttk.Scrollbar(results_frame, command=results_text.yview)
        results_text.configure(yscrollcommand=results_scrollbar.set)
        
        results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        def display_swap_results(result, notional, val_date):
            """Display swap pricing results"""
            results_text.configure(state='normal')
            results_text.delete('1.0', tk.END)
            
            output = []
            output.append("=" * 80)
            output.append("FORWARD-STARTING SWAP VALUATION RESULTS")
            output.append("=" * 80)
            output.append("")
            output.append(f"Valuation Date:     {val_date}")
            output.append(f"Start Date:         {result['start_date']}")
            output.append(f"End Date:           {result['end_date']}")
            output.append(f"Notional:           AUD {notional:,.0f}")
            output.append("")
            output.append("-" * 80)
            output.append("SWAP VALUE")
            output.append("-" * 80)
            output.append(f"Swap Value (MTM):   AUD {result['swap_value']:,.2f}")
            output.append(f"Fixed Leg PV:       AUD {result['fixed_leg_pv']:,.2f}")
            output.append(f"Float Leg PV:       AUD {result['float_leg_pv']:,.2f}")
            output.append("")
            output.append(f"Par Rate:           {result['par_rate_percent']:.4f}%")
            output.append("")
            output.append("-" * 80)
            output.append("FIXED LEG CASH FLOWS")
            output.append("-" * 80)
            output.append(f"{'#':<4} {'Pay Date':<12} {'Year Frac':<10} {'Rate':<10} "
                        f"{'Cash Flow':>15} {'DF':<10} {'PV':>15}")
            output.append("-" * 80)
            
            for i, detail in enumerate(result['fixed_leg_details'], 1):
                output.append(f"{i:<4} {str(detail['pay_date']):<12} "
                            f"{detail['year_fraction']:<10.6f} "
                            f"{detail['rate']*100:<10.4f} "
                            f"{detail['cash_flow']:>15,.2f} "
                            f"{detail['discount_factor']:<10.6f} "
                            f"{detail['pv']:>15,.2f}")
            
            output.append("")
            output.append("-" * 80)
            output.append("FLOAT LEG CASH FLOWS")
            output.append("-" * 80)
            output.append(f"{'#':<4} {'Start Date':<12} {'Pay Date':<12} {'Year Frac':<10} "
                        f"{'Fwd Rate':<10} {'Cash Flow':>15} {'DF':<10} {'PV':>15}")
            output.append("-" * 80)
            
            for i, detail in enumerate(result['float_leg_details'], 1):
                output.append(f"{i:<4} {str(detail['start_date']):<12} "
                            f"{str(detail['pay_date']):<12} "
                            f"{detail['year_fraction']:<10.6f} "
                            f"{detail['forward_rate']*100:<10.4f} "
                            f"{detail['cash_flow']:>15,.2f} "
                            f"{detail['discount_factor']:<10.6f} "
                            f"{detail['pv']:>15,.2f}")
            
            output.append("")
            output.append("=" * 80)
            output.append(f"SUMMARY: Swap MTM = AUD {result['swap_value']:,.2f}")
            output.append("=" * 80)
            
            results_text.insert('1.0', '\n'.join(output))
            results_text.configure(state='disabled')
        
        # Initial placeholder text
        placeholder = """
        FORWARD-STARTING SWAP PRICER
        ════════════════════════════════════════════════════════════════════════════════
        
        This tool prices forward-starting fixed-for-float interest rate swaps using:
        • Zero curve interpolation from your database rates
        • OIS discounting (optional)
        • Convexity adjustments
        • Flexible payment frequencies
        • Professional cash flow schedules
        
        HOW TO USE:
        1. Adjust swap parameters above (or use defaults)
        2. Click "Calculate Swap Value"
        3. Results will display here with full cash flow breakdown
        
        CURVE DATA:
        • Projection curve built from your imported swap rates
        • Interpolation used for missing tenors
        • Continuous compounding assumed
        
        NOTE: Ensure you have imported swap rates before pricing. The tool uses your
        latest data to build the zero curve for forward rate projection.
        
        Click "Calculate Swap Value" when ready!
        """
        results_text.insert('1.0', placeholder)
        results_text.configure(state='disabled')
    
    def launch_simple_pricer(self):
        """Launch Simple Forward Swap Pricer as separate window"""
        import subprocess
        import sys
        
        # Get path to simple_swap_pricer.py
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                   'simple_swap_pricer.py')
        
        if os.path.exists(script_path):
            try:
                # Launch as separate process
                subprocess.Popen([sys.executable, script_path])
                self.status_var.set("Launched Simple Forward Swap Pricer")
            except Exception as e:
                messagebox.showerror("Error", f"Could not launch Simple Pricer:\n{e}")
        else:
            messagebox.showerror("Error", 
                               f"Simple Pricer not found at:\n{script_path}\n\n"
                               "Make sure simple_swap_pricer.py is in the irs_swap_app folder")
    
    def launch_historical_analyzer(self):
        """Launch Historical Forward Swap Analyzer as separate window"""
        import subprocess
        import sys
        
        # Get path to forward_swap_analyzer.py
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                   'forward_swap_analyzer.py')
        
        if os.path.exists(script_path):
            try:
                # Launch as separate process
                subprocess.Popen([sys.executable, script_path])
                self.status_var.set("Launched Historical Forward Swap Analyzer")
            except Exception as e:
                messagebox.showerror("Error", f"Could not launch Historical Analyzer:\n{e}")
        else:
            messagebox.showerror("Error", 
                               f"Historical Analyzer not found at:\n{script_path}\n\n"
                               "Make sure forward_swap_analyzer.py is in the irs_swap_app folder")
    
    def launch_butterfly_analyzer(self):
        """Launch IRS Butterfly Spread Analyzer as separate window"""
        import subprocess
        import sys
        
        # Get path to butterfly_analyzer.py
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                   'butterfly_analyzer.py')
        
        if os.path.exists(script_path):
            try:
                # Launch as separate process
                subprocess.Popen([sys.executable, script_path])
                self.status_var.set("Launched IRS Butterfly Spread Analyzer")
            except Exception as e:
                messagebox.showerror("Error", f"Could not launch Butterfly Analyzer:\n{e}")
        else:
            messagebox.showerror("Error", 
                               f"Butterfly Analyzer not found at:\n{script_path}\n\n"
                               "Make sure butterfly_analyzer.py is in the irs_swap_app folder")
    
    def launch_basis_analyzer(self):
        """Launch Basis Spread Analyzer (3M vs 6M) as separate window"""
        import subprocess
        import sys
        
        # Get path to basis_spread_analyzer.py
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                   'basis_spread_analyzer.py')
        
        if os.path.exists(script_path):
            try:
                # Launch as separate process
                subprocess.Popen([sys.executable, script_path])
                self.status_var.set("Launched Basis Spread Analyzer")
            except Exception as e:
                messagebox.showerror("Error", f"Could not launch Basis Analyzer:\n{e}")
        else:
            messagebox.showerror("Error", 
                               f"Basis Analyzer not found at:\n{script_path}\n\n"
                               "Make sure basis_spread_analyzer.py is in the irs_swap_app folder")
    
    def launch_basis_butterfly_analyzer(self):
        """Launch Basis Butterfly Analyzer (3M vs 6M) as separate window"""
        import subprocess
        import sys
        
        # Get path to basis_butterfly_analyzer.py
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                   'basis_butterfly_analyzer.py')
        
        if os.path.exists(script_path):
            try:
                # Launch as separate process
                subprocess.Popen([sys.executable, script_path])
                self.status_var.set("Launched Basis Butterfly Analyzer")
            except Exception as e:
                messagebox.showerror("Error", f"Could not launch Basis Butterfly Analyzer:\n{e}")
        else:
            messagebox.showerror("Error", 
                               f"Basis Butterfly Analyzer not found at:\n{script_path}\n\n"
                               "Make sure basis_butterfly_analyzer.py is in the irs_swap_app folder")
    
    def launch_forward_matrix(self):
        """Launch Forward Swap Matrix Generator as separate window"""
        import subprocess
        import sys
        
        # Get path to forward_swap_matrix.py
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                   'forward_swap_matrix.py')
        
        if os.path.exists(script_path):
            try:
                # Launch as separate process
                subprocess.Popen([sys.executable, script_path])
                self.status_var.set("Launched Forward Swap Matrix Generator")
            except Exception as e:
                messagebox.showerror("Error", f"Could not launch Forward Matrix Generator:\n{e}")
        else:
            messagebox.showerror("Error", 
                               f"Forward Matrix Generator not found at:\n{script_path}\n\n"
                               "Make sure forward_swap_matrix.py is in the irs_swap_app folder")
    
    def launch_forward_basis_matrix(self):
        """Launch Forward Basis Matrix Generator (6M vs 3M) as separate window"""
        import subprocess
        import sys
        
        # Get path to forward_basis_matrix.py
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                   'forward_basis_matrix.py')
        
        if os.path.exists(script_path):
            try:
                # Launch as separate process
                subprocess.Popen([sys.executable, script_path])
                self.status_var.set("Launched Forward Basis Matrix Generator (6M vs 3M)")
            except Exception as e:
                messagebox.showerror("Error", f"Could not launch Forward Basis Matrix:\n{e}")
        else:
            messagebox.showerror("Error", 
                               f"Forward Basis Matrix not found at:\n{script_path}\n\n"
                               "Make sure forward_basis_matrix.py is in the irs_swap_app folder")
    
    def launch_relative_value(self):
        """Launch Swap Relative Value Analyzer as separate window"""
        import subprocess
        import sys
        
        # Get path to swap_relative_value.py
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                   'swap_relative_value.py')
        
        if os.path.exists(script_path):
            try:
                # Launch as separate process
                subprocess.Popen([sys.executable, script_path])
                self.status_var.set("Launched Swap Relative Value Analyzer")
            except Exception as e:
                messagebox.showerror("Error", f"Could not launch Relative Value Analyzer:\n{e}")
        else:
            messagebox.showerror("Error", 
                               f"Relative Value Analyzer not found at:\n{script_path}\n\n"
                               "Make sure swap_relative_value.py is in the irs_swap_app folder")
    
    def launch_forward_basis_matrix(self):
        """Launch Forward Basis Matrix Generator as separate window"""
        import subprocess
        import sys
        
        # Get path to forward_basis_matrix.py
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                   'forward_basis_matrix.py')
        
        if os.path.exists(script_path):
            try:
                # Launch as separate process
                subprocess.Popen([sys.executable, script_path])
                self.status_var.set("Launched Forward Basis Matrix Generator")
            except Exception as e:
                messagebox.showerror("Error", f"Could not launch Forward Basis Matrix:\n{e}")
        else:
            messagebox.showerror("Error", 
                               f"Forward Basis Matrix not found at:\n{script_path}\n\n"
                               "Make sure forward_basis_matrix.py is in the irs_swap_app folder")
    
    def build_zero_curve_from_database(self, valuation_date):
        """Build a zero curve dictionary from database swap rates"""
        session = self.db_manager.Session()
        try:
            from database_models import SwapRate
            
            # Get rates close to valuation date (within 7 days)
            from datetime import timedelta
            start_date = valuation_date - timedelta(days=7)
            end_date = valuation_date + timedelta(days=7)
            
            # Query rates
            rates = session.query(SwapRate).filter(
                SwapRate.date >= start_date,
                SwapRate.date <= end_date
            ).order_by(SwapRate.date.desc()).all()
            
            if not rates:
                return None
            
            # Take most recent date
            latest_date = rates[0].date
            rates_for_date = [r for r in rates if r.date == latest_date]
            
            # Build curve dictionary (tenor in months -> zero rate as decimal)
            curve = {}
            tenor_to_months = {
                '1M': 1, '3M': 3, '6M': 6, '9M': 9,
                '1Y': 12, '18M': 18, '2Y': 24, '3Y': 36,
                '4Y': 48, '5Y': 60, '7Y': 84, '10Y': 120,
                '12Y': 144, '15Y': 180, '20Y': 240, '30Y': 360
            }
            
            for rate in rates_for_date:
                if rate.tenor in tenor_to_months:
                    curve[tenor_to_months[rate.tenor]] = rate.rate
            
            return curve if curve else None
            
        finally:
            session.close()
    
    def export_to_csv(self):
        """Export data to CSV file"""
        # Get filename
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export to CSV"
        )
        
        if not filename:
            return
        
        try:
            # Get current view data
            session = self.db_manager.Session()
            from database_models import SwapRate
            
            # Build query with current filters
            query = session.query(SwapRate)
            
            if self.currency_var.get() != "All":
                query = query.filter(SwapRate.currency == self.currency_var.get())
            
            if self.tenor_var.get() != "All":
                query = query.filter(SwapRate.tenor == self.tenor_var.get())
            
            if self.start_date_var.get():
                start_date = datetime.strptime(self.start_date_var.get(), '%Y-%m-%d').date()
                query = query.filter(SwapRate.date >= start_date)
            
            if self.end_date_var.get():
                end_date = datetime.strptime(self.end_date_var.get(), '%Y-%m-%d').date()
                query = query.filter(SwapRate.date <= end_date)
            
            rates = query.all()
            
            # Write to CSV
            import csv
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Date', 'Currency', 'Tenor', 'Rate', 'Updated'])
                
                for rate in rates:
                    writer.writerow([
                        rate.date.strftime('%Y-%m-%d'),
                        rate.currency,
                        rate.tenor,
                        f"{rate.rate:.4f}",
                        rate.updated_at.strftime('%Y-%m-%d %H:%M:%S') if rate.updated_at else ''
                    ])
            
            session.close()
            messagebox.showinfo("Export Successful", 
                              f"Exported {len(rates)} records to:\n{filename}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Error exporting to CSV:\n{str(e)}")
    
    def export_to_json(self):
        """Export data to JSON file"""
        # Get filename
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Export to JSON"
        )
        
        if not filename:
            return
        
        try:
            # Get current view data
            session = self.db_manager.Session()
            from database_models import SwapRate
            
            # Build query with current filters
            query = session.query(SwapRate)
            
            if self.currency_var.get() != "All":
                query = query.filter(SwapRate.currency == self.currency_var.get())
            
            if self.tenor_var.get() != "All":
                query = query.filter(SwapRate.tenor == self.tenor_var.get())
            
            if self.start_date_var.get():
                start_date = datetime.strptime(self.start_date_var.get(), '%Y-%m-%d').date()
                query = query.filter(SwapRate.date >= start_date)
            
            if self.end_date_var.get():
                end_date = datetime.strptime(self.end_date_var.get(), '%Y-%m-%d').date()
                query = query.filter(SwapRate.date <= end_date)
            
            rates = query.all()
            
            # Convert to dictionary
            data = {
                'export_date': datetime.now().isoformat(),
                'record_count': len(rates),
                'rates': []
            }
            
            for rate in rates:
                data['rates'].append({
                    'date': rate.date.strftime('%Y-%m-%d'),
                    'currency': rate.currency,
                    'tenor': rate.tenor,
                    'rate': float(rate.rate),
                    'rate_percent': float(rate.rate),
                    'updated_at': rate.updated_at.isoformat() if rate.updated_at else None
                })
            
            # Write to JSON
            import json
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            
            session.close()
            messagebox.showinfo("Export Successful", 
                              f"Exported {len(rates)} records to:\n{filename}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Error exporting to JSON:\n{str(e)}")
    
    def apply_tenor_range_filter(self, min_years, max_years):
        """Apply tenor range filter (e.g., 0-2Y or 2Y+)"""
        try:
            # Import tenor utility
            import sys
            import os
            backend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend')
            if backend_path not in sys.path:
                sys.path.insert(0, backend_path)
            
            from tenor_utils import filter_tenors_by_range, tenor_to_months
            
            # Get current currency
            currency = self.currency_var.get()
            if currency == "All":
                messagebox.showinfo("Select Currency", 
                                  "Please select a specific currency first (USD, JPY, EUR, etc.)")
                return
            
            # Get all tenors for this currency
            all_tenors = self.db_manager.get_available_tenors(currency=currency)
            
            if not all_tenors:
                messagebox.showinfo("No Data", f"No tenors found for {currency}")
                return
            
            # Filter by range
            filtered_tenors = filter_tenors_by_range(all_tenors, min_years=min_years, max_years=max_years)
            
            if not filtered_tenors:
                messagebox.showinfo("No Tenors", 
                                  f"No tenors found in range {min_years}Y-{max_years if max_years else '∞'}Y")
                return
            
            # Update tenor dropdown
            self.tenor_combo['values'] = ['All'] + filtered_tenors
            self.tenor_combo.set('All')
            
            # Update info label
            if max_years:
                range_text = f"Showing: {min_years}Y - {max_years}Y ({len(filtered_tenors)} tenors)"
            else:
                range_text = f"Showing: {min_years}Y+ ({len(filtered_tenors)} tenors)"
            
            self.tenor_range_label.config(text=range_text)
            
            # Refresh data view
            self.apply_filters()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply tenor filter:\n{str(e)}")
    
    def clear_tenor_range_filter(self):
        """Clear tenor range filter and show all tenors"""
        try:
            currency = self.currency_var.get()
            
            # Reset to all tenors
            if currency != "All":
                all_tenors = self.db_manager.get_available_tenors(currency=currency)
                self.tenor_combo['values'] = ['All'] + all_tenors
            else:
                self.update_tenor_list()
            
            self.tenor_combo.set('All')
            
            # Clear info label
            self.tenor_range_label.config(text="")
            
            # Refresh data view
            self.apply_filters()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear filter:\n{str(e)}")
    
    def update_benchmark_rate_type_list(self):
        """Update benchmark rate type dropdown"""
        currency = self.benchmark_currency_var.get()
        if currency and currency != "All":
            types = self.db_manager.get_benchmark_rate_types(currency)
        else:
            types = self.db_manager.get_benchmark_rate_types()
        self.benchmark_rate_type_combo['values'] = ["All"] + types
    
    def apply_benchmark_filters(self):
        """Apply benchmark filters"""
        currency = None if self.benchmark_currency_var.get() == "All" else self.benchmark_currency_var.get()
        rate_type = None if self.benchmark_rate_type_var.get() == "All" else self.benchmark_rate_type_var.get()
        
        start_date = None
        if self.benchmark_start_date_var.get():
            try:
                start_date = datetime.strptime(self.benchmark_start_date_var.get(), '%Y-%m-%d').date()
            except:
                messagebox.showerror("Error", "Invalid start date format. Use YYYY-MM-DD")
                return
        
        end_date = None
        if self.benchmark_end_date_var.get():
            try:
                end_date = datetime.strptime(self.benchmark_end_date_var.get(), '%Y-%m-%d').date()
            except:
                messagebox.showerror("Error", "Invalid end date format. Use YYYY-MM-DD")
                return
        
        self.refresh_benchmark_data(currency, rate_type, start_date, end_date)
    
    def clear_benchmark_filters(self):
        """Clear benchmark filters"""
        self.benchmark_currency_var.set("All")
        self.benchmark_rate_type_var.set("All")
        self.benchmark_start_date_var.set("")
        self.benchmark_end_date_var.set("")
        self.refresh_benchmark_data()
    
    def refresh_benchmark_data(self, currency=None, rate_type=None, start_date=None, end_date=None):
        """Refresh benchmark data"""
        for item in self.benchmark_tree.get_children():
            self.benchmark_tree.delete(item)
        
        rates = self.db_manager.get_benchmark_rates(currency=currency, rate_type=rate_type,
                                                    start_date=start_date, end_date=end_date, limit=1000)
        
        for i, rate in enumerate(rates):
            tags = ('evenrow',) if i % 2 == 0 else ('oddrow',)
            date_str = rate[0] if isinstance(rate[0], str) else rate[0].strftime('%Y-%m-%d')
            self.benchmark_tree.insert('', tk.END, values=(
                date_str, rate[1], rate[2], f"{rate[3] * 100:.4f}"
            ), tags=tags)
        
        self.status_var.set(f"Showing {len(rates)} benchmark rates")
    
    def update_ois_rate_type_list(self):
        """Update OIS rate type dropdown"""
        currency = self.ois_currency_var.get()
        if currency and currency != "All":
            types = self.db_manager.get_ois_rate_types(currency)
        else:
            types = self.db_manager.get_ois_rate_types()
        self.ois_rate_type_combo['values'] = ["All"] + types
    
    def apply_ois_filters(self):
        """Apply OIS filters"""
        currency = None if self.ois_currency_var.get() == "All" else self.ois_currency_var.get()
        rate_type = None if self.ois_rate_type_var.get() == "All" else self.ois_rate_type_var.get()
        
        start_date = None
        if self.ois_start_date_var.get():
            try:
                start_date = datetime.strptime(self.ois_start_date_var.get(), '%Y-%m-%d').date()
            except:
                messagebox.showerror("Error", "Invalid start date format. Use YYYY-MM-DD")
                return
        
        end_date = None
        if self.ois_end_date_var.get():
            try:
                end_date = datetime.strptime(self.ois_end_date_var.get(), '%Y-%m-%d').date()
            except:
                messagebox.showerror("Error", "Invalid end date format. Use YYYY-MM-DD")
                return
        
        self.refresh_ois_data(currency, rate_type, start_date, end_date)
    
    def clear_ois_filters(self):
        """Clear OIS filters"""
        self.ois_currency_var.set("All")
        self.ois_rate_type_var.set("All")
        self.ois_start_date_var.set("")
        self.ois_end_date_var.set("")
        self.refresh_ois_data()
    
    def refresh_ois_data(self, currency=None, rate_type=None, start_date=None, end_date=None):
        """Refresh OIS data"""
        for item in self.ois_tree.get_children():
            self.ois_tree.delete(item)
        
        rates = self.db_manager.get_ois_rates(currency=currency, rate_type=rate_type,
                                             start_date=start_date, end_date=end_date, limit=1000)
        
        for i, rate in enumerate(rates):
            tags = ('evenrow',) if i % 2 == 0 else ('oddrow',)
            date_str = rate[0] if isinstance(rate[0], str) else rate[0].strftime('%Y-%m-%d')
            self.ois_tree.insert('', tk.END, values=(
                date_str, rate[1], rate[2], f"{rate[3] * 100:.4f}"
            ), tags=tags)
        
        self.status_var.set(f"Showing {len(rates)} OIS rates")


    def refresh_current_benchmark_view(self):
        """Refresh whichever benchmark view is currently active"""
        if self.benchmark_view_mode == 'pivot':
            self.refresh_benchmark_pivot_view()
        else:
            self.refresh_benchmark_data()
    
    def toggle_benchmark_view(self):
        """Toggle benchmark view"""
        self.benchmark_view_mode = 'pivot' if self.benchmark_view_mode == 'standard' else 'standard'
        if self.benchmark_view_mode == 'pivot':
            self.refresh_benchmark_pivot_view()
        else:
            self.refresh_benchmark_data()
        self.status_var.set(f"Benchmark: {'Table' if self.benchmark_view_mode == 'pivot' else 'List'} View")
    
    def refresh_benchmark_pivot_view(self):
        """Pivot table for benchmarks"""
        for item in self.benchmark_tree.get_children():
            self.benchmark_tree.delete(item)
        columns = ['Date','Cur','O/N Cash Rate','1M','2M','3M','4M','5M','6M']
        self.benchmark_tree.configure(columns=columns)
        self.benchmark_tree.column('#0', width=0, stretch=False)
        for i, col in enumerate(['Date','Cur','O/N Cash Rate','1M','2M','3M','4M','5M','6M']):
            self.benchmark_tree.heading(col, text=col)
            self.benchmark_tree.column(col, width=100 if col=='Date' else (50 if col=='Cur' else 80), anchor='center')
        import sqlite3, os
        from collections import defaultdict
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'swap_rates.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get currency filter
        currency_filter = self.benchmark_currency_var.get()
        
        # Build WHERE clause with currency filter
        # CRITICAL: Exclude OIS rates (AONIA, SOFR, SONIA, ESTR, CORRA, OCR)
        # Only get true benchmark rates: BBSW, BKBM, and central bank rates: RBA, RBNZ
        sql = """SELECT date, currency, tenor, rate FROM swap_rates
                 WHERE tenor IN ('1M','2M','3M','4M','5M','6M','1D','ON')
                 AND (floating_rate LIKE '%BBSW' OR floating_rate LIKE '%BKBM' 
                      OR floating_rate IN ('RBA','RBNZ'))
                 AND floating_rate NOT IN ('AONIA','SOFR','SONIA','ESTR','CORRA','OCR')"""
        
        if currency_filter != "All":
            sql += f" AND currency = '{currency_filter}'"
        
        sql += " ORDER BY date DESC, currency"
        
        cursor.execute(sql)
        rows = cursor.fetchall()
        conn.close()
        pivot_data = defaultdict(lambda: defaultdict(lambda: ''))
        for row in rows:
            date, currency, tenor, rate = row
            pivot_data[(date, currency)]['O/N Cash Rate' if tenor in ['1D','ON'] else tenor] = f"{rate * 100:.4f}"
        for i, ((date, currency), values) in enumerate(sorted(pivot_data.items(), reverse=True)):
            row_values = [date, currency] + [values.get(c, '') for c in ['O/N Cash Rate','1M','2M','3M','4M','5M','6M']]
            self.benchmark_tree.insert('', 'end', values=row_values, tags=('evenrow' if i%2==0 else 'oddrow',))
        self.benchmark_tree.tag_configure('evenrow', background=self.colors['bg_card'])
        self.benchmark_tree.tag_configure('oddrow', background=self.colors['table_alt'])
        self.status_var.set(f"Benchmark: {len(pivot_data)} dates")
    
    def toggle_ois_view(self):
        """Toggle OIS view"""
        self.ois_view_mode = 'pivot' if self.ois_view_mode == 'standard' else 'standard'
        if self.ois_view_mode == 'pivot':
            self.refresh_ois_pivot_view()
        else:
            self.refresh_ois_standard_view()
        self.status_var.set(f"OIS: {'Table' if self.ois_view_mode == 'pivot' else 'List'} View")
    
    def refresh_ois_pivot_view(self):
        """Pivot table for OIS - All tenors"""
        for item in self.ois_tree.get_children():
            self.ois_tree.delete(item)
        
        # All tenors from short to long
        all_tenors = ['1W','1M','2M','3M','6M','9M','1Y','18M','2Y','3Y','4Y','5Y','7Y','10Y','12Y','15Y','20Y','30Y']
        columns = ['Date', 'Cur'] + all_tenors
        
        self.ois_tree.configure(columns=columns)
        self.ois_tree.column('#0', width=0, stretch=False)
        
        for col in ['Date','Cur'] + all_tenors:
            self.ois_tree.heading(col, text=col)
            self.ois_tree.column(col, width=100 if col=='Date' else (50 if col=='Cur' else 65), anchor='center')
        
        import sqlite3, os
        from collections import defaultdict
        
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'swap_rates.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get currency filter
        currency_filter = self.ois_currency_var.get()
        
        # Build WHERE clause with currency filter
        sql = """SELECT date, currency, tenor, rate FROM swap_rates
                 WHERE floating_rate IN ('AONIA','OCR','SOFR','SONIA','ESTR','CORRA')
                 AND tenor NOT IN ('1D','ON')"""
        
        if currency_filter != "All":
            sql += f" AND currency = '{currency_filter}'"
        
        sql += " ORDER BY date DESC, currency"
        
        cursor.execute(sql)
        rows = cursor.fetchall()
        conn.close()
        
        pivot_data = defaultdict(lambda: defaultdict(lambda: ''))
        for row in rows:
            date, currency, tenor, rate = row
            if tenor in all_tenors:
                pivot_data[(date, currency)][tenor] = f"{rate * 100:.4f}"
        
        for i, ((date, currency), values) in enumerate(sorted(pivot_data.items(), reverse=True)[:100]):
            row_values = [date, currency] + [values.get(t, '') for t in all_tenors]
            self.ois_tree.insert('', 'end', values=row_values, tags=('evenrow' if i%2==0 else 'oddrow',))
        
        self.ois_tree.tag_configure('evenrow', background=self.colors['bg_card'])
        self.ois_tree.tag_configure('oddrow', background=self.colors['table_alt'])
        self.status_var.set(f"OIS: {len(pivot_data)} dates (All Tenors 1W-30Y)")
    
    
    def refresh_ois_standard_view(self):
        """Standard OIS view"""
        for item in self.ois_tree.get_children():
            self.ois_tree.delete(item)
        columns = ('Date', 'Currency', 'Rate Type', 'Rate')
        self.ois_tree.configure(columns=columns)
        self.ois_tree.column('#0', width=0, stretch=False)
        for col in columns:
            self.ois_tree.heading(col, text=col)
        self.ois_tree.column('Date', width=130, anchor='center')
        self.ois_tree.column('Currency', width=110, anchor='center')
        self.ois_tree.column('Rate Type', width=250, anchor='center')
        self.ois_tree.column('Rate', width=150, anchor='center')
        import sqlite3, os
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'swap_rates.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""SELECT date, currency, tenor, floating_rate, rate FROM swap_rates
                         WHERE floating_rate IN ('AONIA','OCR','SOFR','SONIA','ESTR','CORRA')
                         AND tenor NOT IN ('1D','ON') ORDER BY date DESC LIMIT 1000""")
        rows = cursor.fetchall()
        conn.close()
        for i, row in enumerate(rows):
            date, currency, tenor, floating_rate, rate = row
            self.ois_tree.insert('', 'end', values=(date, currency, f"{floating_rate} {tenor}", f"{rate * 100:.4f}"), 
                               tags=('evenrow' if i%2==0 else 'oddrow',))
        self.ois_tree.tag_configure('evenrow', background=self.colors['bg_card'])
        self.ois_tree.tag_configure('oddrow', background=self.colors['table_alt'])
        self.status_var.set(f"OIS: {len(rows)} records")
    
    def toggle_ois_short_view(self):
        """Toggle short term OIS view"""
        self.ois_short_view_mode = 'pivot' if self.ois_short_view_mode == 'standard' else 'standard'
        if self.ois_short_view_mode == 'pivot':
            self.refresh_ois_short_pivot_view()
        else:
            self.refresh_ois_short_standard_view()
        self.status_var.set(f"Short OIS: {'Table' if self.ois_short_view_mode == 'pivot' else 'List'} View")
    
    def refresh_ois_short_pivot_view(self):
        """Pivot table for short term OIS (0-2Y): 1W, 2W, 3W, 1M, 2M, 3M, 6M, 9M, 1Y, 18M, 2Y"""
        for item in self.ois_tree_short.get_children():
            self.ois_tree_short.delete(item)
        
        short_tenors = ['1W','2W','3W','1M','2M','3M','6M','9M','1Y','18M','2Y']
        columns = ['Date','Cur'] + short_tenors
        
        self.ois_tree_short.configure(columns=columns)
        self.ois_tree_short.column('#0', width=0, stretch=False)
        
        for col in ['Date','Cur'] + short_tenors:
            self.ois_tree_short.heading(col, text=col)
            self.ois_tree_short.column(col, width=100 if col=='Date' else (50 if col=='Cur' else 70), anchor='center')
        
        import sqlite3, os
        from collections import defaultdict
        
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'swap_rates.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        currency_filter = self.ois_currency_var.get()
        
        sql = """SELECT date, currency, tenor, rate FROM swap_rates
                 WHERE floating_rate IN ('AONIA','OCR','SOFR','SONIA','ESTR','CORRA')
                 AND tenor IN ('1W','2W','3W','1M','2M','3M','6M','9M','1Y','18M','2Y')"""
        
        if currency_filter != "All":
            sql += f" AND currency = '{currency_filter}'"
        
        sql += " ORDER BY date DESC, currency"
        
        cursor.execute(sql)
        rows = cursor.fetchall()
        conn.close()
        
        pivot_data = defaultdict(lambda: defaultdict(lambda: ''))
        for row in rows:
            date, currency, tenor, rate = row
            pivot_data[(date, currency)][tenor] = f"{rate * 100:.4f}"
        
        for i, ((date, currency), values) in enumerate(sorted(pivot_data.items(), reverse=True)[:100]):
            row_values = [date, currency] + [values.get(t, '') for t in short_tenors]
            self.ois_tree_short.insert('', 'end', values=row_values, tags=('evenrow' if i%2==0 else 'oddrow',))
        
        self.ois_tree_short.tag_configure('evenrow', background=self.colors['bg_card'])
        self.ois_tree_short.tag_configure('oddrow', background=self.colors['table_alt'])
        self.status_var.set(f"Short OIS: {len(pivot_data)} dates (0-2Y)")
    
    def refresh_ois_short_standard_view(self):
        """Standard list view for short term OIS"""
        for item in self.ois_tree_short.get_children():
            self.ois_tree_short.delete(item)
        
        columns = ('Date', 'Currency', 'Rate Type', 'Rate')
        self.ois_tree_short.configure(columns=columns)
        self.ois_tree_short.column('#0', width=0, stretch=False)
        
        for col in columns:
            self.ois_tree_short.heading(col, text=f"{'📅 ' if col=='Date' else '💱 ' if col=='Currency' else '📊 ' if col=='Rate Type' else '📈 '}{col}{'(%)' if col=='Rate' else ''}")
        
        self.ois_tree_short.column('Date', width=130, anchor='center')
        self.ois_tree_short.column('Currency', width=110, anchor='center')
        self.ois_tree_short.column('Rate Type', width=250, anchor='center')
        self.ois_tree_short.column('Rate', width=150, anchor='center')
        
        import sqlite3, os
        
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'swap_rates.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        currency_filter = self.ois_currency_var.get()
        
        sql = """SELECT date, currency, tenor, floating_rate, rate FROM swap_rates
                 WHERE floating_rate IN ('AONIA','OCR','SOFR','SONIA','ESTR','CORRA')
                 AND tenor IN ('1W','2W','3W','1M','2M','3M','6M','9M','1Y','18M','2Y')"""
        
        if currency_filter != "All":
            sql += f" AND currency = '{currency_filter}'"
        
        sql += " ORDER BY date DESC LIMIT 1000"
        
        cursor.execute(sql)
        rows = cursor.fetchall()
        conn.close()
        
        for i, row in enumerate(rows):
            date, currency, tenor, floating_rate, rate = row
            self.ois_tree_short.insert('', 'end', values=(date, currency, f"{floating_rate} {tenor}", f"{rate * 100:.4f}"), 
                                      tags=('evenrow' if i%2==0 else 'oddrow',))
        
        self.ois_tree_short.tag_configure('evenrow', background=self.colors['bg_card'])
        self.ois_tree_short.tag_configure('oddrow', background=self.colors['table_alt'])
        self.status_var.set(f"Short OIS: {len(rows)} records")
    
    def toggle_ois_medium_view(self):
        """Toggle medium term OIS view"""
        self.ois_medium_view_mode = 'pivot' if self.ois_medium_view_mode == 'standard' else 'standard'
        if self.ois_medium_view_mode == 'pivot':
            self.refresh_ois_medium_pivot_view()
        else:
            self.refresh_ois_medium_standard_view()
        self.status_var.set(f"Medium OIS: {'Table' if self.ois_medium_view_mode == 'pivot' else 'List'} View")
    
    def refresh_ois_medium_pivot_view(self):
        """Pivot table for medium term OIS (3Y+)"""
        for item in self.ois_tree_medium.get_children():
            self.ois_tree_medium.delete(item)
        
        medium_tenors = ['3Y','4Y','5Y','7Y','10Y','12Y','15Y','20Y','30Y','35Y','40Y']
        columns = ['Date','Cur'] + medium_tenors
        
        self.ois_tree_medium.configure(columns=columns)
        self.ois_tree_medium.column('#0', width=0, stretch=False)
        
        for col in ['Date','Cur'] + medium_tenors:
            self.ois_tree_medium.heading(col, text=col)
            self.ois_tree_medium.column(col, width=100 if col=='Date' else (50 if col=='Cur' else 80), anchor='center')
        
        import sqlite3, os
        from collections import defaultdict
        
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'swap_rates.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        currency_filter = self.ois_currency_var.get()
        
        sql = """SELECT date, currency, tenor, rate FROM swap_rates
                 WHERE floating_rate IN ('AONIA','OCR','SOFR','SONIA','ESTR','CORRA')
                 AND tenor IN ('3Y','4Y','5Y','7Y','10Y','12Y','15Y','20Y','30Y','35Y','40Y')"""
        
        if currency_filter != "All":
            sql += f" AND currency = '{currency_filter}'"
        
        sql += " ORDER BY date DESC, currency"
        
        cursor.execute(sql)
        rows = cursor.fetchall()
        conn.close()
        
        pivot_data = defaultdict(lambda: defaultdict(lambda: ''))
        for row in rows:
            date, currency, tenor, rate = row
            pivot_data[(date, currency)][tenor] = f"{rate * 100:.4f}"
        
        for i, ((date, currency), values) in enumerate(sorted(pivot_data.items(), reverse=True)[:100]):
            row_values = [date, currency] + [values.get(t, '') for t in medium_tenors]
            self.ois_tree_medium.insert('', 'end', values=row_values, tags=('evenrow' if i%2==0 else 'oddrow',))
        
        self.ois_tree_medium.tag_configure('evenrow', background=self.colors['bg_card'])
        self.ois_tree_medium.tag_configure('oddrow', background=self.colors['table_alt'])
        self.status_var.set(f"Medium OIS: {len(pivot_data)} dates (3Y+)")
    
    def refresh_ois_medium_standard_view(self):
        """Standard list view for medium term OIS"""
        for item in self.ois_tree_medium.get_children():
            self.ois_tree_medium.delete(item)
        
        columns = ('Date', 'Currency', 'Rate Type', 'Rate')
        self.ois_tree_medium.configure(columns=columns)
        self.ois_tree_medium.column('#0', width=0, stretch=False)
        
        for col in columns:
            self.ois_tree_medium.heading(col, text=f"{'📅 ' if col=='Date' else '💱 ' if col=='Currency' else '📊 ' if col=='Rate Type' else '📈 '}{col}{'(%)' if col=='Rate' else ''}")
        
        self.ois_tree_medium.column('Date', width=130, anchor='center')
        self.ois_tree_medium.column('Currency', width=110, anchor='center')
        self.ois_tree_medium.column('Rate Type', width=250, anchor='center')
        self.ois_tree_medium.column('Rate', width=150, anchor='center')
        
        import sqlite3, os
        
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'swap_rates.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        currency_filter = self.ois_currency_var.get()
        
        sql = """SELECT date, currency, tenor, floating_rate, rate FROM swap_rates
                 WHERE floating_rate IN ('AONIA','OCR','SOFR','SONIA','ESTR','CORRA')
                 AND tenor IN ('3Y','4Y','5Y','7Y','10Y','12Y','15Y','20Y','30Y','35Y','40Y')"""
        
        if currency_filter != "All":
            sql += f" AND currency = '{currency_filter}'"
        
        sql += " ORDER BY date DESC LIMIT 1000"
        
        cursor.execute(sql)
        rows = cursor.fetchall()
        conn.close()
        
        for i, row in enumerate(rows):
            date, currency, tenor, floating_rate, rate = row
            self.ois_tree_medium.insert('', 'end', values=(date, currency, f"{floating_rate} {tenor}", f"{rate * 100:.4f}"), 
                                       tags=('evenrow' if i%2==0 else 'oddrow',))
        
        self.ois_tree_medium.tag_configure('evenrow', background=self.colors['bg_card'])
        self.ois_tree_medium.tag_configure('oddrow', background=self.colors['table_alt'])
        self.status_var.set(f"Medium OIS: {len(rows)} records")

def main():
    """Main entry point"""
    root = tk.Tk()
    app = SwapRateApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == '__main__':
    main()
