#!/usr/bin/env python3
"""
E-Commerce Funnel Dashboard - Sample Data Generator
Generates realistic e-commerce data for funnel analysis and dashboard creation.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

def create_data_directories():
    """Create necessary data directories if they don't exist."""
    os.makedirs('data/raw', exist_ok=True)
    os.makedirs('data/processed', exist_ok=True)

def generate_products(n_products=500):
    """Generate sample product data with realistic pricing and categories."""
    np.random.seed(42)
    
    categories = ['Electronics', 'Clothing', 'Home & Garden', 'Sports', 'Books', 'Beauty', 'Automotive']
    brand_prefixes = ['Pro', 'Ultra', 'Premium', 'Essential', 'Classic', 'Modern', 'Smart']
    
    products = []
    for i in range(1, n_products + 1):
        category = np.random.choice(categories)
        brand = np.random.choice(brand_prefixes)
        
        # Category-based pricing
        if category == 'Electronics':
            price_range = (50, 1000)
            cost_margin = 0.6  # 40% margin
        elif category == 'Clothing':
            price_range = (15, 200)
            cost_margin = 0.4  # 60% margin
        elif category == 'Home & Garden':
            price_range = (20, 300)
            cost_margin = 0.5  # 50% margin
        else:
            price_range = (10, 150)
            cost_margin = 0.45  # 55% margin
        
        price = round(np.random.uniform(*price_range), 2)
        cost = round(price * cost_margin, 2)
        
        products.append({
            'product_id': i,
            'product_name': f'{brand} {category.split()[0]} {i}',
            'category': category,
            'price': price,
            'cost': cost,
            'margin_percent': round((price - cost) / price * 100, 2),
            'in_stock': np.random.choice([True, False], p=[0.9, 0.1])
        })
    
    return pd.DataFrame(products)

def generate_customers(n_customers=5000):
    """Generate sample customer data with segments and acquisition channels."""
    np.random.seed(42)
    
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2024, 12, 31)
    
    acquisition_channels = ['Organic Search', 'Paid Search', 'Social Media', 'Email Marketing', 'Direct', 'Referral']
    customer_segments = ['New', 'Regular', 'VIP']
    
    customers = []
    for i in range(1, n_customers + 1):
        registration_date = start_date + timedelta(
            days=random.randint(0, (end_date - start_date).days)
        )
        
        # Segment probability based on registration date (older customers more likely to be VIP)
        days_since_reg = (datetime(2024, 12, 31) - registration_date).days
        if days_since_reg > 300:
            segment_probs = [0.3, 0.5, 0.2]  # More likely to be Regular/VIP
        else:
            segment_probs = [0.7, 0.25, 0.05]  # More likely to be New
        
        customers.append({
            'customer_id': i,
            'registration_date': registration_date.date(),
            'customer_segment': np.random.choice(customer_segments, p=segment_probs),
            'acquisition_channel': np.random.choice(acquisition_channels, 
                                                  p=[0.25, 0.2, 0.2, 0.15, 0.1, 0.1]),
            'country': np.random.choice(['US', 'UK', 'CA', 'AU', 'DE'], 
                                      p=[0.5, 0.2, 0.15, 0.1, 0.05])
        })
    
    return pd.DataFrame(customers)

def generate_web_events(customers, products, n_events=150000):
    """Generate realistic web events following a conversion funnel."""
    np.random.seed(42)
    
    event_types = ['page_view', 'product_view', 'add_to_cart', 'checkout_start', 'purchase']
    abandonment_reasons = ['high_shipping', 'payment_failed', 'long_delivery', 'price_concern', 'technical_issue']
    
    events = []
    event_id = 1
    
    # Generate sessions first
    n_sessions = n_events // 8  # Average 8 events per session
    
    for session_num in range(1, n_sessions + 1):
        customer_id = np.random.choice(customers['customer_id'])
        customer_segment = customers[customers['customer_id'] == customer_id]['customer_segment'].iloc[0]
        
        # Session timestamp
        session_date = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 364))
        session_id = f"session_{customer_id}_{session_date.strftime('%Y%m%d_%H%M%S')}"
        
        # Determine session progression based on customer segment
        if customer_segment == 'VIP':
            progression_probs = [1.0, 0.8, 0.5, 0.4, 0.3]  # Higher conversion
        elif customer_segment == 'Regular':
            progression_probs = [1.0, 0.7, 0.35, 0.25, 0.15]  # Medium conversion
        else:  # New
            progression_probs = [1.0, 0.6, 0.25, 0.15, 0.08]  # Lower conversion
        
        # Generate events for this session
        current_timestamp = session_date
        selected_products = np.random.choice(products['product_id'], size=min(5, len(products)), replace=False)
        
        for stage_idx, event_type in enumerate(event_types):
            if random.random() < progression_probs[stage_idx]:
                for product_id in selected_products[:stage_idx+1]:  # Fewer products as we progress
                    # Add some time between events
                    current_timestamp += timedelta(minutes=random.randint(1, 30))
                    
                    # Determine abandonment reason for checkout_start that don't convert
                    abandonment_reason = None
                    if event_type == 'checkout_start' and random.random() > progression_probs[stage_idx + 1] if stage_idx < 4 else 0:
                        abandonment_reason = np.random.choice(abandonment_reasons, 
                                                            p=[0.3, 0.25, 0.15, 0.2, 0.1])
                    
                    events.append({
                        'event_id': event_id,
                        'customer_id': customer_id,
                        'product_id': product_id,
                        'event_type': event_type,
                        'timestamp': current_timestamp,
                        'session_id': session_id,
                        'abandonment_reason': abandonment_reason,
                        'device_type': np.random.choice(['Desktop', 'Mobile', 'Tablet'], p=[0.5, 0.4, 0.1]),
                        'traffic_source': np.random.choice(['organic', 'paid', 'direct', 'social'], p=[0.4, 0.3, 0.2, 0.1])
                    })
                    event_id += 1
                    
                    if len(events) >= n_events:
                        break
                if len(events) >= n_events:
                    break
            else:
                break  # User dropped off at this stage
        
        if len(events) >= n_events:
            break
    
    return pd.DataFrame(events)

