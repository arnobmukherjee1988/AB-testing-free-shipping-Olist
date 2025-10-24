# E-commerce Free Shipping A/B Test Analysis

A statistical analysis evaluating whether offering free shipping above a threshold increases e-commerce revenue, using Brazilian marketplace transaction data.

## Project Overview

**Business Question:** Should we offer free shipping for orders above 100 BRL to increase revenue?

**Answer:** No for universal free shipping. Yes for targeted free shipping to customers with small orders.

**Key Finding:** Overall treatment shows no effect (-0.50%, p=0.76), but segmentation reveals small orders increase by 35.92% while medium and large orders decrease revenue. This demonstrates Simpson's Paradox where aggregate results hide important subgroup patterns.

## Dataset

Brazilian e-commerce marketplace data containing 98,666 orders from 2016-2018. The dataset includes order values, shipping costs, number of items, and customer information.

## Repository Structure

```
Parent/
├── data/
│   ├── raw/                    # Original dataset (9 CSV files)
│   └── processed/              # Cleaned and processed data
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 01_5_data_quality_validation.ipynb
│   ├── 02_experiment_design.ipynb
│   ├── 03_treatment_assignment.ipynb
│   ├── 04_analysis.ipynb
│   └── 05_results_summary.ipynb
└── results/
    └── figures/                # Analysis visualizations
```

## Methodology

### Analysis Approach
1. Data quality validation (independence, outliers, variance)
2. Power analysis and sample size calculation
3. Treatment effect simulation (40% response rate assumption)
4. Two-sample t-test for statistical significance
5. Segmentation analysis by order size
6. Economic impact and ROI calculation

### Experiment Design
- Sample size: 23,674 orders (11,772 control, 11,902 treatment)
- Statistical power: 80%
- Significance level: 0.05
- Minimum detectable effect: 5% revenue increase
- Treatment: Free shipping for orders above 100 BRL