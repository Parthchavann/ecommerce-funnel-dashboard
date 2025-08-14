#!/usr/bin/env python3
"""
Database Setup Script
Creates SQLite database and loads sample data for the e-commerce funnel dashboard.
"""

import sqlite3
import pandas as pd
import os
import sys

def create_database():
    """Create SQLite database with proper schema."""
    print("🗄️  Creating SQLite database...")
    
    # Remove existing database if it exists
    if os.path.exists('ecommerce.db'):
        os.remove('ecommerce.db')
        print("   Removed existing database")
    
    # Create new database connection
    conn = sqlite3.connect('ecommerce.db')
    
    # Execute schema creation
    with open('sql/create_tables.sql', 'r') as f:
        schema = f.read()
        conn.executescript(schema)
    
    print("✅ Database schema created successfully!")
    return conn

def load_csv_data(conn):
    """Load data from CSV files into database tables."""
    print("📊 Loading CSV data into database...")
    
    # Define table mappings
    tables = {
        'products': 'data/raw/products.csv',
        'customers': 'data/raw/customers.csv',
        'web_events': 'data/raw/web_events.csv',
        'orders': 'data/raw/orders.csv'
    }
    
    for table_name, csv_path in tables.items():
        if os.path.exists(csv_path):
            print(f"   Loading {csv_path}...")
            df = pd.read_csv(csv_path)
            
            # Handle data type conversions for specific tables
            if table_name == 'web_events':
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            elif table_name == 'orders':
                df['order_date'] = pd.to_datetime(df['order_date']).dt.date
            elif table_name == 'customers':
                df['registration_date'] = pd.to_datetime(df['registration_date']).dt.date
            
            # Load into database
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            print(f"   ✅ Loaded {len(df):,} rows into {table_name}")
        else:
            print(f"   ⚠️  File not found: {csv_path}")
    
    print("✅ All data loaded successfully!")

def verify_data_integrity(conn):
    """Verify that data was loaded correctly."""
    print("🔍 Verifying data integrity...")
    
    # Check record counts
    tables = ['products', 'customers', 'web_events', 'orders']
    
    for table in tables:
        result = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
        print(f"   {table}: {result[0]:,} records")
    
    # Check for basic data quality issues
    print("\n🔍 Running data quality checks...")
    
    # Check for NULL values in critical fields
    critical_checks = [
        ("products", "product_name IS NULL OR price IS NULL"),
        ("customers", "customer_id IS NULL OR customer_segment IS NULL"),
        ("web_events", "event_type IS NULL OR timestamp IS NULL"),
        ("orders", "revenue IS NULL OR order_date IS NULL")
    ]
    
    for table, condition in critical_checks:
        result = conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {condition}").fetchone()
        if result[0] > 0:
            print(f"   ⚠️  Found {result[0]} records with NULL critical fields in {table}")
        else:
            print(f"   ✅ No NULL critical fields in {table}")
    
    # Check conversion funnel logic
    print("\n🎯 Verifying funnel metrics...")
    funnel_query = """
    SELECT 
        COUNT(DISTINCT CASE WHEN event_type = 'page_view' THEN session_id END) as visits,
        COUNT(DISTINCT CASE WHEN event_type = 'product_view' THEN session_id END) as product_views,
        COUNT(DISTINCT CASE WHEN event_type = 'add_to_cart' THEN session_id END) as add_to_cart,
        COUNT(DISTINCT CASE WHEN event_type = 'checkout_start' THEN session_id END) as checkout_start,
        COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN session_id END) as purchases
    FROM web_events
    """
    
    result = conn.execute(funnel_query).fetchone()
    visits, views, carts, checkouts, purchases = result
    
    print(f"   Visits: {visits:,}")
    print(f"   Product Views: {views:,}")
    print(f"   Add to Cart: {carts:,}")
    print(f"   Checkouts: {checkouts:,}")
    print(f"   Purchases: {purchases:,}")
    
    # Calculate conversion rates
    if visits > 0:
        overall_conversion = (purchases / visits) * 100
        print(f"   Overall Conversion Rate: {overall_conversion:.2f}%")
    
    if checkouts > 0:
        abandonment_rate = ((checkouts - purchases) / checkouts) * 100
        print(f"   Cart Abandonment Rate: {abandonment_rate:.1f}%")

