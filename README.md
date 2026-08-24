# Financial Distress Early-Warning Model

## Predicting Future Market Drawdowns Using Financial Fundamentals and SEC 8-K Disclosures

This project develops a forward-looking machine learning framework designed to identify elevated risk of significant future stock-price drawdowns using publicly available corporate information.

The model combines quarterly financial statement fundamentals, year-over-year financial deterioration, SEC Form 8-K disclosure activity, and persistent deterioration signals to estimate whether a company will experience a significant market drawdown during the subsequent 12-month period.

The objective is not to predict bankruptcy or accounting insolvency. Instead, the project treats a severe future equity drawdown as a market-based measure of corporate distress.

---

## Research Question

**Can financial deterioration and corporate disclosure activity observable at the time of a quarterly filing help identify companies at elevated risk of a significant stock-price drawdown over the following 12 months?**

The project investigates three related questions:

1. How much predictive information is contained in traditional financial fundamentals?
2. Do SEC 8-K disclosures provide incremental information beyond financial statements?
3. Does persistent deterioration across multiple quarters improve early-warning performance?

---

## Dataset

The final modeling dataset contains:

- **747 quarterly company observations**
- **20 publicly traded U.S. companies**
- Approximately **10 years of historical observations**
- Quarterly financial statement information
- SEC Form 8-K disclosure information
- Market-based forward distress labels

The company universe includes firms from multiple industries in order to expose the model to different financial structures and business models.

Examples include Apple, Microsoft, Amazon, Alphabet, Meta Platforms, Exxon Mobil, Goldman Sachs, Coca-Cola, McDonald's, Nike, Disney, UnitedHealth Group, NVIDIA, Berkshire Hathaway, and others.

---

## Data Sources

### SEC Financial Statement Data

Financial statement information was collected from publicly available SEC filings and XBRL data.

The project uses accounting variables including:

- Revenue
- Net income
- Operating income
- Total assets
- Current assets
- Total liabilities
- Current liabilities
- Cash and cash equivalents

These raw variables were transformed into financial ratios, growth measures, and deterioration indicators.

### SEC Form 8-K Filings

Corporate event information was extracted from SEC Form 8-K filings.

The project tracks events including:

- Management changes
- Restructuring activity
- Material agreements
- Acquisitions and dispositions
- Overall 8-K filing activity

Management-related filings were additionally analyzed at the filing-text level to distinguish potential CEO and CFO departures and appointments.

### Market Data

Historical market-price information was used to calculate forward stock-price drawdowns following each financial filing.

The forward outcome window begins when the financial information becomes publicly observable and measures subsequent market performance over approximately one trading year.

---

## Target Variable

The target variable is a binary **12-month market distress indicator**.

For each observation, the project measures the company's maximum subsequent stock-price drawdown during the forward 12-month window.

Observations crossing the project's predetermined drawdown threshold are classified as:

`distress_12m = 1`

Observations that do not cross the threshold are classified as:

`distress_12m = 0`

This definition is intentionally market based.

**The model does not predict bankruptcy, default, or accounting insolvency.**

Instead, it attempts to identify financial and disclosure patterns associated with elevated risk of a substantial future equity drawdown.

---

## Feature Engineering

### Financial Fundamentals

The model includes financial ratios such as:

- Current ratio
- Liabilities-to-assets
- Return on assets
- Operating margin
- Cash-to-assets

### Financial Change Variables

Year-over-year changes were calculated for:

- Revenue growth
- Net income growth
- Operating margin
- Leverage
- Current ratio
- Cash-to-assets
- Return on assets

These variables allow the model to distinguish between a company's financial level and the direction in which its fundamentals are moving.

### SEC 8-K Event Features

Rolling 12-month event variables include:

- `management_change_12m`
- `restructuring_12m`
- `material_agreement_12m`
- `acquisition_disposition_12m`
- `total_8k_12m`

This allows the model to incorporate corporate events occurring between quarterly financial reports.

### Persistent Deterioration

Single-quarter deterioration can be noisy.

