#!/usr/bin/env python
"""
Health Check Script
Test database connectivity and basic setup
"""

import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_database():
    """Check database connectivity"""
    try:
        from app.database import engine
        with engine.connect() as conn:
            logger.info("✓ Database connection successful")
            return True
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        return False

def check_models():
    """Check if models can be imported"""
    try:
        from app.models import (
            Application, Tenant, Identity, 
            ConnectorTemplate, TenantConnector, MigrationTracker
        )
        logger.info("✓ Models imported successfully")
        return True
    except Exception as e:
        logger.error(f"✗ Model import failed: {e}")
        return False

def check_seeders():
    """Check if seeders are registered"""
    try:
        from app.seeders import SEEDERS
        count = len(SEEDERS)
        logger.info(f"✓ {count} seeders registered")
        return True
    except Exception as e:
        logger.error(f"✗ Seeder check failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("Running health checks...")
    
    checks = [
        ("Database", check_database),
        ("Models", check_models),
        ("Seeders", check_seeders),
    ]
    
    results = []
    for name, check_func in checks:
        logger.info(f"\nChecking {name}...")
        results.append(check_func())
    
    if all(results):
        logger.info("\n✓ All health checks passed")
        sys.exit(0)
    else:
        logger.error("\n✗ Some health checks failed")
        sys.exit(1)
