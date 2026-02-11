"""
Churn Prediction Model Training Pipeline
Trains multiple models, evaluates performance, and generates SHAP explanations
"""

import pandas as pd
import numpy as np
import pickle
import json
import os
from datetime import datetime

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix,
    classification_report, roc_curve, precision_recall_curve
)
import xgboost as xgb
import shap
import matplotlib.pyplot as plt
import seaborn as sns

from data_prep import prepare_data_pipeline, save_preprocessors

ARTIFACTS_DIR = 'ml/artifacts'
RANDOM_STATE = 42


def train_logistic_regression(X_train, y_train):
    """Train Logistic Regression model"""
    model = LogisticRegression(
        random_state=RANDOM_STATE,
        max_iter=1000,
        class_weight='balanced'
    )
    model.fit(X_train, y_train)
    return model


def train_random_forest(X_train, y_train):
    """Train Random Forest model"""
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=RANDOM_STATE,
        class_weight='balanced',
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    return model


def train_xgboost(X_train, y_train):
    """Train XGBoost model"""
    scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
    
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        random_state=RANDOM_STATE,
        eval_metric='logloss',
        use_label_encoder=False
    )
    model.fit(X_train, y_train)
    return model


def evaluate_model(model, X_train, X_test, y_train, y_test, model_name):
    """
    Evaluate model performance with comprehensive metrics
    
    Returns:
        dict: Dictionary of evaluation metrics
    """
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    y_train_pred_proba = model.predict_proba(X_train)[:, 1]
    
    metrics = {
        'model_name': model_name,
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred),
        'recall': recall_score(y_test, y_pred),
        'f1_score': f1_score(y_test, y_pred),
        'roc_auc': roc_auc_score(y_test, y_pred_proba),
        'pr_auc': average_precision_score(y_test, y_pred_proba),
        'train_roc_auc': roc_auc_score(y_train, y_train_pred_proba),
        'confusion_matrix': confusion_matrix(y_test, y_pred).tolist(),
    }
    
    metrics['overfit_gap'] = metrics['train_roc_auc'] - metrics['roc_auc']
    
    print(f"\n{model_name} Performance:")
    print(f"  Accuracy:  {metrics['accuracy']:.4f}")
    print(f"  Precision: {metrics['precision']:.4f}")
    print(f"  Recall:    {metrics['recall']:.4f}")
    print(f"  F1 Score:  {metrics['f1_score']:.4f}")
    print(f"  ROC-AUC:   {metrics['roc_auc']:.4f}")
    print(f"  PR-AUC:    {metrics['pr_auc']:.4f}")
    print(f"  Train AUC: {metrics['train_roc_auc']:.4f}")
    print(f"  Overfit Gap: {metrics['overfit_gap']:.4f}")
    
    return metrics


def cross_validate_model(model, X, y, cv=5, scoring='roc_auc'):
    """
    Perform cross-validation
    
    Returns:
        dict: Cross-validation scores
    """
    skf = StratifiedKFold(n_splits=cv, shuffle=True, random_state=RANDOM_STATE)
    scores = cross_val_score(model, X, y, cv=skf, scoring=scoring, n_jobs=-1)
    
    cv_results = {
        'cv_scores': scores.tolist(),
        'cv_mean': scores.mean(),
        'cv_std': scores.std()
    }
    
    print(f"  Cross-Val {scoring.upper()}: {cv_results['cv_mean']:.4f} (+/- {cv_results['cv_std']:.4f})")
    
    return cv_results


def generate_classification_report(y_test, y_pred, output_path=None):
    """Generate and save classification report"""
    report = classification_report(y_test, y_pred, output_dict=True)
    
    if output_path:
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
    
    return report


def plot_confusion_matrix(cm, model_name, output_path=None):
    """Plot and save confusion matrix"""
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=['Not Churned', 'Churned'],
                yticklabels=['Not Churned', 'Churned'])
    plt.title(f'Confusion Matrix - {model_name}')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Confusion matrix saved to {output_path}")
    
    plt.close()


def plot_roc_curve(y_test, y_pred_proba, model_name, output_path=None):
    """Plot and save ROC curve"""
    fpr, tpr, thresholds = roc_curve(y_test, y_pred_proba)
    auc = roc_auc_score(y_test, y_pred_proba)
    
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, label=f'{model_name} (AUC = {auc:.4f})', linewidth=2)
    plt.plot([0, 1], [0, 1], 'k--', label='Random Classifier')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title(f'ROC Curve - {model_name}')
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"ROC curve saved to {output_path}")
    
    plt.close()


