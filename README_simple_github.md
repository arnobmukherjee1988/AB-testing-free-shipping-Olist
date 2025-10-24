# E-commerce Free Shipping A/B Test Analysis

A statistical analysis evaluating whether offering free shipping above a threshold increases e-commerce revenue, using Brazilian marketplace transaction data.

## Project Overview

**Business Question:** Should we offer free shipping for orders above 100 BRL to increase revenue?

**Answer:** No for universal free shipping. Yes for targeted free shipping to customers with small orders.

**Key Finding:** Overall treatment shows no effect (-0.50%, p=0.76), but segmentation reveals small orders increase by 35.92% while medium and large orders decrease revenue. This demonstrates Simpson's Paradox where aggregate results hide important subgroup patterns.

## Dataset

Brazilian e-commerce marketplace data containing 98,666 orders from 2016-2018. The dataset includes order values, shipping costs, number of items, and customer information.
