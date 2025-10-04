"""Health check HTTP server for Railway monitoring.

This module provides a simple HTTP server for health checks and status monitoring.
"""

import logging
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from typing import Dict, Any, Callable, Optional

logger = logging.getLogger(__name__)


class HealthCheckHandler(BaseHTTPRequestHandler):
    """HTTP request handler for health checks."""

    # Class variable to store health check callback
    health_callback: Optional[Callable[[], Dict[str, Any]]] = None

    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/health' or self.path == '/':
            self._handle_health_check()
        elif self.path == '/status':
            self._handle_status()
        elif self.path == '/metrics':
            self._handle_metrics()
        else:
            self._send_response(404, {'error': 'Not found'})

    def _handle_health_check(self):
        """Handle health check endpoint."""
        health_data = {
            'status': 'healthy',
            'service': 'haystack_simulator'
        }

        if self.health_callback:
            try:
                callback_data = self.health_callback()
                health_data.update(callback_data)
            except Exception as e:
                logger.error(f"Health check callback error: {e}")
                health_data['status'] = 'unhealthy'
                health_data['error'] = str(e)

        status_code = 200 if health_data.get('status') == 'healthy' else 503
        self._send_response(status_code, health_data)

    def _handle_status(self):
        """Handle detailed status endpoint."""
        status_data = {
            'service': 'haystack_simulator',
            'version': '1.0'
        }

        if self.health_callback:
            try:
                callback_data = self.health_callback()
                status_data.update(callback_data)
            except Exception as e:
                logger.error(f"Status callback error: {e}")
                status_data['error'] = str(e)

        self._send_response(200, status_data)

    def _handle_metrics(self):
        """Handle metrics endpoint (basic Prometheus-style)."""
        metrics_text = "# HELP simulator_status Service status (1=running, 0=stopped)\n"
        metrics_text += "# TYPE simulator_status gauge\n"

        if self.health_callback:
            try:
                callback_data = self.health_callback()
                status_value = 1 if callback_data.get('status') == 'running' else 0
                metrics_text += f"simulator_status {status_value}\n"
            except Exception as e:
                logger.error(f"Metrics callback error: {e}")
                metrics_text += "simulator_status 0\n"
        else:
            metrics_text += "simulator_status 0\n"

        self.send_response(200)
        self.send_header('Content-type', 'text/plain; version=0.0.4')
        self.end_headers()
        self.wfile.write(metrics_text.encode())

    def _send_response(self, status_code: int, data: Dict[str, Any]):
        """Send JSON response.

        Args:
            status_code: HTTP status code
            data: Data to send as JSON
        """
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        """Override to use logger instead of stderr."""
        logger.debug(f"{self.address_string()} - {format % args}")


class HealthCheckServer:
    """Manages health check HTTP server in background thread."""

    def __init__(self, port: int = 8080, health_callback: Optional[Callable] = None):
        """Initialize health check server.

        Args:
            port: Port to listen on (default 8080)
            health_callback: Optional callback function for health status
        """
        self.port = port
        self.health_callback = health_callback
        self.server: Optional[HTTPServer] = None
        self.server_thread: Optional[Thread] = None

        # Set class variable for handler
        HealthCheckHandler.health_callback = health_callback

    def start(self):
        """Start the health check server in background thread."""
        try:
            self.server = HTTPServer(('0.0.0.0', self.port), HealthCheckHandler)
            self.server_thread = Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()
            logger.info(f"Health check server started on port {self.port}")
        except Exception as e:
            logger.error(f"Failed to start health check server: {e}")
            raise

    def stop(self):
        """Stop the health check server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            logger.info("Health check server stopped")

        if self.server_thread:
            self.server_thread.join(timeout=5)

    def is_running(self) -> bool:
        """Check if server is running.

        Returns:
            True if running, False otherwise
        """
        return self.server_thread is not None and self.server_thread.is_alive()
