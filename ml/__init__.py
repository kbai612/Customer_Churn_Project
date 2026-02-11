"""
Machine Learning Module for Churn Prediction
Provides model training, evaluation, and prediction capabilities
"""

__version__ = '1.0.0'

from .data_prep import (
    prepare_data_pipeline,
    load_data_from_snowflake,
    load_data_from_csv,
    prepare_features
)

from .predict import (
    load_best_model,
    load_model,
    predict_churn,
    predict_single_customer,
    load_model_metrics,
    load_feature_importance,
    get_model_comparison
)

__all__ = [
    'prepare_data_pipeline',
    'load_data_from_snowflake',
    'load_data_from_csv',
    'prepare_features',
    'load_best_model',
    'load_model',
    'predict_churn',
    'predict_single_customer',
    'load_model_metrics',
    'load_feature_importance',
    'get_model_comparison'
]
