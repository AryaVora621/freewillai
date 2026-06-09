# Auto-generated improvement — Iteration 113
# Suggestion: Add /reset Telegram command: abandon active goals and pick fresh category from next in queue

def handle_reset(update, context):
    """Abandon active goals and pick next category from queue."""
    from collections import deque
    user_id = update.effective_user.id
    data = context.bot_data.setdefault('users', {})
    user = data.setdefault(user_id, {'goals': [], 'categories': deque()})
    # Clear current goals
    user['goals'].clear()
    # Advance to next category
    if not user['categories']:
        # Initialize with default categories if empty
        user['categories'] = deque(['health', 'work', 'hobby'])
    user['categories'].rotate(-1)
    next_cat = user['categories'][0]
    # Optionally start a new goal placeholder
    user['goals'].append({'category': next_cat, 'status': 'pending'})
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=f"Goals reset. New category: {next_cat}")
