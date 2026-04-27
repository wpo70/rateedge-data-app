"""
RateEdge Data Portal - Streamlit Version
Pulls AUD, USD, NZD swap rates from Supabase
Dark theme, email OTP auth with SSL fix
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import psycopg2
import requests
import numpy as np

# Page config - MUST BE FIRST
st.set_page_config(
    page_title="RateEdge Data",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# AUTHENTICATION
# ============================================================================

AUTH_URL = "https://rateedge-auth.onrender.com/api/auth"
SITE_ID = "data"

def request_otp(email: str):
    """Request OTP code via email"""
    try:
        resp = requests.post(
            f"{AUTH_URL}/request-otp", 
            json={"email": email, "site": SITE_ID}, 
            timeout=10
        )
        return resp.status_code, resp.json()
    except Exception as e:
        return 500, {"error": str(e)}

def verify_otp(email: str, code: str):
    """Verify OTP code"""
    try:
        resp = requests.post(
            f"{AUTH_URL}/verify-otp", 
            json={"email": email, "site": SITE_ID, "code": code}, 
            timeout=10
        )
        return resp.status_code, resp.json()
    except Exception as e:
        return 500, {"error": str(e)}

def render_logo():
    """Render RateEdge logo"""
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0 1rem 0;">
        <div style="font-size: 2.5rem; font-weight: 700; letter-spacing: -0.02em;">
            <span style="color: #1e3a5f;">Rate</span><span style="color: #ef4444;">Edge</span>
        </div>
        <div style="color: #64748b; font-size: 0.9rem; margin-top: 0.25rem;">
            AUD • NZD • USD Interest Rate Data
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_sidebar_logo():
    """Render logo for sidebar"""
    st.markdown("""
    <div style="text-align: center; padding: 0.5rem 0;">
        <div style="font-size: 1.3rem; font-weight: 700;">
            <span style="color: #1e3a5f;">Rate</span><span style="color: #ef4444;">Edge</span>
        </div>
        <div style="color: #64748b; font-size: 0.7rem;">DATA PORTAL</div>
    </div>
    """, unsafe_allow_html=True)

def render_login():
    """Render login page"""
    render_logo()
    
    st.markdown("---")
    st.markdown("### 🔐 Login with Email")
    
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        if 'auth_step' not in st.session_state:
            st.session_state.auth_step = 'email'
        
        if st.session_state.auth_step == 'email':
            with st.form("email_form"):
                email = st.text_input("Email address", key="login_email", placeholder="your.email@company.com")
                submitted = st.form_submit_button("📧 Send Verification Code", use_container_width=True, type="primary")
            if submitted:
                if email and '@' in email:
                    status, data = request_otp(email)
                    if status == 200:
                        st.session_state.auth_step = 'otp'
                        st.session_state.auth_email = email
                        st.success("✅ Code sent!")
                        st.rerun()
                    elif status == 403 and data.get("error") == "access_pending":
                        st.info(data.get("message", "Access request submitted."))
                    else:
                        st.error(f"❌ {data.get('error', 'Failed to send code')}")
                else:
                    st.error("❌ Please enter a valid email")
        
        elif st.session_state.auth_step == 'otp':
            email = st.session_state.get('auth_email', '')
            st.info(f"📧 Code sent to: **{email}**")
            with st.form("otp_form"):
                code = st.text_input("Enter 6-digit code", key="otp_code", max_chars=6)
                submitted = st.form_submit_button("✅ Verify", use_container_width=True, type="primary")
            if submitted:
                if code and len(code) == 6:
                    status, data = verify_otp(email, code)
                    if status == 200:
                        st.session_state["authenticated"] = True
                        st.session_state["username"] = email
                        st.session_state.auth_step = 'email'
                        st.success("✅ Login successful!")
                        st.rerun()
                    else:
                        st.error(f"❌ {data.get('error', 'Invalid code')}")
                else:
                    st.error("❌ Please enter the 6-digit code")
            
            if st.button("← Back", key="back_btn"):
                st.session_state.auth_step = 'email'
                st.rerun()
    
    st.markdown("---")
    st.caption("Contact wpo@rateedge.au to request access")

# ============================================================================
# DATABASE CONNECTION
# ============================================================================

def get_db_url():
    """Get Supabase database URL"""
    try:
        return st.secrets["DATABASE_URL"]
    except:
        return "postgresql://postgres.oxwbyotzdqccaajyaqhn:RateEdge2026!@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"

@st.cache_resource
def get_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(get_db_url())
        return conn
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None

def run_query(query, params=None):
    """Run a query and return results as DataFrame"""
    conn = get_connection()
    if not conn:
        return pd.DataFrame()
    try:
        df = pd.read_sql(query, conn, params=params)
        return df
    except Exception as e:
        st.error(f"Query failed: {e}")
        return pd.DataFrame()

# ============================================================================
# DATA FETCHING
# ============================================================================

@st.cache_data(ttl=300)
def get_swap_rates(currency: str = None, days: int = 30):
    """Fetch swap rates from Supabase"""
    query = """
        SELECT date, currency, tenor, rate, floating_rate
        FROM swap_rates
        WHERE date >= CURRENT_DATE - INTERVAL '%s days'
    """
    params = [days]
    
    if currency and currency != "All":
        query += " AND currency = %s"
        params.append(currency)
    
    query += " ORDER BY date DESC, currency, tenor"
    
    return run_query(query, params)

@st.cache_data(ttl=300)
def get_benchmark_rates(currency: str = None, days: int = 30):
    """Fetch benchmark rates (excluding basis swaps) from Supabase"""
    query = """
        SELECT date, currency, rate_type, rate
        FROM benchmark_rates
        WHERE date >= CURRENT_DATE - INTERVAL '%s days'
        AND rate_type NOT LIKE 'BASIS%%'
        AND rate_type NOT LIKE 'SOFR_FF_BASIS%%'
    """
    params = [days]
    
    if currency and currency != "All":
        query += " AND currency = %s"
        params.append(currency)
    
    query += " ORDER BY date DESC, currency, rate_type"
    
    return run_query(query, params)

@st.cache_data(ttl=300)
def get_basis_swaps(currency: str = None, days: int = 30):
    """Fetch basis swap rates from Supabase"""
    query = """
        SELECT date, currency, rate_type, rate
        FROM benchmark_rates
        WHERE date >= CURRENT_DATE - INTERVAL '%s days'
        AND (rate_type LIKE 'BASIS%%' OR rate_type LIKE 'SOFR_FF_BASIS%%')
    """
    params = [days]
    
    if currency and currency != "All":
        query += " AND currency = %s"
        params.append(currency)
    
    query += " ORDER BY date DESC, currency, rate_type"
    
    return run_query(query, params)

@st.cache_data(ttl=300)
def get_latest_rates(currency: str):
    """Get latest rates for a currency"""
    query = """
        SELECT DISTINCT ON (tenor, floating_rate) 
            date, currency, tenor, rate, floating_rate
        FROM swap_rates
        WHERE currency = %s
        ORDER BY tenor, floating_rate, date DESC
    """
    return run_query(query, [currency])

@st.cache_data(ttl=300)
def get_available_currencies():
    """Get list of available currencies from database"""
    query = "SELECT DISTINCT currency FROM swap_rates ORDER BY currency"
    df = run_query(query)
    if not df.empty:
        return df['currency'].tolist()
    return ["AUD", "NZD", "USD"]

@st.cache_data(ttl=300)
def get_rate_history(currency: str, tenor: str, floating_rate: str, days: int = 1825):
    """Get historical rates for charting - default 5 years"""
    query = """
        SELECT date, rate
        FROM swap_rates
        WHERE currency = %s AND tenor = %s AND floating_rate = %s
        AND date >= CURRENT_DATE - INTERVAL '%s days'
        ORDER BY date
    """
    return run_query(query, [currency, tenor, floating_rate, days])

# ============================================================================
# UI COMPONENTS
# ============================================================================

def render_rate_chart(currency: str, tenor: str, floating_rate: str, days: int = 1825):
    """Render historical rate chart - default 5 years"""
    df = get_rate_history(currency, tenor, floating_rate, days)
    
    if df.empty:
        st.info("No historical data available")
        return
    
    # Display name for floating rate
    display_name = floating_rate
    
    fig = px.line(
        df, x='date', y='rate',
        title=f"{currency} {tenor} {display_name} Rate History",
        labels={'date': 'Date', 'rate': 'Rate (%)'}
    )
    fig.update_layout(
        hovermode='x unified',
        xaxis_title="",
        yaxis_title="Rate (%)",
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

def render_curve(currency: str):
    """Render current swap curve"""
    df = get_latest_rates(currency)
    
    if df.empty:
        st.info(f"No curve data for {currency}")
        return
    
    # Get unique floating rates
    floating_rates = df['floating_rate'].unique()
    
    # Tenor ordering with proper labels
    tenor_order = ['1W', '1M', '2M', '3M', '4M', '5M', '6M', '9M', '1Y', '2Y', '3Y', '4Y', '5Y', 
                   '6Y', '7Y', '8Y', '9Y', '10Y', '12Y', '15Y', '20Y', '25Y', '30Y', '40Y', '50Y']
    
    # Filter to only include valid tenors (string format like 1M, 5Y etc)
    valid_tenors = [t for t in tenor_order]
    df_filtered = df[df['tenor'].str.upper().isin([t.upper() for t in tenor_order])].copy()
    
    if df_filtered.empty:
        st.warning(f"No standard tenor data for {currency}")
        return
    
    # Colors for lines - distinct and visible
    colors = ['#2563eb', '#10b981', '#ef4444', '#f59e0b', '#8b5cf6', '#ec4899']
    # Blue, Green, Red, Orange, Purple, Pink
    
    fig = go.Figure()
    
    # Collect all tenors used across all floating rates for x-axis ordering
    all_tenors_used = set()
    
    for idx, fr in enumerate(floating_rates):
        subset = df_filtered[df_filtered['floating_rate'] == fr].copy()
        
        if subset.empty:
            continue
        
        # Use original floating rate name
        display_name = fr
        
        # Sort by tenor order
        def get_tenor_order(t):
            t_upper = t.upper() if isinstance(t, str) else str(t).upper()
            if t_upper in [x.upper() for x in tenor_order]:
                return [x.upper() for x in tenor_order].index(t_upper)
            return 99
        
        subset['tenor_order'] = subset['tenor'].apply(get_tenor_order)
        subset = subset.sort_values('tenor_order')
        
        # Normalize tenor labels to uppercase
        subset['tenor_label'] = subset['tenor'].str.upper()
        all_tenors_used.update(subset['tenor_label'].tolist())
        
        fig.add_trace(go.Scatter(
            x=subset['tenor_label'],
            y=subset['rate'],
            mode='lines+markers',
            name=display_name,
            line=dict(color=colors[idx % len(colors)], width=2),
            marker=dict(size=6)
        ))
    
    # Create ordered category list for x-axis
    ordered_tenors = [t for t in tenor_order if t in all_tenors_used]
    
    fig.update_layout(
        title=f"{currency} Swap Curve (Latest)",
        xaxis_title="Tenor",
        yaxis_title="Rate (%)",
        hovermode='x unified',
        height=450,
        xaxis=dict(
            type='category',
            categoryorder='array',
            categoryarray=ordered_tenors
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# PAGES
# ============================================================================

def page_dashboard():
    """Dashboard page"""
    render_logo()
    
    # Get currencies from database
    currencies = get_available_currencies()
    
    # Summary metrics
    st.markdown("### 📊 Market Overview")
    
    cols = st.columns(len(currencies))
    
    for i, ccy in enumerate(currencies):
        with cols[i]:
            df = get_latest_rates(ccy)
            if not df.empty:
                # Get 5Y rate as headline
                rate_5y = df[df['tenor'].str.upper() == '5Y']
                if not rate_5y.empty:
                    rate = rate_5y.iloc[0]['rate']
                    st.metric(f"{ccy} 5Y", f"{rate:.3f}%")
                else:
                    st.metric(f"{ccy}", "No 5Y data")
            else:
                st.metric(f"{ccy}", "No data")
    
    st.markdown("---")
    
    # Curves
    st.markdown("### 📈 Swap Curves")
    
    tabs = st.tabs(currencies)
    
    for i, ccy in enumerate(currencies):
        with tabs[i]:
            render_curve(ccy)

def page_swap_rates():
    """Swap rates page"""
    st.header("📊 Swap Rates")
    
    # Get currencies from database
    db_currencies = get_available_currencies()
    currencies = ["All"] + db_currencies
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        currency = st.selectbox("Currency", currencies)
    with col2:
        days = st.selectbox("Period", [7, 14, 30, 60, 90, 180, 365, 730, 1825], index=4, 
                           format_func=lambda x: f"{x} days" if x < 365 else f"{x//365}Y")
    with col3:
        st.write("")  # Spacer
    
    # Fetch data
    df = get_swap_rates(currency if currency != "All" else None, days)
    
    if df.empty:
        st.warning("No swap rate data found")
        return
    
    # Summary
    st.info(f"Showing {len(df):,} records from last {days} days")
    
    # Pivot table view
    st.subheader("Latest Rates by Tenor")
    
    # Tenor ordering
    tenor_order = ['1W', '1M', '2M', '3M', '4M', '5M', '6M', '9M', '1Y', '2Y', '3Y', '4Y', '5Y', 
                   '6Y', '7Y', '8Y', '9Y', '10Y', '12Y', '15Y', '20Y', '25Y', '30Y', '40Y', '50Y']
    
    def sort_and_filter_pivot(df):
        """Sort pivot table by tenor order and filter out numeric tenors"""
        # Filter to only valid string tenors
        valid_tenors = [t for t in df.index if str(t).upper() in [x.upper() for x in tenor_order]]
        df_filtered = df.loc[valid_tenors].copy()
        
        # Sort by tenor order
        def get_order(t):
            t_upper = str(t).upper()
            if t_upper in [x.upper() for x in tenor_order]:
                return [x.upper() for x in tenor_order].index(t_upper)
            return 99
        
        df_filtered['_order'] = [get_order(t) for t in df_filtered.index]
        df_filtered = df_filtered.sort_values('_order').drop('_order', axis=1)
        
        # Uppercase the index labels
        df_filtered.index = [str(t).upper() for t in df_filtered.index]
        
        return df_filtered
    
    if currency != "All":
        latest = get_latest_rates(currency)
        if not latest.empty:
            # Filter to valid tenors only
            latest = latest[latest['tenor'].str.upper().isin([t.upper() for t in tenor_order])]
            latest['tenor'] = latest['tenor'].str.upper()
            
            pivot = latest.pivot_table(
                index='tenor', 
                columns='floating_rate', 
                values='rate',
                aggfunc='first'
            )
            pivot = sort_and_filter_pivot(pivot)
            st.dataframe(pivot, use_container_width=True)
    else:
        for ccy in db_currencies:
            with st.expander(f"🔹 {ccy}", expanded=True):
                latest = get_latest_rates(ccy)
                if not latest.empty:
                    # Filter to valid tenors only
                    latest = latest[latest['tenor'].str.upper().isin([t.upper() for t in tenor_order])]
                    latest['tenor'] = latest['tenor'].str.upper()
                    
                    pivot = latest.pivot_table(
                        index='tenor', 
                        columns='floating_rate', 
                        values='rate',
                        aggfunc='first'
                    )
                    pivot = sort_and_filter_pivot(pivot)
                    st.dataframe(pivot, use_container_width=True)
    
    # Raw data
    with st.expander("📋 Raw Data"):
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Download
    csv = df.to_csv(index=False)
    st.download_button(
        "📥 Download CSV",
        csv,
        f"swap_rates_{currency}_{datetime.now().strftime('%Y%m%d')}.csv",
        "text/csv"
    )

def page_benchmark_rates():
    """Benchmark rates & central banks page"""
    st.header("📈 Benchmarks & Central Banks")
    
    # Get currencies from database
    db_currencies = get_available_currencies()
    currencies = ["All"] + db_currencies
    
    # Filters
    col1, col2 = st.columns(2)
    
    with col1:
        currency = st.selectbox("Currency", currencies, key="bench_ccy")
    with col2:
        days = st.selectbox("Period", [7, 14, 30, 60, 90, 180, 365, 730, 1825], index=4, key="bench_days",
                           format_func=lambda x: f"{x} days" if x < 365 else f"{x//365}Y")
    
    # Fetch data
    df = get_benchmark_rates(currency if currency != "All" else None, days)
    
    if df.empty:
        st.warning("No benchmark rate data found")
        return
    
    # Column ordering per currency
    col_order = {
        'AUD': ['RBA_CASH', 'BBSW_1M', 'BBSW_2M', 'BBSW_3M', 'BBSW_4M', 'BBSW_5M', 'BBSW_6M', 'AONIA'],
        'NZD': ['RBNZ_OCR', 'OCR_1D', 'BKBM_1M', 'BKBM_2M', 'BKBM_3M'],
        'USD': ['FED_FUNDS_TARGET', 'FED_FUNDS_EFF', 'SOFR_1D', 'SOFR_COMP_1M', 'SOFR_COMP_3M', 'SOFR_COMP_6M', 'SOFR_COMP_12M', 
                'TERM_SOFR_1M', 'TERM_SOFR_3M', 'TERM_SOFR_6M', 'TERM_SOFR_12M']
    }
    
    def pivot_benchmarks(ccy_df, ccy):
        """Pivot benchmark data: dates as rows, rate_types as columns"""
        if ccy_df.empty:
            return pd.DataFrame()
        
        # Pivot
        pivot = ccy_df.pivot_table(index='date', columns='rate_type', values='rate', aggfunc='last')
        pivot = pivot.sort_index(ascending=False)
        
        # Reorder columns based on currency
        if ccy in col_order:
            ordered_cols = [c for c in col_order[ccy] if c in pivot.columns]
            other_cols = [c for c in pivot.columns if c not in col_order[ccy]]
            pivot = pivot[ordered_cols + other_cols]
        
        # Format column names (remove underscores for display)
        pivot.columns = [c.replace('_', ' ') for c in pivot.columns]
        
        # Reset index to show date as column
        pivot = pivot.reset_index()
        pivot['date'] = pd.to_datetime(pivot['date']).dt.strftime('%Y-%m-%d')
        
        return pivot
    
    # Group by currency
    if currency == "All":
        for ccy in sorted(df['currency'].unique()):
            with st.expander(f"🔹 {ccy} Benchmarks", expanded=True):
                ccy_df = df[df['currency'] == ccy]
                pivot = pivot_benchmarks(ccy_df, ccy)
                if not pivot.empty:
                    st.dataframe(pivot, use_container_width=True, hide_index=True)
                else:
                    st.info(f"No data for {ccy}")
    else:
        pivot = pivot_benchmarks(df, currency)
        if not pivot.empty:
            st.dataframe(pivot, use_container_width=True, hide_index=True)
        else:
            st.info("No data")
    
    # Download
    csv = df.to_csv(index=False)
    st.download_button(
        "📥 Download CSV",
        csv,
        f"benchmark_rates_{currency}_{datetime.now().strftime('%Y%m%d')}.csv",
        "text/csv"
    )

def page_basis_swaps():
    """Basis swaps page"""
    st.header("🔄 Basis Swaps")
    
    st.markdown("""
    **Available Basis Swaps:**
    - **AUD**: 3v1 (3M BBSW vs 1M OIS), 6v3 (6M BBSW vs 3M BBSW)
    - **USD**: SOFR vs Fed Funds
    """)
    
    # Get currencies that have basis data
    currencies = ["All", "AUD", "USD"]
    
    # Filters
    col1, col2 = st.columns(2)
    
    with col1:
        currency = st.selectbox("Currency", currencies, key="basis_ccy")
    with col2:
        days = st.selectbox("Period", [7, 14, 30, 60, 90, 180, 365, 730, 1825], index=4, key="basis_days",
                           format_func=lambda x: f"{x} days" if x < 365 else f"{x//365}Y")
    
    # Fetch data
    df = get_basis_swaps(currency if currency != "All" else None, days)
    
    if df.empty:
        st.warning("No basis swap data found")
        return
    
    # Summary
    st.info(f"Showing {len(df):,} records from last {days} days")
    
    # Tenor order for sorting
    tenor_order = ['3M', '6M', '1Y', '2Y', '3Y', '4Y', '5Y', '6Y', '7Y', '8Y', '9Y', '10Y', '12Y', '15Y', '20Y', '25Y', '30Y']
    
    # Parse basis type and tenor from rate_type
    def parse_basis(rate_type):
        # e.g., BASIS_3v1_5Y -> (3v1, 5Y), SOFR_FF_BASIS_5Y -> (SOFR-FF, 5Y)
        if rate_type.startswith('BASIS_'):
            parts = rate_type.replace('BASIS_', '').split('_')
            return parts[0], parts[1] if len(parts) > 1 else ''
        elif rate_type.startswith('SOFR_FF_BASIS_'):
            tenor = rate_type.replace('SOFR_FF_BASIS_', '')
            return 'SOFR-FF', tenor
        return rate_type, ''
    
    # Create pivot tables by currency and basis type
    if currency == "All":
        for ccy in ['AUD', 'USD']:
            ccy_df = df[df['currency'] == ccy].copy()
            if ccy_df.empty:
                continue
            
            with st.expander(f"🔹 {ccy}", expanded=True):
                # Get latest date
                latest_date = ccy_df['date'].max()
                latest = ccy_df[ccy_df['date'] == latest_date].copy()
                
                latest[['basis_type', 'tenor']] = latest['rate_type'].apply(lambda x: pd.Series(parse_basis(x)))
                
                # Pivot by basis type
                pivot = latest.pivot_table(
                    index='tenor',
                    columns='basis_type',
                    values='rate',
                    aggfunc='first'
                )
                
                # Sort by tenor
                def get_order(t):
                    if t in tenor_order:
                        return tenor_order.index(t)
                    return 99
                pivot['_order'] = [get_order(t) for t in pivot.index]
                pivot = pivot.sort_values('_order').drop('_order', axis=1)
                
                st.dataframe(pivot, use_container_width=True)
    else:
        ccy_df = df.copy()
        latest_date = ccy_df['date'].max()
        latest = ccy_df[ccy_df['date'] == latest_date].copy()
        
        latest[['basis_type', 'tenor']] = latest['rate_type'].apply(lambda x: pd.Series(parse_basis(x)))
        
        # Pivot by basis type
        pivot = latest.pivot_table(
            index='tenor',
            columns='basis_type',
            values='rate',
            aggfunc='first'
        )
        
        # Sort by tenor
        def get_order(t):
            if t in tenor_order:
                return tenor_order.index(t)
            return 99
        pivot['_order'] = [get_order(t) for t in pivot.index]
        pivot = pivot.sort_values('_order').drop('_order', axis=1)
        
        st.dataframe(pivot, use_container_width=True)
    
    # Raw data
    with st.expander("📋 Raw Data"):
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Download
    csv = df.to_csv(index=False)
    st.download_button(
        "📥 Download CSV",
        csv,
        f"basis_swaps_{currency}_{datetime.now().strftime('%Y%m%d')}.csv",
        "text/csv"
    )

def page_charts():
    """Historical charts page"""
    st.header("📉 Historical Charts")
    
    # Get currencies from database
    currencies = get_available_currencies()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        currency = st.selectbox("Currency", currencies, key="chart_ccy")
    
    # Get available tenors for this currency
    df = get_latest_rates(currency)
    tenors = df['tenor'].unique().tolist() if not df.empty else ['5Y']
    floating_rates = df['floating_rate'].unique().tolist() if not df.empty else ['3M BBSW']
    
    with col2:
        tenor = st.selectbox("Tenor", tenors, key="chart_tenor")
    with col3:
        floating_rate = st.selectbox("Floating Rate", floating_rates, key="chart_float")
    with col4:
        days = st.selectbox("Period", [30, 60, 90, 180, 365, 730, 1825], index=6, key="chart_days",
                           format_func=lambda x: f"{x} days" if x < 365 else f"{x//365}Y")
    
    render_rate_chart(currency, tenor, floating_rate, days)

def page_about():
    """About page"""
    st.header("ℹ️ About RateEdge Data")
    
    st.markdown("""
    ### RateEdge Data Portal
    
    This portal provides access to interest rate swap data for multiple currencies.
    Data is sourced from Bloomberg terminal exports, DTCC SDR trade data, and market data providers.
    
    #### Contact
    - Email: wpo@rateedge.au
    - Website: [rateedge.au](https://rateedge.au)
    
    ---
    
    © 2026 RateEdge (Aust.) ABN 95 601 693 766
    """)

# ============================================================================
# FORWARD MATRICES
# ============================================================================

def _tenor_to_years(t: str) -> float:
    """Convert tenor string to years: 1W→0.019, 3M→0.25, 1Y→1.0, etc."""
    t = t.strip().upper()
    if t.endswith("W"): return float(t[:-1]) / 52.0
    if t.endswith("M"): return float(t[:-1]) / 12.0
    if t.endswith("Y"): return float(t[:-1])
    return float(t)

@st.cache_data(ttl=300, show_spinner="Loading latest curve…")
def _get_par_curve(currency: str, floating_rate: str):
    """Get latest par rates as sorted (years, rates) arrays."""
    query = """
        SELECT DISTINCT ON (tenor) tenor, rate
        FROM swap_rates
        WHERE currency = %s AND floating_rate = %s
        ORDER BY tenor, date DESC
    """
    df = run_query(query, [currency, floating_rate])
    if df.empty:
        return None, None, None
    pairs = []
    for _, row in df.iterrows():
        try:
            y = _tenor_to_years(row["tenor"])
            pairs.append((y, float(row["rate"])))
        except:
            pass
    if not pairs:
        return None, None, None
    pairs.sort()
    xs = np.array([p[0] for p in pairs])
    ys = np.array([p[1] for p in pairs])
    # latest date
    dq = run_query("SELECT MAX(date) as d FROM swap_rates WHERE currency = %s AND floating_rate = %s", [currency, floating_rate])
    dt = str(dq.iloc[0]["d"]) if not dq.empty else "?"
    return xs, ys, dt

def _compute_fwd_matrix(par_x, par_y, expiries_y, tenors_y):
    """Compute forward matrix from par curve using fwd = (par(t2)*t2 - par(t1)*t1) / tenor.
    par_x/par_y: sorted arrays of maturities(years) and par rates(%)."""
    matrix = []
    for exp in expiries_y:
        row = []
        for tenor in tenors_y:
            t1 = exp
            t2 = exp + tenor
            r1 = float(np.interp(t1, par_x, par_y))
            r2 = float(np.interp(t2, par_x, par_y))
            fwd = (r2 * t2 - r1 * t1) / tenor
            row.append(round(fwd, 4))
        matrix.append(row)
    return matrix

def page_fwd_matrices():
    """Forward swap rate matrices with heatmaps."""
    st.header("📐 Forward Matrices")

    EXPIRY_LABELS = ["1W","1M","2M","3M","6M","9M","1Y","18M","2Y","3Y","4Y","5Y","6Y","7Y","8Y","9Y","10Y","12Y","15Y","20Y","25Y","30Y"]
    EXPIRY_YEARS  = [_tenor_to_years(e) for e in EXPIRY_LABELS]
    TENOR_LABELS  = ["1Y","2Y","3Y","4Y","5Y","7Y","10Y","12Y","15Y","20Y","25Y","30Y"]
    TENOR_YEARS   = [_tenor_to_years(t) for t in TENOR_LABELS]

    ccy = st.selectbox("Currency", ["AUD", "USD", "NZD"], key="fm_ccy")

    def _render_heatmap(matrix, title, exp_labels, tenor_labels, fmt=".2f", unit="%", colorscale="RdYlGn_r"):
        """Render a forward matrix as a heatmap + data table."""

        z = [[round(v, 4) if v is not None else 0 for v in row] for row in matrix]
        text = [[f"{v:{fmt}}" if v is not None else "" for v in row] for row in matrix]

        fig = go.Figure(data=go.Heatmap(
            z=z, x=tenor_labels, y=exp_labels,
            text=text, texttemplate="%{text}", textfont=dict(size=10),
            colorscale=colorscale, showscale=True,
            colorbar=dict(title=unit, titlefont=dict(color="#94a3b8"), tickfont=dict(color="#94a3b8")),
        ))
        fig.update_layout(
            title=title, height=max(500, len(exp_labels) * 26),
            margin=dict(l=60, r=20, t=50, b=40),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,23,42,0.8)",
            xaxis=dict(title="Tenor", color="#94a3b8", side="top"),
            yaxis=dict(title="Expiry", color="#94a3b8", autorange="reversed"),
            font=dict(color="#94a3b8", size=11),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Also show as dataframe
        with st.expander("📋 Data Table"):
            df = pd.DataFrame(matrix, index=exp_labels, columns=tenor_labels)
            st.dataframe(df.style.format(fmt), use_container_width=True)

    if ccy == "AUD":
        st.markdown("---")
        # Load all three AUD curves
        qq_x, qq_y, qq_dt = _get_par_curve("AUD", "3M BBSW")
        ss_x, ss_y, ss_dt = _get_par_curve("AUD", "6M BBSW")
        ois_x, ois_y, ois_dt = _get_par_curve("AUD", "AONIA")

        if ss_x is None:
            st.error("No 6M BBSW data found.")
            return

        st.caption(f"Curve date: {ss_dt}")

        _fm_tab = st.radio("Matrix", ["Market (Dual)", "Q/Q (3M BBSW)", "S/S (6M BBSW)",
                                       "6v3 Basis", "3v1 Basis"], horizontal=True, key="fm_aud_tab")

        if _fm_tab == "Market (Dual)":
            # ≤3Y tenor → QQ, ≥4Y → SS
            matrix = []
            for exp in EXPIRY_YEARS:
                row = []
                for i, tenor in enumerate(TENOR_YEARS):
                    if tenor <= 3.0 and qq_x is not None:
                        px, py = qq_x, qq_y
                    else:
                        px, py = ss_x, ss_y
                    t1 = exp; t2 = exp + tenor
                    r1 = float(np.interp(t1, px, py))
                    r2 = float(np.interp(t2, px, py))
                    row.append(round((r2*t2 - r1*t1) / tenor, 4))
                matrix.append(row)
            _render_heatmap(matrix, "AUD Forward Matrix — Market Convention (QQ ≤3Y, SS ≥4Y)",
                           EXPIRY_LABELS, TENOR_LABELS)

        elif _fm_tab == "Q/Q (3M BBSW)":
            if qq_x is None:
                st.error("No 3M BBSW data found.")
            else:
                matrix = _compute_fwd_matrix(qq_x, qq_y, EXPIRY_YEARS, TENOR_YEARS)
                _render_heatmap(matrix, "AUD Forward Matrix — Q/Q (3M BBSW)", EXPIRY_LABELS, TENOR_LABELS)

        elif _fm_tab == "S/S (6M BBSW)":
            matrix = _compute_fwd_matrix(ss_x, ss_y, EXPIRY_YEARS, TENOR_YEARS)
            _render_heatmap(matrix, "AUD Forward Matrix — S/S (6M BBSW)", EXPIRY_LABELS, TENOR_LABELS)

        elif _fm_tab == "6v3 Basis":
            if qq_x is None:
                st.error("No 3M BBSW data found.")
            else:
                m_ss = _compute_fwd_matrix(ss_x, ss_y, EXPIRY_YEARS, TENOR_YEARS)
                m_qq = _compute_fwd_matrix(qq_x, qq_y, EXPIRY_YEARS, TENOR_YEARS)
                basis = [[(s - q) * 100 for s, q in zip(sr, qr)] for sr, qr in zip(m_ss, m_qq)]
                _render_heatmap(basis, "AUD 6v3 Forward Basis (bp) — SS fwd − QQ fwd",
                               EXPIRY_LABELS, TENOR_LABELS, fmt=".1f", unit="bp", colorscale="RdYlBu_r")

        elif _fm_tab == "3v1 Basis":
            if qq_x is None or ois_x is None:
                st.error("Need both 3M BBSW and AONIA data.")
            else:
                m_qq = _compute_fwd_matrix(qq_x, qq_y, EXPIRY_YEARS, TENOR_YEARS)
                m_ois = _compute_fwd_matrix(ois_x, ois_y, EXPIRY_YEARS, TENOR_YEARS)
                basis = [[(q - o) * 100 for q, o in zip(qr, orow)] for qr, orow in zip(m_qq, m_ois)]
                _render_heatmap(basis, "AUD 3v1 Forward Basis (bp) — QQ fwd − AONIA fwd",
                               EXPIRY_LABELS, TENOR_LABELS, fmt=".1f", unit="bp", colorscale="RdYlBu_r")

    elif ccy == "USD":
        st.markdown("---")
        sofr_x, sofr_y, sofr_dt = _get_par_curve("USD", "SOFR")
        ff_x, ff_y, ff_dt = _get_par_curve("USD", "FEDFUNDS")

        if sofr_x is None:
            st.error("No USD SOFR data found.")
            return

        st.caption(f"Curve date: {sofr_dt}")

        _fm_tab = st.radio("Matrix", ["SOFR", "Fed Funds", "SOFR-FF Basis"], horizontal=True, key="fm_usd_tab")

        if _fm_tab == "SOFR":
            matrix = _compute_fwd_matrix(sofr_x, sofr_y, EXPIRY_YEARS, TENOR_YEARS)
            _render_heatmap(matrix, "USD Forward Matrix — SOFR", EXPIRY_LABELS, TENOR_LABELS)

        elif _fm_tab == "Fed Funds":
            if ff_x is None:
                st.error("No FEDFUNDS data found.")
            else:
                matrix = _compute_fwd_matrix(ff_x, ff_y, EXPIRY_YEARS, TENOR_YEARS)
                _render_heatmap(matrix, "USD Forward Matrix — Fed Funds", EXPIRY_LABELS, TENOR_LABELS)

        elif _fm_tab == "SOFR-FF Basis":
            if ff_x is None:
                st.error("No FEDFUNDS data found.")
            else:
                m_sofr = _compute_fwd_matrix(sofr_x, sofr_y, EXPIRY_YEARS, TENOR_YEARS)
                m_ff = _compute_fwd_matrix(ff_x, ff_y, EXPIRY_YEARS, TENOR_YEARS)
                basis = [[(s - f) * 100 for s, f in zip(sr, fr)] for sr, fr in zip(m_sofr, m_ff)]
                _render_heatmap(basis, "USD SOFR-FF Forward Basis (bp)",
                               EXPIRY_LABELS, TENOR_LABELS, fmt=".1f", unit="bp", colorscale="RdYlBu_r")

    elif ccy == "NZD":
        st.markdown("---")
        nzd_x, nzd_y, nzd_dt = _get_par_curve("NZD", "BKBM 3M")
        nzd_ois_x, nzd_ois_y, nzd_ois_dt = _get_par_curve("NZD", "NZONIA")

        if nzd_x is None:
            st.error("No NZD BKBM 3M data found.")
            return

        st.caption(f"Curve date: {nzd_dt}")

        if nzd_ois_x is not None:
            _fm_tab = st.radio("Matrix", ["BKBM 3M", "NZONIA", "BKBM-OIS Basis"], horizontal=True, key="fm_nzd_tab")
        else:
            _fm_tab = "BKBM 3M"

        if _fm_tab == "BKBM 3M":
            matrix = _compute_fwd_matrix(nzd_x, nzd_y, EXPIRY_YEARS, TENOR_YEARS)
            _render_heatmap(matrix, "NZD Forward Matrix — BKBM 3M", EXPIRY_LABELS, TENOR_LABELS)

        elif _fm_tab == "NZONIA":
            matrix = _compute_fwd_matrix(nzd_ois_x, nzd_ois_y, EXPIRY_YEARS, TENOR_YEARS)
            _render_heatmap(matrix, "NZD Forward Matrix — NZONIA", EXPIRY_LABELS, TENOR_LABELS)

        elif _fm_tab == "BKBM-OIS Basis":
            m_bk = _compute_fwd_matrix(nzd_x, nzd_y, EXPIRY_YEARS, TENOR_YEARS)
            m_ois = _compute_fwd_matrix(nzd_ois_x, nzd_ois_y, EXPIRY_YEARS, TENOR_YEARS)
            basis = [[(b - o) * 100 for b, o in zip(br, orow)] for br, orow in zip(m_bk, m_ois)]
            _render_heatmap(basis, "NZD BKBM-OIS Forward Basis (bp)",
                           EXPIRY_LABELS, TENOR_LABELS, fmt=".1f", unit="bp", colorscale="RdYlBu_r")


# ============================================================================
# HISTORICALS — FWD IRS ANALYSIS
# ============================================================================

@st.cache_data(ttl=300, show_spinner="Loading swap rate history…")
def load_swap_history(currency: str, floating_rate: str, years_back: int = 8) -> pd.DataFrame:
    """Load historical swap rates as wide table (date × tenor)."""
    query = """
        SELECT date, tenor, rate FROM swap_rates
        WHERE currency = %s AND floating_rate = %s
          AND date >= CURRENT_DATE - INTERVAL '%s years'
        ORDER BY date
    """
    df = run_query(query, [currency, floating_rate, years_back])
    if df.empty:
        return pd.DataFrame()
    df["date"] = pd.to_datetime(df["date"])
    df["rate"] = df["rate"].astype(float)
    return df.pivot_table(index="date", columns="tenor", values="rate", aggfunc="last").sort_index()

def page_historicals():
    """FWD IRS Historical Analysis page"""
    st.header("📈 FWD IRS Analysis")

    # ── Currency selector ──
    col_ccy, col_load, col_info = st.columns([1, 1, 2])
    with col_ccy:
        ccy = st.selectbox("Currency", ["AUD", "USD", "NZD"], key="hist_ccy")

    # ── Define floating rates per currency ──
    if ccy == "AUD":
        fr_a, fr_b = "3M BBSW", "6M BBSW"
        basis_label = "6v3"
    elif ccy == "USD":
        fr_a, fr_b = "SOFR", "FEDFUNDS"
        basis_label = "SOFR-FF"
    else:
        fr_a, fr_b = "BKBM 3M", None
        basis_label = None

    with col_load:
        if st.button("🔄 Load History", key="hist_load", type="primary", use_container_width=True):
            load_swap_history.clear()
            st.session_state["_hist_wa"] = load_swap_history(ccy, fr_a)
            if fr_b:
                st.session_state["_hist_wb"] = load_swap_history(ccy, fr_b)
            else:
                st.session_state["_hist_wb"] = pd.DataFrame()
            if ccy == "AUD":
                st.session_state["_hist_wois"] = load_swap_history(ccy, "AONIA")
            else:
                st.session_state["_hist_wois"] = pd.DataFrame()

    _wa = st.session_state.get("_hist_wa", pd.DataFrame())
    _wb = st.session_state.get("_hist_wb", pd.DataFrame())
    _wois = st.session_state.get("_hist_wois", pd.DataFrame())

    with col_info:
        if _wa.empty:
            st.info("Click **🔄 Load History** to populate charts.")
        else:
            _n = len(_wa)
            _d0 = _wa.index.min().strftime("%d-%b-%Y") if _n else "?"
            _d1 = _wa.index.max().strftime("%d-%b-%Y") if _n else "?"
            st.success(f"✅ {ccy}: {_n} dates loaded ({_d0} → {_d1})")

    # ── Helpers ──
    _STANDARD_TENORS = [1,2,3,4,5,6,7,8,9,10,12,15,20,25,30,40,50]
    _yr_tenors = sorted(list(set(
        _STANDARD_TENORS +
        [int(c[:-1]) for c in _wa.columns if c.endswith("Y") and c[:-1].isdigit()] +
        ([int(c[:-1]) for c in _wb.columns if c.endswith("Y") and c[:-1].isdigit()] if not _wb.empty else [])
    )))
    _tn_opts = [f"{y}Y" for y in _yr_tenors]
    _fwd_starts = [1,2,3,4,5,7,10,12,15,20]
    _fwd_tenors = [1,2,3,5,7,10]
    _sp_colors = ["#3b82f6","#ef4444","#22c55e","#f59e0b","#a855f7","#06b6d4","#f43f5e","#84cc16"]

    def _conv_rate(tenor_y, conv="Market"):
        """Return rate series for a given tenor using selected convention."""
        t = f"{int(tenor_y)}Y" if tenor_y == int(tenor_y) else f"{round(tenor_y*12)}M"
        if conv == f"Q/Q ({fr_a})" or (fr_b is None):
            return _wa[t] if t in _wa.columns else None
        elif conv == f"S/S ({fr_b})":
            return _wb[t] if not _wb.empty and t in _wb.columns else None
        else:  # Market
            if ccy == "AUD":
                return _wa[t] if tenor_y <= 3 and t in _wa.columns else (_wb[t] if not _wb.empty and t in _wb.columns else None)
            else:
                return _wa[t] if t in _wa.columns else None

    def _fwd(wide, start_y, tenor_y):
        """Fwd-fwd rate: (par(end)*end - par(start)*start) / tenor"""
        end_y = start_y + tenor_y
        s = f"{int(start_y)}Y" if start_y == int(start_y) else f"{round(start_y*12)}M"
        e = f"{int(end_y)}Y" if end_y == int(end_y) else f"{round(end_y*12)}M"
        if s not in wide.columns or e not in wide.columns:
            return None
        return (wide[e] * end_y - wide[s] * start_y) / tenor_y

    def _fwd_conv(start_y, tenor_y, conv="Market"):
        """Fwd-fwd rate using convention-appropriate curve."""
        end_y = start_y + tenor_y
        r_s = _conv_rate(start_y, conv)
        r_e = _conv_rate(end_y, conv)
        if r_s is None or r_e is None:
            return None
        return (r_e * end_y - r_s * start_y) / tenor_y

    def _fig_layout(fig, cut, ylab):
        fig.update_layout(
            height=460, margin=dict(l=50,r=20,t=40,b=40),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,23,42,0.8)",
            legend=dict(orientation="h", y=1.06, font=dict(color="#e2e8f0", size=12)),
            yaxis_title=ylab,
            xaxis=dict(gridcolor="#334155", color="#94a3b8", range=[cut, pd.Timestamp.now()]),
            yaxis=dict(gridcolor="#334155", color="#94a3b8"),
            font=dict(color="#94a3b8"),
        )

    def _add_series(fig, label, series, color, bands=False):
        fig.add_trace(go.Scatter(x=series.index, y=series.values, mode="lines",
            name=label, line=dict(color=color, width=1.8)))
        if bands:
            mu, sd = series.mean(), series.std()
            fig.add_hline(y=mu, line=dict(color=color, dash="dash", width=1), opacity=0.5)
            fig.add_hrect(y0=mu-sd, y1=mu+sd, fillcolor=color, opacity=0.06, line_width=0)
        else:
            fig.add_hline(y=series.mean(), line=dict(color=color, dash="dot", width=1), opacity=0.4)

    def _chart_stats(series_dict, key, ylab="bp"):
        """Hi/Lo/Mean/Std/Current stats box."""
        if not series_dict:
            return
        _rows = []
        for _name, _ser in series_dict.items():
            _s = _ser.dropna()
            if _s.empty:
                continue
            _rows.append({
                "Series": _name,
                "Hi": round(_s.max(), 4),
                "Lo": round(_s.min(), 4),
                "Mean": round(_s.mean(), 4),
                "Std": round(_s.std(), 4),
                "Current": round(_s.iloc[-1], 4),
                "vs Mean": round(_s.iloc[-1] - _s.mean(), 4),
            })
        if _rows:
            _sdf = pd.DataFrame(_rows).set_index("Series")
            st.dataframe(_sdf.style.format("{:.4f}", na_rep="  —  "),
                         use_container_width=True, height=min(38 + 38*len(_rows), 280))

    # ── Convention selector (AUD only) ──
    if ccy == "AUD" and (not _wa.empty or not _wb.empty):
        _conv = st.radio("Rate Convention", [f"Market (≤3Y Q/Q, ≥4Y S/S)", f"Q/Q ({fr_a})", f"S/S ({fr_b})"],
                         horizontal=True, key="hist_conv")
        _conv_key = "Market" if "Market" in _conv else _conv
    else:
        _conv_key = "Market"

    # ── Sub-tab navigation ──
    if basis_label:
        _tab_names = ["IRS Spreads", "IRS Butterflies", "Fwd-Fwd Rates",
                      f"{basis_label} Outright", f"{basis_label} Fwd-Fwd",
                      f"{basis_label} Spreads", f"{basis_label} Butterflies"]
    else:
        _tab_names = ["IRS Spreads", "IRS Butterflies", "Fwd-Fwd Rates"]

    _active = st.session_state.get("_hist_active_tab", 0)
    if _active >= len(_tab_names):
        _active = 0
    _cols = st.columns(len(_tab_names))
    for _i, _name in enumerate(_tab_names):
        with _cols[_i]:
            if st.button(_name, key=f"_hist_tab_{_i}",
                         type="primary" if _i == _active else "secondary",
                         use_container_width=True):
                st.session_state["_hist_active_tab"] = _i
                st.rerun()
    st.markdown("---")

    # ════════════════════════════════════════════════════════════
    # TAB 0: IRS SPREADS
    # ════════════════════════════════════════════════════════════
    if _active == 0:
        st.markdown("#### IRS Curve Spreads")
        if "hist_sp_list" not in st.session_state:
            st.session_state["hist_sp_list"] = [("2Y","10Y"), ("5Y","30Y")]

        bc1, bc2, bc3, bc4 = st.columns([1.2, 1.2, 0.8, 1.8])
        with bc1:
            _sp_l1 = st.selectbox("Leg 1 (short)", _tn_opts, index=_tn_opts.index("2Y") if "2Y" in _tn_opts else 0, key="hsp_l1")
        with bc2:
            _sp_l2 = st.selectbox("Leg 2 (long)", _tn_opts, index=_tn_opts.index("10Y") if "10Y" in _tn_opts else 4, key="hsp_l2")
        with bc3:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("➕ Add", key="hsp_add", use_container_width=True):
                if _sp_l1 != _sp_l2 and (_sp_l1, _sp_l2) not in st.session_state["hist_sp_list"]:
                    st.session_state["hist_sp_list"].append((_sp_l1, _sp_l2))
        with bc4:
            rc1, rc2 = st.columns([3,1])
            with rc1:
                _sp_rm = st.selectbox("Remove", ["  —  "] + [f"{a} → {b}" for a,b in st.session_state["hist_sp_list"]], key="hsp_rm")
            with rc2:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                if st.button("➖", key="hsp_rm_btn", use_container_width=True) and _sp_rm != "  —  ":
                    _rp = _sp_rm.split(" → ")
                    if len(_rp)==2 and (_rp[0],_rp[1]) in st.session_state["hist_sp_list"]:
                        st.session_state["hist_sp_list"].remove((_rp[0],_rp[1]))

        c1, c2, c3 = st.columns(3)
        with c1: _sp_yr = st.slider("History (years)", 1, 8, 5, key="hsp_yr")
        with c2: _sp_bands = st.checkbox("Mean ± 1σ bands", True, key="hsp_bands")
        with c3: _sp_as_spread = st.checkbox("Show as spread", False, key="hsp_as_spread")

        _cut = pd.Timestamp.now() - pd.DateOffset(years=_sp_yr)
        _fig = go.Figure()
        _sp_series = {}
        for _a, _b in st.session_state["hist_sp_list"]:
            try:
                _ay = int(_a[:-1]); _by = int(_b[:-1])
            except: continue
            _ra = _conv_rate(_ay, _conv_key); _rb = _conv_rate(_by, _conv_key)
            if _ra is None or _rb is None: continue
            _sr = (_rb - _ra).dropna()
            _sr = _sr[_sr.index >= _cut] * 100
            if not _sr.empty:
                _sp_series[f"{_a} → {_b}"] = _sr

        if _sp_as_spread and len(_sp_series) >= 2:
            _sk = list(_sp_series.keys())
            _sc1, _sc2 = st.columns(2)
            with _sc1: _s1 = st.selectbox("Series A", _sk, index=0, key="hsp_s1")
            with _sc2: _s2 = st.selectbox("Series B (subtract)", [k for k in _sk if k != _s1], index=0, key="hsp_s2")
            if _s1 in _sp_series and _s2 in _sp_series:
                _cmb = (_sp_series[_s1] - _sp_series[_s2]).dropna()
                _fig.add_trace(go.Scatter(x=_cmb.index, y=_cmb.values, mode="lines",
                    name=f"{_s1}  v  {_s2}", line=dict(color=_sp_colors[0], width=1.8)))
                _fig.add_hline(y=_cmb.mean(), line=dict(color="#94a3b8", dash="dash", width=1))
                _sp_active = {f"{_s1}  v  {_s2}": _cmb}
            else:
                _sp_active = _sp_series
        else:
            _sp_active = _sp_series
            for _i, (_lbl, _sr) in enumerate(_sp_series.items()):
                _add_series(_fig, _lbl, _sr, _sp_colors[_i % len(_sp_colors)], _sp_bands)

        if _sp_series:
            _fig_layout(_fig, _cut, "Spread (bp)")
            st.plotly_chart(_fig, use_container_width=True)
            _chart_stats(_sp_active, "sp", "bp")

    # ════════════════════════════════════════════════════════════
    # TAB 1: IRS BUTTERFLIES
    # ════════════════════════════════════════════════════════════
    if _active == 1:
        st.markdown("#### IRS Rate Butterflies")
        if "hist_fl_list" not in st.session_state:
            st.session_state["hist_fl_list"] = [("2Y","5Y","10Y")]

        bc1,bc2,bc3,bc4,bc5 = st.columns([1,1,1,0.7,1.5])
        with bc1: _fl_w = st.selectbox("Wing 1", _tn_opts, index=_tn_opts.index("2Y") if "2Y" in _tn_opts else 0, key="hfl_w")
        with bc2: _fl_m = st.selectbox("Body", _tn_opts, index=_tn_opts.index("5Y") if "5Y" in _tn_opts else 2, key="hfl_m")
        with bc3: _fl_e = st.selectbox("Wing 2", _tn_opts, index=_tn_opts.index("10Y") if "10Y" in _tn_opts else 4, key="hfl_e")
        with bc4:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("➕ Add", key="hfl_add", use_container_width=True):
                if len({_fl_w,_fl_m,_fl_e})==3 and (_fl_w,_fl_m,_fl_e) not in st.session_state["hist_fl_list"]:
                    st.session_state["hist_fl_list"].append((_fl_w,_fl_m,_fl_e))
        with bc5:
            rc1, rc2 = st.columns([3,1])
            with rc1: _fl_rm = st.selectbox("Remove", ["  —  "]+[f"{w}/{m}/{e}" for w,m,e in st.session_state["hist_fl_list"]], key="hfl_rm")
            with rc2:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                if st.button("➖", key="hfl_rm_btn", use_container_width=True) and _fl_rm != "  —  ":
                    _rp = _fl_rm.split("/")
                    if len(_rp)==3 and tuple(_rp) in st.session_state["hist_fl_list"]:
                        st.session_state["hist_fl_list"].remove(tuple(_rp))

        c1,c2 = st.columns(2)
        with c1: _fl_yr = st.slider("History (years)",1,8,5,key="hfl_yr")
        with c2: _fl_bands = st.checkbox("Mean ± 1σ bands", True, key="hfl_bands")

        _cut_fl = pd.Timestamp.now() - pd.DateOffset(years=_fl_yr)
        _fig_fl = go.Figure()
        _fl_series = {}
        for _fw,_fm,_fe in st.session_state["hist_fl_list"]:
            try:
                _wy=int(_fw[:-1]); _my=int(_fm[:-1]); _ey=int(_fe[:-1])
            except: continue
            _rw=_conv_rate(_wy,_conv_key); _rm=_conv_rate(_my,_conv_key); _re=_conv_rate(_ey,_conv_key)
            if _rw is None or _rm is None or _re is None: continue
            _fly = (_rm - 0.5*(_rw+_re)).dropna()
            _fly = _fly[_fly.index>=_cut_fl]*100
            if not _fly.empty:
                _fl_series[f"{_fw}/{_fm}/{_fe}"] = _fly

        for _i,(_l,_s) in enumerate(_fl_series.items()):
            _add_series(_fig_fl, _l, _s, _sp_colors[_i%len(_sp_colors)], _fl_bands)
        if _fl_series:
            _fig_fl.add_hline(y=0, line=dict(color="#64748b", width=1))
            _fig_layout(_fig_fl, _cut_fl, "Butterfly (bp)")
            st.plotly_chart(_fig_fl, use_container_width=True)
            _chart_stats(_fl_series, "fl", "bp")

    # ════════════════════════════════════════════════════════════
    # TAB 2: FWD-FWD RATES
    # ════════════════════════════════════════════════════════════
    if _active == 2:
        st.markdown("#### Forward-Forward Swap Rates")
        if "hist_fv_list" not in st.session_state:
            st.session_state["hist_fv_list"] = [(2,2), (5,5)]

        bc1,bc2,bc3,bc4 = st.columns([1,1,0.7,1.5])
        with bc1: _fv_st = st.selectbox("Start (years)", _fwd_starts, index=_fwd_starts.index(2) if 2 in _fwd_starts else 0, key="hfv_st")
        with bc2: _fv_tn = st.selectbox("Tenor (years)", _fwd_tenors, index=_fwd_tenors.index(2) if 2 in _fwd_tenors else 0, key="hfv_tn")
        with bc3:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("➕ Add", key="hfv_add", use_container_width=True):
                if (_fv_st, _fv_tn) not in st.session_state["hist_fv_list"]:
                    st.session_state["hist_fv_list"].append((_fv_st, _fv_tn))
        with bc4:
            rc1, rc2 = st.columns([3,1])
            with rc1: _fv_rm = st.selectbox("Remove", ["  —  "]+[f"{s}y{t}y" for s,t in st.session_state["hist_fv_list"]], key="hfv_rm")
            with rc2:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                if st.button("➖", key="hfv_rm_btn", use_container_width=True) and _fv_rm != "  —  ":
                    _rp = _fv_rm[:-1].split("y")
                    if len(_rp)==2:
                        try:
                            if (int(_rp[0]),int(_rp[1])) in st.session_state["hist_fv_list"]:
                                st.session_state["hist_fv_list"].remove((int(_rp[0]),int(_rp[1])))
                        except: pass

        c1,c2,c3 = st.columns(3)
        with c1: _fv_yr = st.slider("History (years)",1,8,5,key="hfv_yr")
        with c2: _fv_as_spread = st.checkbox("Show as spread", False, key="hfv_sprd")

        _cut_fv = pd.Timestamp.now() - pd.DateOffset(years=_fv_yr)
        _fig_fv = go.Figure()
        _fv_series = {}
        for _s,_t in st.session_state["hist_fv_list"]:
            _r = _fwd_conv(_s,_t,_conv_key)
            if _r is not None:
                _rs = _r[_r.index>=_cut_fv].dropna()
                if not _rs.empty:
                    _fv_series[f"{_s}y{_t}y"] = _rs

        if _fv_as_spread and len(_fv_series) >= 2:
            _fk = list(_fv_series.keys())
            _vc1, _vc2 = st.columns(2)
            with _vc1: _fv_s1 = st.selectbox("Series A", _fk, index=0, key="hfv_s1")
            with _vc2: _fv_s2 = st.selectbox("Series B (subtract)", [k for k in _fk if k != _fv_s1], index=0, key="hfv_s2")
            if _fv_s1 in _fv_series and _fv_s2 in _fv_series:
                _cmb=(_fv_series[_fv_s1]-_fv_series[_fv_s2]).dropna()*100
                _fig_fv.add_trace(go.Scatter(x=_cmb.index,y=_cmb.values,mode="lines",
                    name=f"{_fv_s1} v {_fv_s2}",line=dict(color=_sp_colors[0],width=1.8)))
                _fig_fv.add_hline(y=_cmb.mean(),line=dict(color="#94a3b8",dash="dash",width=1))
                _fv_active = {f"{_fv_s1} v {_fv_s2}": _cmb}
                _fig_layout(_fig_fv, _cut_fv, "Spread (bp)")
            else:
                _fv_active = _fv_series
        else:
            _fv_active = _fv_series
            for _i,(_l,_s) in enumerate(_fv_series.items()):
                _add_series(_fig_fv, _l, _s, _sp_colors[_i%len(_sp_colors)])
            _fig_layout(_fig_fv, _cut_fv, "Rate (%)")
        if _fv_series:
            st.plotly_chart(_fig_fv, use_container_width=True)
            _chart_stats(_fv_active, "fv", "%")

    # ════════════════════════════════════════════════════════════
    # TAB 3: BASIS OUTRIGHT
    # ════════════════════════════════════════════════════════════
    if _active == 3 and basis_label:
        st.markdown(f"#### {basis_label} Basis — Outright ({fr_b} → {fr_a})")
        _com = sorted([c for c in _wb.columns if c in _wa.columns and c.endswith("Y")],
                       key=lambda x: int(x[:-1])) if not _wb.empty else []
        if not _com:
            st.info(f"No overlapping tenors between {fr_a} and {fr_b}.")
        else:
            if "hist_b_list" not in st.session_state:
                st.session_state["hist_b_list"] = _com[:3] if len(_com) >= 3 else _com

            bc1,bc2,bc3 = st.columns([1.5,0.7,1.5])
            with bc1:
                _avail = [t for t in _com if t not in st.session_state["hist_b_list"]] or _com
                _b_add_tn = st.selectbox("Add tenor", _avail, key="hb_add_tn")
            with bc2:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                if st.button("➕ Add", key="hb_add", use_container_width=True):
                    if _b_add_tn not in st.session_state["hist_b_list"]:
                        st.session_state["hist_b_list"].append(_b_add_tn)
            with bc3:
                rc1, rc2 = st.columns([3,1])
                with rc1: _b_rm = st.selectbox("Remove", ["  —  "]+st.session_state["hist_b_list"], key="hb_rm")
                with rc2:
                    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                    if st.button("➖", key="hb_rm_btn", use_container_width=True) and _b_rm != "  —  " and _b_rm in st.session_state["hist_b_list"]:
                        st.session_state["hist_b_list"].remove(_b_rm)

            c1,c2 = st.columns(2)
            with c1: _b_yr = st.slider("History (years)",1,8,5,key="hb_yr")
            _cut_b = pd.Timestamp.now() - pd.DateOffset(years=_b_yr)
            _fig_b = go.Figure()
            _b_series = {}
            for _i,_tn in enumerate(st.session_state["hist_b_list"]):
                if _tn not in _wb.columns or _tn not in _wa.columns: continue
                _bs = (_wb[_tn]-_wa[_tn]).dropna()
                _bs = _bs[_bs.index>=_cut_b]*100
                if not _bs.empty:
                    _b_series[f"{_tn} {basis_label}"] = _bs
                    _add_series(_fig_b, f"{_tn} {basis_label}", _bs, _sp_colors[_i%len(_sp_colors)])
            _fig_b.add_hline(y=0, line=dict(color="#64748b", width=1))
            _fig_layout(_fig_b, _cut_b, f"{basis_label} Basis (bp)")
            if _b_series:
                st.plotly_chart(_fig_b, use_container_width=True)
                _chart_stats(_b_series, "b", "bp")

    # ════════════════════════════════════════════════════════════
    # TAB 4: BASIS FWD-FWD
    # ════════════════════════════════════════════════════════════
    if _active == 4 and basis_label:
        st.markdown(f"#### {basis_label} Forward-Forward Basis")
        st.caption(f"Fwd-fwd {fr_b} → fwd-fwd {fr_a} for same start/tenor")
        if "hist_fvb_list" not in st.session_state:
            st.session_state["hist_fvb_list"] = [(2,2)]

        bc1,bc2,bc3,bc4 = st.columns([1,1,0.7,1.5])
        with bc1: _fvb_st = st.selectbox("Start (years)", _fwd_starts, index=_fwd_starts.index(2), key="hfvb_st")
        with bc2: _fvb_tn = st.selectbox("Tenor (years)", _fwd_tenors, index=_fwd_tenors.index(2), key="hfvb_tn")
        with bc3:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("➕ Add", key="hfvb_add", use_container_width=True):
                if (_fvb_st, _fvb_tn) not in st.session_state["hist_fvb_list"]:
                    st.session_state["hist_fvb_list"].append((_fvb_st, _fvb_tn))
        with bc4:
            rc1, rc2 = st.columns([3,1])
            with rc1: _fvb_rm = st.selectbox("Remove", ["  —  "]+[f"{s}y{t}y" for s,t in st.session_state["hist_fvb_list"]], key="hfvb_rm")
            with rc2:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                if st.button("➖", key="hfvb_rm_btn", use_container_width=True) and _fvb_rm != "  —  ":
                    _rp = _fvb_rm[:-1].split("y")
                    if len(_rp)==2:
                        try:
                            if (int(_rp[0]),int(_rp[1])) in st.session_state["hist_fvb_list"]:
                                st.session_state["hist_fvb_list"].remove((int(_rp[0]),int(_rp[1])))
                        except: pass

        c1,c2 = st.columns(2)
        with c1: _fvb_yr = st.slider("History (years)",1,8,5,key="hfvb_yr")
        _cut_fvb = pd.Timestamp.now() - pd.DateOffset(years=_fvb_yr)
        _fig_fvb = go.Figure()
        _fvb_series = {}
        for _s,_t in st.session_state["hist_fvb_list"]:
            _rb = _fwd(_wb,_s,_t) if not _wb.empty else None
            _ra = _fwd(_wa,_s,_t)
            if _rb is not None and _ra is not None:
                _b = (_rb-_ra).dropna()
                _b = _b[_b.index>=_cut_fvb]*100
                if not _b.empty:
                    _fvb_series[f"{_s}y{_t}y {basis_label}"] = _b

        for _i,(_l,_b) in enumerate(_fvb_series.items()):
            _add_series(_fig_fvb, _l, _b, _sp_colors[_i%len(_sp_colors)])
        _fig_fvb.add_hline(y=0, line=dict(color="#64748b", width=1))
        _fig_layout(_fig_fvb, _cut_fvb, f"{basis_label} Fwd-Fwd Basis (bp)")
        if _fvb_series:
            st.plotly_chart(_fig_fvb, use_container_width=True)
            _chart_stats(_fvb_series, "fvb", "bp")

    # ════════════════════════════════════════════════════════════
    # TAB 5: BASIS SPREADS
    # ════════════════════════════════════════════════════════════
    if _active == 5 and basis_label:
        st.markdown(f"#### {basis_label} Basis Spreads")
        _com_sp = sorted([c for c in _wb.columns if c in _wa.columns and c.endswith("Y")],
                          key=lambda x: int(x[:-1])) if not _wb.empty else []
        if len(_com_sp) < 2:
            st.info("Need at least 2 overlapping tenors.")
        else:
            if "hist_bsp_list" not in st.session_state:
                st.session_state["hist_bsp_list"] = [(_com_sp[0], _com_sp[-1])] if _com_sp else []

            bc1,bc2,bc3,bc4 = st.columns([1.2,1.2,0.7,1.5])
            with bc1: _bsp_l1 = st.selectbox(f"Leg 1 ({basis_label} tenor)", _com_sp, index=0, key="hbsp_l1")
            with bc2: _bsp_l2 = st.selectbox(f"Leg 2 ({basis_label} tenor)", _com_sp, index=min(2,len(_com_sp)-1), key="hbsp_l2")
            with bc3:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                if st.button("➕ Add", key="hbsp_add", use_container_width=True):
                    if _bsp_l1 != _bsp_l2 and (_bsp_l1, _bsp_l2) not in st.session_state["hist_bsp_list"]:
                        st.session_state["hist_bsp_list"].append((_bsp_l1, _bsp_l2))
            with bc4:
                rc1, rc2 = st.columns([3,1])
                with rc1: _bsp_rm = st.selectbox("Remove", ["  —  "]+[f"{a} → {b}" for a,b in st.session_state["hist_bsp_list"]], key="hbsp_rm")
                with rc2:
                    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                    if st.button("➖", key="hbsp_rm_btn", use_container_width=True) and _bsp_rm != "  —  ":
                        _rp=_bsp_rm.split(" → ")
                        if len(_rp)==2 and tuple(_rp) in st.session_state["hist_bsp_list"]:
                            st.session_state["hist_bsp_list"].remove(tuple(_rp))

            c1,c2 = st.columns(2)
            with c1: _bsp_yr = st.slider("History (years)",1,8,5,key="hbsp_yr")
            _cut_bsp = pd.Timestamp.now() - pd.DateOffset(years=_bsp_yr)
            _fig_bsp = go.Figure()
            _bsp_series = {}
            for _a,_b in st.session_state["hist_bsp_list"]:
                if _a not in _wb.columns or _a not in _wa.columns: continue
                if _b not in _wb.columns or _b not in _wa.columns: continue
                _ba=(_wb[_a]-_wa[_a]).dropna()*100
                _bb=(_wb[_b]-_wa[_b]).dropna()*100
                _bsprd=(_ba-_bb).dropna()
                _bsprd = _bsprd[_bsprd.index>=_cut_bsp]
                if not _bsprd.empty:
                    _bsp_series[f"{_a} → {_b} {basis_label}"] = _bsprd

            for _i,(_lbl,_s) in enumerate(_bsp_series.items()):
                _add_series(_fig_bsp, _lbl, _s, _sp_colors[_i%len(_sp_colors)])
            _fig_bsp.add_hline(y=0, line=dict(color="#64748b", width=1))
            _fig_layout(_fig_bsp, _cut_bsp, f"{basis_label} Spread (bp)")
            if _bsp_series:
                st.plotly_chart(_fig_bsp, use_container_width=True)
                _chart_stats(_bsp_series, "bsp", "bp")

    # ════════════════════════════════════════════════════════════
    # TAB 6: BASIS BUTTERFLIES
    # ════════════════════════════════════════════════════════════
    if _active == 6 and basis_label:
        st.markdown(f"#### {basis_label} Basis Butterflies")
        st.caption(f"Fly = {basis_label}(body) − 0.5×[{basis_label}(wing1) + {basis_label}(wing2)]")
        _com_bf = sorted([c for c in _wb.columns if c in _wa.columns and c.endswith("Y")],
                          key=lambda x: int(x[:-1])) if not _wb.empty else []
        if len(_com_bf) < 3:
            st.info("Need at least 3 overlapping tenors.")
        else:
            if "hist_bbf_list" not in st.session_state:
                st.session_state["hist_bbf_list"] = [(_com_bf[0], _com_bf[len(_com_bf)//2], _com_bf[-1])]

            bc1,bc2,bc3,bc4,bc5 = st.columns([1,1,1,0.7,1.5])
            with bc1: _bf_w1 = st.selectbox("Wing 1", _com_bf, index=0, key="hbbf_w1")
            with bc2: _bf_bd = st.selectbox("Body", _com_bf, index=min(2,len(_com_bf)-1), key="hbbf_bd")
            with bc3: _bf_w2 = st.selectbox("Wing 2", _com_bf, index=min(4,len(_com_bf)-1), key="hbbf_w2")
            with bc4:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                if st.button("➕ Add", key="hbbf_add", use_container_width=True):
                    if len({_bf_w1,_bf_bd,_bf_w2})==3 and (_bf_w1,_bf_bd,_bf_w2) not in st.session_state["hist_bbf_list"]:
                        st.session_state["hist_bbf_list"].append((_bf_w1,_bf_bd,_bf_w2))
            with bc5:
                rc1,rc2 = st.columns([3,1])
                with rc1: _bf_rm = st.selectbox("Remove", ["  —  "]+[f"{w}/{m}/{e}" for w,m,e in st.session_state["hist_bbf_list"]], key="hbbf_rm")
                with rc2:
                    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                    if st.button("➖", key="hbbf_rm_btn", use_container_width=True) and _bf_rm != "  —  ":
                        _rp = _bf_rm.split("/")
                        if len(_rp)==3 and tuple(_rp) in st.session_state["hist_bbf_list"]:
                            st.session_state["hist_bbf_list"].remove(tuple(_rp))

            c1,c2 = st.columns(2)
            with c1: _bf_yr = st.slider("History (years)",1,8,5,key="hbbf_yr")
            _cut_bf = pd.Timestamp.now() - pd.DateOffset(years=_bf_yr)
            _fig_bf = go.Figure()
            _bf_series = {}
            for _w1,_bd,_w2 in st.session_state["hist_bbf_list"]:
                if any(t not in _wb.columns or t not in _wa.columns for t in [_w1,_bd,_w2]): continue
                _b_w1 = (_wb[_w1]-_wa[_w1]).dropna()*100
                _b_bd = (_wb[_bd]-_wa[_bd]).dropna()*100
                _b_w2 = (_wb[_w2]-_wa[_w2]).dropna()*100
                _bfly = (_b_bd - 0.5*(_b_w1+_b_w2)).dropna()
                _bfly = _bfly[_bfly.index>=_cut_bf]
                if not _bfly.empty:
                    _bf_series[f"{_w1}/{_bd}/{_w2}"] = _bfly

            for _i,(_lbl,_s) in enumerate(_bf_series.items()):
                _add_series(_fig_bf, _lbl, _s, _sp_colors[_i%len(_sp_colors)])
            _fig_bf.add_hline(y=0, line=dict(color="#64748b", width=1))
            _fig_layout(_fig_bf, _cut_bf, f"{basis_label} Fly (bp)")
            if _bf_series:
                st.plotly_chart(_fig_bf, use_container_width=True)
                _chart_stats(_bf_series, "bbf", "bp")


# ============================================================================
# MAIN
# ============================================================================

def main():
    # Check authentication
    if not st.session_state.get("authenticated"):
        render_login()
        return
    
    # Sidebar navigation
    with st.sidebar:
        render_sidebar_logo()
        
        st.markdown(f"**👤 {st.session_state.get('username', 'User')}**")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state["authenticated"] = False
            st.session_state["username"] = None
            st.rerun()
        
        st.markdown("---")
        
        page = st.radio(
            "Navigation",
            ["🏠 Dashboard", "📊 Swap Rates", "📈 Benchmarks", "🔄 Basis Swaps", "📉 Charts",
             "🔥 Forward Matrices", "📐 Historicals", "ℹ️ About"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.caption("RateEdge Data Portal v1.8")
        st.caption("© 2026 RateEdge (Aust.)")
    
    # Route to page
    if page == "🏠 Dashboard":
        page_dashboard()
    elif page == "📊 Swap Rates":
        page_swap_rates()
    elif page == "📈 Benchmarks":
        page_benchmark_rates()
    elif page == "🔄 Basis Swaps":
        page_basis_swaps()
    elif page == "📉 Charts":
        page_charts()
    elif page == "🔥 Forward Matrices":
        page_fwd_matrices()
    elif page == "📐 Historicals":
        page_historicals()
    elif page == "ℹ️ About":
        page_about()

if __name__ == "__main__":
    main()
