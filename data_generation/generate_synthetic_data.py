"""
Synthetic Data Generator for Retail Customer Churn Project
Generates realistic customer, transaction, and subscription data with churn patterns.
"""

import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta
import uuid
import random

fake = Faker()
Faker.seed(42)
np.random.seed(42)
random.seed(42)

NUM_CUSTOMERS = 25000
TARGET_CHURN_RATE = 0.27
CHURN_THRESHOLD_DAYS = 90
ENGAGEMENT_DECAY_RATE = 0.15

def generate_customers():
    """Generate customer data with demographics, acquisition, and engagement information."""
    print("Generating customers data...")
    
    customers = []
    signup_start = datetime(2022, 1, 1)
    signup_end = datetime(2025, 6, 30)
    
    acquisition_channels = ['Organic Search', 'Paid Search', 'Social Media', 'Referral', 'Email', 'Direct']
    device_types = ['Desktop', 'Mobile', 'Tablet']
    timezones = ['America/New_York', 'America/Chicago', 'America/Denver', 'America/Los_Angeles', 
                 'America/Toronto', 'Europe/London', 'Asia/Tokyo']
    
    for _ in range(NUM_CUSTOMERS):
        signup_date = fake.date_between(start_date=signup_start, end_date=signup_end)
        if not isinstance(signup_date, datetime):
            signup_date = datetime.combine(signup_date, datetime.min.time())
        
        acquisition_channel = np.random.choice(acquisition_channels, p=[0.25, 0.20, 0.20, 0.15, 0.10, 0.10])
        
        customer = {
            'customer_id': str(uuid.uuid4()),
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
            'email': fake.email(),
            'age': np.random.randint(18, 76),
            'gender': np.random.choice(['Male', 'Female', 'Other'], p=[0.48, 0.48, 0.04]),
            'signup_date': signup_date,
            'city': fake.city(),
            'state': fake.state_abbr(),
            'segment': np.random.choice(['Consumer', 'Corporate', 'Home Office'], p=[0.6, 0.25, 0.15]),
            'acquisition_channel': acquisition_channel,
            'device_type': np.random.choice(device_types, p=[0.45, 0.45, 0.10]),
            'timezone': np.random.choice(timezones),
            'preferred_language': np.random.choice(['English', 'Spanish', 'French'], p=[0.80, 0.15, 0.05]),
            'customer_lifetime_days': (datetime(2026, 2, 10) - signup_date).days,
            'initial_referral_credits': np.random.randint(0, 51) if acquisition_channel == 'Referral' else 0
        }
        customers.append(customer)
    
    df = pd.DataFrame(customers)
    print(f"Generated {len(df)} customers")
    return df

