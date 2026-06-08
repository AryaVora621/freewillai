# Auto-generated improvement — Iteration 115
# Suggestion: Write function score_goal_difficulty(goal_desc) that returns 1-5 based on keywords: add=1, implement=2, build=3, rewrite=4, redesign=5

def score_goal_difficulty(goal_desc):
    """Return difficulty 1-5 based on keywords in goal_desc."""
    desc = goal_desc.lower()
    if "rewrite" in desc:
        return 5
    if "build" in desc:
        return 3
    if "implement" in desc:
        return 2
    if "add" in desc:
        return 1
    return 0
