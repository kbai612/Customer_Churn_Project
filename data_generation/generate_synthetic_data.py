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

NUM_CUSTOMERS = 5000
TARGET_CHURN_RATE = 0.27
CHURN_THRESHOLD_DAYS = 90

def generate_customers():
    """Generate customer data with demographics and signup information."""
    print("Generating customers data...")
    
    customers = []
    signup_start = datetime(2022, 1, 1)
    signup_end = datetime(2025, 6, 30)
    
    for _ in range(NUM_CUSTOMERS):
        signup_date = fake.date_between(start_date=signup_start, end_date=signup_end)
        
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
            'segment': np.random.choice(['Consumer', 'Corporate', 'Home Office'], p=[0.6, 0.25, 0.15])
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
            days_since_last_payment = np.random.randint(CHURN_THRESHOLD_DAYS + 1, min(tenure_days, 365))
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
        is_churned = customer['is_active'] == 0
        last_payment_date = customer['last_payment_date']
        
        tenure_days = (current_date - signup_date).days
        
        if is_churned:
            num_transactions = max(1, int(np.random.poisson(5)))
            transaction_end_date = last_payment_date - timedelta(days=np.random.randint(0, 60))
        else:
            base_transactions = max(1, tenure_days // 30)
            num_transactions = int(np.random.poisson(base_transactions * 0.8))
            transaction_end_date = current_date - timedelta(days=np.random.randint(0, 7))
        
        transaction_start_date = max(signup_date, transaction_end_date - timedelta(days=tenure_days))
        
        for _ in range(num_transactions):
            transaction_date = fake.date_between(
                start_date=transaction_start_date,
                end_date=transaction_end_date
            )
            
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
    
    print("=" * 50)
    print("Saving data to CSV files...")
    
    customers_df.to_csv('data_generation/customers.csv', index=False)
    print(f"Saved customers.csv ({len(customers_df)} rows)")
    
    subscriptions_df.to_csv('data_generation/subscriptions.csv', index=False)
    print(f"Saved subscriptions.csv ({len(subscriptions_df)} rows)")
    
    transactions_df.to_csv('data_generation/transactions.csv', index=False)
    print(f"Saved transactions.csv ({len(transactions_df)} rows)")
    
    print("=" * 50)
    print("Data generation completed successfully!")
    print("\nSummary Statistics:")
    print(f"Total Customers: {len(customers_df)}")
    print(f"Total Transactions: {len(transactions_df)}")
    print(f"Churn Rate: {(subscriptions_df['is_active'] == 0).sum() / len(subscriptions_df):.2%}")
    print(f"Avg Transactions per Customer: {len(transactions_df) / len(customers_df):.1f}")

if __name__ == "__main__":
    main()
