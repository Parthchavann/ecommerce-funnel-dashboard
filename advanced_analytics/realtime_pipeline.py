#!/usr/bin/env python3
"""
Real-Time Data Pipeline Simulation for E-Commerce Analytics
Enterprise-Grade Streaming Analytics with Event Processing
"""

import json
import time
import threading
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from collections import deque
import queue

class RealTimeEventGenerator:
    """Simulates real-time e-commerce events"""
    
    def __init__(self):
        self.customers = list(range(1, 10001))
        self.products = list(range(1, 501))
        self.channels = ['organic', 'paid_search', 'social', 'email', 'direct']
        self.devices = ['desktop', 'mobile', 'tablet']
        self.countries = ['US', 'UK', 'CA', 'AU', 'DE', 'FR', 'ES', 'IT']
        
    def generate_event(self):
        """Generate a single realistic e-commerce event"""
        event_types = ['page_view', 'product_view', 'add_to_cart', 'checkout_start', 'purchase']
        weights = [0.45, 0.25, 0.15, 0.10, 0.05]  # Realistic funnel distribution
        
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_id': f"evt_{int(time.time() * 1000000)}",
            'customer_id': np.random.choice(self.customers),
            'session_id': f"sess_{np.random.randint(1000000, 9999999)}",
            'event_type': np.random.choice(event_types, p=weights),
            'product_id': np.random.choice(self.products),
            'channel': np.random.choice(self.channels, p=[0.35, 0.25, 0.15, 0.15, 0.1]),
            'device_type': np.random.choice(self.devices, p=[0.45, 0.45, 0.1]),
            'country': np.random.choice(self.countries, p=[0.4, 0.15, 0.12, 0.08, 0.08, 0.06, 0.06, 0.05]),
            'page_url': f"/product/{np.random.choice(self.products)}",
            'referrer': np.random.choice(['google.com', 'facebook.com', 'direct', 'email_campaign']),
            'user_agent': np.random.choice(['Chrome', 'Safari', 'Firefox', 'Edge']),
            'ip_address': f"{np.random.randint(1,255)}.{np.random.randint(1,255)}.{np.random.randint(1,255)}.{np.random.randint(1,255)}",
            'revenue': np.random.lognormal(4.2, 0.6) if np.random.random() < 0.05 else None,
            'currency': 'USD'
        }
        
        # Add event-specific attributes
        if event['event_type'] == 'checkout_start':
            event['cart_value'] = np.random.lognormal(4.5, 0.5)
            event['items_in_cart'] = np.random.poisson(2.3) + 1
            
        elif event['event_type'] == 'purchase':
            event['order_id'] = f"ord_{np.random.randint(100000, 999999)}"
            event['revenue'] = np.random.lognormal(4.3, 0.7)
            event['profit_margin'] = np.random.uniform(0.15, 0.35)
            
        return event

