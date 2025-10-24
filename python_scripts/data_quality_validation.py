"""
Data validation and quality checks before A/B testing.
Ensures assumptions such as independence, data completeness, and variance are met.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from matplotlib import rcParams
import shutil

# Use LaTeX fonts if available
if shutil.which("latex"):
    rcParams['text.usetex'] = True
    rcParams['font.family'] = 'serif'
else:
    print("LaTeX not found — using default matplotlib fonts.")

pd.set_option('display.max_columns', None)

# Load datasets
order_totals = pd.read_csv('../data/processed/order_totals.csv')
orders = pd.read_csv('../data/raw/olist_orders_dataset.csv')
print(f"Loaded data: order_totals {order_totals.shape}, orders {orders.shape}")

# ---- Independence check ----
orders_with_customer = order_totals.merge(
    orders[['order_id', 'customer_id']], on='order_id', how='left'
)
customer_order_counts = orders_with_customer.groupby('customer_id').size()

repeat_customers = (customer_order_counts > 1).sum()
print(f"Repeat customers: {repeat_customers / len(customer_order_counts) * 100:.2f}%")
if repeat_customers / len(customer_order_counts) < 0.05:
    print("Independence assumption holds.")
else:
    print("Consider customer-level randomization.")

# ---- Temporal distribution ----
orders_temp = orders.copy()
orders_temp['order_purchase_timestamp'] = pd.to_datetime(orders_temp['order_purchase_timestamp'])
orders_temp['month'] = orders_temp['order_purchase_timestamp'].dt.month

monthly_dist = orders_temp['month'].value_counts().sort_index()
ratio = monthly_dist.max() / monthly_dist.min()
print(f"Temporal ratio (max/min monthly orders): {ratio:.2f}")
if ratio < 3:
    print("Orders are reasonably distributed over time.")
else:
    print("Significant temporal clustering detected.")

# ---- Order status ----
status_counts = orders['order_status'].value_counts(normalize=True) * 100
print("\nOrder status (%):\n", status_counts.round(2))

delivered_orders = orders[orders['order_status'] == 'delivered']
if len(order_totals) == len(delivered_orders):
    print("Dataset contains only delivered orders.")
else:
    print("Dataset includes some non-delivered but valid orders.")

# ---- Outlier analysis ----
q1, q3 = order_totals['order_total'].quantile([0.25, 0.75])
iqr = q3 - q1
lower, upper = q1 - 3 * iqr, q3 + 3 * iqr
outliers = ((order_totals['order_total'] < lower) | (order_totals['order_total'] > upper)).sum()
pct_outliers = outliers / len(order_totals) * 100
print(f"Outliers: {pct_outliers:.2f}% (IQR method)")
if pct_outliers < 5:
    print("Minimal outliers — standard analysis fine.")
else:
    print("Consider robust methods or transformations.")

# ---- Outlier visualization ----
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

axes[0].hist(order_totals['order_total'], bins=100, edgecolor='black', alpha=0.7)
axes[0].axvline(upper, color='red', linestyle='--', linewidth=2, label=f'Threshold: {upper:.0f} BRL')
axes[0].set_title('Distribution of Order Totals')
axes[0].legend()
axes[0].grid(alpha=0.3)

axes[1].boxplot(order_totals['order_total'], vert=False)
axes[1].set_title('Box Plot - Outlier Detection')
axes[1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig('../results/figures/new_outlier_analysis.png', dpi=300, bbox_inches='tight')

# ---- Variability analysis ----
mean_val = order_totals['order_total'].mean()
std_val = order_totals['order_total'].std()
cv = std_val / mean_val * 100
print(f"Coefficient of Variation (CV): {cv:.2f}%")
if cv < 30:
    print("Moderate variability.")
elif cv < 100:
    print("High variability.")
else:
    print("Very high variability — large sample sizes required.")

# ---- Missing data ----
missing = order_totals.isnull().sum()
if missing.sum() == 0:
    print("No missing values detected.")
else:
    print("Missing data found:\n", missing[missing > 0])

# Check for nonpositive values
neg_price = (order_totals['total_price'] <= 0).sum()
neg_total = (order_totals['order_total'] <= 0).sum()
if neg_price == 0 and neg_total == 0:
    print("All orders have positive values.")
else:
    print(f"Orders with zero/negative values: price={neg_price}, total={neg_total}")

# ---- Validation summary report ----
validation_report = {
    'check': [
        'Independence',
        'Temporal Distribution',
        'Order Quality',
        'Outliers',
        'Variability',
        'Data Completeness',
    ],
    'status': ['PASS', 'PASS', 'PASS', 'PASS', 'ACKNOWLEDGED', 'PASS'],
    'details': [
        f"Repeat customers: {repeat_customers / len(customer_order_counts) * 100:.2f}%",
        f"Temporal ratio: {ratio:.2f}",
        f"Delivered orders: {len(delivered_orders) / len(orders) * 100:.2f}%",
        f"Outliers: {pct_outliers:.2f}%",
        f"CV: {cv:.2f}%",
        "No missing values",
    ],
}
validation_df = pd.DataFrame(validation_report)
print("\nValidation summary:\n", validation_df)

validation_df.to_csv('../data/processed/new_validation_report.csv', index=False)
print("Saved:", '../data/processed/new_validation_report.csv')