def create_sample_queries():
    """Create a file with sample queries for testing."""
    print("📝 Creating sample queries file...")
    
    sample_queries = """
-- Sample Queries for E-Commerce Funnel Dashboard
-- Use these queries to test your database setup

-- 1. Basic Funnel Metrics
SELECT 
    COUNT(DISTINCT CASE WHEN event_type = 'page_view' THEN session_id END) as visits,
    COUNT(DISTINCT CASE WHEN event_type = 'add_to_cart' THEN session_id END) as add_to_cart,
    COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN session_id END) as purchases,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN session_id END) / 
          COUNT(DISTINCT CASE WHEN event_type = 'page_view' THEN session_id END), 2) as conversion_rate
FROM web_events;

-- 2. Top Products by Revenue
SELECT 
    p.product_name,
    p.category,
    SUM(o.revenue) as total_revenue,
    COUNT(o.order_id) as total_orders
FROM products p
JOIN orders o ON p.product_id = o.product_id
GROUP BY p.product_id, p.product_name, p.category
ORDER BY total_revenue DESC
LIMIT 10;

-- 3. Abandonment Reasons
SELECT 
    abandonment_reason,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 1) as percentage
FROM web_events
WHERE abandonment_reason IS NOT NULL
GROUP BY abandonment_reason
ORDER BY count DESC;

-- 4. Customer Segment Performance
SELECT 
    c.customer_segment,
    COUNT(DISTINCT c.customer_id) as customers,
    COALESCE(AVG(o.revenue), 0) as avg_order_value,
    COALESCE(SUM(o.revenue), 0) as total_revenue
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_segment
ORDER BY total_revenue DESC;

-- 5. Daily Trend Analysis
SELECT 
    DATE(timestamp) as date,
    COUNT(DISTINCT session_id) as sessions,
    COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN session_id END) as conversions,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN session_id END) / 
          COUNT(DISTINCT session_id), 2) as daily_conversion_rate
FROM web_events
WHERE timestamp >= DATE('now', '-30 days')
GROUP BY DATE(timestamp)
ORDER BY date DESC;
"""
    
    with open('sql/sample_queries.sql', 'w') as f:
        f.write(sample_queries)
    
    print("✅ Sample queries saved to sql/sample_queries.sql")

def main():
    """Main execution function."""
    print("🚀 Setting up E-Commerce Funnel Dashboard Database...")
    print("="*50)
    
    try:
        # Check if required files exist
        required_files = [
            'sql/create_tables.sql',
            'data/raw/products.csv',
            'data/raw/customers.csv',
            'data/raw/web_events.csv',
            'data/raw/orders.csv'
        ]
        
        missing_files = [f for f in required_files if not os.path.exists(f)]
        if missing_files:
            print("❌ Missing required files:")
            for f in missing_files:
                print(f"   - {f}")
            print("\nPlease run 'python scripts/generate_sample_data.py' first to create sample data.")
            sys.exit(1)
        
        # Create database and load data
        conn = create_database()
        load_csv_data(conn)
        verify_data_integrity(conn)
        create_sample_queries()
        
        conn.close()
        
        print("\n" + "="*50)
        print("✅ Database setup completed successfully!")
        print("📁 Database file: ecommerce.db")
        print("🎯 Ready to run analysis with: python scripts/funnel_analyzer.py")
        print("💡 Test queries available in: sql/sample_queries.sql")
        
    except Exception as e:
        print(f"❌ Error during database setup: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()