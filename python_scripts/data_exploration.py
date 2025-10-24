"""
Basic data exploration for A/B testing dataset.
Loads order data, computes descriptive statistics, and visualizes price distributions.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import rcParams
import shutil

# Use LaTeX fonts if available
if shutil.which("latex"):
    rcParams['text.usetex'] = True
    rcParams['font.family'] = 'serif'
else:
    print("LaTeX not found — using default matplotlib fonts.")

# Display settings
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

# Load datasets
orders = pd.read_csv('../data/raw/olist_orders_dataset.csv')
order_items = pd.read_csv('../data/raw/olist_order_items_dataset.csv')
print(f"Orders: {orders.shape}, Order items: {order_items.shape}")

# Merge orders with item data
orders_with_items = orders.merge(order_items, on='order_id', how='inner')
orders_with_items['total_value'] = orders_with_items['price'] + orders_with_items['freight_value']
print(f"Merged dataset shape: {orders_with_items.shape}")

# Summary statistics
print(f"Price mean: {orders_with_items['price'].mean():.2f}, median: {orders_with_items['price'].median():.2f}")
print(f"Shipping mean: {orders_with_items['freight_value'].mean():.2f}")
print(f"Total order value mean: {orders_with_items['total_value'].mean():.2f}")

# Histogram of item prices
plt.figure(figsize=(8, 4))
plt.hist(orders_with_items['price'], bins=5000, edgecolor='black')
plt.xlabel('Order Price (BRL)')
plt.ylabel('Frequency')
plt.title('Distribution of Order Prices')
plt.axvline(x=100, color='red', linestyle='--', label='Threshold: 100 BRL')
plt.legend()
plt.grid(alpha=0.3)
plt.savefig("../results/figures/new_item_price_distribution_with_threshold.png", dpi=300, bbox_inches='tight')

# Orders above and below threshold
below_100 = (orders_with_items['price'] < 100).sum()
above_100 = (orders_with_items['price'] >= 100).sum()
print(f"Orders below 100 BRL: {below_100}, above: {above_100} ({above_100 / len(orders_with_items) * 100:.2f}%)")

# Aggregate to order level
order_totals = (
    orders_with_items.groupby('order_id')
    .agg(
        total_price=('price', 'sum'),
        total_shipping=('freight_value', 'sum'),
        num_items=('order_item_id', 'count')
    )
    .reset_index()
)
order_totals['order_total'] = order_totals['total_price'] + order_totals['total_shipping']

print(f"Order-level dataset: {order_totals.shape}")
print(f"Mean total order value: {order_totals['order_total'].mean():.2f}")

# Order-level histogram
plt.figure(figsize=(8, 4))
plt.hist(order_totals['total_price'], bins=50, edgecolor='black')
plt.xlabel('Total Order Price (BRL)')
plt.ylabel('Frequency')
plt.title('Distribution of Total Order Prices (Order Level)')
plt.axvline(x=100, color='red', linestyle='--', label='Threshold: 100 BRL')
plt.legend()
plt.grid(alpha=0.3)
plt.savefig("../results/figures/new_order_price_distribution_with_threshold.png", dpi=300, bbox_inches='tight')

# Save processed data
order_totals.to_csv('../data/processed/new_order_totals.csv', index=False)
print(f"Saved processed data: {len(order_totals)} orders.")
