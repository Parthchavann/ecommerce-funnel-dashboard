#!/usr/bin/env python3
"""
Live E-Commerce Dashboard - Production API Server
Real-time data processing with multiple data source integrations
"""

import asyncio
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import sqlite3
import random
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class LiveMetrics:
    """Real-time metrics structure"""
    timestamp: str
    active_sessions: int
    conversion_rate: float
    cart_abandonment_rate: float
    revenue_today: float
    revenue_this_hour: float
    average_order_value: float
    top_products: List[Dict]
    traffic_sources: Dict[str, int]
    device_breakdown: Dict[str, int]
    geographic_data: Dict[str, int]
    funnel_metrics: Dict[str, int]
    alerts: List[Dict]

class LiveDataConnector:
    """Handles connections to various live data sources"""
    
    def __init__(self):
        self.db_path = "data/live_ecommerce.db"
        self.setup_database()
        
    def setup_database(self):
        """Initialize live database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Real-time events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS live_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id VARCHAR(50),
                user_id VARCHAR(50),
                event_type VARCHAR(30),
                product_id INTEGER,
                value DECIMAL(10,2),
                device_type VARCHAR(20),
                traffic_source VARCHAR(30),
                country VARCHAR(50),
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Live sessions tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS active_sessions (
                session_id VARCHAR(50) PRIMARY KEY,
                user_id VARCHAR(50),
                start_time DATETIME,
                last_activity DATETIME,
                page_views INTEGER DEFAULT 1,
                cart_value DECIMAL(10,2) DEFAULT 0,
                device_type VARCHAR(20),
                traffic_source VARCHAR(30),
                country VARCHAR(50)
            )
        ''')
        
        # Orders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS live_orders (
                order_id VARCHAR(50) PRIMARY KEY,
                user_id VARCHAR(50),
                session_id VARCHAR(50),
                total_amount DECIMAL(10,2),
                items_count INTEGER,
                payment_method VARCHAR(30),
                status VARCHAR(20),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()

    # Shopify API Integration
    def connect_shopify(self, shop_name: str, access_token: str) -> Dict:
        """Connect to Shopify API for live data"""
        try:
            # Simulated Shopify connection (replace with real API calls)
            logger.info(f"Connecting to Shopify store: {shop_name}")
            
            # Mock Shopify data structure
            shopify_data = {
                'orders': self._get_mock_shopify_orders(),
                'products': self._get_mock_shopify_products(),
                'customers': self._get_mock_shopify_customers(),
                'analytics': self._get_mock_shopify_analytics()
            }
            
            return shopify_data
        except Exception as e:
            logger.error(f"Shopify connection failed: {e}")
            return {}

    def connect_google_analytics(self, property_id: str, credentials_path: str) -> Dict:
        """Connect to Google Analytics 4 for real-time data"""
        try:
            logger.info(f"Connecting to GA4 property: {property_id}")
            
            # Mock GA4 real-time data
            ga4_data = {
                'realtime_users': random.randint(50, 200),
                'active_sessions': random.randint(30, 150),
                'page_views': random.randint(100, 500),
                'conversions': random.randint(2, 15),
                'top_pages': [
                    {'page': '/products/laptop', 'views': 45},
                    {'page': '/checkout', 'views': 23},
                    {'page': '/cart', 'views': 67}
                ],
                'traffic_sources': {
                    'organic': 45,
                    'direct': 25,
                    'social': 15,
                    'paid': 15
                }
            }
            
            return ga4_data
        except Exception as e:
            logger.error(f"GA4 connection failed: {e}")
            return {}

    def connect_database(self, connection_string: str) -> Dict:
        """Connect to production database"""
        try:
            logger.info("Connecting to production database")
            
            # Mock database connection
            return self._get_database_metrics()
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return {}

    def _get_mock_shopify_orders(self) -> List[Dict]:
        """Generate mock Shopify orders"""
        orders = []
        for i in range(random.randint(5, 20)):
            orders.append({
                'id': f'order_{i}',
                'total_price': round(random.uniform(25, 500), 2),
                'created_at': (datetime.now() - timedelta(hours=random.randint(0, 24))).isoformat(),
                'financial_status': random.choice(['paid', 'pending', 'refunded']),
                'fulfillment_status': random.choice(['fulfilled', 'partial', 'unfulfilled']),
                'line_items_count': random.randint(1, 5)
            })
        return orders

    def _get_mock_shopify_products(self) -> List[Dict]:
        """Generate mock Shopify products"""
        products = []
        categories = ['Electronics', 'Clothing', 'Home & Garden', 'Sports', 'Books']
        
        for i in range(10):
            products.append({
                'id': f'product_{i}',
                'title': f'Product {i}',
                'vendor': f'Vendor {i % 3}',
                'product_type': random.choice(categories),
                'variants': [{
                    'price': round(random.uniform(20, 300), 2),
                    'inventory_quantity': random.randint(0, 100)
                }]
            })
        return products

    def _get_mock_shopify_customers(self) -> List[Dict]:
        """Generate mock Shopify customers"""
        customers = []
        for i in range(50):
            customers.append({
                'id': f'customer_{i}',
                'email': f'user{i}@example.com',
                'total_spent': round(random.uniform(50, 1000), 2),
                'orders_count': random.randint(1, 10),
                'created_at': (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat()
            })
        return customers

    def _get_mock_shopify_analytics(self) -> Dict:
        """Generate mock Shopify analytics"""
        return {
            'total_sales': round(random.uniform(5000, 25000), 2),
            'total_orders': random.randint(50, 200),
            'conversion_rate': round(random.uniform(2, 8), 2),
            'average_order_value': round(random.uniform(75, 200), 2),
            'returning_customer_rate': round(random.uniform(25, 45), 2)
        }

    def _get_database_metrics(self) -> Dict:
        """Get metrics from production database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get recent metrics
        cursor.execute('''
            SELECT COUNT(DISTINCT session_id) as active_sessions,
                   COUNT(*) as total_events,
                   AVG(CASE WHEN value > 0 THEN value END) as avg_value
            FROM live_events 
            WHERE timestamp > datetime('now', '-1 hour')
        ''')
        
        result = cursor.fetchone()
        conn.close()
        
        return {
            'active_sessions': result[0] if result[0] else 0,
            'total_events': result[1] if result[1] else 0,
            'average_value': round(result[2], 2) if result[2] else 0
        }

