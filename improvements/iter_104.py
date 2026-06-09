# Auto-generated improvement — Iteration 104
# Suggestion: Add a /stats Telegram command showing iteration count, goals completed, improvements applied, and current Ollama model

def add_stats_command(bot, state):
    """Add /stats command to Telegram bot showing iteration, goals, improvements, and Ollama model."""
    async def stats_handler(update, context):
        it = state.get('iteration', 0)
        goals = state.get('goals_completed', 0)
        improves = state.get('improvements_applied', 0)
        model = state.get('ollama_model', 'unknown')
        text = (f"📊 Stats:\n"
                f"Iteration: {it}\n"
                f"Goals completed: {goals}\n"
                f"Improvements applied: {improves}\n"
                f"Ollama model: {model}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
    bot.add_handler(CommandHandler('stats', stats_handler))