The project therefore engineered multi-quarter indicators designed to identify persistent weakening.

The final specification includes:

- `cash_deteriorating_3q`
- `leverage_rising_3q`

These indicators identify financial deterioration persisting across three consecutive quarterly observations.

---

## Quarter-Sequence Validation

Because deterioration streaks depend on consecutive observations, fiscal-period continuity was explicitly validated.

Of the 747 observations:

- **725** had a valid previous-quarter gap
- **705** had a valid three-quarter sequence
- **94.38%** of the dataset supported valid three-quarter sequences

Only two irregular fiscal-period gaps were identified in the underlying quarterly history.

This validation was performed before using multi-quarter deterioration variables in the final model.

---

## Modeling Approach

The final model uses a **Random Forest classifier**.

The pipeline includes:

1. Median imputation for missing feature values
2. Class-balanced Random Forest classification
3. Fixed model hyperparameters
4. A probability threshold of **0.50** for binary classification

The final feature specification was selected during model development and then frozen before final holdout evaluation.

---

## Temporal Validation

Financial prediction creates a major risk of look-ahead bias.

The project therefore uses chronological model development rather than randomly splitting quarterly observations.

Training, validation, and final testing were separated through time.

Observations whose forward outcome windows could overlap later evaluation periods were purged where appropriate during model development.

The final evaluation uses **2024 as a frozen temporal holdout**.

Once the final 2024 results were inspected, the model specification was not subsequently altered based on holdout performance.

---

# Final 2024 Holdout Results

The frozen final model produced:

| Metric | Result |
|---|---:|
| ROC-AUC | **0.654** |
| PR-AUC | **0.484** |
| Accuracy | **0.625** |
| Precision | **0.429** |
| Recall | **0.600** |
| F1 Score | **0.500** |

The 2024 holdout contained **80 observations**.

The confusion matrix was:

| | Predicted No Distress | Predicted Distress |
|---|---:|---:|
| Actual No Distress | 35 | 20 |
| Actual Distress | 10 | 15 |

The model therefore identified **15 of 25 distress observations**, corresponding to **60% recall** at the frozen 0.50 classification threshold.

---

## ROC Curve

![2024 Holdout ROC Curve](05_OUTPUTS/final_roc_curve.png)

ROC-AUC measures the model's ability to rank distress observations above non-distress observations across classification thresholds.

The final holdout ROC-AUC was **0.654**.

---

## Precision-Recall Curve

![2024 Holdout Precision-Recall Curve](05_OUTPUTS/final_pr_curve.png)

Because distress observations are less common than non-distress observations, the Precision-Recall curve provides an important complementary measure of model performance.

The final PR-AUC was **0.484**.

---

## Feature Importance

![Final Feature Importance](05_OUTPUTS/final_feature_importance.png)

The strongest model features were primarily financial fundamentals and changes in financial condition.

Leading features included:

- Change in cash-to-assets
- Cash-to-assets
- Liabilities-to-assets
- Return on assets
- Revenue growth
- Total 8-K activity
- Change in current ratio
- Current ratio
- Change in leverage
- Net income growth

The results suggest that liquidity, leverage, profitability, and changes in financial condition contain more predictive information than any individual corporate event category.

Importantly, feature importance in a Random Forest should be interpreted as model relevance rather than causal impact.

---

## Persistent Financial Deterioration

One of the clearest descriptive patterns in the dataset involved persistent cash deterioration.

For observations without a three-quarter cash deterioration streak, the distress rate was approximately:

**20.6%**

For observations experiencing a three-quarter cash deterioration streak, the distress rate increased to approximately:

**37.4%**

Persistent leverage increases also corresponded with a higher distress rate:

- No 3-quarter leverage increase: **22.3%**
- 3-quarter leverage increase: **28.5%**

These results motivated inclusion of cash and leverage persistence variables in the final model.

---

## SEC 8-K Findings

The project initially tested whether unusually high overall 8-K activity was itself a warning signal.

Raw results did not support a simple interpretation that more 8-K filings necessarily imply greater distress risk.

