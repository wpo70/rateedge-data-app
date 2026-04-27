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
            ["🏠 Dashboard", "📊 Swap Rates", "📈 Benchmarks", "🔄 Basis Swaps", "📉 Charts", "ℹ️ About"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.caption("RateEdge Data Portal v1.6")
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
    elif page == "ℹ️ About":
        page_about()

if __name__ == "__main__":
    main()
