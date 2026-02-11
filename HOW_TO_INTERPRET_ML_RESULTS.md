# How to Interpret ML Results - Practical Guide

## Overview

This guide explains how to extract actionable insights from your trained ML models. After running `python ml\train_model.py`, you'll have extensive output and artifacts. This document shows you exactly what to look at and how to use it.

---

## Step 1: Review Training Output

### What to Look For in Console Output

After training completes, you'll see output like this:

```
STEP 3: MODEL EVALUATION
================================================================================

Evaluating Logistic Regression...

Logistic Regression Performance:
  Accuracy:  0.8234
  Precision: 0.7456
  Recall:    0.7189
  F1 Score:  0.7320
  ROC-AUC:   0.8123
  PR-AUC:    0.7234
  Train AUC: 0.8156
  Overfit Gap: 0.0033
  Cross-Val ROC-AUC: 0.8098 (+/- 0.0145)
```

### How to Interpret These Metrics

**ROC-AUC (0.81 - 0.92 range):**
- **0.90+**: Excellent - Model is highly accurate
- **0.85-0.90**: Very good - Production ready
- **0.80-0.85**: Good - Useful but room for improvement
- **<0.80**: Fair - Consider feature engineering or data quality

**Precision (0.74 - 0.82):**
- **High Precision (>0.80)**: When model says "will churn," it's usually right
- **Use case**: Minimize wasted retention spend on false alarms
- **Trade-off**: May miss some at-risk customers

**Recall (0.72 - 0.78):**
- **High Recall (>0.75)**: Model catches most customers who will churn
- **Use case**: Maximize customer saves, even with some false positives
- **Trade-off**: More retention campaigns sent to stable customers

**Overfit Gap (<0.05 is good):**
- Difference between training AUC and test AUC
- **<0.03**: Excellent generalization
- **0.03-0.05**: Good, model isn't overfitting
- **>0.05**: Model may be too tuned to training data

---

## Step 2: Compare Models

### Check `ml/artifacts/model_comparison.csv`

```csv
model_name,accuracy,precision,recall,f1_score,roc_auc,pr_auc
XGBoost,0.8534,0.8234,0.7812,0.8018,0.8834,0.8456
Random Forest,0.8423,0.7923,0.7634,0.7776,0.8623,0.8234
Logistic Regression,0.8234,0.7456,0.7189,0.7320,0.8123,0.7834
```

### How to Pick the Best Model

**Decision Framework:**

1. **ROC-AUC is highest priority** - Overall discriminative ability
2. **Balance Precision vs Recall** based on business needs:
   - **High Precision needed?** → Minimize false alarms, target only confident predictions
   - **High Recall needed?** → Catch all at-risk customers, accept some false positives
3. **Check overfitting** - Prefer model with smallest gap

**In this example:** XGBoost wins (highest AUC + best balance)

---

## Step 3: Understand Feature Importance

### Check `ml/artifacts/xgboost/feature_importance.csv`

```csv
feature,importance
events_last_30_days,0.2872
days_since_last_event,0.2451
contract_type,0.2183
logins_last_30_days,0.1964
engagement_composite_score,0.1823
```

### What This Means

**High Importance (>0.20):**
- These features have the biggest impact on predictions
- Focus monitoring and interventions on these metrics
- Changes in these features will most affect churn risk

**Example Interpretation:**

```
events_last_30_days: 0.287 (28.7% of model decision)
```

**Business Translation:**
- "Customer activity in last 30 days is our #1 churn predictor"
- "If a customer goes from 15 events → 3 events, churn risk jumps 40-60%"
- "Monitor this metric weekly and alert when it drops below 5"

**Action Items from Top Features:**

| Feature | Importance | Action |
|---------|-----------|--------|
| events_last_30_days | 0.287 | Set alert at <5 events, trigger re-engagement |
| days_since_last_event | 0.245 | Auto-email at 7 days, call at 14 days |
| contract_type | 0.218 | Offer upgrade incentive to month-to-month users |
| logins_last_30_days | 0.196 | Flag customers with <2 logins for outreach |

