"""
Example Usage of the ML Churn Prediction Module
Demonstrates how to use the various components of the ML pipeline
"""

import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.data_prep import prepare_data_pipeline
from ml.train_model import train_pipeline
from ml.predict import (
    load_best_model,
    load_model_metrics,
    load_feature_importance,
    get_model_comparison,
    predict_churn,
    predict_single_customer,
    load_preprocessors
)


def example_1_train_models():
    """Example 1: Train models from CSV data"""
    print("=" * 80)
    print("EXAMPLE 1: Training Models from CSV")
    print("=" * 80)
    
    csv_path = "data_generation/churn_features.csv"
    
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        print("Generate data first using: python data_generation/generate_synthetic_data.py")
        print("Or export from Snowflake")
        return
    
    results = train_pipeline(data_source='csv', csv_path=csv_path)
    
    print(f"\nBest model: {results['best_model_name']}")
    print("All artifacts saved to ml/artifacts/")


def example_2_view_model_comparison():
    """Example 2: View model comparison results"""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: View Model Comparison")
    print("=" * 80)
    
    comparison = get_model_comparison()
    
    if comparison is None:
        print("No trained models found. Train models first using example_1_train_models()")
        return
    
    print("\nModel Performance Comparison:")
    print(comparison[['model_name', 'accuracy', 'precision', 'recall', 
                      'f1_score', 'roc_auc', 'pr_auc']].to_string(index=False))
    
    best_model = comparison.iloc[0]
    print(f"\nBest Model: {best_model['model_name']}")
    print(f"ROC-AUC: {best_model['roc_auc']:.4f}")


def example_3_view_feature_importance():
    """Example 3: View feature importance from SHAP"""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: View Feature Importance")
    print("=" * 80)
    
    model_name = 'xgboost'
    importance_df = load_feature_importance(model_name)
    
    if importance_df is None:
        print(f"No feature importance found for {model_name}")
        return
    
    print(f"\nTop 15 Most Important Features ({model_name.upper()}):")
    print(importance_df.head(15).to_string(index=False))


def example_4_make_predictions_from_csv():
    """Example 4: Make predictions on new data from CSV"""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Make Predictions from CSV")
    print("=" * 80)
    
    csv_path = "data_generation/churn_features.csv"
    
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        return
    
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.lower()
    
    sample_df = df.sample(n=10, random_state=42)
    
    print(f"\nLoading best model...")
    model = load_best_model()
    
    print(f"Making predictions on {len(sample_df)} customers...")
    predictions, probabilities = predict_churn(sample_df)
    
    results_df = sample_df[['customer_id', 'first_name', 'last_name']].copy()
    results_df['churn_probability'] = probabilities
    results_df['prediction'] = predictions
    results_df['risk_category'] = pd.cut(
        probabilities,
        bins=[0, 0.3, 0.5, 0.7, 1.0],
        labels=['Very Low Risk', 'Low Risk', 'Medium Risk', 'High Risk']
    )
    
    print("\nPrediction Results:")
    print(results_df.to_string(index=False))


