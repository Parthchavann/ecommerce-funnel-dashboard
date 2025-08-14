-- E-Commerce Funnel Dashboard - Database Schema
-- Creates tables for products, customers, web events, and orders

-- Products table
CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY,
    product_name VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    cost DECIMAL(10,2) NOT NULL,
    margin_percent DECIMAL(5,2),
    in_stock BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Customers table
CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY,
    registration_date DATE NOT NULL,
    customer_segment VARCHAR(20) NOT NULL,
    acquisition_channel VARCHAR(50) NOT NULL,
    country VARCHAR(5) DEFAULT 'US',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Web events table for funnel tracking
CREATE TABLE IF NOT EXISTS web_events (
    event_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    session_id VARCHAR(100) NOT NULL,
    abandonment_reason VARCHAR(50),
    device_type VARCHAR(20),
    traffic_source VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    order_date DATE NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price DECIMAL(10,2) NOT NULL,
    shipping_cost DECIMAL(10,2) DEFAULT 0,
    discount_applied DECIMAL(10,2) DEFAULT 0,
    revenue DECIMAL(10,2) NOT NULL,
    profit DECIMAL(10,2),
    order_status VARCHAR(20) DEFAULT 'completed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_web_events_timestamp ON web_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_web_events_event_type ON web_events(event_type);
CREATE INDEX IF NOT EXISTS idx_web_events_session ON web_events(session_id);
CREATE INDEX IF NOT EXISTS idx_web_events_customer ON web_events(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date);
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_customers_segment ON customers(customer_segment);