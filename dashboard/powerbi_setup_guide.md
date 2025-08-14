# Power BI Dashboard Setup Guide

This guide walks you through creating the E-Commerce Funnel Dashboard in Power BI Desktop (free version).

## Prerequisites

1. **Power BI Desktop** (free download from Microsoft)
2. **Generated data files** in `data/processed/` directory
3. **Run the analysis** scripts to generate processed data

## Step 1: Data Import

1. Open Power BI Desktop
2. Click **Get Data** > **Text/CSV**
3. Import the following files from `data/processed/`:
   - `funnel_metrics.csv`
   - `product_performance.csv`
   - `customer_segments.csv`
   - `abandonment_reasons.csv`
   - `recommendations.csv`

## Step 2: Create Relationships

Go to **Model** view and create relationships:
- No relationships needed for this dashboard (all summary tables)

## Step 3: Create Measures

Go to **Data** view and create these DAX measures:

### Key Performance Indicators
```dax
Total Visits = SUM(funnel_metrics[visits])
Total Purchases = SUM(funnel_metrics[purchases])
Overall Conversion Rate = DIVIDE([Total Purchases], [Total Visits], 0) * 100
Cart Abandonment Rate = AVERAGE(funnel_metrics[abandonment_rate])
Total Revenue = SUM(product_performance[total_revenue])
Average Order Value = DIVIDE([Total Revenue], [Total Purchases], 0)
```

### Conditional Formatting
```dax
Conversion Rate Color = 
IF([Overall Conversion Rate] >= 7, "Green",
IF([Overall Conversion Rate] >= 5, "Yellow", "Red"))

Performance Tier Color = 
SWITCH(
    TRUE(),
    product_performance[performance_score] >= 70, "Green",
    product_performance[performance_score] >= 40, "Orange",
    "Red"
)
```

## Step 4: Create Visualizations

### Page Layout: E-Commerce Funnel Dashboard

#### Row 1: KPI Cards
Create 4 **Card** visualizations:

1. **Conversion Rate Card**
   - Value: `Overall Conversion Rate`
   - Format: Percentage with 1 decimal
   - Conditional formatting based on `Conversion Rate Color`

2. **Cart Abandonment Card** 
   - Value: `Cart Abandonment Rate`
   - Format: Percentage with 1 decimal
   - Color: Red if >65%, Yellow if >55%, Green otherwise

3. **Average Order Value Card**
   - Value: `Average Order Value`
   - Format: Currency

4. **Total Revenue Card**
   - Value: `Total Revenue`
   - Format: Currency, abbreviated (K/M)

#### Row 2: Main Analysis

1. **Funnel Chart** (Left Half)
   - Visual: **Funnel** chart
   - Category: Custom column with stages
   ```dax
   Funnel Stages = 
   DATATABLE(
       "Stage", STRING,
       "Value", INTEGER,
       {
           {"Visits", [Total Visits]},
           {"Product Views", SUM(funnel_metrics[product_views])},
           {"Add to Cart", SUM(funnel_metrics[add_to_cart])},
           {"Checkout", SUM(funnel_metrics[checkout_start])},
           {"Purchase", [Total Purchases]}
       }
   )
   ```

2. **Abandonment Reasons** (Right Half)
   - Visual: **Donut** chart
   - Legend: `abandonment_reasons[abandonment_reason]`
   - Values: `abandonment_reasons[percentage]`
   - Colors: Custom palette (reds/oranges)

#### Row 3: Product Performance

1. **Product Performance Matrix**
   - Visual: **Table**
   - Columns:
     - `product_performance[product_name]`
     - `product_performance[category]`
     - `product_performance[views]`
     - `product_performance[overall_conversion_rate]`
     - `product_performance[total_revenue]`
     - `product_performance[performance_score]`
   - Conditional formatting on performance_score column
   - Sort by: `performance_score` descending

#### Row 4: Trends and Recommendations

1. **Customer Segment Performance** (Left)
   - Visual: **Clustered Bar Chart**
   - Axis: `customer_segments[customer_segment]`
   - Values: `customer_segments[conversion_rate]`
   - Secondary values: `customer_segments[avg_order_value]`

2. **Top Recommendations** (Right)
   - Visual: **Table**
   - Columns:
     - `recommendations[priority]`
     - `recommendations[category]`
     - `recommendations[recommendation]`
     - `recommendations[expected_impact]`
   - Conditional formatting on priority column

## Step 5: Formatting and Styling

### Theme and Colors
1. Go to **View** > **Themes** > **Colorblind Safe**
2. Custom colors:
   - Primary: #1f77b4 (Blue)
   - Secondary: #ff7f0e (Orange)  
   - Accent: #2ca02c (Green)
   - Warning: #d62728 (Red)