class StreamProcessor:
    """Real-time stream processing engine"""
    
    def __init__(self, window_size=60):
        self.window_size = window_size  # seconds
        self.event_buffer = deque()
        self.metrics_history = deque(maxlen=1440)  # 24 hours of minute data
        self.anomaly_threshold = 2.0  # Standard deviations
        self.alerts_queue = queue.Queue()
        
    def process_event(self, event):
        """Process incoming event and update real-time metrics"""
        current_time = datetime.now()
        
        # Add to buffer
        self.event_buffer.append((current_time, event))
        
        # Clean old events from buffer
        while self.event_buffer and (current_time - self.event_buffer[0][0]).seconds > self.window_size:
            self.event_buffer.popleft()
        
        # Calculate real-time metrics
        metrics = self._calculate_realtime_metrics()
        
        # Detect anomalies
        anomalies = self._detect_anomalies(metrics)
        
        # Generate alerts if needed
        if anomalies:
            for anomaly in anomalies:
                self.alerts_queue.put(anomaly)
        
        return metrics
    
    def _calculate_realtime_metrics(self):
        """Calculate real-time performance metrics"""
        if not self.event_buffer:
            return {}
            
        events = [event for _, event in self.event_buffer]
        
        # Basic counts
        total_events = len(events)
        unique_sessions = len(set(e['session_id'] for e in events))
        unique_customers = len(set(e['customer_id'] for e in events))
        
        # Event type breakdown
        event_types = {}
        for event in events:
            event_type = event['event_type']
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        # Conversion metrics
        purchases = event_types.get('purchase', 0)
        page_views = event_types.get('page_view', 0)
        cart_adds = event_types.get('add_to_cart', 0)
        checkouts = event_types.get('checkout_start', 0)
        
        conversion_rate = (purchases / unique_sessions * 100) if unique_sessions > 0 else 0
        cart_conversion = (purchases / cart_adds * 100) if cart_adds > 0 else 0
        checkout_conversion = (purchases / checkouts * 100) if checkouts > 0 else 0
        
        # Revenue metrics
        revenue_events = [e for e in events if e.get('revenue')]
        total_revenue = sum(e['revenue'] for e in revenue_events)
        avg_order_value = total_revenue / len(revenue_events) if revenue_events else 0
        
        # Device and channel breakdown
        devices = {}
        channels = {}
        for event in events:
            device = event['device_type']
            channel = event['channel']
            devices[device] = devices.get(device, 0) + 1
            channels[channel] = channels.get(channel, 0) + 1
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'window_seconds': self.window_size,
            'total_events': total_events,
            'unique_sessions': unique_sessions,
            'unique_customers': unique_customers,
            'events_per_second': total_events / self.window_size,
            'conversion_rate': round(conversion_rate, 3),
            'cart_conversion_rate': round(cart_conversion, 3),
            'checkout_conversion_rate': round(checkout_conversion, 3),
            'total_revenue': round(total_revenue, 2),
            'avg_order_value': round(avg_order_value, 2),
            'event_breakdown': event_types,
            'device_breakdown': devices,
            'channel_breakdown': channels,
            'revenue_per_second': round(total_revenue / self.window_size, 2)
        }
        
        # Store for historical analysis
        self.metrics_history.append(metrics)
        
        return metrics
    
    def _detect_anomalies(self, current_metrics):
        """Detect anomalies in real-time metrics"""
        anomalies = []
        
        if len(self.metrics_history) < 30:  # Need historical data
            return anomalies
        
        # Get recent historical data for comparison
        recent_history = list(self.metrics_history)[-30:]  # Last 30 minutes
        
        # Key metrics to monitor for anomalies
        metrics_to_monitor = [
            'conversion_rate', 'events_per_second', 'avg_order_value', 'revenue_per_second'
        ]
        
        for metric in metrics_to_monitor:
            current_value = current_metrics.get(metric, 0)
            historical_values = [m.get(metric, 0) for m in recent_history]
            
            if len(historical_values) > 5:
                mean_val = np.mean(historical_values)
                std_val = np.std(historical_values)
                
                if std_val > 0:
                    z_score = abs(current_value - mean_val) / std_val
                    
                    if z_score > self.anomaly_threshold:
                        anomalies.append({
                            'metric': metric,
                            'current_value': current_value,
                            'expected_range': (mean_val - 2*std_val, mean_val + 2*std_val),
                            'z_score': z_score,
                            'severity': 'high' if z_score > 3 else 'medium',
                            'timestamp': datetime.now().isoformat()
                        })
        
        return anomalies

class RealTimeDashboard:
    """Real-time dashboard data provider"""
    
    def __init__(self):
        self.event_generator = RealTimeEventGenerator()
        self.stream_processor = StreamProcessor()
        self.is_running = False
        self.current_metrics = {}
        
    def start_streaming(self, events_per_second=5):
        """Start the real-time data stream"""
        self.is_running = True
        
        def generate_events():
            while self.is_running:
                try:
                    # Generate event
                    event = self.event_generator.generate_event()
                    
                    # Process event
                    metrics = self.stream_processor.process_event(event)
                    self.current_metrics = metrics
                    
                    # Wait for next event
                    time.sleep(1 / events_per_second)
                    
                except Exception as e:
                    print(f"Error in event generation: {e}")
                    time.sleep(1)
        
        # Start background thread
        self.event_thread = threading.Thread(target=generate_events)
        self.event_thread.daemon = True
        self.event_thread.start()
        
        print(f"🔥 Real-time streaming started: {events_per_second} events/second")
    
    def stop_streaming(self):
        """Stop the real-time data stream"""
        self.is_running = False
        print("🛑 Real-time streaming stopped")
    
    def get_current_metrics(self):
        """Get current real-time metrics"""
        return self.current_metrics.copy() if self.current_metrics else {}
    
    def get_alerts(self):
        """Get pending alerts"""
        alerts = []
        while not self.stream_processor.alerts_queue.empty():
            try:
                alerts.append(self.stream_processor.alerts_queue.get_nowait())
            except queue.Empty:
                break
        return alerts
    
    def get_metrics_history(self, minutes=60):
        """Get historical metrics"""
        history = list(self.stream_processor.metrics_history)
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        filtered_history = [
            m for m in history 
            if datetime.fromisoformat(m['timestamp']) > cutoff_time
        ]
        
        return filtered_history

