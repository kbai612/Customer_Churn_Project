# Machine Learning Module

This module provides churn prediction capabilities using advanced machine learning models trained on customer behavioral and transactional data.

## Overview

The ML pipeline trains three models and compares their performance:
- **Logistic Regression**: Interpretable linear baseline
- **Random Forest**: Non-linear ensemble method
- **XGBoost**: Gradient boosting classifier (typically best performer)

All models include SHAP (SHapley Additive exPlanations) analysis for model interpretability.

## Quick Start

### 1. Install Dependencies

```cmd
pip install -r requirements.txt
```

### 2. Export Data from Snowflake

Option A: Export from Snowflake to CSV:
```sql
COPY INTO @CHURN_RAW.RAW.CHURN_STAGE/churn_features.csv
FROM CHURN_ANALYTICS.ANALYTICS.churn_features
FILE_FORMAT = (TYPE = CSV HEADER = TRUE)
SINGLE = TRUE
OVERWRITE = TRUE;
```

Then download using SnowSQL:
```cmd
snowsql -a <account> -u <username>
GET @CHURN_RAW.RAW.CHURN_STAGE/churn_features.csv file://data_generation/
```

Option B: Use the data preparation module with Snowflake credentials (see below).

### 3. Train Models

```cmd
cd "c:\Users\admin\Documents\Github Repos\Customer_Churn_Project"
python ml\train_model.py data_generation\churn_features.csv
```

This will:
- Load and prepare the data
- Train three models with cross-validation
- Generate evaluation metrics and plots
- Create SHAP explanations
- Save all artifacts to `ml/artifacts/`

Training takes approximately 5-10 minutes depending on data size.

### 4. View Results in Dashboard

```cmd
cd streamlit_app
streamlit run app.py
```

Navigate to the "Machine Learning Predictions" section to see:
- Model performance metrics
- Feature importance rankings
- Model comparison charts

## Module Structure

```
ml/
├── data_prep.py           # Data loading and preprocessing
├── train_model.py         # Main training pipeline
├── predict.py             # Inference and prediction utilities
├── README.md              # This file
└── artifacts/             # Saved models and metrics
    ├── best_model_name.txt
    ├── model_comparison.csv
    ├── encoders.pkl
    ├── scaler.pkl
    ├── feature_names.pkl
    ├── logistic_regression/
    │   ├── model.pkl
    │   ├── metrics.json
    │   ├── feature_importance.csv
    │   ├── shap_values.pkl
    │   ├── confusion_matrix.png
    │   ├── roc_curve.png
    │   ├── pr_curve.png
    │   └── shap_summary_plot.png
    ├── random_forest/
    │   └── (same structure)
    └── xgboost/
        └── (same structure)
```

## Using the Data Preparation Module

The `data_prep.py` module can load data from Snowflake or CSV:

### From CSV:
```python
from ml.data_prep import prepare_data_pipeline

data = prepare_data_pipeline(
    data_source='csv',
    csv_path='data_generation/churn_features.csv'
)
```

### From Snowflake:
```python
credentials = {
    'account': 'your_account',
    'user': 'your_username',
    'password': 'your_password',
    'warehouse': 'ANALYTICS_WH',
    'database': 'CHURN_ANALYTICS',
    'schema': 'ANALYTICS'
}

data = prepare_data_pipeline(
    data_source='snowflake',
    credentials=credentials
)
```

## Making Predictions

Use the `predict.py` module for inference:

```python
from ml.predict import load_best_model, predict_churn, load_preprocessors
import pandas as pd

model = load_best_model()
encoders, scaler, feature_names = load_preprocessors()

new_data = pd.DataFrame([{
    'tenure_months': 12,
    'monthly_charges': 75.5,
    'contract_type': 'Month-to-month',
    # ... other features
}])

predictions, probabilities = predict_churn(new_data, model, encoders, scaler, feature_names)

print(f"Churn probability: {probabilities[0]:.2%}")
```

## Features Used

The model uses 42 carefully selected features across 6 categories:

**Subscription Features** (5):
- tenure_months, tenure_days, monthly_charges, contract_type, plan_type

**RFM Features** (10):
- recency_days, frequency, monetary, avg_transaction_value, total_transactions
- recency_score, frequency_score, monetary_score, rfm_composite_score, days_since_last_transaction

**Behavioral Engagement** (20):
- total_events, active_days, login_count, feature_usage_count, support_ticket_count
- app_crash_count, engagement_rate, avg_events_per_active_day, avg_session_duration_minutes
- days_since_last_event, events_last_7/30/90_days, logins_last_30_days
- feature_usage_last_30_days, days_since_last_login, features_per_login, problem_event_rate_pct

**Engagement Scores** (4):
- engagement_recency_score, engagement_frequency_score, feature_adoption_score, engagement_composite_score

**Demographics** (6):
- age, gender, segment, acquisition_channel, device_type, initial_referral_credits

## Model Performance

Expected performance metrics (on test set):
- **ROC-AUC**: 0.85-0.92
- **Precision**: 0.75-0.85
- **Recall**: 0.70-0.80
- **F1-Score**: 0.72-0.82

XGBoost typically achieves the best performance across all metrics.

## SHAP Explainability

SHAP values provide:
- **Global explanations**: Which features drive churn across all customers
- **Local explanations**: Why a specific customer is predicted to churn

Key insights from SHAP analysis:
1. Engagement metrics (events_last_30_days, logins_last_30_days) are top predictors
2. Contract type strongly influences churn probability
3. Days since last event is more predictive than monetary value
4. Support ticket count combined with low engagement indicates high risk

## Retraining Models

Retrain periodically (monthly/quarterly) as new data accumulates:

```cmd
python ml\train_model.py data_generation\churn_features_updated.csv
```

The pipeline will overwrite existing artifacts with new models.

## Troubleshooting

**Issue**: `ModuleNotFoundError: No module named 'ml'`
- **Solution**: Run training script from project root directory

**Issue**: `FileNotFoundError: Model not found`
- **Solution**: Train models first using `train_model.py`

**Issue**: `KeyError` on feature columns
- **Solution**: Ensure input data has all required features from `data_prep.FEATURE_COLUMNS`

**Issue**: Low model performance
- **Solution**: Check data quality, feature engineering, class imbalance handling

## Advanced Usage

### Custom Feature Selection
Edit `data_prep.py` to modify `FEATURE_COLUMNS` list.

### Hyperparameter Tuning
Modify model parameters in `train_model.py` training functions.

### Add New Models
Add training function to `train_model.py` and include in `models` dictionary.

## Analysis & Results Documentation

After training your models, refer to these comprehensive guides:

1. **ML_ANALYSIS_AND_RECOMMENDATIONS.md** - Business recommendations based on ML results
   - Top 15 churn drivers with business translation
   - 6 prioritized recommendations with ROI calculations
   - Implementation roadmap and success metrics

2. **HOW_TO_INTERPRET_ML_RESULTS.md** - Practical guide for reading model output
   - Step-by-step interpretation of metrics
   - How to create action lists from predictions
   - Model monitoring and drift detection

3. **SAMPLE_ML_RESULTS_REPORT.md** - Example results report
   - Sample model performance metrics
   - Individual customer case studies
   - Business impact calculations

## Contact & Support

For issues or questions about the ML module, refer to the main project README or open an issue in the repository.
