#!/usr/bin/env python3
"""
Live Dashboard Web Server with WebSocket Support
Production-ready server for real-time e-commerce analytics
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Set
import threading
import time
from pathlib import Path

# Simple HTTP server implementation
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs
import socket
import struct
import hashlib
import base64

from api_server import start_live_backend, metrics_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSocketHandler:
    """WebSocket handler for real-time updates"""
    
    def __init__(self):
        self.clients: Set[socket.socket] = set()
        self.is_running = False
        
    def add_client(self, client_socket: socket.socket):
        """Add a WebSocket client"""
        self.clients.add(client_socket)
        logger.info(f"WebSocket client connected. Total clients: {len(self.clients)}")
        
    def remove_client(self, client_socket: socket.socket):
        """Remove a WebSocket client"""
        if client_socket in self.clients:
            self.clients.remove(client_socket)
            logger.info(f"WebSocket client disconnected. Total clients: {len(self.clients)}")
    
    def broadcast_metrics(self, data: dict):
        """Broadcast metrics to all connected clients"""
        if not self.clients:
            return
            
        message = json.dumps(data)
        
        # Remove disconnected clients
        disconnected = set()
        
        for client in self.clients.copy():
            try:
                self._send_websocket_message(client, message)
            except Exception as e:
                logger.warning(f"Failed to send to client: {e}")
                disconnected.add(client)
        
        # Clean up disconnected clients
        for client in disconnected:
            self.remove_client(client)
    
    def _send_websocket_message(self, client_socket: socket.socket, message: str):
        """Send WebSocket message to client"""
        message_bytes = message.encode('utf-8')
        message_length = len(message_bytes)
        
        if message_length <= 125:
            header = struct.pack('!BB', 0x81, message_length)
        elif message_length <= 65535:
            header = struct.pack('!BBH', 0x81, 126, message_length)
        else:
            header = struct.pack('!BBQ', 0x81, 127, message_length)
        
        client_socket.send(header + message_bytes)

class LiveDashboardHTTPHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler for serving dashboard and API endpoints"""
    
    websocket_handler = WebSocketHandler()
    
    def __init__(self, *args, **kwargs):
        # Set the directory to serve files from
        super().__init__(*args, directory=str(Path(__file__).parent.parent), **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/live-metrics':
            self._handle_api_metrics()
        elif parsed_path.path == '/api/historical-data':
            self._handle_api_historical()
        elif parsed_path.path == '/websocket':
            self._handle_websocket_upgrade()
        else:
            # Serve static files
            super().do_GET()
    
    def _handle_api_metrics(self):
        """Handle live metrics API endpoint"""
        try:
            metrics = metrics_engine.get_current_metrics()
            
            # Add CORS headers
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            
            # Send metrics
            self.wfile.write(json.dumps(metrics).encode('utf-8'))
            
        except Exception as e:
            logger.error(f"API metrics error: {e}")
            self.send_error(500, f"Internal server error: {e}")
    
    def _handle_api_historical(self):
        """Handle historical data API endpoint"""
        try:
            # Get query parameters
            query_params = parse_qs(urlparse(self.path).query)
            hours = int(query_params.get('hours', [24])[0])
            
            historical_data = metrics_engine.get_historical_data(hours)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            self.wfile.write(json.dumps(historical_data).encode('utf-8'))
            
        except Exception as e:
            logger.error(f"API historical error: {e}")
            self.send_error(500, f"Internal server error: {e}")
    
    def _handle_websocket_upgrade(self):
        """Handle WebSocket upgrade request"""
        try:
            # Get WebSocket key
            websocket_key = self.headers.get('Sec-WebSocket-Key')
            if not websocket_key:
                self.send_error(400, "Missing WebSocket key")
                return
            
            # Generate accept key
            accept_key = self._generate_websocket_accept_key(websocket_key)
            
            # Send upgrade response
            self.send_response(101, 'Switching Protocols')
            self.send_header('Upgrade', 'websocket')
            self.send_header('Connection', 'Upgrade')
            self.send_header('Sec-WebSocket-Accept', accept_key)
            self.end_headers()
            
            # Add client to WebSocket handler
            self.websocket_handler.add_client(self.connection)
            
            # Keep connection alive
            self._handle_websocket_connection()
            
        except Exception as e:
            logger.error(f"WebSocket upgrade error: {e}")
            self.send_error(500, f"WebSocket upgrade failed: {e}")
    
    def _generate_websocket_accept_key(self, key: str) -> str:
        """Generate WebSocket accept key"""
        websocket_magic = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
        combined = key + websocket_magic
        sha1_hash = hashlib.sha1(combined.encode()).digest()
        return base64.b64encode(sha1_hash).decode()
    
    def _handle_websocket_connection(self):
        """Handle WebSocket connection"""
        try:
            while True:
                # Simple keep-alive (in production, handle incoming messages)
                time.sleep(1)
        except Exception as e:
            logger.info(f"WebSocket connection closed: {e}")
        finally:
            self.websocket_handler.remove_client(self.connection)

class LiveDashboardServer:
    """Production-ready live dashboard server"""
    
    def __init__(self, host: str = 'localhost', port: int = 8080):
        self.host = host
        self.port = port
        self.httpd = None
        self.websocket_handler = WebSocketHandler()
        self.is_running = False
        
    def start(self):
        """Start the live dashboard server"""
        try:
            # Start the backend metrics engine
            logger.info("Starting live backend...")
            start_live_backend()
            
            # Start HTTP server
            logger.info(f"Starting HTTP server on {self.host}:{self.port}")
            self.httpd = socketserver.TCPServer((self.host, self.port), LiveDashboardHTTPHandler)
            self.is_running = True
            
            # Start WebSocket broadcast thread
            threading.Thread(target=self._websocket_broadcast_loop, daemon=True).start()
            
            logger.info(f"""
🔴 LIVE DASHBOARD SERVER STARTED!

📊 Dashboard URLs:
   http://{self.host}:{self.port}/dashboard/live_dashboard.html
   http://{self.host}:{self.port}/dashboard/standalone_dashboard.html

🔌 API Endpoints:
   http://{self.host}:{self.port}/api/live-metrics
   http://{self.host}:{self.port}/api/historical-data
   ws://{self.host}:{self.port}/websocket

🚀 Production Features:
   ✅ Real-time metrics processing
   ✅ WebSocket live updates
   ✅ CORS enabled for external access
   ✅ Multiple data source integration ready
   ✅ Automatic anomaly detection
   ✅ Historical data API

Press Ctrl+C to stop the server.
            """)
            
            # Serve forever
            self.httpd.serve_forever()
            
        except KeyboardInterrupt:
            logger.info("Server shutdown requested")
            self.stop()
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise
    
    def stop(self):
        """Stop the server"""
        self.is_running = False
        if self.httpd:
            logger.info("Shutting down server...")
            self.httpd.shutdown()
            self.httpd.server_close()
            logger.info("Server stopped")
    
    def _websocket_broadcast_loop(self):
        """Broadcast live metrics to WebSocket clients"""
        while self.is_running:
            try:
                if LiveDashboardHTTPHandler.websocket_handler.clients:
                    # Get current metrics
                    metrics = metrics_engine.get_current_metrics()
                    
                    # Add timestamp for client sync
                    metrics['server_time'] = datetime.now().isoformat()
                    
                    # Broadcast to all clients
                    LiveDashboardHTTPHandler.websocket_handler.broadcast_metrics(metrics)
                
                time.sleep(5)  # Broadcast every 5 seconds
                
            except Exception as e:
                logger.error(f"WebSocket broadcast error: {e}")
                time.sleep(10)

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Live E-Commerce Dashboard Server')
    parser.add_argument('--host', default='localhost', help='Server host (default: localhost)')
    parser.add_argument('--port', type=int, default=8080, help='Server port (default: 8080)')
    
    args = parser.parse_args()
    
    # Create and start server
    server = LiveDashboardServer(args.host, args.port)
    server.start()

if __name__ == "__main__":
    main()