### Dashboard Styling
1. **Background**: Light gray (#f8f9fa)
2. **Card backgrounds**: White with subtle shadow
3. **Title**: "E-Commerce Funnel & Sales Performance Dashboard"
4. **Font**: Segoe UI, 12pt for content, 16pt for titles

### Interactive Features
1. **Cross-filtering**: Enable between charts
2. **Drill-through**: Product table to detailed view
3. **Tooltips**: Custom tooltips with additional context
4. **Bookmarks**: Save different views (Overview, Product Focus, Customer Focus)

## Step 6: Advanced Features

### Custom Tooltips
Create tooltip pages for enhanced interactivity:

1. **Product Tooltip**
   - Mini chart showing trend
   - Key metrics summary
   - Recommendation if low performing

2. **Funnel Stage Tooltip**
   - Stage-specific insights
   - Drop-off reasons
   - Improvement suggestions

### Slicers and Filters
Add these interactive elements:

1. **Date Range Slicer**
   - If you have date dimension
   - Last 7/30/90 days options

2. **Category Filter**
   - Product category dropdown
   - Multi-select capability

3. **Customer Segment Filter**
   - VIP/Regular/New selection
   - Default: All selected

## Step 7: Dashboard Layout

```
┌─────────────────────────────────────────────────────────┐
│               E-Commerce Funnel Dashboard               │
├─────────────────────────────────────────────────────────┤
│  [Conv Rate] [Cart Aband] [AOV]      [Total Rev]       │
│     5.2%        68.5%     $127       $2.5M             │
├─────────────────────────────────────────────────────────┤
│  Funnel Chart                │  Abandonment Reasons     │
│  ┌──────────────────┐       │  ┌────────────────────┐   │
│  │ Visits: 100K     │       │  │ Shipping: 30%      │   │
│  │   ↓              │       │  │ Payment: 20%       │   │
│  │ Views: 65K       │       │  │ Price: 25%         │   │
│  │   ↓              │       │  │ Delivery: 15%      │   │
│  │ Cart: 26K        │       │  │ Technical: 10%     │   │
│  │   ↓              │       │  └────────────────────┘   │
│  │ Checkout: 9K     │       │                           │
│  │   ↓              │       │                           │
│  │ Purchase: 2.7K   │       │                           │
│  └──────────────────┘       │                           │
├─────────────────────────────────────────────────────────┤
│  Product Performance Table                              │
│  ┌───────────────────────────────────────────────────┐ │
│  │Product │Cat│Views│Conv%│Revenue│Score│Tier       │ │
│  │Laptop  │El │15K  │8.5% │$450K  │85  │High      │ │
│  │Phone   │El │12K  │7.2% │$380K  │78  │High      │ │
│  └───────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│  Segment Performance        │  Top Recommendations     │
│  ┌──────────────────┐      │  ┌──────────────────────┐ │
│  │ VIP: 12.5%       │      │  │[HIGH] Free Shipping  │ │
│  │ Regular: 7.8%    │      │  │[HIGH] Simplify       │ │
│  │ New: 3.2%        │      │  │       Checkout       │ │
│  └──────────────────┘      │  │[MED]  Product Pages  │ │
│                             │  └──────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Step 8: Publishing and Sharing

### Save and Export
1. **Save** the .pbix file to `dashboard/` folder
2. **Export** to PDF for presentations
3. **Publish** to Power BI Service (free tier) if needed

### Performance Optimization
1. **Reduce data size**: Use aggregated tables
2. **Optimize queries**: Pre-calculate measures
3. **Use DirectQuery**: For large datasets (if needed)

## Step 9: Scheduled Refresh

For real-world implementation:
1. Set up **automated data refresh**
2. Configure **email alerts** for metric thresholds
3. Create **mobile-friendly** version

## Troubleshooting

### Common Issues
1. **Data not loading**: Check file paths and permissions
2. **Charts not displaying**: Verify column names match exactly
3. **Performance issues**: Reduce data granularity
4. **Formatting problems**: Check data types in queries

### Best Practices
1. **Test with sample data** first
2. **Document all measures** and calculations
3. **Use consistent naming** conventions
4. **Regular backups** of .pbix files

## Next Steps

1. **Create mobile layout** for tablet/phone viewing
2. **Add more interactivity** with drill-through pages
3. **Implement real-time data** connections
4. **Create automated reports** with Power Automate
5. **Set up monitoring alerts** for key metrics

This dashboard provides a complete view of e-commerce performance and actionable insights for optimization. The visual design makes it easy for stakeholders to understand funnel performance and prioritize improvements.