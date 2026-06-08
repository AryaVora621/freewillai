# Auto-generated improvement — Iteration 115
# Suggestion: Write function score_goal_difficulty(goal_desc) that returns 1-5 based on keywords: add=1, implement=2, build=3, rewrite=4, redesign=5

def score_goal_difficulty(goal_desc):
    """Return difficulty 1-5 based on keywords in goal description."""
    s = goal_desc.lower()
    if 'rewrite' in s:
        return 5
    if 'build' in s:
        return 4
    if 'implement' in s:
        return 3
    if 'add' in s:
        return 2
    return 1
