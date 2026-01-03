"""
Health Check Endpoint for ELB
Runs on a separate port (8080) for load balancer health checks.
Includes dependency checks for Milvus.
"""
from flask import Flask, jsonify
from datetime import datetime
import logging
import os

# Import configuration
try:
    from config import (
        MILVUS_HOST, MILVUS_PORT, MILVUS_USE_CLOUD,
        HEALTH_CHECK_PORT
    )
except ImportError:
    # Fallback if config import fails
    MILVUS_HOST = os.getenv("MILVUS_HOST", "")
    MILVUS_PORT = int(os.getenv("MILVUS_PORT", "443"))
    MILVUS_USE_CLOUD = os.getenv("MILVUS_USE_CLOUD", "true").lower() == "true"
    HEALTH_CHECK_PORT = int(os.getenv("HEALTH_CHECK_PORT", "8080"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def check_milvus():
    """Check Milvus connection."""
    if not MILVUS_USE_CLOUD or not MILVUS_HOST:
        return {"status": "skipped", "reason": "Milvus not configured"}
    
    try:
        from pymilvus import connections, utility
        # Try to connect (quick check)
        connections.connect(
            alias="health_check",
            host=MILVUS_HOST,
            port=MILVUS_PORT,
            timeout=2
        )
        connections.disconnect("health_check")
        return {"status": "healthy"}
    except Exception as e:
        logger.warning(f"Milvus health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}

@app.route('/health')
def health_check():
    """Comprehensive health check endpoint for ELB."""
    try:
        health_status = {
            "status": "healthy",
            "service": "huaweict-health-assistant",
            "timestamp": datetime.now().isoformat(),
            "checks": {
                "application": {"status": "healthy"},
                "milvus": check_milvus()
            }
        }
        
        # Determine overall status
        all_healthy = all(
            check.get("status") in ("healthy", "skipped")
            for check in health_status["checks"].values()
        )
        
        status_code = 200 if all_healthy else 503
        health_status["status"] = "healthy" if all_healthy else "degraded"
        
        return jsonify(health_status), status_code
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 503

@app.route('/health/liveness')
def liveness():
    """Liveness probe - simple check that app is running."""
    return jsonify({
        "status": "alive",
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/health/readiness')
def readiness():
    """Readiness probe - check if app is ready to serve traffic."""
    return health_check()

@app.route('/')
def root():
    """Root endpoint."""
    return jsonify({
        "service": "huaweict-health-assistant",
        "status": "running",
        "version": "1.0.0"
    }), 200

if __name__ == '__main__':
    port = HEALTH_CHECK_PORT
    logger.info(f"Starting health check server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

