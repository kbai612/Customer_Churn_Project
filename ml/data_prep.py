"""
Data Preparation Module for Churn Prediction
Handles data loading, feature selection, encoding, and train/test split
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
import snowflake.connector
import pickle
import os

CHURN_THRESHOLD_DAYS = 90

FEATURE_COLUMNS = [
    'tenure_months',
    'tenure_days',
    'monthly_charges',
    'contract_type',
    'plan_type',
    'recency_days',
    'frequency',
    'monetary',
    'avg_transaction_value',
    'total_transactions',
    'days_since_last_transaction',
    'recency_score',
    'frequency_score',
    'monetary_score',
    'rfm_composite_score',
    'total_events',
    'active_days',
    'login_count',
    'feature_usage_count',
    'support_ticket_count',
    'app_crash_count',
    'engagement_rate',
    'avg_events_per_active_day',
    'avg_session_duration_minutes',
    'days_since_last_event',
    'events_last_7_days',
    'events_last_30_days',
    'events_last_90_days',
    'logins_last_30_days',
    'feature_usage_last_30_days',
    'days_since_last_login',
    'features_per_login',
    'problem_event_rate_pct',
    'engagement_recency_score',
    'engagement_frequency_score',
    'feature_adoption_score',
    'engagement_composite_score',
    'age',
    'gender',
    'segment',
    'acquisition_channel',
    'device_type',
    'initial_referral_credits',
]

CATEGORICAL_COLUMNS = [
    'contract_type',
    'plan_type',
    'gender',
    'segment',
    'acquisition_channel',
    'device_type',
]

TARGET_COLUMN = 'churn_flag'


def load_data_from_snowflake(credentials):
    """
    Load churn_features data from Snowflake
    
    Args:
        credentials (dict): Snowflake connection credentials
        
    Returns:
        pd.DataFrame: Raw data from churn_features mart
    """
    conn = snowflake.connector.connect(
        account=credentials['account'],
        user=credentials['user'],
        password=credentials['password'],
        warehouse=credentials['warehouse'],
        database=credentials['database'],
        schema=credentials['schema'],
        role=credentials.get('role', 'ACCOUNTADMIN')
    )
    
    query = "SELECT * FROM churn_features"
    df = pd.read_sql(query, conn)
    conn.close()
    
    return df


def load_data_from_csv(csv_path):
    """
    Load churn_features data from CSV export
    
    Args:
        csv_path (str): Path to CSV file
        
    Returns:
        pd.DataFrame: Raw data
    """
    # Auto-detect compression (handles .gz files automatically)
    df = pd.read_csv(csv_path, compression='infer', encoding='utf-8')
    
    # Normalize column names to lowercase (Snowflake exports uppercase)
    df.columns = df.columns.str.lower()
    
    return df


def prepare_features(df, feature_cols=None, categorical_cols=None, target_col=TARGET_COLUMN):
    """
    Prepare features for modeling:
    - Select relevant columns
    - Handle missing values
    - Encode categorical variables
    
    Args:
        df (pd.DataFrame): Raw data
        feature_cols (list): List of feature column names
        categorical_cols (list): List of categorical column names
        target_col (str): Target column name
        
    Returns:
        tuple: (X, y, feature_names, encoders)
    """
    if feature_cols is None:
        feature_cols = FEATURE_COLUMNS
    if categorical_cols is None:
        categorical_cols = CATEGORICAL_COLUMNS
    
    df_work = df.copy()
    
    available_features = [col for col in feature_cols if col in df_work.columns]
    missing_features = [col for col in feature_cols if col not in df_work.columns]
    if missing_features:
        print(f"Warning: The following features are not in the dataset: {missing_features}")
    
    if target_col not in df_work.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataset")
    
    X_raw = df_work[available_features].copy()
    y = df_work[target_col].copy()
    
    for col in X_raw.columns:
        if X_raw[col].dtype in ['object', 'category']:
            X_raw[col].fillna('MISSING', inplace=True)
        else:
            X_raw[col].fillna(X_raw[col].median(), inplace=True)
    
    encoders = {}
    X_encoded = X_raw.copy()
    
    for col in categorical_cols:
        if col in X_encoded.columns:
            le = LabelEncoder()
            X_encoded[col] = le.fit_transform(X_encoded[col].astype(str))
            encoders[col] = le
    
    feature_names = X_encoded.columns.tolist()
    
    return X_encoded, y, feature_names, encoders


def create_train_test_split(X, y, test_size=0.2, random_state=42):
    """
    Create stratified train/test split
    
    Args:
        X (pd.DataFrame): Features
        y (pd.Series): Target
        test_size (float): Proportion of test set
        random_state (int): Random seed
        
    Returns:
        tuple: (X_train, X_test, y_train, y_test)
    """
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=test_size,
        stratify=y,
        random_state=random_state
    )
    
    return X_train, X_test, y_train, y_test


def scale_features(X_train, X_test):
    """
    Scale features using StandardScaler
    
    Args:
        X_train (pd.DataFrame): Training features
        X_test (pd.DataFrame): Test features
        
    Returns:
        tuple: (X_train_scaled, X_test_scaled, scaler)
    """
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    X_train_scaled = pd.DataFrame(X_train_scaled, columns=X_train.columns, index=X_train.index)
    X_test_scaled = pd.DataFrame(X_test_scaled, columns=X_test.columns, index=X_test.index)
    
    return X_train_scaled, X_test_scaled, scaler


def save_preprocessors(encoders, scaler, feature_names, output_dir='ml/artifacts'):
    """
    Save preprocessing artifacts for inference
    
    Args:
        encoders (dict): Label encoders for categorical features
        scaler (StandardScaler): Feature scaler
        feature_names (list): List of feature names in order
        output_dir (str): Directory to save artifacts
    """
    os.makedirs(output_dir, exist_ok=True)
    
    with open(f'{output_dir}/encoders.pkl', 'wb') as f:
        pickle.dump(encoders, f)
    
    with open(f'{output_dir}/scaler.pkl', 'wb') as f:
        pickle.dump(scaler, f)
    
    with open(f'{output_dir}/feature_names.pkl', 'wb') as f:
        pickle.dump(feature_names, f)
    
    print(f"Preprocessors saved to {output_dir}")


def load_preprocessors(input_dir='ml/artifacts'):
    """
    Load preprocessing artifacts for inference
    
    Args:
        input_dir (str): Directory containing artifacts
        
    Returns:
        tuple: (encoders, scaler, feature_names)
    """
    with open(f'{input_dir}/encoders.pkl', 'rb') as f:
        encoders = pickle.load(f)
    
    with open(f'{input_dir}/scaler.pkl', 'rb') as f:
        scaler = pickle.load(f)
    
    with open(f'{input_dir}/feature_names.pkl', 'rb') as f:
        feature_names = pickle.load(f)
    
    return encoders, scaler, feature_names


def prepare_data_pipeline(data_source, credentials=None, csv_path=None, 
                          test_size=0.2, random_state=42, scale=True):
    """
    Complete data preparation pipeline
    
    Args:
        data_source (str): 'snowflake' or 'csv'
        credentials (dict): Snowflake credentials (if data_source='snowflake')
        csv_path (str): Path to CSV file (if data_source='csv')
        test_size (float): Test set proportion
        random_state (int): Random seed
        scale (bool): Whether to scale features
        
    Returns:
        dict: Dictionary containing all prepared data and artifacts
    """
    if data_source == 'snowflake':
        if credentials is None:
            raise ValueError("Credentials required for Snowflake connection")
        df = load_data_from_snowflake(credentials)
    elif data_source == 'csv':
        if csv_path is None:
            raise ValueError("CSV path required for CSV loading")
        df = load_data_from_csv(csv_path)
    else:
        raise ValueError("data_source must be 'snowflake' or 'csv'")
    
    print(f"Loaded {len(df)} records")
    
    # Check if target column exists
    if TARGET_COLUMN not in df.columns:
        print(f"\nERROR: Target column '{TARGET_COLUMN}' not found!")
        print(f"Available columns ({len(df.columns)}): {', '.join(df.columns.tolist()[:20])}")
        if len(df.columns) > 20:
            print(f"... and {len(df.columns) - 20} more columns")
        raise ValueError(f"Target column '{TARGET_COLUMN}' not found in dataset. Check that you exported the correct table.")
    
    print(f"Churn rate: {df[TARGET_COLUMN].mean():.2%}")
    
    X, y, feature_names, encoders = prepare_features(df)
    print(f"Prepared {len(feature_names)} features")
    
    X_train, X_test, y_train, y_test = create_train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )
    print(f"Train set: {len(X_train)} records")
    print(f"Test set: {len(X_test)} records")
    
    if scale:
        X_train, X_test, scaler = scale_features(X_train, X_test)
        print("Features scaled")
    else:
        scaler = None
    
    return {
        'X_train': X_train,
        'X_test': X_test,
        'y_train': y_train,
        'y_test': y_test,
        'feature_names': feature_names,
        'encoders': encoders,
        'scaler': scaler,
        'raw_data': df
    }


if __name__ == '__main__':
    print("Data Preparation Module")
    print("This module is meant to be imported by train_model.py")
    print("\nAvailable features:")
    for i, feat in enumerate(FEATURE_COLUMNS, 1):
        print(f"{i}. {feat}")