---

## Step 4: Analyze Confusion Matrix

### Check `ml/artifacts/xgboost/confusion_matrix.png`

Or look at the JSON metrics:

```json
"confusion_matrix": [[3285, 365], [297, 1053]]
```

Format: `[[TN, FP], [FN, TP]]`

### Reading the Matrix

```
                    Predicted: No Churn    Predicted: Churn
Actual: No Churn         3,285                 365
Actual: Churn              297               1,053
```

**True Negatives (3,285):**
- Customers correctly predicted as staying
- These customers are stable, standard nurture campaigns

**True Positives (1,053):**
- Customers correctly predicted as churning
- **Action:** Immediate intervention, these predictions are accurate

**False Positives (365):**
- Stable customers incorrectly flagged as at-risk
- **Cost:** Wasted retention spend (~$150 × 365 = $55K)
- **Benefit:** Some may appreciate extra attention
- **10% false positive rate is acceptable**

**False Negatives (297):**
- Churning customers missed by model
- **Cost:** Lost customers (~$750 × 297 = $223K)
- **Action:** Analyze these cases to improve model

### Calculate Business Impact

```
Customers Saved = True Positives × Intervention Success Rate
                = 1,053 × 60%
                = 632 customers

Revenue Saved = 632 × Average LTV
              = 632 × $850
              = $537,200

Cost of Intervention = (TP + FP) × Cost per Intervention
                     = (1,053 + 365) × $150
                     = $212,700

Net Benefit = $537,200 - $212,700 = $324,500
ROI = 152%
```

---

## Step 5: Review SHAP Visualizations

### Check `ml/artifacts/xgboost/shap_summary_plot.png`

This shows how each feature impacts predictions:

**What to Look For:**

1. **Features at the top** = Most important
2. **Red dots** = High feature values
3. **Blue dots** = Low feature values
4. **X-axis** = Impact on prediction (left = reduces churn risk, right = increases churn risk)

**Example Interpretation:**

```
events_last_30_days:
- Blue dots (low values) on right side = Low events → High churn risk
- Red dots (high values) on left side = High events → Low churn risk
- Wide spread = Strong impact
```

**Business Translation:**
"Customers with fewer than 5 events per month (blue dots) have significantly higher churn risk. Increasing engagement is our top retention lever."

### Check `ml/artifacts/xgboost/shap_feature_importance.png`

This is a bar chart showing feature importance rankings.

**How to Use:**
1. Top 5 features = Your "churn driver dashboard" KPIs
2. Monitor these weekly
3. Set alerts when they cross thresholds
4. Design interventions to improve these metrics

---

## Step 6: Identify High-Risk Customers

### Load Model and Score Your Customer Base

```python
from ml.predict import load_best_model, predict_churn
import pandas as pd

# Load data
df = pd.read_csv('data_generation/churn_features.csv')

# Get predictions
model = load_best_model()
predictions, probabilities = predict_churn(df)

# Add to dataframe
df['churn_probability'] = probabilities
df['churn_prediction'] = predictions

# Segment by risk
critical = df[df['churn_probability'] >= 0.70]
high = df[(df['churn_probability'] >= 0.50) & (df['churn_probability'] < 0.70)]
medium = df[(df['churn_probability'] >= 0.30) & (df['churn_probability'] < 0.50)]
low = df[df['churn_probability'] < 0.30]

print(f"Critical Risk: {len(critical)} customers - Immediate action required")
print(f"High Risk: {len(high)} customers - Targeted campaigns")
print(f"Medium Risk: {len(medium)} customers - Monitoring")
print(f"Low Risk: {len(low)} customers - Standard nurture")
```

### Create Action Lists

