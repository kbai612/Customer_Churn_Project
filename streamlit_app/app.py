"""
Retention Intelligence Report
An editorial-style analytics dashboard for customer lifecycle optimization and churn prediction.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import snowflake.connector
from datetime import datetime

st.set_page_config(
    page_title="Retention Intelligence Report",
    page_icon="▪️",
    layout="wide",
    initial_sidebar_state="expanded"
)

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Newsreader:ital,wght@0,300;0,400;0,600;1,300;1,400&family=Libre+Baskerville:wght@400;700&display=swap');

:root {
    --bg-primary: #0d0f12;
    --bg-secondary: #16181d;
    --bg-elevated: #1a1d23;
    --accent-primary: #ff6b35;
    --accent-secondary: #f7931e;
    --text-primary: #f8f9fa;
    --text-muted: #8b92a0;
    --text-dim: #5a6070;
    --border-subtle: #252830;
    --border-accent: rgba(255, 107, 53, 0.125);
    --success: #00d9a3;
    --danger: #ff4757;
}

* {
    font-family: 'JetBrains Mono', monospace !important;
}

.stApp {
    background: var(--bg-primary);
    position: relative;
}

.stApp::before {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: 
        radial-gradient(circle at 20% 50%, rgba(255, 107, 53, 0.03) 0%, transparent 50%),
        radial-gradient(circle at 80% 20%, rgba(247, 147, 30, 0.03) 0%, transparent 50%);
    pointer-events: none;
    z-index: 0;
}

.stApp > div {
    position: relative;
    z-index: 1;
}

h1, h2, h3 {
    font-family: 'Newsreader', serif !important;
    font-weight: 300 !important;
    letter-spacing: -0.03em !important;
}

h1 {
    font-size: 3.5rem !important;
    line-height: 1.1 !important;
    margin-bottom: 0.25rem !important;
    color: var(--text-primary) !important;
    font-style: italic !important;
    position: relative !important;
}

h1::after {
    content: '';
    position: absolute;
    bottom: -8px;
    left: 0;
    width: 120px;
    height: 3px;
    background: linear-gradient(90deg, var(--accent-primary), transparent);
}

h2 {
    font-size: 1.75rem !important;
    color: var(--text-primary) !important;
    margin-top: 3rem !important;
    margin-bottom: 1.5rem !important;
    border-left: 3px solid var(--accent-primary);
    padding-left: 1rem;
    font-weight: 400 !important;
}

h3 {
    font-size: 1.1rem !important;
    color: var(--text-muted) !important;
    font-weight: 300 !important;
    letter-spacing: 0.02em !important;
}

h4 {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85rem !important;
    color: var(--text-muted) !important;
    font-weight: 400 !important;
    letter-spacing: 0.01em !important;
    font-style: normal !important;
}

[data-testid="stMetric"] {
    background: var(--bg-elevated);
    border: 1px solid var(--border-subtle);
    border-left: 3px solid var(--accent-primary);
    padding: 1.75rem 1.5rem;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}

[data-testid="stMetric"]::before {
    content: '';
    position: absolute;
    top: 0;
    right: 0;
    width: 100px;
    height: 100%;
    background: linear-gradient(90deg, transparent, var(--border-accent));
    opacity: 0;
    transition: opacity 0.4s ease;
}

[data-testid="stMetric"]:hover::before {
    opacity: 1;
}

[data-testid="stMetric"]:hover {
    transform: translateX(4px);
    border-left-color: var(--accent-secondary);
    box-shadow: -4px 0 16px rgba(255, 107, 53, 0.1);
}

[data-testid="stMetricLabel"] {
    font-size: 0.7rem !important;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: var(--text-dim) !important;
    font-weight: 600 !important;
    margin-bottom: 0.5rem !important;
}

[data-testid="stMetricValue"] {
    font-size: 2.25rem !important;
    font-weight: 700 !important;
    color: var(--text-primary) !important;
    font-family: 'JetBrains Mono', monospace !important;
    line-height: 1 !important;
}

[data-testid="stMetricDelta"] {
    font-size: 0.75rem !important;
    margin-top: 0.5rem !important;
}

.stPlotlyChart {
    background: var(--bg-elevated);
    border: 1px solid var(--border-subtle);
    padding: 1.5rem;
    position: relative;
    transition: border-color 0.3s ease;
}

.stPlotlyChart:hover {
    border-color: var(--border-accent);
}

[data-testid="stSidebar"] {
    background: var(--bg-secondary);
    border-right: 1px solid var(--border-subtle);
    position: relative;
}

[data-testid="stSidebar"]::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-image: 
        repeating-linear-gradient(
            0deg,
            transparent,
            transparent 2px,
            rgba(255, 107, 53, 0.01) 2px,
            rgba(255, 107, 53, 0.01) 4px
        );
    pointer-events: none;
}

[data-testid="stSidebar"] h2 {
    color: var(--accent-primary) !important;
    border-left: none;
    padding-left: 0;
    font-size: 1.25rem !important;
    margin-bottom: 2rem !important;
    font-style: normal !important;
}

.stSelectbox label, .stRadio label {
    color: var(--text-muted) !important;
    font-size: 0.75rem !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-weight: 500 !important;
}

.stDataFrame {
    background: var(--bg-elevated);
    border: 1px solid var(--border-subtle);
    overflow: hidden;
    font-size: 0.85rem;
}

.stDataFrame thead tr th {
    background-color: var(--bg-secondary) !important;
    color: var(--accent-primary) !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    font-size: 0.65rem !important;
    letter-spacing: 0.15em;
    border-bottom: 2px solid var(--accent-primary) !important;
    padding: 1rem !important;
}

.stDataFrame tbody tr {
    border-bottom: 1px solid var(--border-subtle) !important;
    transition: all 0.2s ease;
}

.stDataFrame tbody tr:hover {
    background-color: var(--border-accent) !important;
    transform: translateX(2px);
}

div[data-testid="stMarkdownContainer"] p {
    color: var(--text-muted);
    line-height: 1.7;
    font-size: 0.9rem;
}

div[data-testid="stMarkdownContainer"] em {
    color: var(--text-dim);
    font-style: italic;
    font-family: 'Newsreader', serif !important;
}

.stCodeBlock {
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border-subtle) !important;
    border-left: 3px solid var(--accent-primary) !important;
}

code {
    background: var(--bg-elevated) !important;
    color: var(--accent-secondary) !important;
    padding: 0.2rem 0.4rem !important;
    border-radius: 3px !important;
    font-size: 0.85em !important;
}

hr {
    border: none !important;
    height: 1px !important;
    background: linear-gradient(90deg, transparent, var(--border-subtle), transparent) !important;
    margin: 4rem 0 !important;
    opacity: 1 !important;
}

[data-testid="stSidebar"] .stMarkdown strong {
    color: var(--text-primary);
    font-weight: 600;
}

@keyframes slideInRight {
    from {
        opacity: 0;
        transform: translateX(-20px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

[data-testid="stMetric"] {
    animation: slideInRight 0.6s cubic-bezier(0.4, 0, 0.2, 1) forwards;
    opacity: 0;
}

[data-testid="stMetric"]:nth-child(1) { animation-delay: 0.1s; }
[data-testid="stMetric"]:nth-child(2) { animation-delay: 0.2s; }
[data-testid="stMetric"]:nth-child(3) { animation-delay: 0.3s; }
[data-testid="stMetric"]:nth-child(4) { animation-delay: 0.4s; }

h2 {
    animation: fadeInUp 0.6s ease forwards;
}

.element-container:has(.stPlotlyChart) {
    animation: fadeInUp 0.8s ease forwards;
    opacity: 0;
}

.element-container:has(.stPlotlyChart):nth-of-type(1) { animation-delay: 0.2s; }
.element-container:has(.stPlotlyChart):nth-of-type(2) { animation-delay: 0.3s; }
.element-container:has(.stPlotlyChart):nth-of-type(3) { animation-delay: 0.4s; }
.element-container:has(.stPlotlyChart):nth-of-type(4) { animation-delay: 0.5s; }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

@st.cache_resource
def get_snowflake_connection():
    """Create Snowflake connection using secrets."""
    try:
        conn = snowflake.connector.connect(
            user=st.secrets["snowflake"]["user"],
            password=st.secrets["snowflake"]["password"],
            account=st.secrets["snowflake"]["account"],
            warehouse=st.secrets["snowflake"]["warehouse"],
            database=st.secrets["snowflake"]["database"],
            schema=st.secrets["snowflake"]["schema"],
            insecure_mode=True
        )
        return conn
    except Exception as e:
        st.markdown(f"Connection failed: {e}")
        st.markdown("Configure credentials in `.streamlit/secrets.toml`")
        return None

@st.cache_data(ttl=600)
def load_data(_conn):
    """Load churn features data from Snowflake."""
    query = "SELECT * FROM CHURN_ANALYTICS.ANALYTICS.churn_features"
    df = pd.read_sql(query, _conn)
    
    if df.empty:
        raise ValueError("No data returned from churn_features table")
    
    df.columns = df.columns.str.lower()
    
    required_columns = ['cohort_month', 'signup_date', 'customer_id', 'churn_flag', 
                       'churn_risk_score', 'estimated_lifetime_value', 'segment', 
                       'contract_type', 'age_group', 'rfm_segment']
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}. Available columns: {list(df.columns)}")
    
    df['cohort_month'] = pd.to_datetime(df['cohort_month'])
    df['signup_date'] = pd.to_datetime(df['signup_date'])
    if 'last_transaction_date' in df.columns:
        df['last_transaction_date'] = pd.to_datetime(df['last_transaction_date'])
    if 'last_payment_date' in df.columns:
        df['last_payment_date'] = pd.to_datetime(df['last_payment_date'])
    
    return df

def create_kpi_cards(df):
    """Create KPI metrics cards."""
    total_customers = len(df)
    churned_customers = df['churn_flag'].sum()
    churn_rate = (churned_customers / total_customers * 100) if total_customers > 0 else 0
    avg_ltv = df['estimated_lifetime_value'].mean()
    at_risk_customers = len(df[df['churn_risk_score'] >= 65])
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Customers",
            value=f"{total_customers:,}",
            delta=None
        )
    
    with col2:
        st.metric(
            label="Churn Rate",
            value=f"{churn_rate:.1f}%",
            delta=f"-{churned_customers:,} customers",
            delta_color="inverse"
        )
    
    with col3:
        st.metric(
            label="Avg Lifetime Value",
            value=f"${avg_ltv:.2f}",
            delta=None
        )
    
    with col4:
        st.metric(
            label="At-Risk Customers",
            value=f"{at_risk_customers:,}",
            delta=f"{at_risk_customers/total_customers*100:.1f}% of total",
            delta_color="inverse"
        )

def create_cohort_chart(df):
    """Create churn rate by cohort line chart."""
    cohort_data = df.groupby('cohort_month').agg({
        'customer_id': 'count',
        'churn_flag': 'sum'
    }).reset_index()
    
    cohort_data['churn_rate'] = (cohort_data['churn_flag'] / cohort_data['customer_id'] * 100)
    cohort_data['cohort_month'] = cohort_data['cohort_month'].dt.strftime('%Y-%m')
    
    fig = px.line(
        cohort_data,
        x='cohort_month',
        y='churn_rate',
        markers=True,
        title='Cohort Churn Analysis',
        labels={'cohort_month': 'Cohort Period', 'churn_rate': 'Churn Rate (%)'}
    )
    
    fig.update_layout(
        hovermode='x unified',
        height=380,
        plot_bgcolor='#1a1d23',
        paper_bgcolor='#1a1d23',
        font=dict(color='#8b92a0', family='JetBrains Mono', size=10),
        title_font=dict(size=13, color='#f8f9fa', family='Newsreader'),
        xaxis=dict(
            gridcolor='#252830',
            showgrid=True,
            gridwidth=1,
            zeroline=False
        ),
        yaxis=dict(
            gridcolor='#252830',
            showgrid=True,
            gridwidth=1,
            zeroline=False
        ),
        margin=dict(l=60, r=20, t=60, b=60)
    )
    
    fig.update_traces(
        line=dict(color='#ff6b35', width=2.5),
        marker=dict(size=7, color='#f7931e', line=dict(width=2, color='#ff6b35'))
    )
    
    return fig

def create_rfm_scatter(df):
    """Create RFM scatter plot."""
    sample_df = df.sample(n=min(1000, len(df)), random_state=42)
    
    fig = px.scatter(
        sample_df,
        x='recency_days',
        y='monetary',
        size='frequency',
        color='churn_flag',
        hover_data=['first_name', 'last_name', 'rfm_segment', 'churn_risk_score'],
        title='RFM Customer Positioning',
        labels={
            'recency_days': 'Days Since Last Transaction',
            'monetary': 'Total Value ($)',
            'frequency': 'Transaction Count',
            'churn_flag': 'Status'
        },
        color_discrete_map={0: '#00d9a3', 1: '#ff4757'}
    )
    
    fig.update_layout(
        height=480,
        hovermode='closest',
        plot_bgcolor='#1a1d23',
        paper_bgcolor='#1a1d23',
        font=dict(color='#8b92a0', family='JetBrains Mono', size=10),
        title_font=dict(size=13, color='#f8f9fa', family='Newsreader'),
        xaxis=dict(gridcolor='#252830', showgrid=True, zeroline=False),
        yaxis=dict(gridcolor='#252830', showgrid=True, zeroline=False),
        legend=dict(
            bgcolor='#16181d',
            bordercolor='#252830',
            borderwidth=1,
            font=dict(size=10)
        ),
        margin=dict(l=60, r=20, t=60, b=60)
    )
    
    return fig

def create_segment_distribution(df):
    """Create RFM segment distribution chart."""
    segment_data = df['rfm_segment'].value_counts().reset_index()
    segment_data.columns = ['segment', 'count']
    segment_data = segment_data.sort_values('count', ascending=True)
    
    fig = px.bar(
        segment_data,
        x='count',
        y='segment',
        orientation='h',
        title='Segment Distribution',
        labels={'count': 'Customer Count', 'segment': ''},
        color='count',
        color_continuous_scale=[
            [0, '#252830'],
            [0.3, 'rgba(255, 107, 53, 0.25)'],
            [0.7, '#ff6b35'],
            [1, '#f7931e']
        ]
    )
    
    fig.update_layout(
        height=480,
        plot_bgcolor='#1a1d23',
        paper_bgcolor='#1a1d23',
        font=dict(color='#8b92a0', family='JetBrains Mono', size=10),
        title_font=dict(size=13, color='#f8f9fa', family='Newsreader'),
        xaxis=dict(gridcolor='#252830', showgrid=True, zeroline=False),
        yaxis=dict(gridcolor='#252830', showgrid=False),
        coloraxis_colorbar=dict(
            bgcolor='#16181d',
            bordercolor='#252830',
            borderwidth=1,
            thickness=12,
            len=0.7
        ),
        margin=dict(l=120, r=20, t=60, b=60)
    )
    
    fig.update_traces(marker_line=dict(width=0))
    
    return fig

def create_churn_by_contract(df):
    """Create churn rate by contract type chart."""
    contract_data = df.groupby('contract_type').agg({
        'customer_id': 'count',
        'churn_flag': 'sum'
    }).reset_index()
    
    contract_data['churn_rate'] = (contract_data['churn_flag'] / contract_data['customer_id'] * 100)
    
    colors = ['#ff6b35' if rate == contract_data['churn_rate'].max() 
              else 'rgba(255, 107, 53, 0.5)' for rate in contract_data['churn_rate']]
    
    fig = go.Figure(data=[
        go.Bar(
            x=contract_data['contract_type'],
            y=contract_data['churn_rate'],
            text=contract_data['churn_rate'].round(1),
            texttemplate='<b>%{text}%</b>',
            textposition='outside',
            textfont=dict(size=14, color='#f8f9fa', family='JetBrains Mono'),
            marker=dict(
                color=colors,
                line=dict(width=0)
            ),
            hovertemplate='<b>%{x}</b><br>Churn Rate: %{y:.1f}%<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title='Contract Type Churn Rates',
        xaxis_title='',
        yaxis_title='Churn Rate (%)',
        height=380,
        plot_bgcolor='#1a1d23',
        paper_bgcolor='#1a1d23',
        font=dict(color='#8b92a0', family='JetBrains Mono', size=10),
        title_font=dict(size=13, color='#f8f9fa', family='Newsreader'),
        xaxis=dict(gridcolor='#252830', showgrid=False),
        yaxis=dict(gridcolor='#252830', showgrid=True, zeroline=False),
        margin=dict(l=60, r=20, t=60, b=60),
        showlegend=False
    )
    
    return fig

def display_at_risk_table(df):
    """Display at-risk customers table."""
    at_risk_df = df[df['churn_risk_score'] >= 65].sort_values('churn_risk_score', ascending=False)
    
    display_columns = [
        'first_name', 'last_name', 'email', 'churn_risk_score',
        'rfm_segment', 'monetary', 'frequency', 'recency_days',
        'recommended_action'
    ]
    
    available_columns = [col for col in display_columns if col in at_risk_df.columns]
    
    st.dataframe(
        at_risk_df[available_columns].head(50),
        use_container_width=True,
        hide_index=True
    )

def main():
    """Main application function."""
    st.markdown(f'<p style="font-family: JetBrains Mono; font-size: 0.7rem; color: #5a6070; margin-bottom: 1rem; text-transform: uppercase; letter-spacing: 0.1em;">Report Generated: {datetime.now().strftime("%B %d, %Y — %H:%M")}</p>', unsafe_allow_html=True)
    st.title("Retention Intelligence Report")
    st.markdown("#### Predictive analytics and strategic insights for customer lifecycle optimization")
    
    st.sidebar.header("Filters")
    
    conn = get_snowflake_connection()
    
    if conn is None:
        st.markdown("### Configuration Required")
        st.markdown("Configure Snowflake connection in `.streamlit/secrets.toml`")
        st.code("""[snowflake]