def plot_precision_recall_curve(y_test, y_pred_proba, model_name, output_path=None):
    """Plot and save Precision-Recall curve"""
    precision, recall, thresholds = precision_recall_curve(y_test, y_pred_proba)
    pr_auc = average_precision_score(y_test, y_pred_proba)
    
    plt.figure(figsize=(8, 6))
    plt.plot(recall, precision, label=f'{model_name} (PR-AUC = {pr_auc:.4f})', linewidth=2)
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title(f'Precision-Recall Curve - {model_name}')
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"PR curve saved to {output_path}")
    
    plt.close()


def generate_shap_analysis(model, X_train, X_test, feature_names, model_name, max_display=20):
    """
    Generate SHAP analysis for model explainability
    
    Returns:
        tuple: (shap_values, explainer)
    """
    print(f"\nGenerating SHAP analysis for {model_name}...")
    
    if model_name == 'XGBoost':
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_test)
    elif model_name == 'Random Forest':
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_test)
        if isinstance(shap_values, list):
            shap_values = shap_values[1]
    else:
        sample_size = min(100, len(X_train))
        X_train_sample = shap.sample(X_train, sample_size, random_state=RANDOM_STATE)
        explainer = shap.KernelExplainer(model.predict_proba, X_train_sample)
        shap_values = explainer.shap_values(X_test[:100])
        if isinstance(shap_values, list):
            shap_values = shap_values[1]
    
    shap_values_df = pd.DataFrame(shap_values, columns=feature_names)
    feature_importance = pd.DataFrame({
        'feature': feature_names,
        'importance': np.abs(shap_values).mean(axis=0)
    }).sort_values('importance', ascending=False)
    
    print("\nTop 10 Most Important Features (SHAP):")
    for idx, row in feature_importance.head(10).iterrows():
        print(f"  {row['feature']}: {row['importance']:.4f}")
    
    output_dir = f"{ARTIFACTS_DIR}/{model_name.lower().replace(' ', '_')}"
    os.makedirs(output_dir, exist_ok=True)
    
    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values, X_test, feature_names=feature_names, 
                      max_display=max_display, show=False)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/shap_summary_plot.png", dpi=300, bbox_inches='tight')
    print(f"SHAP summary plot saved to {output_dir}/shap_summary_plot.png")
    plt.close()
    
    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values, X_test, feature_names=feature_names, 
                      plot_type='bar', max_display=max_display, show=False)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/shap_feature_importance.png", dpi=300, bbox_inches='tight')
    print(f"SHAP feature importance saved to {output_dir}/shap_feature_importance.png")
    plt.close()
    
    feature_importance.to_csv(f"{output_dir}/feature_importance.csv", index=False)
    
    with open(f"{output_dir}/shap_values.pkl", 'wb') as f:
        pickle.dump({'shap_values': shap_values, 'explainer': explainer}, f)
    
    return shap_values, explainer, feature_importance


def save_model(model, model_name, metrics, feature_importance=None):
    """Save trained model and associated artifacts"""
    output_dir = f"{ARTIFACTS_DIR}/{model_name.lower().replace(' ', '_')}"
    os.makedirs(output_dir, exist_ok=True)
    
    with open(f"{output_dir}/model.pkl", 'wb') as f:
        pickle.dump(model, f)
    print(f"Model saved to {output_dir}/model.pkl")
    
    with open(f"{output_dir}/metrics.json", 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"Metrics saved to {output_dir}/metrics.json")
    
    if feature_importance is not None:
        feature_importance.to_csv(f"{output_dir}/feature_importance.csv", index=False)
        print(f"Feature importance saved to {output_dir}/feature_importance.csv")


def compare_models(all_metrics):
    """Compare all models and identify the best one"""
    comparison = pd.DataFrame(all_metrics)
    comparison = comparison.sort_values('roc_auc', ascending=False)
    
    print("\n" + "="*80)
    print("MODEL COMPARISON")
    print("="*80)
    print(comparison[['model_name', 'accuracy', 'precision', 'recall', 
                      'f1_score', 'roc_auc', 'pr_auc']].to_string(index=False))
    
    best_model_name = comparison.iloc[0]['model_name']
    print(f"\nBest Model: {best_model_name} (ROC-AUC: {comparison.iloc[0]['roc_auc']:.4f})")
    
    comparison.to_csv(f"{ARTIFACTS_DIR}/model_comparison.csv", index=False)
    print(f"\nModel comparison saved to {ARTIFACTS_DIR}/model_comparison.csv")
    
    return best_model_name, comparison