**Critical Risk List (≥70% probability):**
```python
critical_customers = critical[['customer_id', 'first_name', 'last_name', 
                                'email', 'churn_probability', 'monetary',
                                'events_last_30_days', 'contract_type']]

critical_customers = critical_customers.sort_values('monetary', ascending=False)

# Export for CS team
critical_customers.to_csv('outreach_list_critical.csv', index=False)
```

**Action:** Personal phone call within 24 hours

---

## Step 7: Validate Model Performance

### A/B Testing Framework

To validate the model is actually working:

**Test Group (ML-driven):**
- Score all customers with ML model
- Intervene on top 1,000 highest risk predictions
- Track actual churn rate over 90 days

**Control Group (Rule-based):**
- Use existing rule-based churn score
- Intervene on top 1,000 by rule-based score
- Track actual churn rate over 90 days

**Success Metric:**
```
Lift = (Control Churn Rate - Test Churn Rate) / Control Churn Rate × 100%

Example:
Control: 68% of identified customers churned
Test: 52% of identified customers churned
Lift = (68% - 52%) / 68% = 23.5% improvement
```

---

## Step 8: Monitor Model Drift

### Weekly Monitoring Checklist

**1. Prediction Distribution:**
```python
import pandas as pd

# Load latest predictions
df = pd.read_csv('ml/artifacts/scored_customers.csv')

# Check distribution
print(df['churn_probability'].describe())
```

**What to Look For:**
- Mean probability should be ~0.27 (your churn rate)
- If mean drifts to 0.40+ or 0.15-, model may need retraining

**2. Calibration Check:**
```python
# Group by predicted probability
bins = [0, 0.3, 0.5, 0.7, 1.0]
df['risk_tier'] = pd.cut(df['churn_probability'], bins)

# Calculate actual churn rate in each tier (after 90 days)
calibration = df.groupby('risk_tier')['actual_churn'].mean()
print(calibration)
```

**Well-Calibrated Model:**
```
Risk Tier       Predicted    Actual
Low (0-30%)       15%         18%    ✓ Good
Medium (30-50%)   40%         43%    ✓ Good
High (50-70%)     60%         57%    ✓ Good
Critical (70%+)   82%         79%    ✓ Good
```

**Poorly-Calibrated Model:**
```
Risk Tier       Predicted    Actual
Low (0-30%)       15%         42%    ✗ Underestimating
Critical (70%+)   82%         51%    ✗ Overestimating
```

**Action:** If off by >10%, retrain model

---

## Step 9: Understand Individual Predictions

### SHAP Waterfall Plot for Single Customer

To explain why a specific customer has high churn risk:

```python
from ml.predict import explain_prediction_shap
import pandas as pd

# Get customer data
customer = df[df['customer_id'] == 12345].iloc[0]

# Get SHAP explanation
explanation = explain_prediction_shap(customer, model_name='xgboost')

# View impact of each feature
shap_df = pd.DataFrame({
    'feature': explanation['shap_values'].keys(),
    'impact': explanation['shap_values'].values()
}).sort_values('impact', ascending=False)

print(f"Churn Probability: {explanation['prediction']:.2%}")
print("\nTop Risk Factors:")
print(shap_df.head(10))
```

**Example Output:**
```
Churn Probability: 73%

Top Risk Factors:
                         feature    impact
events_last_30_days             +0.18  (only 2 events)
days_since_last_event           +0.15  (21 days inactive)
contract_type                   +0.12  (month-to-month)
support_ticket_count            +0.09  (4 open tickets)
logins_last_30_days             +0.07  (1 login only)
```

**Use Case:** Include in outreach email to CS team
"Customer #12345 is at 73% churn risk primarily due to low activity (2 events in 30 days) and 21 days of inactivity. They also have 4 open support tickets."

---

## Step 10: Create Business Dashboards

### Key Metrics to Track

