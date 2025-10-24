"""
Statistical analysis for A/B test:
Performs t-tests, confidence intervals, effect size (Cohen's d), power check, and segment analysis.
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

# ---- Load data ----
df = pd.read_csv('../data/processed/new_experiment_results.csv')
print(f"Loaded: {df.shape}")
print(df['group'].value_counts())

control = df[df['group'] == 'control']['final_revenue']
treatment = df[df['group'] == 'treatment']['final_revenue']

# ---- Descriptive stats ----
mean_diff = treatment.mean() - control.mean()
pct_diff = (mean_diff / control.mean()) * 100
print(f"Control mean: {control.mean():.2f}, Treatment mean: {treatment.mean():.2f}, Delta={mean_diff:.2f} ({pct_diff:.2f}%)")

# ---- Two-sample t-test ----
t_stat, p_val = stats.ttest_ind(treatment, control)
print(f"T-test: t={t_stat:.3f}, p={p_val:.4f}")

# ---- Confidence intervals ----
n1, n2 = len(control), len(treatment)
s1, s2 = control.std(), treatment.std()
se_diff = np.sqrt((s1**2 / n1) + (s2**2 / n2))
dfree = min(n1 - 1, n2 - 1)
t_crit = stats.t.ppf(0.975, dfree)
ci_low, ci_high = mean_diff - t_crit * se_diff, mean_diff + t_crit * se_diff
print(f"95% CI: [{ci_low:.2f}, {ci_high:.2f}] BRL")

# ---- Effect size (Cohen’s d) ----
pooled_std = np.sqrt(((n1 - 1)*s1**2 + (n2 - 1)*s2**2) / (n1 + n2 - 2))
cohens_d = mean_diff / pooled_std
print(f"Cohen's d = {cohens_d:.4f}")

# ---- Power analysis ----
alpha = 0.05
power_target = 0.8
z_alpha = stats.norm.ppf(1 - alpha / 2)
z_beta = stats.norm.ppf(power_target)
detectable_effect = ((z_alpha + z_beta) * pooled_std) / np.sqrt(n1 / 2)
print(f"Detectable effect (80% power): {detectable_effect:.2f} BRL ({(detectable_effect / control.mean())*100:.2f}%)")

# ---- Segmentation analysis ----
df['segment'] = pd.cut(
    df['total_price'],
    bins=[0, 75, 150, float('inf')],
    labels=['Small (<75 BRL)', 'Medium (75-150 BRL)', 'Large (>150 BRL)']
)

segments = []
for seg in df['segment'].unique():
    subset = df[df['segment'] == seg]
    c_seg = subset[subset['group'] == 'control']['final_revenue']
    t_seg = subset[subset['group'] == 'treatment']['final_revenue']
    if len(c_seg) and len(t_seg):
        t_s, p_s = stats.ttest_ind(t_seg, c_seg)
        diff_s = t_seg.mean() - c_seg.mean()
        pct_s = (diff_s / c_seg.mean()) * 100
        segments.append({
            'segment': seg,
            'control_mean': c_seg.mean(),
            'treatment_mean': t_seg.mean(),
            'difference': diff_s,
            'pct_diff': pct_s,
            'p_value': p_s
        })

seg_df = pd.DataFrame(segments)
print("\nSegment results:")
print(seg_df[['segment', 'control_mean', 'treatment_mean', 'difference', 'pct_diff', 'p_value']].to_string(index=False))

# ---- Plot segmentation results ----
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Plot 1: Mean revenue by segment
x = np.arange(len(seg_df))
width = 0.35
axes[0, 0].bar(x - width/2, seg_df['control_mean'], width, label='Control', color='lightblue', edgecolor='black')
axes[0, 0].bar(x + width/2, seg_df['treatment_mean'], width, label='Treatment', color='lightcoral', edgecolor='black')
axes[0, 0].set_xticks(x)
axes[0, 0].set_xticklabels(seg_df['segment'], rotation=15)
axes[0, 0].set_title('Mean Revenue by Segment')
axes[0, 0].legend()
axes[0, 0].grid(alpha=0.3, axis='y')

# Plot 2: % difference
colors = ['green' if val > 0 else 'red' for val in seg_df['pct_diff']]
axes[0, 1].bar(seg_df['segment'], seg_df['pct_diff'], color=colors, edgecolor='black')
axes[0, 1].axhline(0, color='black', linestyle='--')
axes[0, 1].set_title('Treatment Effect (%) by Segment')
axes[0, 1].grid(alpha=0.3, axis='y')

# Plot 3: P-values
axes[1, 0].bar(seg_df['segment'], seg_df['p_value'], color='lightgray', edgecolor='black')
axes[1, 0].axhline(0.05, color='red', linestyle='--', label=r'$\alpha=0.05$')
axes[1, 0].set_title('P-values by Segment')
axes[1, 0].legend()
axes[1, 0].grid(alpha=0.3, axis='y')

# Plot 4: Differences in BRL
axes[1, 1].bar(seg_df['segment'], seg_df['difference'], color=colors, edgecolor='black')
axes[1, 1].axhline(0, color='black', linestyle='--')
axes[1, 1].set_title('Revenue Difference (BRL) by Segment')
axes[1, 1].grid(alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('../results/figures/new_segmentation_analysis.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: ../results/figures/new_segmentation_analysis.png")

# ---- Save summary ----
summary = pd.DataFrame({
    'Metric': ['Overall Effect (BRL)', 'Effect (%)', 'P-value', '95% CI Lower', '95% CI Upper', "Cohen's d"],
    'Value': [f"{mean_diff:.2f}", f"{pct_diff:.2f}%", f"{p_val:.4f}", f"{ci_low:.2f}", f"{ci_high:.2f}", f"{cohens_d:.4f}"]
})
summary.to_csv('../data/processed/new_analysis_results.csv', index=False)
print("Saved: ../data/processed/new_analysis_results.csv")