Instead, specific event categories displayed more economically intuitive relationships.

For example, restructuring events showed higher raw distress rates, while management changes and material agreements also exhibited elevated rates relative to observations without those events.

However, event-level regression estimates were statistically uncertain, with wide confidence intervals.

This suggests that the **content and context of corporate disclosures matter more than filing volume alone**.

---

# Uncertainty Analysis

A standard row-level bootstrap produced:

| Metric | Point Estimate | 95% CI |
|---|---:|---:|
| ROC-AUC | 0.654 | 0.514–0.786 |
| PR-AUC | 0.484 | 0.318–0.697 |

However, quarterly observations from the same company are not fully independent.

A second bootstrap therefore resampled **entire companies** rather than individual quarterly observations.

The company-clustered bootstrap produced:

| Metric | Point Estimate | Company-Clustered 95% CI |
|---|---:|---:|
| ROC-AUC | 0.654 | **0.445–0.844** |
| PR-AUC | 0.484 | **0.235–0.721** |

The wider intervals demonstrate substantial uncertainty associated with the relatively small 20-company universe.

![Company-Clustered Bootstrap](05_OUTPUTS/bootstrap_roc_distribution.png)

The company-clustered bootstrap distribution remained centered near the observed model performance:

- ROC bootstrap mean: **0.655**
- ROC bootstrap median: **0.660**

This suggests that the central estimate is not obviously driven by bootstrap bias, although cross-company uncertainty remains high.

---

# Cross-Company Generalization

A Leave-One-Company-Out (LOCO) robustness analysis was performed using pre-2024 observations.

For each iteration:

1. One company was completely removed from training.
2. The model was trained using the other 19 companies.
3. Predictions were generated for the unseen company.
4. The procedure was repeated for all 20 companies.

Combined LOCO performance was:

| Metric | Result |
|---|---:|
| ROC-AUC | **0.522** |
| PR-AUC | **0.253** |
| Accuracy | **0.642** |
| Precision | **0.247** |
| Recall | **0.265** |
| F1 Score | **0.255** |

The median company-level ROC-AUC among companies for which ROC-AUC could be calculated was approximately **0.598**.

These results indicate substantially weaker performance when predicting companies with no historical observations in the training dataset.

The model therefore appears more useful as a **within-company temporal early-warning framework** than as a universal model for completely unseen firms.

---

# Error Analysis

![2024 Holdout Confusion Matrix](05_OUTPUTS/final_confusion_matrix.png)

The frozen 2024 holdout produced:

- **35 True Negatives**
- **20 False Positives**
- **15 True Positives**
- **10 False Negatives**

False-negative analysis showed that some significant future drawdowns occurred even when the company's financial and disclosure features did not produce a sufficiently high model probability.

This is consistent with an important limitation of fundamentally driven market-risk models: stock-price drawdowns may be triggered by information or events not contained in historical accounting fundamentals or SEC event variables.

---

# Key Findings

The project produced several main findings.

### 1. Financial fundamentals contain meaningful predictive information

Liquidity, leverage, profitability, and their year-over-year changes consistently ranked among the most important model inputs.

### 2. Persistent deterioration can be more informative than isolated changes

Three-quarter cash deterioration was associated with a substantially higher future distress rate.

This supports modeling the persistence of deterioration rather than relying exclusively on single-period financial changes.

### 3. SEC disclosures provide contextual information

Overall 8-K filing volume was not a simple distress indicator.

Specific disclosure categories and overall filing activity contributed information to the model, but their predictive relationships were more complex than the original hypothesis that unusually high filing activity necessarily signals distress.

### 4. Temporal prediction is stronger than cross-company transfer

The frozen 2024 model achieved ROC-AUC of **0.654**, while the LOCO robustness test produced ROC-AUC of **0.522**.

This suggests that historical company-specific behavior contributes substantially to predictive performance.

### 5. Model uncertainty is material

Company-clustered confidence intervals were considerably wider than row-level confidence intervals.

The small company universe is therefore an important limitation when interpreting the headline performance estimate.