def generate_subscriptions(customers_df):
    """Generate subscription data with churn probability based on contract type and tenure."""
    print("Generating subscriptions data...")
    
    subscriptions = []
    current_date = datetime(2026, 2, 10)
    
    for _, customer in customers_df.iterrows():
        signup_date = customer['signup_date']
        tenure_days = (current_date - signup_date).days
        
        contract_type = np.random.choice(
            ['Month-to-month', 'One year', 'Two year'],
            p=[0.55, 0.30, 0.15]
        )
        
        plan_type = np.random.choice(
            ['Basic', 'Standard', 'Premium'],
            p=[0.40, 0.35, 0.25]
        )
        
        if plan_type == 'Basic':
            monthly_charges = round(np.random.uniform(9.99, 29.99), 2)
        elif plan_type == 'Standard':
            monthly_charges = round(np.random.uniform(30.00, 54.99), 2)
        else:
            monthly_charges = round(np.random.uniform(55.00, 79.99), 2)
        
        # Calculate churn probability
        churn_prob = 0.15
        if contract_type == 'Month-to-month':
            churn_prob += 0.20
        if tenure_days < 180:
            churn_prob += 0.15
        if monthly_charges > 60:
            churn_prob += 0.10
        if customer['age'] < 25:
            churn_prob += 0.05
        
        is_churned = np.random.random() < churn_prob
        
        if is_churned:
            max_days = min(tenure_days, 365)
            if max_days <= CHURN_THRESHOLD_DAYS + 1:
                days_since_last_payment = np.random.randint(max(1, tenure_days // 2), max(2, tenure_days))
            else:
                days_since_last_payment = np.random.randint(CHURN_THRESHOLD_DAYS + 1, max_days)
            last_payment_date = current_date - timedelta(days=days_since_last_payment)
            is_active = 0
        else:
            days_since_last_payment = np.random.randint(0, 30)
            last_payment_date = current_date - timedelta(days=days_since_last_payment)
            is_active = 1
        
        subscription = {
            'customer_id': customer['customer_id'],
            'plan_type': plan_type,
            'monthly_charges': monthly_charges,
            'contract_type': contract_type,
            'last_payment_date': last_payment_date,
            'is_active': is_active
        }
        subscriptions.append(subscription)
    
    df = pd.DataFrame(subscriptions)
    churn_rate = (df['is_active'] == 0).sum() / len(df)
    print(f"Generated {len(df)} subscriptions (Churn rate: {churn_rate:.2%})")
    return df

def generate_behavioral_events(customers_df, subscriptions_df):
    """Generate behavioral events for product analytics (logins, feature usage, support tickets)."""
    print("Generating behavioral events data...")
    
    merged = customers_df.merge(subscriptions_df, on='customer_id')
    events = []
    current_date = datetime(2026, 2, 10)
    
    event_types = {
        'login': 0.50,
        'feature_browse': 0.15,
        'feature_search': 0.10,
        'feature_checkout': 0.08,
        'feature_wishlist': 0.07,
        'feature_review': 0.05,
        'support_ticket': 0.03,
        'app_crash': 0.02
    }
    
    for _, customer in merged.iterrows():
        signup_date = customer['signup_date']
        if not isinstance(signup_date, datetime):
            signup_date = datetime.combine(signup_date, datetime.min.time())
        
        is_churned = customer['is_active'] == 0
        last_payment_date = customer['last_payment_date']
        if not isinstance(last_payment_date, datetime):
            last_payment_date = datetime.combine(last_payment_date, datetime.min.time())
        
        tenure_days = (current_date - signup_date).days
        
        if is_churned:
            event_end_date = last_payment_date - timedelta(days=np.random.randint(0, min(30, tenure_days // 4)))
            num_events = max(5, int(np.random.poisson(20)))
        else:
            event_end_date = current_date - timedelta(days=np.random.randint(0, 3))
            base_events = max(10, tenure_days // 7)
            num_events = int(np.random.poisson(base_events * 1.5))
        
        event_start_date = signup_date
        
        if not isinstance(event_start_date, datetime):
            event_start_date = datetime.combine(event_start_date, datetime.min.time())
        if not isinstance(event_end_date, datetime):
            event_end_date = datetime.combine(event_end_date, datetime.min.time())
        
        if event_start_date > event_end_date:
            event_start_date = event_end_date - timedelta(days=max(1, tenure_days // 3))
        
        for _ in range(num_events):
            event_date = fake.date_between(
                start_date=event_start_date,
                end_date=event_end_date
            )
            if not isinstance(event_date, datetime):
                event_date = datetime.combine(event_date, datetime.min.time())
            
            event_type = np.random.choice(
                list(event_types.keys()),
                p=list(event_types.values())
            )
            
            session_duration_minutes = np.random.exponential(scale=12) if event_type == 'login' else None
            if session_duration_minutes:
                session_duration_minutes = min(session_duration_minutes, 120)
            
            event = {
                'event_id': str(uuid.uuid4()),
                'customer_id': customer['customer_id'],
                'event_date': event_date,
                'event_type': event_type,
                'device_type': customer['device_type'],
                'session_duration_minutes': round(session_duration_minutes, 2) if session_duration_minutes else None,
                'pages_viewed': np.random.randint(1, 15) if event_type in ['login', 'feature_browse'] else None
            }
            events.append(event)
    
    df = pd.DataFrame(events)
    print(f"Generated {len(df)} behavioral events")
    return df

def generate_transactions(customers_df, subscriptions_df):
    """Generate transaction data with realistic patterns for active and churned customers."""
    print("Generating transactions data...")
    
    merged = customers_df.merge(subscriptions_df, on='customer_id')
    transactions = []
    current_date = datetime(2026, 2, 10)
    
    product_categories = ['Electronics', 'Clothing', 'Groceries', 'Home', 'Sports']
    payment_methods = ['Credit', 'Debit', 'Cash', 'Digital Wallet']
    
    for _, customer in merged.iterrows():
        signup_date = customer['signup_date']
        if not isinstance(signup_date, datetime):
            signup_date = datetime.combine(signup_date, datetime.min.time())
        
        is_churned = customer['is_active'] == 0
        last_payment_date = customer['last_payment_date']
        if not isinstance(last_payment_date, datetime):
            last_payment_date = datetime.combine(last_payment_date, datetime.min.time())
        
        tenure_days = (current_date - signup_date).days
        
        if is_churned:
            num_transactions = max(1, int(np.random.poisson(5)))
            transaction_end_date = last_payment_date - timedelta(days=np.random.randint(0, min(60, tenure_days // 2)))
        else:
            base_transactions = max(1, tenure_days // 30)
            num_transactions = int(np.random.poisson(base_transactions * 0.8))
            transaction_end_date = current_date - timedelta(days=np.random.randint(0, 7))
        
        transaction_start_date = signup_date
        
        if not isinstance(transaction_start_date, datetime):
            transaction_start_date = datetime.combine(transaction_start_date, datetime.min.time())
        if not isinstance(transaction_end_date, datetime):
            transaction_end_date = datetime.combine(transaction_end_date, datetime.min.time())
        
        if transaction_start_date > transaction_end_date:
            transaction_start_date = transaction_end_date - timedelta(days=max(1, tenure_days // 2))
        
        for _ in range(num_transactions):
            transaction_date = fake.date_between(
                start_date=transaction_start_date,
                end_date=transaction_end_date
            )
            if not isinstance(transaction_date, datetime):
                transaction_date = datetime.combine(transaction_date, datetime.min.time())
            
            product_category = np.random.choice(product_categories)
            quantity = np.random.randint(1, 6)
            
            if product_category == 'Electronics':
                unit_price = round(np.random.uniform(50, 500), 2)
            elif product_category == 'Clothing':
                unit_price = round(np.random.uniform(15, 150), 2)
            elif product_category == 'Groceries':
                unit_price = round(np.random.uniform(5, 50), 2)
            elif product_category == 'Home':
                unit_price = round(np.random.uniform(20, 300), 2)
            else:
                unit_price = round(np.random.uniform(10, 200), 2)
            
            total_amount = round(unit_price * quantity, 2)
            
            transaction = {
                'transaction_id': str(uuid.uuid4()),
                'customer_id': customer['customer_id'],
                'transaction_date': transaction_date,
                'product_category': product_category,
                'quantity': quantity,
                'unit_price': unit_price,
                'total_amount': total_amount,
                'payment_method': np.random.choice(payment_methods)
            }
            transactions.append(transaction)
    
    df = pd.DataFrame(transactions)
    print(f"Generated {len(df)} transactions")
    return df

def main():
    """Main function to generate all datasets and save to CSV."""
    print("Starting synthetic data generation...")
    print("=" * 50)
    
    customers_df = generate_customers()
    subscriptions_df = generate_subscriptions(customers_df)
    transactions_df = generate_transactions(customers_df, subscriptions_df)
    behavioral_events_df = generate_behavioral_events(customers_df, subscriptions_df)
    
    print("=" * 50)
    print("Saving data to CSV files...")
    
    customers_df.to_csv('data_generation/customers.csv', index=False)
    print(f"Saved customers.csv ({len(customers_df)} rows)")
    
    subscriptions_df.to_csv('data_generation/subscriptions.csv', index=False)
    print(f"Saved subscriptions.csv ({len(subscriptions_df)} rows)")
    
    transactions_df.to_csv('data_generation/transactions.csv', index=False)
    print(f"Saved transactions.csv ({len(transactions_df)} rows)")
    
    behavioral_events_df.to_csv('data_generation/behavioral_events.csv', index=False)
    print(f"Saved behavioral_events.csv ({len(behavioral_events_df)} rows)")
    
    print("=" * 50)
    print("Data generation completed successfully!")
    print("\nSummary Statistics:")
    print(f"Total Customers: {len(customers_df)}")
    print(f"Total Transactions: {len(transactions_df)}")
    print(f"Total Behavioral Events: {len(behavioral_events_df)}")
    print(f"Churn Rate: {(subscriptions_df['is_active'] == 0).sum() / len(subscriptions_df):.2%}")
    print(f"Avg Transactions per Customer: {len(transactions_df) / len(customers_df):.1f}")
    print(f"Avg Events per Customer: {len(behavioral_events_df) / len(customers_df):.1f}")

if __name__ == "__main__":
    main()
