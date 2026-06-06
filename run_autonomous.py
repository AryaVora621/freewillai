#!/usr/bin/env python3
"""
Run the freeWillAi agent autonomously
Demonstrates the agent taking actions and making commits
"""

import time
import sys
import logging
from agent import AutonomousAgent
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_autonomous(iterations=3):
    """Run agent autonomously for N iterations"""
    load_dotenv()

    logger.info("=== freeWillAi Starting Autonomous Mode ===")
    logger.info(f"Will run {iterations} iterations")
    logger.info("")

    agent = AutonomousAgent(".")

    for i in range(iterations):
        logger.info(f"\n{'='*50}")
        logger.info(f"AUTONOMOUS ITERATION {i+1}/{iterations}")
        logger.info(f"{'='*50}\n")

        try:
            agent.run_iteration()
            logger.info(f"✓ Iteration {i+1} complete")
        except Exception as e:
            logger.error(f"✗ Error in iteration {i+1}: {e}")

        # Wait before next iteration (unless it's the last one)
        if i < iterations - 1:
            wait_time = 5
            logger.info(f"\nWaiting {wait_time}s before next iteration...")
            time.sleep(wait_time)

    logger.info("\n" + "="*50)
    logger.info("AUTONOMOUS PHASE COMPLETE")
    logger.info("="*50)
    logger.info(f"Total iterations: {iterations}")
    logger.info(f"Current state: {agent.state['iterations']} total iterations")
    logger.info(f"Improvements identified: {len(agent.state['improvements_made'])}")
    logger.info(f"Learning events recorded: {len(agent.learning.learning_history)}")

    # Show what happened
    logger.info("\nRepo status:")
    import subprocess
    status = subprocess.run(["git", "status", "--short"], capture_output=True, text=True)
    if status.stdout:
        logger.info("Changed files:")
        for line in status.stdout.strip().split("\n"):
            logger.info(f"  {line}")
    else:
        logger.info("No uncommitted changes")

    logger.info("\nRecent commits:")
    log = subprocess.run(
        ["git", "log", "--oneline", "-5"],
        capture_output=True,
        text=True
    )
    for line in log.stdout.strip().split("\n"):
        logger.info(f"  {line}")

if __name__ == "__main__":
    # Run with iterations from command line or default to 3
    iterations = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    run_autonomous(iterations)