def example_5_predict_single_customer():
    """Example 5: Predict churn for a single customer"""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Predict Single Customer")
    print("=" * 80)
    
    customer_data = {
        'tenure_months': 3,
        'tenure_days': 90,
        'monthly_charges': 85.0,
        'contract_type': 'Month-to-month',
        'plan_type': 'Premium',
        'recency_days': 45,
        'frequency': 2,
        'monetary': 250.0,
        'avg_transaction_value': 125.0,
        'total_transactions': 2,
        'days_since_last_transaction': 45,
        'recency_score': 2,
        'frequency_score': 1,
        'monetary_score': 3,
        'rfm_composite_score': 6,
        'total_events': 15,
        'active_days': 10,
        'login_count': 5,
        'feature_usage_count': 8,
        'support_ticket_count': 2,
        'app_crash_count': 1,
        'engagement_rate': 0.5,
        'avg_events_per_active_day': 1.5,
        'avg_session_duration_minutes': 8.5,
        'days_since_last_event': 10,
        'events_last_7_days': 3,
        'events_last_30_days': 12,
        'events_last_90_days': 15,
        'logins_last_30_days': 4,
        'feature_usage_last_30_days': 7,
        'days_since_last_login': 5,
        'features_per_login': 1.6,
        'problem_event_rate_pct': 13.3,
        'engagement_recency_score': 3,
        'engagement_frequency_score': 2,
        'feature_adoption_score': 2,
        'engagement_composite_score': 7,
        'age': 28,
        'gender': 'Male',
        'segment': 'Consumer',
        'acquisition_channel': 'Social Media',
        'device_type': 'Mobile',
        'initial_referral_credits': 10.0,
    }
    
    print("\nCustomer Profile:")
    print(f"  Tenure: {customer_data['tenure_months']} months")
    print(f"  Contract: {customer_data['contract_type']}")
    print(f"  Monthly Charges: ${customer_data['monthly_charges']}")
    print(f"  Total Transactions: {customer_data['total_transactions']}")
    print(f"  Days Since Last Login: {customer_data['days_since_last_login']}")
    print(f"  Support Tickets: {customer_data['support_ticket_count']}")
    
    result = predict_single_customer(customer_data)
    
    print("\nPrediction Result:")
    print(f"  Churn Probability: {result['churn_probability']:.2%}")
    print(f"  Risk Category: {result['risk_category']}")
    print(f"  Prediction: {'WILL CHURN' if result['prediction'] == 1 else 'WILL RETAIN'}")


def example_6_batch_scoring():
    """Example 6: Batch scoring for production use"""
    print("\n" + "=" * 80)
    print("EXAMPLE 6: Batch Scoring for Production")
    print("=" * 80)
    
    csv_path = "data_generation/churn_features.csv"
    
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        return
    
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.lower()
    
    print(f"Loading model and preprocessors...")
    model = load_best_model()
    encoders, scaler, feature_names = load_preprocessors()
    
    print(f"Scoring {len(df)} customers...")
    predictions, probabilities = predict_churn(df, model, encoders, scaler, feature_names)
    
    df['ml_churn_probability'] = probabilities
    df['ml_churn_prediction'] = predictions
    df['ml_risk_category'] = pd.cut(
        probabilities,
        bins=[0, 0.3, 0.5, 0.7, 1.0],
        labels=['Very Low Risk', 'Low Risk', 'Medium Risk', 'High Risk']
    )
    
    high_risk = df[probabilities >= 0.7]
    print(f"\nHigh-Risk Customers (probability >= 70%): {len(high_risk)}")
    print(f"Medium-Risk Customers (probability 50-70%): {len(df[(probabilities >= 0.5) & (probabilities < 0.7)])}")
    print(f"Low-Risk Customers (probability < 50%): {len(df[probabilities < 0.5])}")
    
    output_path = "ml/artifacts/scored_customers.csv"
    df.to_csv(output_path, index=False)
    print(f"\nScored data saved to: {output_path}")


def main():
    """Run all examples"""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "ML CHURN PREDICTION EXAMPLES" + " " * 30 + "║")
    print("╚" + "═" * 78 + "╝")
    print("\n")
    
    examples = [
        ("Train models (takes 5-10 minutes)", example_1_train_models),
        ("View model comparison", example_2_view_model_comparison),
        ("View feature importance", example_3_view_feature_importance),
        ("Make predictions from CSV", example_4_make_predictions_from_csv),
        ("Predict single customer", example_5_predict_single_customer),
        ("Batch scoring", example_6_batch_scoring),
    ]
    
    print("Available examples:")
    for i, (desc, _) in enumerate(examples, 1):
        print(f"  {i}. {desc}")
    
    print("\nRunning examples that don't require training:")
    
    example_2_view_model_comparison()
    example_3_view_feature_importance()
    example_4_make_predictions_from_csv()
    example_5_predict_single_customer()
    example_6_batch_scoring()
    
    print("\n" + "=" * 80)
    print("EXAMPLES COMPLETE")
    print("=" * 80)
    print("\nTo train models, run: python ml/train_model.py data_generation/churn_features.csv")


if __name__ == '__main__':
    main()