class LiveMetricsEngine:
    """Real-time metrics calculation and processing"""
    
    def __init__(self):
        self.connector = LiveDataConnector()
        self.metrics_history = deque(maxlen=1440)  # 24 hours of minute data
        self.alerts_queue = deque(maxlen=100)
        self.is_running = False
        
    def start_processing(self):
        """Start real-time processing"""
        self.is_running = True
        
        # Start background threads
        threading.Thread(target=self._generate_live_events, daemon=True).start()
        threading.Thread(target=self._process_metrics, daemon=True).start()
        threading.Thread(target=self._monitor_alerts, daemon=True).start()
        
        logger.info("Live metrics engine started")

    def stop_processing(self):
        """Stop real-time processing"""
        self.is_running = False
        logger.info("Live metrics engine stopped")

    def _generate_live_events(self):
        """Simulate live events for demo purposes"""
        conn = sqlite3.connect(self.connector.db_path)
        cursor = conn.cursor()
        
        while self.is_running:
            # Generate realistic events
            event_types = ['page_view', 'product_view', 'add_to_cart', 'checkout_start', 'purchase']
            weights = [40, 25, 15, 10, 10]  # Realistic funnel distribution
            
            event_type = random.choices(event_types, weights=weights)[0]
            session_id = f"session_{random.randint(1000, 9999)}"
            
            # Event details
            cursor.execute('''
                INSERT INTO live_events 
                (session_id, user_id, event_type, product_id, value, device_type, traffic_source, country)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_id,
                f"user_{random.randint(1, 1000)}",
                event_type,
                random.randint(1, 100) if event_type in ['product_view', 'add_to_cart', 'purchase'] else None,
                round(random.uniform(25, 300), 2) if event_type == 'purchase' else None,
                random.choice(['desktop', 'mobile', 'tablet']),
                random.choice(['organic', 'direct', 'social', 'email', 'paid']),
                random.choice(['US', 'UK', 'CA', 'AU', 'DE', 'FR'])
            ))
            
            conn.commit()
            
            # Random interval between events (1-10 seconds)
            time.sleep(random.uniform(1, 10))
        
        conn.close()

    def _process_metrics(self):
        """Process and calculate live metrics"""
        while self.is_running:
            try:
                metrics = self.calculate_live_metrics()
                self.metrics_history.append(metrics)
                
                # Check for anomalies and alerts
                self._check_anomalies(metrics)
                
                time.sleep(30)  # Update every 30 seconds
                
            except Exception as e:
                logger.error(f"Metrics processing error: {e}")
                time.sleep(5)

    def calculate_live_metrics(self) -> LiveMetrics:
        """Calculate current live metrics"""
        conn = sqlite3.connect(self.connector.db_path)
        cursor = conn.cursor()
        
        # Get current hour metrics
        cursor.execute('''
            SELECT 
                COUNT(DISTINCT session_id) as active_sessions,
                COUNT(DISTINCT CASE WHEN event_type = 'page_view' THEN session_id END) as visits,
                COUNT(DISTINCT CASE WHEN event_type = 'add_to_cart' THEN session_id END) as carts,
                COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN session_id END) as purchases,
                SUM(CASE WHEN event_type = 'purchase' THEN value ELSE 0 END) as revenue,
                AVG(CASE WHEN event_type = 'purchase' THEN value END) as aov
            FROM live_events 
            WHERE timestamp > datetime('now', '-1 hour')
        ''')
        
        hourly_data = cursor.fetchone()
        
        # Get today's metrics
        cursor.execute('''
            SELECT 
                SUM(CASE WHEN event_type = 'purchase' THEN value ELSE 0 END) as revenue_today,
                COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN session_id END) as purchases_today
            FROM live_events 
            WHERE date(timestamp) = date('now')
        ''')
        
        daily_data = cursor.fetchone()
        
        # Get top products
        cursor.execute('''
            SELECT product_id, COUNT(*) as views
            FROM live_events 
            WHERE event_type = 'product_view' 
            AND timestamp > datetime('now', '-1 hour')
            AND product_id IS NOT NULL
            GROUP BY product_id 
            ORDER BY views DESC 
            LIMIT 5
        ''')
        
        top_products = [{'product_id': row[0], 'views': row[1]} for row in cursor.fetchall()]
        
        # Get traffic sources
        cursor.execute('''
            SELECT traffic_source, COUNT(DISTINCT session_id) as sessions
            FROM live_events 
            WHERE timestamp > datetime('now', '-1 hour')
            GROUP BY traffic_source
        ''')
        
        traffic_sources = dict(cursor.fetchall())
        
        # Get device breakdown
        cursor.execute('''
            SELECT device_type, COUNT(DISTINCT session_id) as sessions
            FROM live_events 
            WHERE timestamp > datetime('now', '-1 hour')
            GROUP BY device_type
        ''')
        
        device_breakdown = dict(cursor.fetchall())
        
        # Get geographic data
        cursor.execute('''
            SELECT country, COUNT(DISTINCT session_id) as sessions
            FROM live_events 
            WHERE timestamp > datetime('now', '-1 hour')
            GROUP BY country
        ''')
        
        geographic_data = dict(cursor.fetchall())
        
        conn.close()
        
        # Calculate metrics
        visits = hourly_data[1] or 0
        carts = hourly_data[2] or 0
        purchases = hourly_data[3] or 0
        revenue_hour = hourly_data[4] or 0
        aov = hourly_data[5] or 0
        revenue_today = daily_data[0] or 0
        
        conversion_rate = (purchases / visits * 100) if visits > 0 else 0
        cart_abandonment = ((carts - purchases) / carts * 100) if carts > 0 else 0
        
        # Create metrics object
        metrics = LiveMetrics(
            timestamp=datetime.now().isoformat(),
            active_sessions=hourly_data[0] or 0,
            conversion_rate=round(conversion_rate, 2),
            cart_abandonment_rate=round(cart_abandonment, 2),
            revenue_today=round(revenue_today, 2),
            revenue_this_hour=round(revenue_hour, 2),
            average_order_value=round(aov, 2),
            top_products=top_products,
            traffic_sources=traffic_sources,
            device_breakdown=device_breakdown,
            geographic_data=geographic_data,
            funnel_metrics={
                'visits': visits,
                'carts': carts,
                'purchases': purchases
            },
            alerts=list(self.alerts_queue)
        )
        
        return metrics

    def _check_anomalies(self, current_metrics: LiveMetrics):
        """Check for anomalies and generate alerts"""
        if len(self.metrics_history) < 10:
            return
        
        # Calculate recent averages
        recent_conversion = [m.conversion_rate for m in list(self.metrics_history)[-10:]]
        avg_conversion = sum(recent_conversion) / len(recent_conversion)
        
        # Check for significant drops
        if current_metrics.conversion_rate < avg_conversion * 0.7:  # 30% drop
            alert = {
                'type': 'conversion_drop',
                'severity': 'high',
                'message': f'Conversion rate dropped to {current_metrics.conversion_rate}% (avg: {avg_conversion:.1f}%)',
                'timestamp': current_metrics.timestamp,
                'action': 'Check checkout process and payment systems'
            }
            self.alerts_queue.append(alert)
            logger.warning(f"ALERT: {alert['message']}")

        # Check for high cart abandonment
        if current_metrics.cart_abandonment_rate > 85:
            alert = {
                'type': 'high_abandonment',
                'severity': 'medium',
                'message': f'Cart abandonment at {current_metrics.cart_abandonment_rate}%',
                'timestamp': current_metrics.timestamp,
                'action': 'Activate cart recovery campaigns'
            }
            self.alerts_queue.append(alert)

    def _monitor_alerts(self):
        """Monitor system health and generate alerts"""
        while self.is_running:
            try:
                # Check system health
                if len(self.metrics_history) > 0:
                    latest = self.metrics_history[-1]
                    
                    # Check if no recent activity
                    if latest.active_sessions == 0:
                        alert = {
                            'type': 'no_activity',
                            'severity': 'medium',
                            'message': 'No active sessions detected',
                            'timestamp': datetime.now().isoformat(),
                            'action': 'Check tracking implementation'
                        }
                        self.alerts_queue.append(alert)
                
                time.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Alert monitoring error: {e}")
                time.sleep(60)

    def get_current_metrics(self) -> Dict:
        """Get current metrics as dictionary"""
        if not self.metrics_history:
            # Return empty metrics if no data
            return asdict(LiveMetrics(
                timestamp=datetime.now().isoformat(),
                active_sessions=0,
                conversion_rate=0.0,
                cart_abandonment_rate=0.0,
                revenue_today=0.0,
                revenue_this_hour=0.0,
                average_order_value=0.0,
                top_products=[],
                traffic_sources={},
                device_breakdown={},
                geographic_data={},
                funnel_metrics={'visits': 0, 'carts': 0, 'purchases': 0},
                alerts=[]
            ))
        
        return asdict(self.metrics_history[-1])

    def get_historical_data(self, hours: int = 24) -> List[Dict]:
        """Get historical metrics data"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        historical = [
            asdict(metric) for metric in self.metrics_history
            if datetime.fromisoformat(metric.timestamp) > cutoff_time
        ]
        
        return historical

# Global metrics engine instance
metrics_engine = LiveMetricsEngine()

def start_live_backend():
    """Start the live backend system"""
    logger.info("Starting Live E-Commerce Backend...")
    metrics_engine.start_processing()
    return metrics_engine

def stop_live_backend():
    """Stop the live backend system"""
    logger.info("Stopping Live E-Commerce Backend...")
    metrics_engine.stop_processing()

if __name__ == "__main__":
    # Start the backend
    engine = start_live_backend()
    
    try:
        # Keep running
        while True:
            current_metrics = engine.get_current_metrics()
            print(f"\n🔴 LIVE METRICS - {current_metrics['timestamp']}")
            print(f"Active Sessions: {current_metrics['active_sessions']}")
            print(f"Conversion Rate: {current_metrics['conversion_rate']}%")
            print(f"Revenue Today: ${current_metrics['revenue_today']}")
            print(f"Alerts: {len(current_metrics['alerts'])}")
            
            time.sleep(30)
            
    except KeyboardInterrupt:
        stop_live_backend()
        print("\nLive backend stopped.")