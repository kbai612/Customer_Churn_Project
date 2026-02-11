"""
Prediction Module for Churn Prediction
Handles loading models and making predictions on new data
"""

import pandas as pd
import numpy as np
import pickle
import os
import json

# Resolve artifacts path relative to this file so it works when app runs from streamlit_app/
_ML_DIR = os.path.dirname(os.path.abspath(__file__))
ARTIFACTS_DIR = os.path.join(_ML_DIR, 'artifacts')


def load_model(model_name='xgboost'):
    """
    Load trained model
    
    Args:
        model_name (str): Name of model to load ('logistic_regression', 'random_forest', 'xgboost')
        
    Returns:
        model: Loaded model
    """
    model_path = f"{ARTIFACTS_DIR}/{model_name}/model.pkl"
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found at {model_path}")
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    return model


def load_best_model():
    """Load the best performing model"""
    best_model_path = f"{ARTIFACTS_DIR}/best_model_name.txt"
    
    if not os.path.exists(best_model_path):
        print("Best model name not found, defaulting to XGBoost")
        return load_model('xgboost')
    
    with open(best_model_path, 'r') as f:
        best_model_name = f.read().strip()
    
    model_name_map = {
        'Logistic Regression': 'logistic_regression',
        'Random Forest': 'random_forest',
        'XGBoost': 'xgboost'
    }
    
    model_key = model_name_map.get(best_model_name, 'xgboost')
    return load_model(model_key)


def load_preprocessors():
    """Load preprocessing artifacts"""
    from data_prep import load_preprocessors as load_prep
    return load_prep(ARTIFACTS_DIR)


def load_model_metrics(model_name='xgboost'):
    """Load model evaluation metrics"""
    metrics_path = f"{ARTIFACTS_DIR}/{model_name}/metrics.json"
    
    if not os.path.exists(metrics_path):
        return None
    
    with open(metrics_path, 'r') as f:
        metrics = json.load(f)
    
    return metrics


def load_feature_importance(model_name='xgboost'):
    """Load feature importance from SHAP analysis"""
    importance_path = f"{ARTIFACTS_DIR}/{model_name}/feature_importance.csv"
    
    if not os.path.exists(importance_path):
        return None
    
    importance_df = pd.read_csv(importance_path)
    return importance_df


def load_shap_values(model_name='xgboost'):
    """Load SHAP values and explainer"""
    shap_path = f"{ARTIFACTS_DIR}/{model_name}/shap_values.pkl"
    
    if not os.path.exists(shap_path):
        return None, None
    
    with open(shap_path, 'rb') as f:
        shap_data = pickle.load(f)
    
    return shap_data['shap_values'], shap_data['explainer']


def preprocess_input(df, encoders, feature_names):
    """
    Preprocess input data for prediction
    
    Args:
        df (pd.DataFrame): Input data
        encoders (dict): Label encoders
        feature_names (list): List of required features
        
    Returns:
        pd.DataFrame: Preprocessed data
    """
    df_processed = df.copy()
    
    for col in df_processed.columns:
        if df_processed[col].dtype in ['object', 'category']:
            df_processed[col].fillna('MISSING', inplace=True)
        else:
            df_processed[col].fillna(df_processed[col].median(), inplace=True)
    
    for col, encoder in encoders.items():
        if col in df_processed.columns:
            df_processed[col] = df_processed[col].astype(str)
            known_classes = set(encoder.classes_)
            df_processed[col] = df_processed[col].apply(
                lambda x: x if x in known_classes else encoder.classes_[0]
            )
            df_processed[col] = encoder.transform(df_processed[col])
    
    available_features = [col for col in feature_names if col in df_processed.columns]
    missing_features = [col for col in feature_names if col not in df_processed.columns]
    
    if missing_features:
        for col in missing_features:
            df_processed[col] = 0
    
    df_processed = df_processed[feature_names]
    
    return df_processed