user = "your_username"
password = "your_password"
account = "your_account"
warehouse = "ANALYTICS_WH"
database = "CHURN_ANALYTICS"
schema = "ANALYTICS"
        """)
        return
    
    try:
        df = load_data(conn)
        
        if df.empty:
            st.markdown("### No Data Available")
            st.markdown("Run dbt models to generate data: `cd churn_project && dbt run`")
            return
        
        segments = ['All'] + sorted(df['segment'].unique().tolist())
        selected_segment = st.sidebar.selectbox("Customer Segment", segments)
        
        contract_types = ['All'] + sorted(df['contract_type'].unique().tolist())
        selected_contract = st.sidebar.selectbox("Contract Type", contract_types)
        
        age_groups = ['All'] + sorted(df['age_group'].unique().tolist())
        selected_age_group = st.sidebar.selectbox("Age Group", age_groups)
        
        churn_status = st.sidebar.radio("Churn Status", ['All', 'Active Only', 'Churned Only'])
        
        filtered_df = df.copy()
        
        if selected_segment != 'All':
            filtered_df = filtered_df[filtered_df['segment'] == selected_segment]
        
        if selected_contract != 'All':
            filtered_df = filtered_df[filtered_df['contract_type'] == selected_contract]
        
        if selected_age_group != 'All':
            filtered_df = filtered_df[filtered_df['age_group'] == selected_age_group]
        
        if churn_status == 'Active Only':
            filtered_df = filtered_df[filtered_df['churn_flag'] == 0]
        elif churn_status == 'Churned Only':
            filtered_df = filtered_df[filtered_df['churn_flag'] == 1]
        
        st.sidebar.markdown(f"**Showing {len(filtered_df):,} of {len(df):,} customers**")
        
        st.markdown("---")
        st.subheader("Performance Overview")
        create_kpi_cards(filtered_df)
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(create_cohort_chart(filtered_df), use_container_width=True)
        
        with col2:
            st.plotly_chart(create_churn_by_contract(filtered_df), use_container_width=True)
        
        st.markdown("---")
        
        col3, col4 = st.columns(2)
        
        with col3:
            st.plotly_chart(create_rfm_scatter(filtered_df), use_container_width=True)
        
        with col4:
            st.plotly_chart(create_segment_distribution(filtered_df), use_container_width=True)
        
        st.markdown("---")
        st.subheader("At-Risk Customer Portfolio")
        
        at_risk_count = len(filtered_df[filtered_df['churn_risk_score'] >= 65])
        st.markdown(f"*{at_risk_count:,} customers identified as high-risk and requiring immediate intervention*")
        
        display_at_risk_table(filtered_df)
        
        st.markdown("---")
        st.subheader("Financial Impact Analysis")
        
        potential_revenue_loss = filtered_df[filtered_df['churn_flag'] == 1]['estimated_lifetime_value'].sum()
        at_risk_revenue = filtered_df[filtered_df['churn_risk_score'] >= 65]['estimated_lifetime_value'].sum()
        total_ltv = filtered_df['estimated_lifetime_value'].sum()
        
        impact_col1, impact_col2, impact_col3 = st.columns(3)
        
        with impact_col1:
            st.metric(
                "Total Lifetime Value",
                f"${total_ltv:,.0f}",
                delta=f"{len(filtered_df):,} customers"
            )
        
        with impact_col2:
            st.metric(
                "Revenue at Risk",
                f"${at_risk_revenue:,.0f}",
                delta=f"{(at_risk_revenue/total_ltv*100):.1f}% of total",
                delta_color="inverse"
            )
        
        with impact_col3:
            st.metric(
                "Lost to Churn",
                f"${potential_revenue_loss:,.0f}",
                delta=f"{(potential_revenue_loss/total_ltv*100):.1f}% of total",
                delta_color="inverse"
            )
        
    except Exception as e:
        st.markdown("### Error Loading Data")
        st.code(str(e))
        st.markdown("""
        **Troubleshooting:**
        
        1. Run dbt models: `cd churn_project && dbt run`
        2. Verify table: `dbt run --select churn_features`
        3. Check Snowflake connection settings
        """)
    
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
