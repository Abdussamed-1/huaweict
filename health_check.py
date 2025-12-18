"""
Health Check Endpoint for ELB
Runs on a separate port (8080) for load balancer health checks
"""
from flask import Flask, jsonify
from datetime import datetime
import logging

app = Flask(__name__)
logger = logging.getLogger(__name__)

@app.route('/health')
def health_check():
    """Health check endpoint for ELB."""
    try:
        # Basic health check
        return jsonify({
            "status": "healthy",
            "service": "huaweict-health-assistant",
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 503

@app.route('/')
def root():
    """Root endpoint."""
    return jsonify({
        "service": "huaweict-health-assistant",
        "status": "running"
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)

