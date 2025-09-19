"""
Health check and monitoring endpoints for AI Guardian.
"""
import os
import time
import psutil
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

from app.database.database import get_db
from app.security_testing import security_tester

router = APIRouter(tags=["Health & Monitoring"])
logger = logging.getLogger(__name__)

@router.get("/health")
async def health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Basic health check endpoint.
    Returns system status and basic metrics.
    """
    start_time = time.time()
    
    try:
        # Check database connectivity
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    # Basic system metrics
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        system_metrics = {
            "memory_usage_percent": memory.percent,
            "memory_available_gb": round(memory.available / (1024**3), 2),
            "disk_usage_percent": disk.percent,
            "disk_free_gb": round(disk.free / (1024**3), 2),
            "cpu_usage_percent": cpu_percent
        }
    except Exception as e:
        logger.warning(f"Failed to get system metrics: {e}")
        system_metrics = {"error": "metrics_unavailable"}
    
    response_time = round((time.time() - start_time) * 1000, 2)
    
    status = "healthy" if db_status == "healthy" else "unhealthy"
    
    return {
        "status": status,
        "timestamp": time.time(),
        "response_time_ms": response_time,
        "database": db_status,
        "system_metrics": system_metrics,
        "environment": os.getenv("ENVIRONMENT", "unknown"),
        "version": "1.0.0"
    }

@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Detailed health check with additional service checks.
    """
    start_time = time.time()
    checks = {}
    
    # Database check with more details
    try:
        db.execute(text("SELECT 1"))
        # Test table access
        db.execute(text("SELECT COUNT(*) FROM pii_mappings"))
        checks["database"] = {"status": "healthy", "message": "All database operations successful"}
    except Exception as e:
        logger.error(f"Database detailed check failed: {e}")
        checks["database"] = {"status": "unhealthy", "message": str(e)}
    
    # Environment variables check
    required_env_vars = [
        "DATABASE_URL", "SECRET_KEY", "SUPABASE_URL", "SUPABASE_ANON_KEY"
    ]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        checks["environment"] = {
            "status": "unhealthy", 
            "message": f"Missing environment variables: {', '.join(missing_vars)}"
        }
    else:
        checks["environment"] = {"status": "healthy", "message": "All required environment variables present"}
    
    # File system checks
    try:
        # Check if we can write to temp directory
        import tempfile
        with tempfile.NamedTemporaryFile(delete=True) as tmp:
            tmp.write(b"health check")
        checks["filesystem"] = {"status": "healthy", "message": "File system read/write successful"}
    except Exception as e:
        checks["filesystem"] = {"status": "unhealthy", "message": f"File system error: {str(e)}"}
    
    # Memory and resource checks
    try:
        memory = psutil.virtual_memory()
        if memory.percent > 90:
            checks["memory"] = {"status": "warning", "message": f"High memory usage: {memory.percent}%"}
        elif memory.percent > 95:
            checks["memory"] = {"status": "unhealthy", "message": f"Critical memory usage: {memory.percent}%"}
        else:
            checks["memory"] = {"status": "healthy", "message": f"Memory usage normal: {memory.percent}%"}
    except Exception as e:
        checks["memory"] = {"status": "error", "message": f"Cannot check memory: {str(e)}"}
    
    overall_status = "healthy"
    if any(check["status"] == "unhealthy" for check in checks.values()):
        overall_status = "unhealthy"
    elif any(check["status"] == "warning" for check in checks.values()):
        overall_status = "warning"
    
    response_time = round((time.time() - start_time) * 1000, 2)
    
    return {
        "status": overall_status,
        "timestamp": time.time(),
        "response_time_ms": response_time,
        "checks": checks,
        "environment": os.getenv("ENVIRONMENT", "unknown"),
        "version": "1.0.0"
    }

@router.get("/security/scan")
async def security_scan() -> Dict[str, Any]:
    """
    Run security scan and return results.
    Only available in development environment for safety.
    """
    if os.getenv("ENVIRONMENT") == "production":
        raise HTTPException(
            status_code=403, 
            detail="Security scanning not available in production environment"
        )
    
    logger.info("Starting security scan via API endpoint")
    
    try:
        results = security_tester.run_all_security_checks()
        return results
    except Exception as e:
        logger.error(f"Security scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"Security scan failed: {str(e)}")

@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """
    Get application metrics for monitoring.
    """
    try:
        # System metrics
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Process metrics
        process = psutil.Process()
        process_memory = process.memory_info()
        
        metrics = {
            "system": {
                "memory_total_gb": round(memory.total / (1024**3), 2),
                "memory_used_gb": round(memory.used / (1024**3), 2),
                "memory_percent": memory.percent,
                "disk_total_gb": round(disk.total / (1024**3), 2),
                "disk_used_gb": round(disk.used / (1024**3), 2),
                "disk_percent": disk.percent,
                "cpu_percent": cpu_percent,
                "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None
            },
            "process": {
                "memory_rss_mb": round(process_memory.rss / (1024**2), 2),
                "memory_vms_mb": round(process_memory.vms / (1024**2), 2),
                "cpu_percent": process.cpu_percent(),
                "num_threads": process.num_threads(),
                "num_fds": process.num_fds() if hasattr(process, 'num_fds') else None,
                "create_time": process.create_time()
            },
            "timestamp": time.time()
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")