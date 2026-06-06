#!/usr/bin/env python3
"""
Launcher script for freeWillAi agent daemon
Runs on aiserver, manages agent lifecycle and communication
"""

import os
import sys
import time
import logging
import asyncio
import signal
from pathlib import Path
from dotenv import load_dotenv
from agent import AutonomousAgent
from comms import TelegramBot, DiscordBot

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AgentDaemon:
    """Manages agent lifecycle and communication"""
    def __init__(self, repo_path: str = "."):
        load_dotenv()
        self.repo_path = repo_path
        self.agent = AutonomousAgent(repo_path)
        self.telegram = TelegramBot()
        self.discord = DiscordBot()
        self.running = False
        self.iteration_interval = int(os.getenv("AGENT_ITERATION_INTERVAL", "3600"))

        # Set up signal handlers
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

    def shutdown(self, signum, frame):
        """Graceful shutdown"""
        logger.info("Shutdown signal received")
        self.running = False
        sys.exit(0)

    def handle_message(self, message: str) -> str:
        """Process incoming message from user"""
        logger.info(f"User message: {message}")

        # Agent thinks about the message
        prompt = f"User message: {message}\n\nRespond as {self.agent.personality.name}."
        response = self.agent.ollama.generate(prompt)

        if response:
            logger.info(f"Agent response: {response}")
            return response
        return "I'm thinking... Ollama seems unavailable right now."

    def iteration_loop(self):
        """Main agent iteration loop"""
        logger.info("Starting iteration loop")
        iteration = 0

        while self.running:
            iteration += 1
            logger.info(f"=== Iteration {iteration} ===")

            try:
                self.agent.run_iteration()
            except Exception as e:
                logger.error(f"Error in iteration: {e}")

            # Wait for next iteration
            logger.info(f"Sleeping for {self.iteration_interval}s until next iteration")
            for _ in range(self.iteration_interval):
                if not self.running:
                    break
                time.sleep(1)

    async def start(self):
        """Start agent daemon with communication"""
        logger.info("=== freeWillAi Agent Starting ===")
        self.running = True

        # Register message callbacks
        self.telegram.set_callback(self.handle_message)
        self.discord.set_callback(self.handle_message)

        # Start communication in background tasks
        tasks = []

        if os.getenv("TELEGRAM_BOT_TOKEN"):
            logger.info("Starting Telegram bot")
            tasks.append(asyncio.create_task(self.telegram.run()))

        if os.getenv("DISCORD_BOT_TOKEN"):
            logger.info("Starting Discord bot")
            tasks.append(asyncio.create_task(self.discord.run()))

        # Start iteration loop in thread
        import threading
        iteration_thread = threading.Thread(target=self.iteration_loop, daemon=True)
        iteration_thread.start()

        # Notify startup
        startup_msg = f"freeWill agent started at {time.ctime()}"
        await self.telegram.send_message(startup_msg)
        await self.discord.send_message(startup_msg)

        # Keep running
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Error in startup: {e}")

def main():
    """Entry point"""
    daemon = AgentDaemon(".")
    asyncio.run(daemon.start())

if __name__ == "__main__":
    main()