def train_pipeline(data_source='csv', credentials=None, csv_path=None):
    """
    Complete training pipeline
    
    Args:
        data_source (str): 'snowflake' or 'csv'
        credentials (dict): Snowflake credentials (if using Snowflake)
        csv_path (str): Path to CSV file (if using CSV)
    """
    print("="*80)
    print("CHURN PREDICTION MODEL TRAINING PIPELINE")
    print("="*80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    
    print("\n" + "="*80)
    print("STEP 1: DATA PREPARATION")
    print("="*80)
    
    data = prepare_data_pipeline(
        data_source=data_source,
        credentials=credentials,
        csv_path=csv_path,
        test_size=0.2,
        random_state=RANDOM_STATE,
        scale=True
    )
    
    X_train = data['X_train']
    X_test = data['X_test']
    y_train = data['y_train']
    y_test = data['y_test']
    feature_names = data['feature_names']
    
    save_preprocessors(data['encoders'], data['scaler'], feature_names, ARTIFACTS_DIR)
    
    print("\n" + "="*80)
    print("STEP 2: MODEL TRAINING")
    print("="*80)
    
    models = {
        'Logistic Regression': train_logistic_regression(X_train, y_train),
        'Random Forest': train_random_forest(X_train, y_train),
        'XGBoost': train_xgboost(X_train, y_train)
    }
    
    print("\n" + "="*80)
    print("STEP 3: MODEL EVALUATION")
    print("="*80)
    
    all_metrics = []
    
    for model_name, model in models.items():
        print(f"\nEvaluating {model_name}...")
        
        metrics = evaluate_model(model, X_train, X_test, y_train, y_test, model_name)
        
        cv_results = cross_validate_model(model, X_train, y_train, cv=5, scoring='roc_auc')
        metrics.update(cv_results)
        
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        
        output_dir = f"{ARTIFACTS_DIR}/{model_name.lower().replace(' ', '_')}"
        os.makedirs(output_dir, exist_ok=True)
        
        report = generate_classification_report(y_test, y_pred, 
                                                f"{output_dir}/classification_report.json")
        
        plot_confusion_matrix(np.array(metrics['confusion_matrix']), model_name,
                            f"{output_dir}/confusion_matrix.png")
        plot_roc_curve(y_test, y_pred_proba, model_name,
                      f"{output_dir}/roc_curve.png")
        plot_precision_recall_curve(y_test, y_pred_proba, model_name,
                                   f"{output_dir}/pr_curve.png")
        
        all_metrics.append(metrics)
    
    print("\n" + "="*80)
    print("STEP 4: SHAP EXPLAINABILITY")
    print("="*80)
    
    for model_name, model in models.items():
        shap_values, explainer, feature_importance = generate_shap_analysis(
            model, X_train, X_test, feature_names, model_name
        )
        
        save_model(model, model_name, 
                  [m for m in all_metrics if m['model_name'] == model_name][0],
                  feature_importance)
    
    print("\n" + "="*80)
    print("STEP 5: MODEL COMPARISON")
    print("="*80)
    
    best_model_name, comparison = compare_models(all_metrics)
    
    with open(f"{ARTIFACTS_DIR}/best_model_name.txt", 'w') as f:
        f.write(best_model_name)
    
    print("\n" + "="*80)
    print("TRAINING PIPELINE COMPLETE")
    print("="*80)
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nAll artifacts saved to: {ARTIFACTS_DIR}")
    print(f"Best model: {best_model_name}")
    
    return {
        'models': models,
        'metrics': all_metrics,
        'best_model_name': best_model_name,
        'data': data
    }


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python train_model.py <csv_path>")
        print("Example: python train_model.py data_generation/churn_features.csv")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    
    if not os.path.exists(csv_path):
        print(f"Error: File not found: {csv_path}")
        sys.exit(1)
    
    results = train_pipeline(data_source='csv', csv_path=csv_path)
    
    print("\nTraining complete!")