def predict_churn(df, model=None, encoders=None, scaler=None, feature_names=None):
    """
    Predict churn probability for new data
    
    Args:
        df (pd.DataFrame): Input data with features
        model: Trained model (if None, loads best model)
        encoders: Label encoders (if None, loads from artifacts)
        scaler: Feature scaler (if None, loads from artifacts)
        feature_names: List of features (if None, loads from artifacts)
        
    Returns:
        tuple: (predictions, probabilities)
    """
    if model is None:
        model = load_best_model()
    
    if encoders is None or scaler is None or feature_names is None:
        encoders, scaler, feature_names = load_preprocessors()
    
    X = preprocess_input(df, encoders, feature_names)
    
    if scaler is not None:
        X_scaled = scaler.transform(X)
        X_scaled = pd.DataFrame(X_scaled, columns=X.columns, index=X.index)
    else:
        X_scaled = X
    
    predictions = model.predict(X_scaled)
    probabilities = model.predict_proba(X_scaled)[:, 1]
    
    return predictions, probabilities


def predict_single_customer(customer_data, model=None):
    """
    Predict churn for a single customer
    
    Args:
        customer_data (dict or pd.Series): Customer feature data
        model: Trained model (if None, loads best model)
        
    Returns:
        dict: Prediction results with probability and risk category
    """
    if isinstance(customer_data, dict):
        df = pd.DataFrame([customer_data])
    else:
        df = pd.DataFrame([customer_data.to_dict()])
    
    predictions, probabilities = predict_churn(df, model=model)
    
    probability = probabilities[0]
    prediction = predictions[0]
    
    if probability >= 0.7:
        risk_category = 'High Risk'
    elif probability >= 0.5:
        risk_category = 'Medium Risk'
    elif probability >= 0.3:
        risk_category = 'Low Risk'
    else:
        risk_category = 'Very Low Risk'
    
    return {
        'prediction': int(prediction),
        'churn_probability': float(probability),
        'risk_category': risk_category
    }


def get_model_comparison():
    """Load model comparison results"""
    comparison_path = f"{ARTIFACTS_DIR}/model_comparison.csv"
    
    if not os.path.exists(comparison_path):
        return None
    
    comparison_df = pd.read_csv(comparison_path)
    return comparison_df


def explain_prediction_shap(customer_data, model_name='xgboost'):
    """
    Get SHAP explanation for a single prediction
    
    Args:
        customer_data (dict or pd.Series): Customer feature data
        model_name (str): Model name
        
    Returns:
        dict: SHAP values and base value
    """
    import shap
    
    model = load_model(model_name)
    encoders, scaler, feature_names = load_preprocessors()
    
    if isinstance(customer_data, dict):
        df = pd.DataFrame([customer_data])
    else:
        df = pd.DataFrame([customer_data.to_dict()])
    
    X = preprocess_input(df, encoders, feature_names)
    
    if scaler is not None:
        X_scaled = scaler.transform(X)
        X_scaled = pd.DataFrame(X_scaled, columns=X.columns, index=X.index)
    else:
        X_scaled = X
    
    if model_name == 'xgboost' or model_name == 'random_forest':
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_scaled)
        
        if isinstance(shap_values, list):
            shap_values = shap_values[1]
        
        if len(shap_values.shape) > 1:
            shap_values = shap_values[0]
        
        explanation = {
            'shap_values': dict(zip(feature_names, shap_values)),
            'base_value': explainer.expected_value if not isinstance(explainer.expected_value, np.ndarray) else explainer.expected_value[1],
            'prediction': float(model.predict_proba(X_scaled)[0, 1])
        }
    else:
        explanation = {
            'shap_values': {},
            'base_value': 0.5,
            'prediction': float(model.predict_proba(X_scaled)[0, 1])
        }
    
    return explanation


if __name__ == '__main__':
    print("Prediction Module")
    print("This module is meant to be imported by the Streamlit app")
    
    try:
        comparison = get_model_comparison()
        if comparison is not None:
            print("\nModel Comparison:")
            print(comparison[['model_name', 'roc_auc', 'precision', 'recall']].to_string(index=False))
        else:
            print("\nNo model comparison found. Train models first using train_model.py")
    except Exception as e:
        print(f"\nError: {e}")
        print("Train models first using train_model.py")