def generate_orders(events, products):
    """Generate order data from purchase events."""
    purchase_events = events[events['event_type'] == 'purchase'].copy()
    
    orders = []
    for idx, event in purchase_events.iterrows():
        product = products[products['product_id'] == event['product_id']].iloc[0]
        
        quantity = np.random.choice([1, 2, 3], p=[0.7, 0.25, 0.05])
        
        # Shipping cost based on order value
        base_price = product['price'] * quantity
        if base_price > 75:
            shipping_cost = 0  # Free shipping
        elif base_price > 50:
            shipping_cost = 5.99
        else:
            shipping_cost = round(np.random.uniform(8.99, 19.99), 2)
        
        # Discounts (10% of orders have discounts)
        if random.random() < 0.1:
            discount_percent = np.random.uniform(5, 25)
            discount_applied = round(base_price * discount_percent / 100, 2)
        else:
            discount_applied = 0
        
        revenue = base_price - discount_applied
        profit = revenue - (quantity * product['cost']) - shipping_cost
        
        orders.append({
            'order_id': len(orders) + 1,
            'customer_id': event['customer_id'],
            'product_id': event['product_id'],
            'order_date': event['timestamp'].date(),
            'quantity': quantity,
            'unit_price': product['price'],
            'shipping_cost': shipping_cost,
            'discount_applied': discount_applied,
            'revenue': revenue,
            'profit': profit,
            'order_status': np.random.choice(['completed', 'shipped', 'delivered'], p=[0.1, 0.3, 0.6])
        })
    
    return pd.DataFrame(orders)

def main():
    """Main function to generate all sample data."""
    print("🚀 Generating E-Commerce Sample Data...")
    
    # Create directories
    create_data_directories()
    
    # Generate data
    print("📦 Generating products...")
    products = generate_products(500)
    
    print("👥 Generating customers...")
    customers = generate_customers(5000)
    
    print("🔍 Generating web events...")
    events = generate_web_events(customers, products, 150000)
    
    print("🛒 Generating orders...")
    orders = generate_orders(events, products)
    
    # Save data
    print("💾 Saving data to CSV files...")
    products.to_csv('data/raw/products.csv', index=False)
    customers.to_csv('data/raw/customers.csv', index=False)
    events.to_csv('data/raw/web_events.csv', index=False)
    orders.to_csv('data/raw/orders.csv', index=False)
    
    # Print summary statistics
    print("\n📊 Data Generation Summary:")
    print(f"   Products: {len(products):,}")
    print(f"   Customers: {len(customers):,}")
    print(f"   Web Events: {len(events):,}")
    print(f"   Orders: {len(orders):,}")
    print(f"   Revenue: ${orders['revenue'].sum():,.2f}")
    print(f"   Profit: ${orders['profit'].sum():,.2f}")
    
    # Calculate basic funnel metrics
    print("\n🎯 Basic Funnel Metrics:")
    visits = events[events['event_type'] == 'page_view']['session_id'].nunique()
    carts = events[events['event_type'] == 'add_to_cart']['session_id'].nunique()
    checkouts = events[events['event_type'] == 'checkout_start']['session_id'].nunique()
    purchases = events[events['event_type'] == 'purchase']['session_id'].nunique()
    
    print(f"   Visits: {visits:,}")
    print(f"   Add to Cart: {carts:,} ({carts/visits*100:.1f}% conversion)")
    print(f"   Checkout Start: {checkouts:,} ({checkouts/carts*100:.1f}% from cart)")
    print(f"   Purchases: {purchases:,} ({purchases/checkouts*100:.1f}% from checkout)")
    print(f"   Overall Conversion: {purchases/visits*100:.2f}%")
    print(f"   Cart Abandonment: {(1-purchases/checkouts)*100:.1f}%")
    
    print("\n✅ Sample data generated successfully!")
    print("📁 Files saved in data/raw/ directory")

if __name__ == "__main__":
    main()