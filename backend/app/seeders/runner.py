"""
Seeder Runner
Centralized entry point for running all seeders
"""

import os
import sys
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import SessionLocal
from app.seeders import SEEDERS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run_all_seeders():
    """
    Run all registered seeders in order.
    
    Respects the following environment variables:
    - RUN_SEEDERS: If "false", skip all seeders (default: "true")
    - SEED_DEMO_DATA: If "true", include demo data seeder (default: "false")
    """
    # Check if seeding is enabled
    if os.environ.get("RUN_SEEDERS", "true").lower() in ("false", "0", "no"):
        logger.info("Seeding disabled (RUN_SEEDERS=false)")
        return
    
    logger.info(f"Running {len(SEEDERS)} seeders...")
    
    db = SessionLocal()
    
    try:
        # Sort seeders by order
        sorted_seeders = sorted(SEEDERS, key=lambda s: s.order)
        
        success_count = 0
        skip_count = 0
        fail_count = 0
        
        for SeederClass in sorted_seeders:
            seeder = SeederClass()
            
            # Check if seeder requires env flag
            if seeder.requires_env_flag:
                env_var = f"SEED_{seeder.name.upper().replace('seed_', '')}"
                if not os.environ.get(env_var, "").lower() in ("true", "1", "yes"):
                    # Also check generic SEED_DEMO_DATA for demo seeders
                    if seeder.name == "seed_demo_data":
                        if not os.environ.get("SEED_DEMO_DATA", "").lower() in ("true", "1", "yes"):
                            skip_count += 1
                            continue
                    else:
                        skip_count += 1
                        continue
            
            if seeder.execute(db):
                success_count += 1
            else:
                fail_count += 1
        
        logger.info(f"Seeding complete: {success_count} succeeded, {skip_count} skipped, {fail_count} failed")
        
    finally:
        db.close()


if __name__ == "__main__":
    run_all_seeders()
