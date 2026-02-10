"""
Retail Customer Churn Prediction & Retention Dashboard
A Streamlit application for visualizing customer churn patterns and retention strategies.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import snowflake.connector
from datetime import datetime

st.set_page_config(
    page_title="Customer Churn Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
            schema=st.secrets["snowflake"]["schema"]
        )
        return conn
    except Exception as e:
        st.error(f"Failed to connect to Snowflake: {e}")
        st.info("Please configure your Snowflake credentials in .streamlit/secrets.toml")
        return None

@st.cache_data(ttl=600)
def load_data(_conn):
    """Load churn features data from Snowflake."""
    query = "SELECT * FROM churn_features"
    df = pd.read_sql(query, _conn)
    
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
        title='Churn Rate by Signup Cohort',
        labels={'cohort_month': 'Cohort Month', 'churn_rate': 'Churn Rate (%)'}
    )
    
    fig.update_layout(
        hovermode='x unified',
        height=400
    )
    
    fig.update_traces(
        line_color='#FF4B4B',
        marker=dict(size=8)
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
        title='RFM Analysis: Recency vs Monetary Value',
        labels={
            'recency_days': 'Recency (Days Since Last Transaction)',
            'monetary': 'Monetary Value ($)',
            'frequency': 'Transaction Frequency',
            'churn_flag': 'Churned'
        },
        color_discrete_map={0: '#00CC96', 1: '#FF4B4B'}
    )
    
    fig.update_layout(
        height=500,
        hovermode='closest'
    )
    
    return fig

def create_segment_distribution(df):
    """Create RFM segment distribution chart."""
    segment_data = df['rfm_segment'].value_counts().reset_index()
    segment_data.columns = ['segment', 'count']
    
    fig = px.bar(
        segment_data,
        x='count',
        y='segment',
        orientation='h',
        title='Customer Distribution by RFM Segment',
        labels={'count': 'Number of Customers', 'segment': 'RFM Segment'},
        color='count',
        color_continuous_scale='Blues'
    )
    
    fig.update_layout(height=500)
    
    return fig

def create_churn_by_contract(df):
    """Create churn rate by contract type chart."""
    contract_data = df.groupby('contract_type').agg({
        'customer_id': 'count',
        'churn_flag': 'sum'
    }).reset_index()
    
    contract_data['churn_rate'] = (contract_data['churn_flag'] / contract_data['customer_id'] * 100)
    
    fig = go.Figure(data=[
        go.Bar(
            x=contract_data['contract_type'],
            y=contract_data['churn_rate'],
            text=contract_data['churn_rate'].round(1),
            texttemplate='%{text}%',
            textposition='outside',
            marker_color=['#FF6B6B', '#FFA500', '#4ECDC4']
        )
    ])
    
    fig.update_layout(
        title='Churn Rate by Contract Type',
        xaxis_title='Contract Type',
        yaxis_title='Churn Rate (%)',
        height=400
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
    st.title("📊 Retail Customer Churn Prediction & Retention Dashboard")
    st.markdown("### Predict churn, identify at-risk customers, and recommend retention strategies")
    
    st.sidebar.header("🎛️ Filters")
    
    conn = get_snowflake_connection()
    
    if conn is None:
        st.warning("Please configure Snowflake connection in `.streamlit/secrets.toml`")
        st.code("""
# .streamlit/secrets.toml
[snowflake]
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
            st.error("No data available. Please run dbt models first.")
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
        st.subheader("📈 Key Performance Indicators")
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
        st.subheader("🚨 High-Risk Customers Requiring Immediate Action")
        
        at_risk_count = len(filtered_df[filtered_df['churn_risk_score'] >= 65])
        st.info(f"**{at_risk_count:,} customers** are at high risk of churning and require immediate attention.")
        
        display_at_risk_table(filtered_df)
        
        st.markdown("---")
        st.markdown("### 💡 Business Impact")
        
        potential_revenue_loss = filtered_df[filtered_df['churn_flag'] == 1]['estimated_lifetime_value'].sum()
        at_risk_revenue = filtered_df[filtered_df['churn_risk_score'] >= 65]['estimated_lifetime_value'].sum()
        
        impact_col1, impact_col2 = st.columns(2)
        
        with impact_col1:
            st.metric(
                "Revenue Lost to Churn",
                f"${potential_revenue_loss:,.2f}",
                delta="Already churned"
            )
        
        with impact_col2:
            st.metric(
                "At-Risk Revenue",
                f"${at_risk_revenue:,.2f}",
                delta="Can be saved with retention efforts"
            )
        
        st.success("""
        **Recommended Actions:**
        - Implement targeted retention campaigns for high-risk customers
        - Offer personalized discounts and loyalty rewards
        - Conduct customer satisfaction surveys to identify pain points
        - Provide proactive customer support for at-risk segments
        - Monitor month-to-month contract customers closely
        """)
        
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.info("Make sure you have run `dbt run` to create the churn_features table in Snowflake.")
    
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
