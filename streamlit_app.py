"""
RateEdge Data Portal - Streamlit Version
Pulls AUD, USD, NZD swap rates from Supabase
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor

# Page config
st.set_page_config(
    page_title="RateEdge Data",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    """Get list of available currencies"""
    query = "SELECT DISTINCT currency FROM swap_rates ORDER BY currency"
    df = run_query(query)
    if not df.empty:
        return df['currency'].tolist()
    return ["AUD", "NZD", "USD"]

@st.cache_data(ttl=300)
def get_rate_history(currency: str, tenor: str, floating_rate: str, days: int = 90):
    """Get historical rates for charting"""
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

def render_header():
    """Render header"""
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <h1 style="margin: 0;">
                <span style="color: #1e3a5f;">Rate</span><span style="color: #ef4444;">Edge</span> Data
            </h1>
            <p style="color: #64748b; margin-top: 0.5rem;">
                AUD • NZD • USD Interest Rate Data
            </p>
        </div>
        """, unsafe_allow_html=True)

def render_rate_table(df: pd.DataFrame, title: str):
    """Render a rate table"""
    if df.empty:
        st.info(f"No {title} data available")
        return
    
    st.subheader(title)
    st.dataframe(df, use_container_width=True, hide_index=True)

def render_rate_chart(currency: str, tenor: str, floating_rate: str, days: int = 90):
    """Render historical rate chart"""
    df = get_rate_history(currency, tenor, floating_rate, days)
    
    if df.empty:
        st.info("No historical data available")
        return
    
    fig = px.line(
        df, x='date', y='rate',
        title=f"{currency} {tenor} {floating_rate} Rate History",
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
    
    # Tenor ordering
    tenor_order = ['1M', '2M', '3M', '6M', '9M', '1Y', '2Y', '3Y', '4Y', '5Y', 
                   '6Y', '7Y', '8Y', '9Y', '10Y', '12Y', '15Y', '20Y', '25Y', '30Y']
    
    fig = go.Figure()
    
    for fr in floating_rates:
        subset = df[df['floating_rate'] == fr].copy()
        # Sort by tenor
        subset['tenor_order'] = subset['tenor'].apply(
            lambda x: tenor_order.index(x) if x in tenor_order else 99
        )
        subset = subset.sort_values('tenor_order')
        
        fig.add_trace(go.Scatter(
            x=subset['tenor'],
            y=subset['rate'],
            mode='lines+markers',
            name=fr
        ))
    
    fig.update_layout(
        title=f"{currency} Swap Curve (Latest)",
        xaxis_title="Tenor",
        yaxis_title="Rate (%)",
        hovermode='x unified',
        height=450
    )
    
    st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# PAGES
# ============================================================================

def page_dashboard():
    """Dashboard page"""
    render_header()
    
    # Get currencies
    currencies = get_available_currencies()
    
    # Summary metrics
    st.markdown("### 📊 Market Overview")
    
    cols = st.columns(len(currencies))
    
    for i, ccy in enumerate(currencies):
        with cols[i]:
            df = get_latest_rates(ccy)
            if not df.empty:
                # Get 5Y rate as headline
                rate_5y = df[df['tenor'] == '5Y']
                if not rate_5y.empty:
                    rate = rate_5y.iloc[0]['rate']
                    st.metric(f"{ccy} 5Y", f"{rate:.3f}%")
                else:
                    st.metric(f"{ccy}", "No data")
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
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    currencies = ["All"] + get_available_currencies()
    
    with col1:
        currency = st.selectbox("Currency", currencies)
    with col2:
        days = st.selectbox("Period", [7, 14, 30, 60, 90, 180, 365], index=2)
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
            pivot = latest.pivot_table(
                index='tenor', 
                columns='floating_rate', 
                values='rate',
                aggfunc='first'
            )
            st.dataframe(pivot, use_container_width=True)
    else:
        for ccy in get_available_currencies():
            with st.expander(f"🔹 {ccy}", expanded=True):
                latest = get_latest_rates(ccy)
                if not latest.empty:
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
    
    # Filters
    col1, col2 = st.columns(2)
    
    currencies = ["All"] + get_available_currencies()
    
    with col1:
        currency = st.selectbox("Currency", currencies, key="bench_ccy")
    with col2:
        days = st.selectbox("Period", [7, 14, 30, 60, 90, 180, 365], index=2, key="bench_days")
    
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
        days = st.selectbox("Period", [30, 60, 90, 180, 365], index=2, key="chart_days")
    
    render_rate_chart(currency, tenor, floating_rate, days)

def page_about():
    """About page"""
    st.header("ℹ️ About RateEdge Data")
    
    st.markdown("""
    ### RateEdge Data Portal
    
    This portal provides access to interest rate swap data for:
    - 🇦🇺 **AUD** - Australian Dollar
    - 🇳🇿 **NZD** - New Zealand Dollar  
    - 🇺🇸 **USD** - US Dollar
    
    #### Data Sources
    - Bloomberg terminal exports
    - DTCC SDR trade data
    - Market data providers
    
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
    # Sidebar navigation
    with st.sidebar:
        st.image("https://rateedge.au/logo.png", width=200)
        st.markdown("---")
        
        page = st.radio(
            "Navigation",
            ["🏠 Dashboard", "📊 Swap Rates", "📈 Benchmarks", "📉 Charts", "ℹ️ About"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.caption("RateEdge Data Portal v1.0")
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