---

# Limitations

This project has several important limitations.

### Small Company Universe

The dataset contains only 20 companies.

Although the quarterly panel provides hundreds of observations, observations belonging to the same company are correlated.

Future work should substantially expand the company universe.

### Market Distress Is Not Corporate Failure

A severe stock-price drawdown does not necessarily indicate bankruptcy, default, or fundamental insolvency.

The target captures **market-based distress**, which may reflect macroeconomic conditions, valuation changes, regulatory events, or investor sentiment.

### Industry Heterogeneity

Financial ratios have different meanings across industries.

For example, leverage and liquidity structures differ significantly between financial institutions, technology companies, industrial firms, and consumer businesses.

Future versions could incorporate industry normalization or industry-specific models.

### Event Classification

SEC event variables were constructed using rule-based classification and filing-text analysis.

More advanced natural-language-processing methods could potentially distinguish routine corporate disclosures from genuinely adverse events more accurately.

### Limited Cross-Company Generalization

LOCO testing suggests that the model does not currently generalize strongly to companies with no historical observations.

This limits its usefulness as a universal screening model for entirely new firms.

---

# Future Research

Potential extensions include:

- Expanding the dataset to hundreds or thousands of companies
- Industry-normalized financial ratios
- Macroeconomic controls
- Interest-rate and credit-spread variables
- Earnings-call transcript analysis
- More advanced SEC filing NLP
- Executive turnover severity classification
- Debt covenant and refinancing indicators
- Analyst guidance revisions
- Alternative distress thresholds
- Survival-analysis approaches
- Gradient boosting and other model architectures
- Probability calibration
- Longer out-of-sample evaluation periods

A substantially larger cross-sectional universe would be the most important next step.

---

# Technology Stack

The project combines multiple analytical technologies.

### R

Used for data collection, SEC filing processing, text classification, and event engineering.

### PostgreSQL / SQL

Used to store, organize, query, and validate the structured financial dataset.

### Python

Used for:

- Feature engineering
- Model development
- Temporal validation
- Random Forest classification
- Performance evaluation
- Bootstrap confidence intervals
- Error analysis
- Cross-company robustness testing
- Visualization

Key Python libraries include:

- pandas
- NumPy
- scikit-learn
- SQLAlchemy
- psycopg2
- Matplotlib

---

# Project Workflow

The overall pipeline can be summarized as:

```text
SEC Financial Data
        +
SEC 8-K Filings
        +
Historical Market Data
        |
        v
Data Cleaning / Standardization
        |
        v
PostgreSQL Database
        |
        v
Financial Ratio Engineering
        +
YoY Deterioration Features
        +
8-K Event Features
        +
Multi-Quarter Deterioration Streaks
        |
        v
Chronological Model Development
        |
        v
Purged Validation
        |
        v
Frozen Random Forest Specification
        |
        v
2024 Holdout Test
        |
        +--> Bootstrap Uncertainty Analysis
        |
        +--> Error Analysis
        |
        +--> Leave-One-Company-Out Robustness
```

---

# Conclusion

This project finds evidence that publicly observable financial deterioration and corporate disclosure information contain useful, but limited, forward-looking information about severe future equity drawdowns.

The final frozen model achieved a **2024 holdout ROC-AUC of 0.654 and PR-AUC of 0.484**, with **60% recall** at the predetermined classification threshold.

Persistent deterioration in liquidity, particularly cash relative to assets, emerged as one of the clearest warning patterns.

At the same time, company-clustered uncertainty intervals were wide and performance declined substantially when the model was applied to completely unseen companies.

The evidence therefore supports a cautious conclusion:

> **Financial fundamentals and SEC disclosures can contribute to a market-distress early-warning system, particularly when historical company-specific information is available, but the current model should not be interpreted as a universal predictor of corporate failure or future stock performance.**

The project demonstrates an end-to-end empirical workflow combining financial statement analysis, SEC filing data, SQL database management, feature engineering, machine learning, temporal validation, and statistical robustness testing.