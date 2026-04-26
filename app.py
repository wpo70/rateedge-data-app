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
import urllib3

# Suppress SSL warnings if needed
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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

AUTH_URL = "https://auth.rateedge.au"

def request_otp(email: str):
    """Request OTP code via email"""
    try:
        resp = requests.post(
            f"{AUTH_URL}/request-otp", 
            json={"email": email}, 
            timeout=10,
            verify=False  # Skip SSL verification - Streamlit Cloud TLS issue
        )
        return resp.status_code, resp.json()
    except Exception as e:
        return 500, {"error": str(e)}

def verify_otp(email: str, code: str):
    """Verify OTP code"""
    try:
        resp = requests.post(
            f"{AUTH_URL}/verify-otp", 
            json={"email": email, "code": code}, 
            timeout=10,
            verify=False  # Skip SSL verification - Streamlit Cloud TLS issue
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
            email = st.text_input("Email address", key="login_email", placeholder="your.email@company.com")
            if st.button("📧 Send Verification Code", key="send_btn", use_container_width=True, type="primary"):
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
            code = st.text_input("Enter 6-digit code", key="otp_code", max_chars=6)
            
            if st.button("✅ Verify", key="verify_btn", use_container_width=True, type="primary"):
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
    """Fetch benchmark rates from Supabase"""
    query = """
        SELECT date, currency, rate_type, rate
        FROM benchmark_rates
        WHERE date >= CURRENT_DATE - INTERVAL '%s days'
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
    if currency == "AUD" and floating_rate == "AONIA":
        display_name = "OIS"
    
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
    
    # Colors for lines
    colors = ['#3b82f6', '#06b6d4', '#ef4444', '#f59e0b', '#10b981', '#8b5cf6']
    
    fig = go.Figure()
    
    for idx, fr in enumerate(floating_rates):
        subset = df[df['floating_rate'] == fr].copy()
        
        # Rename AONIA to OIS for AUD
        display_name = fr
        if currency == "AUD" and fr == "AONIA":
            display_name = "OIS"
        
        # Sort by tenor order (case insensitive)
        def get_tenor_order(t):
            t_upper = t.upper() if isinstance(t, str) else str(t).upper()
            if t_upper in tenor_order:
                return tenor_order.index(t_upper)
            return 99
        
        subset['tenor_order'] = subset['tenor'].apply(get_tenor_order)
        subset = subset.sort_values('tenor_order')
        
        fig.add_trace(go.Scatter(
            x=subset['tenor'],
            y=subset['rate'],
            mode='lines+markers',
            name=display_name,
            line=dict(color=colors[idx % len(colors)], width=2),
            marker=dict(size=6)
        ))
    
    fig.update_layout(
        title=f"{currency} Swap Curve (Latest)",
        xaxis_title="Tenor",
        yaxis_title="Rate (%)",
        hovermode='x unified',
        height=450,
        xaxis=dict(type='category')
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
    
    if currency != "All":
        latest = get_latest_rates(currency)
        if not latest.empty:
            # Rename AONIA to OIS for AUD
            if currency == "AUD":
                latest['floating_rate'] = latest['floating_rate'].replace('AONIA', 'OIS')
            pivot = latest.pivot_table(
                index='tenor', 
                columns='floating_rate', 
                values='rate',
                aggfunc='first'
            )
            st.dataframe(pivot, use_container_width=True)
    else:
        for ccy in db_currencies:
            with st.expander(f"🔹 {ccy}", expanded=True):
                latest = get_latest_rates(ccy)
                if not latest.empty:
                    # Rename AONIA to OIS for AUD
                    if ccy == "AUD":
                        latest['floating_rate'] = latest['floating_rate'].replace('AONIA', 'OIS')
                    pivot = latest.pivot_table(
                        index='tenor', 
                        columns='floating_rate', 
                        values='rate',
                        aggfunc='first'
                    )
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
    """Benchmark rates page"""
    st.header("📈 Benchmark Rates")
    
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
    
    # Summary
    st.info(f"Showing {len(df):,} records from last {days} days")
    
    # Display
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Download
    csv = df.to_csv(index=False)
    st.download_button(
        "📥 Download CSV",
        csv,
        f"benchmark_rates_{currency}_{datetime.now().strftime('%Y%m%d')}.csv",
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
    
    # Rename AONIA to OIS for display
    display_floating_rates = []
    for fr in floating_rates:
        if currency == "AUD" and fr == "AONIA":
            display_floating_rates.append("OIS")
        else:
            display_floating_rates.append(fr)
    
    with col2:
        tenor = st.selectbox("Tenor", tenors, key="chart_tenor")
    with col3:
        fr_display = st.selectbox("Floating Rate", display_floating_rates, key="chart_float")
        # Map back to actual value
        floating_rate = floating_rates[display_floating_rates.index(fr_display)]
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
            ["🏠 Dashboard", "📊 Swap Rates", "📈 Benchmarks", "📉 Charts", "ℹ️ About"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.caption("RateEdge Data Portal v1.3")
        st.caption("© 2026 RateEdge (Aust.)")
    
    # Route to page
    if page == "🏠 Dashboard":
        page_dashboard()
    elif page == "📊 Swap Rates":
        page_swap_rates()
    elif page == "📈 Benchmarks":
        page_benchmark_rates()
    elif page == "📉 Charts":
        page_charts()
    elif page == "ℹ️ About":
        page_about()

if __name__ == "__main__":
    main()