class RealTimeMLScoring:
    """Real-time ML model scoring"""
    
    def __init__(self):
        self.model_cache = {}
        self.prediction_history = deque(maxlen=10000)
        
    def score_cart_abandonment_risk(self, customer_id, session_data):
        """Real-time cart abandonment risk scoring"""
        # Simulate feature extraction from session
        features = {
            'session_duration': session_data.get('duration', 300),
            'pages_viewed': session_data.get('page_views', 3),
            'items_in_cart': session_data.get('cart_items', 1),
            'device_mobile': 1 if session_data.get('device') == 'mobile' else 0,
            'returning_customer': 1 if session_data.get('returning', False) else 0,
            'high_value_items': 1 if session_data.get('cart_value', 0) > 200 else 0
        }
        
        # Simulate ML model scoring
        risk_score = np.random.beta(2, 6)  # Most customers have low risk
        
        # Adjust based on features
        if features['device_mobile']:
            risk_score += 0.1
        if features['items_in_cart'] > 3:
            risk_score += 0.05
        if not features['returning_customer']:
            risk_score += 0.15
            
        risk_score = min(risk_score, 1.0)
        
        prediction = {
            'customer_id': customer_id,
            'timestamp': datetime.now().isoformat(),
            'abandonment_risk': round(risk_score, 4),
            'risk_category': 'high' if risk_score > 0.7 else 'medium' if risk_score > 0.4 else 'low',
            'recommended_action': self._get_intervention_strategy(risk_score, features)
        }
        
        self.prediction_history.append(prediction)
        return prediction
    
    def _get_intervention_strategy(self, risk_score, features):
        """Get recommended intervention strategy"""
        if risk_score > 0.8:
            return "Immediate discount popup + exit intent trigger"
        elif risk_score > 0.6:
            return "Free shipping offer + urgency messaging"
        elif risk_score > 0.4:
            return "Product recommendations + social proof"
        else:
            return "Continue normal flow"

def simulate_realtime_analytics():
    """Demonstrate real-time analytics capabilities"""
    print("🚀 Starting Real-Time E-Commerce Analytics Simulation")
    print("="*60)
    
    # Initialize components
    dashboard = RealTimeDashboard()
    ml_scorer = RealTimeMLScoring()
    
    # Start real-time streaming
    dashboard.start_streaming(events_per_second=8)
    
    # Collect data for demonstration
    print("📊 Collecting real-time metrics...")
    
    try:
        for i in range(30):  # Run for 30 seconds
            time.sleep(1)
            
            # Get current metrics
            metrics = dashboard.get_current_metrics()
            alerts = dashboard.get_alerts()
            
            # Print status every 5 seconds
            if i % 5 == 0 and metrics:
                print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')}")
                print(f"   Events/sec: {metrics.get('events_per_second', 0):.1f}")
                print(f"   Conversion: {metrics.get('conversion_rate', 0):.2f}%")
                print(f"   Revenue/sec: ${metrics.get('revenue_per_second', 0):.2f}")
                print(f"   Active Sessions: {metrics.get('unique_sessions', 0)}")
                
                if alerts:
                    print(f"   🚨 Alerts: {len(alerts)}")
            
            # Simulate ML scoring for random sessions
            if np.random.random() < 0.3:  # 30% chance
                customer_id = np.random.randint(1, 1001)
                session_data = {
                    'duration': np.random.exponential(400),
                    'page_views': np.random.poisson(4),
                    'cart_items': np.random.poisson(2) + 1,
                    'device': np.random.choice(['desktop', 'mobile'], p=[0.5, 0.5]),
                    'returning': np.random.random() < 0.3,
                    'cart_value': np.random.lognormal(4.5, 0.5)
                }
                
                prediction = ml_scorer.score_cart_abandonment_risk(customer_id, session_data)
                
                if prediction['abandonment_risk'] > 0.8:
                    print(f"   🎯 High risk customer {customer_id}: {prediction['abandonment_risk']:.3f}")
    
    except KeyboardInterrupt:
        print("\n⏸️  Simulation interrupted by user")
    
    finally:
        dashboard.stop_streaming()
        
        # Generate final report
        print("\n" + "="*60)
        print("📈 REAL-TIME ANALYTICS SUMMARY")
        print("="*60)
        
        final_metrics = dashboard.get_current_metrics()
        if final_metrics:
            print(f"Total Events Processed: {final_metrics.get('total_events', 0):,}")
            print(f"Average Conversion Rate: {final_metrics.get('conversion_rate', 0):.3f}%")
            print(f"Total Revenue Generated: ${final_metrics.get('total_revenue', 0):,.2f}")
            print(f"Peak Events/Second: {final_metrics.get('events_per_second', 0):.1f}")
        
        # ML Predictions Summary
        predictions = list(ml_scorer.prediction_history)
        if predictions:
            high_risk_count = len([p for p in predictions if p['abandonment_risk'] > 0.7])
            print(f"ML Predictions Generated: {len(predictions):,}")
            print(f"High Risk Sessions Identified: {high_risk_count:,}")
            print(f"Average Risk Score: {np.mean([p['abandonment_risk'] for p in predictions]):.3f}")
        
        print("="*60)
        
        # Save results
        results = {
            'simulation_duration': 30,
            'final_metrics': final_metrics,
            'ml_predictions_sample': predictions[-10:] if predictions else [],
            'metrics_history_sample': dashboard.get_metrics_history(minutes=1),
            'total_alerts': len(dashboard.get_alerts())
        }
        
        with open('data/realtime_simulation_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print("💾 Results saved to: data/realtime_simulation_results.json")
        
        return results

if __name__ == "__main__":
    simulate_realtime_analytics()