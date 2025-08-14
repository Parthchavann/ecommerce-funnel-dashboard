#!/usr/bin/env python3
"""
E-Commerce Funnel Analyzer
Comprehensive analysis tool for e-commerce conversion funnel and product performance.
Generates insights and recommendations for improving conversion rates.
"""

import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os

class FunnelAnalyzer:
    def __init__(self, db_path='ecommerce.db'):
        """Initialize the funnel analyzer with database connection."""
        self.db_path = db_path
        self.conn = None
        self.recommendations = []
        
    def connect_db(self):
        """Create database connection."""
        self.conn = sqlite3.connect(self.db_path)
        return self.conn
    
    def close_db(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
    
    def load_data(self):
        """Load data from CSV files if database doesn't exist."""
        if not os.path.exists(self.db_path):
            print("📊 Loading data from CSV files...")
            self.conn = sqlite3.connect(self.db_path)
            
            # Load and create tables
            with open('sql/create_tables.sql', 'r') as f:
                self.conn.executescript(f.read())
            
            # Load data from CSV files
            tables = {
                'products': 'data/raw/products.csv',
                'customers': 'data/raw/customers.csv', 
                'web_events': 'data/raw/web_events.csv',
                'orders': 'data/raw/orders.csv'
            }
            
            for table_name, csv_path in tables.items():
                if os.path.exists(csv_path):
                    df = pd.read_csv(csv_path)
                    df.to_sql(table_name, self.conn, if_exists='replace', index=False)
                    print(f"   ✅ Loaded {len(df):,} rows into {table_name}")
            
            print("📊 Database created successfully!")
        else:
            self.connect_db()
    
    def calculate_funnel_metrics(self):
        """Calculate comprehensive funnel metrics."""
        query = """
        WITH funnel_stages AS (
            SELECT 
                COUNT(DISTINCT CASE WHEN event_type = 'page_view' THEN session_id END) as visits,
                COUNT(DISTINCT CASE WHEN event_type = 'product_view' THEN session_id END) as product_views,
                COUNT(DISTINCT CASE WHEN event_type = 'add_to_cart' THEN session_id END) as add_to_cart,
                COUNT(DISTINCT CASE WHEN event_type = 'checkout_start' THEN session_id END) as checkout_start,
                COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN session_id END) as purchases
            FROM web_events
            WHERE timestamp >= DATE('now', '-30 days')
        )
        SELECT 
            visits,
            product_views,
            add_to_cart, 
            checkout_start,
            purchases,
            ROUND(100.0 * product_views / visits, 2) as visit_to_view_rate,
            ROUND(100.0 * add_to_cart / product_views, 2) as view_to_cart_rate,
            ROUND(100.0 * checkout_start / add_to_cart, 2) as cart_to_checkout_rate,
            ROUND(100.0 * purchases / checkout_start, 2) as checkout_to_purchase_rate,
            ROUND(100.0 * purchases / visits, 2) as overall_conversion_rate,
            ROUND(100.0 * (1 - purchases * 1.0 / checkout_start), 2) as abandonment_rate
        FROM funnel_stages
        """
        return pd.read_sql_query(query, self.conn)
    
    def analyze_abandonment_reasons(self):
        """Analyze reasons for cart abandonment."""
        query = """
        SELECT 
            abandonment_reason,
            COUNT(*) as count,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 1) as percentage
        FROM web_events
        WHERE abandonment_reason IS NOT NULL
          AND timestamp >= DATE('now', '-30 days')
        GROUP BY abandonment_reason
        ORDER BY count DESC
        """
        return pd.read_sql_query(query, self.conn)
    
    def analyze_product_performance(self):
        """Analyze product-level conversion and profitability."""
        query = """
        WITH product_metrics AS (
            SELECT 
                p.product_id,
                p.product_name,
                p.category,
                p.price,
                p.margin_percent,
                COUNT(DISTINCT CASE WHEN we.event_type = 'product_view' THEN we.session_id END) as views,
                COUNT(DISTINCT CASE WHEN we.event_type = 'add_to_cart' THEN we.session_id END) as cart_adds,
                COUNT(DISTINCT CASE WHEN we.event_type = 'purchase' THEN we.session_id END) as purchases,
                COALESCE(SUM(o.revenue), 0) as total_revenue,
                COALESCE(SUM(o.profit), 0) as total_profit,
                COALESCE(SUM(o.quantity), 0) as units_sold
            FROM products p
            LEFT JOIN web_events we ON p.product_id = we.product_id 
                AND we.timestamp >= DATE('now', '-30 days')
            LEFT JOIN orders o ON p.product_id = o.product_id 
                AND o.order_date >= DATE('now', '-30 days')
            GROUP BY p.product_id, p.product_name, p.category, p.price, p.margin_percent
        )
        SELECT 
            *,
            ROUND(100.0 * cart_adds / NULLIF(views, 0), 2) as view_to_cart_rate,
            ROUND(100.0 * purchases / NULLIF(cart_adds, 0), 2) as cart_to_purchase_rate,
            ROUND(100.0 * purchases / NULLIF(views, 0), 2) as overall_conversion_rate,
            ROUND(total_profit / NULLIF(total_revenue, 0) * 100, 2) as profit_margin,
            -- Performance score calculation
            ROUND(
                (COALESCE(100.0 * cart_adds / NULLIF(views, 0), 0) * 0.3) +
                (COALESCE(100.0 * purchases / NULLIF(cart_adds, 0), 0) * 0.4) +
                (COALESCE(total_profit / NULLIF(total_revenue, 0) * 100, 0) * 0.3), 2
            ) as performance_score
        FROM product_metrics
        WHERE views > 0
        ORDER BY performance_score DESC
        """
        return pd.read_sql_query(query, self.conn)
    
    def analyze_customer_segments(self):
        """Analyze performance by customer segment."""
        query = """
        SELECT 
            c.customer_segment,
            COUNT(DISTINCT c.customer_id) as customers,
            COUNT(DISTINCT we.session_id) as sessions,
            COUNT(DISTINCT CASE WHEN we.event_type = 'purchase' THEN we.session_id END) as conversions,
            ROUND(100.0 * COUNT(DISTINCT CASE WHEN we.event_type = 'purchase' THEN we.session_id END) / 
                  COUNT(DISTINCT we.session_id), 2) as conversion_rate,
            COALESCE(AVG(o.revenue), 0) as avg_order_value,
            COALESCE(SUM(o.revenue), 0) as total_revenue
        FROM customers c
        LEFT JOIN web_events we ON c.customer_id = we.customer_id 
            AND we.timestamp >= DATE('now', '-30 days')
        LEFT JOIN orders o ON c.customer_id = o.customer_id 
            AND o.order_date >= DATE('now', '-30 days')
        GROUP BY c.customer_segment
        ORDER BY conversion_rate DESC
        """
        return pd.read_sql_query(query, self.conn)
    
    def calculate_revenue_impact(self, current_conversion, improved_conversion, revenue):
        """Calculate potential revenue impact of conversion improvements."""
        return revenue * (improved_conversion / current_conversion - 1)
    
    def generate_recommendations(self):
        """Generate actionable recommendations based on analysis."""
        recommendations = []
        
        # Get funnel metrics
        funnel_df = self.calculate_funnel_metrics()
        abandonment_df = self.analyze_abandonment_reasons()
        product_df = self.analyze_product_performance()
        
        if len(funnel_df) > 0:
            funnel = funnel_df.iloc[0]
            
            # High-level funnel recommendations
            if funnel['abandonment_rate'] > 60:
                recommendations.append({
                    'priority': 'HIGH',
                    'category': 'Checkout Process',
                    'issue': f"Cart abandonment rate is {funnel['abandonment_rate']:.1f}%",
                    'recommendation': 'Simplify checkout process to 3 steps maximum and add progress indicators',
                    'expected_impact': f"15-20% reduction in abandonment (potential +{self.calculate_revenue_impact(funnel['overall_conversion_rate'], funnel['overall_conversion_rate'] * 1.15, 100000):.0f}% revenue)",
                    'implementation_effort': 'Medium (2-3 weeks)'
                })
        
        # Abandonment reason recommendations
        if len(abandonment_df) > 0:
            top_reason = abandonment_df.iloc[0]
            if top_reason['abandonment_reason'] == 'high_shipping':
                recommendations.append({
                    'priority': 'HIGH',
                    'category': 'Shipping Strategy',
                    'issue': f"{top_reason['percentage']}% abandon due to high shipping costs",
                    'recommendation': 'A/B test free shipping threshold at $50 vs current policy',
                    'expected_impact': '8-12% increase in conversion rate',
                    'implementation_effort': 'Low (1 week)'
                })
            elif top_reason['abandonment_reason'] == 'payment_failed':
                recommendations.append({
                    'priority': 'HIGH',
                    'category': 'Payment Processing',
                    'issue': f"{top_reason['percentage']}% abandon due to payment failures",
                    'recommendation': 'Add alternative payment methods (PayPal, Apple Pay, Google Pay)',
                    'expected_impact': '5-8% increase in successful transactions',
                    'implementation_effort': 'Medium (2-3 weeks)'
                })
        
        # Product-specific recommendations
        if len(product_df) > 0:
            # Low performing products with high views
            low_performers = product_df[
                (product_df['view_to_cart_rate'] < product_df['view_to_cart_rate'].median()) &
                (product_df['views'] > product_df['views'].quantile(0.75))
            ].head(3)
            
            for _, product in low_performers.iterrows():
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': f"Product Optimization",
                    'issue': f"Product '{product['product_name']}' has {product['views']} views but only {product['view_to_cart_rate']:.1f}% add to cart",
                    'recommendation': 'Review product images, descriptions, and competitive pricing',
                    'expected_impact': f"Potential ${product['price'] * 20:.0f} additional monthly revenue per product",
                    'implementation_effort': 'Low (1-2 days per product)'
                })
            
            # High margin products with low conversion
            high_margin_low_conv = product_df[
                (product_df['profit_margin'] > 30) &
                (product_df['overall_conversion_rate'] < product_df['overall_conversion_rate'].median()) &
                (product_df['views'] > 10)
            ].head(5)
            
            if len(high_margin_low_conv) > 0:
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': 'Pricing Strategy',
                    'issue': f"{len(high_margin_low_conv)} high-margin products with below-average conversion",
                    'recommendation': 'A/B test 10-15% price reduction on these products',
                    'expected_impact': '20-30% increase in conversion for tested products',
                    'implementation_effort': 'Low (1 week for setup)'
                })
        
        # Technical recommendations
        recommendations.append({
            'priority': 'MEDIUM',
            'category': 'User Experience',
            'issue': 'Mobile vs desktop conversion analysis needed',
            'recommendation': 'Implement mobile-first checkout design with larger buttons and simplified forms',
            'expected_impact': '10-15% increase in mobile conversion',
            'implementation_effort': 'High (4-6 weeks)'
        })
        
        return recommendations
    
    def create_dashboard_data(self):
        """Create processed data files for dashboard creation."""
        print("📊 Creating dashboard data files...")
        
        # Ensure processed directory exists
        os.makedirs('data/processed', exist_ok=True)
        
        # Generate all analysis data
        funnel_metrics = self.calculate_funnel_metrics()
        abandonment_reasons = self.analyze_abandonment_reasons()
        product_performance = self.analyze_product_performance()
        customer_segments = self.analyze_customer_segments()
        
        # Save to CSV files
        funnel_metrics.to_csv('data/processed/funnel_metrics.csv', index=False)
        abandonment_reasons.to_csv('data/processed/abandonment_reasons.csv', index=False)
        product_performance.to_csv('data/processed/product_performance.csv', index=False)
        customer_segments.to_csv('data/processed/customer_segments.csv', index=False)
        
        # Generate recommendations
        recommendations = self.generate_recommendations()
        recommendations_df = pd.DataFrame(recommendations)
        recommendations_df.to_csv('data/processed/recommendations.csv', index=False)
        
        # Create summary metrics for KPI cards
        if len(funnel_metrics) > 0:
            funnel = funnel_metrics.iloc[0]
            summary_metrics = {
                'total_visits': int(funnel['visits']),
                'conversion_rate': float(funnel['overall_conversion_rate']),
                'abandonment_rate': float(funnel['abandonment_rate']),
                'avg_order_value': float(product_performance['total_revenue'].sum() / product_performance['purchases'].sum()) if product_performance['purchases'].sum() > 0 else 0,
                'total_revenue': float(product_performance['total_revenue'].sum()),
                'total_profit': float(product_performance['total_profit'].sum())
            }
            
            with open('data/processed/summary_metrics.json', 'w') as f:
                json.dump(summary_metrics, f, indent=2)
        
        print("✅ Dashboard data files created successfully!")
        return {
            'funnel_metrics': funnel_metrics,
            'abandonment_reasons': abandonment_reasons, 
            'product_performance': product_performance,
            'customer_segments': customer_segments,
            'recommendations': recommendations
        }
    
    def print_analysis_summary(self):
        """Print a comprehensive analysis summary."""
        print("\n" + "="*60)
        print("🎯 E-COMMERCE FUNNEL ANALYSIS SUMMARY")
        print("="*60)
        
        # Funnel Overview
        funnel_df = self.calculate_funnel_metrics()
        if len(funnel_df) > 0:
            funnel = funnel_df.iloc[0]
            print(f"\n📈 CONVERSION FUNNEL (Last 30 Days)")
            print(f"   Visits: {funnel['visits']:,}")
            print(f"   Product Views: {funnel['product_views']:,} ({funnel['visit_to_view_rate']:.1f}% of visits)")
            print(f"   Add to Cart: {funnel['add_to_cart']:,} ({funnel['view_to_cart_rate']:.1f}% of views)")
            print(f"   Checkout Started: {funnel['checkout_start']:,} ({funnel['cart_to_checkout_rate']:.1f}% of carts)")
            print(f"   Purchases: {funnel['purchases']:,} ({funnel['checkout_to_purchase_rate']:.1f}% of checkouts)")
            print(f"   Overall Conversion: {funnel['overall_conversion_rate']:.2f}%")
            print(f"   Cart Abandonment: {funnel['abandonment_rate']:.1f}%")
        
        # Abandonment Reasons
        abandonment_df = self.analyze_abandonment_reasons()
        if len(abandonment_df) > 0:
            print(f"\n🚫 TOP ABANDONMENT REASONS")
            for _, reason in abandonment_df.head(3).iterrows():
                print(f"   {reason['abandonment_reason'].replace('_', ' ').title()}: {reason['percentage']:.1f}%")
        
        # Product Performance
        product_df = self.analyze_product_performance()
        if len(product_df) > 0:
            print(f"\n🏆 TOP PERFORMING PRODUCTS")
            top_products = product_df.head(3)
            for _, product in top_products.iterrows():
                print(f"   {product['product_name']}: {product['overall_conversion_rate']:.1f}% conversion, ${product['total_revenue']:,.0f} revenue")
            
            print(f"\n⚠️  PRODUCTS NEEDING ATTENTION")
            low_products = product_df[product_df['performance_score'] < 30].head(3)
            for _, product in low_products.iterrows():
                print(f"   {product['product_name']}: {product['performance_score']:.1f} performance score")
        
        # Customer Segments
        segment_df = self.analyze_customer_segments()
        if len(segment_df) > 0:
            print(f"\n👥 CUSTOMER SEGMENT PERFORMANCE")
            for _, segment in segment_df.iterrows():
                print(f"   {segment['customer_segment']}: {segment['conversion_rate']:.1f}% conversion, ${segment['avg_order_value']:.0f} AOV")
        
        # Recommendations
        recommendations = self.generate_recommendations()
        print(f"\n💡 TOP RECOMMENDATIONS")
        for rec in recommendations[:3]:
            print(f"   [{rec['priority']}] {rec['category']}")
            print(f"       Issue: {rec['issue']}")
            print(f"       Action: {rec['recommendation']}")
            print(f"       Impact: {rec['expected_impact']}")
            print()
        
        print("="*60)

def main():
    """Main execution function."""
    print("🚀 Starting E-Commerce Funnel Analysis...")
    
    analyzer = FunnelAnalyzer()
    
    try:
        # Load data and connect to database
        analyzer.load_data()
        
        # Generate dashboard data
        dashboard_data = analyzer.create_dashboard_data()
        
        # Print comprehensive analysis
        analyzer.print_analysis_summary()
        
        print(f"\n✅ Analysis completed successfully!")
        print(f"📁 Processed data saved to data/processed/")
        print(f"🎯 Ready for dashboard creation!")
        
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        analyzer.close_db()

if __name__ == "__main__":
    main()