**Model Performance Dashboard:**
- ROC-AUC (weekly trend)
- Precision/Recall (weekly)
- Calibration plot (monthly)
- Feature importance stability (monthly)

**Business Impact Dashboard:**
- Customers by risk tier (daily)
- Revenue at risk (daily)
- Intervention success rate (weekly)
- Churn prevented (monthly)
- ROI of retention program (monthly)

**Leading Indicator Dashboard:**
- Top 5 SHAP features (weekly averages)
- Alert volume by trigger type (daily)
- Days to intervention (daily)
- Feature adoption trends (weekly)

---

## Common Pitfalls & How to Avoid Them

### Pitfall 1: Ignoring False Negatives

**Problem:** Focus only on high-probability predictions, miss 22% of churners

**Solution:** Analyze false negative customers
```python
false_negatives = df[(df['churn_prediction'] == 0) & (df['actual_churn'] == 1)]
print(false_negatives[['events_last_30_days', 'monetary', 'tenure_months']].describe())
```

Look for patterns - maybe high-value, long-tenure customers aren't captured well

### Pitfall 2: Over-Relying on Probability Threshold

**Problem:** Using 50% as hard cutoff misses nuance

**Solution:** Use probability tiers with different actions
- 70%+: Personal outreach
- 50-70%: Automated campaign
- 30-50%: Monitoring + light touch
- <30%: Standard nurture

### Pitfall 3: Static Model

**Problem:** Model becomes stale as customer behavior changes

**Solution:** Retrain monthly
```cmd
python ml\train_model.py data_generation\churn_features_latest.csv
```

### Pitfall 4: Ignoring Intervention Feedback

**Problem:** Not tracking what happens after intervention

**Solution:** Create feedback loop
```python
# Tag customers who received intervention
df['intervention_date'] = intervention_date
df['intervention_type'] = 'phone_call'

# Track outcome after 30 days
df['retained_30d'] = df['churn_flag_after_30d'] == 0

# Measure effectiveness
success_rate = df.groupby('intervention_type')['retained_30d'].mean()
```

---

## Quick Reference: Decision Tree

```
START: Trained ML model

1. Is ROC-AUC > 0.85?
   YES → Model is production-ready, proceed
   NO → Review feature engineering, consider data quality issues

2. Check top 5 features from SHAP
   → These are your KPIs to monitor

3. Score entire customer base
   → Export critical risk customers (≥70%)

4. Set up alerts on top features
   → Trigger interventions when thresholds crossed

5. A/B test ML vs rule-based
   → Validate actual improvement

6. Monitor weekly
   → Check calibration and drift

7. Retrain monthly
   → Keep model fresh with new data

8. Measure ROI
   → Track customers saved vs intervention cost
```

---

## Summary: From ML Output to Business Action

| ML Output | Business Translation | Action |
|-----------|---------------------|--------|
| ROC-AUC: 0.88 | 88% accurate at ranking risk | Deploy to production |
| Top feature: events_last_30_days | Activity is #1 predictor | Monitor weekly, alert at <5 |
| Confusion Matrix: 1,053 TP | Will catch ~1,050 churners | Build intervention program |
| False Positives: 365 | 365 false alarms | Budget $55K for over-outreach |
| Churn Probability: 73% | High-confidence prediction | Personal outreach within 24h |
| SHAP: +0.18 from low events | Inactivity is specific risk driver | Focus on re-engagement |

---

## Next Steps

1. ✅ Train models: `python ml\train_model.py data.csv`
2. ✅ Review this guide to interpret results
3. ⬜ Score customer base: `python ml\example_usage.py`
4. ⬜ Export high-risk list for CS team
5. ⬜ Set up monitoring dashboard
6. ⬜ Launch intervention campaign
7. ⬜ Track results and measure ROI
8. ⬜ Retrain model with feedback data

For detailed recommendations based on these results, see `ML_ANALYSIS_AND_RECOMMENDATIONS.md`.
