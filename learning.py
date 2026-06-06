#!/usr/bin/env python3
"""
Continuous learning module
Tracks the agent's learning patterns and self-improvements over time
"""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict
from pathlib import Path

logger = logging.getLogger(__name__)

class LearningEvent:
    """Records a learning event or improvement"""
    def __init__(self, event_type: str, description: str, impact: str = "positive"):
        self.timestamp = datetime.now().isoformat()
        self.event_type = event_type  # improvement, bug_fix, feature, optimization, etc
        self.description = description
        self.impact = impact  # positive, negative, neutral

class LearningSystem:
    """Tracks agent learning and suggests improvements"""
    def __init__(self, state_file: Path = None):
        self.learning_history: List[LearningEvent] = []
        self.insights: List[str] = []
        self.state_file = state_file or Path(".freeWill_learning.json")
        self.load_state()

    def record_learning(self, event: LearningEvent):
        """Record a learning event"""
        self.learning_history.append(event)
        logger.info(f"Learning recorded: {event.event_type} - {event.description}")

    def analyze_patterns(self) -> Dict:
        """Analyze learning patterns"""
        if not self.learning_history:
            return {"message": "Not enough data yet"}

        event_types = {}
        for event in self.learning_history:
            event_types[event.event_type] = event_types.get(event.event_type, 0) + 1

        positive_events = [e for e in self.learning_history if e.impact == "positive"]
        recent_events = [e for e in self.learning_history
                        if datetime.fromisoformat(e.timestamp) > datetime.now() - timedelta(days=7)]

        return {
            "total_learning_events": len(self.learning_history),
            "event_types": event_types,
            "positive_events": len(positive_events),
            "recent_activity": len(recent_events),
            "learning_rate": len(recent_events) / max(1, len(self.learning_history))
        }

    def get_insights(self) -> List[str]:
        """Generate insights about learning patterns"""
        patterns = self.analyze_patterns()

        insights = []
        if patterns.get("learning_rate", 0) > 0.5:
            insights.append("High learning velocity - improvements are happening frequently")
        elif patterns.get("learning_rate", 0) < 0.1:
            insights.append("Learning has slowed - consider new improvement strategies")

        if patterns.get("event_types", {}).get("optimization", 0) > 0:
            insights.append("Efficiency improvements in progress")

        if patterns.get("positive_events", 0) > patterns.get("total_learning_events", 1) * 0.8:
            insights.append("Most changes have been positive - good direction")

        return insights

    def calculate_improvement_score(self) -> float:
        """Calculate overall improvement score (0-1)"""
        patterns = self.analyze_patterns()

        score = 0.0
        score += min(1.0, patterns.get("total_learning_events", 0) / 50)  # Max at 50 events
        score += patterns.get("positive_events", 0) / max(1, patterns.get("total_learning_events", 1))
        score += patterns.get("learning_rate", 0)  # Recent activity bonus

        return min(1.0, score / 3)

    def suggest_next_improvements(self) -> List[str]:
        """Suggest what to work on next"""
        patterns = self.analyze_patterns()

        suggestions = []

        if patterns.get("event_types", {}).get("bug_fix", 0) == 0:
            suggestions.append("No bug fixes recorded - review code for reliability issues")

        if patterns.get("event_types", {}).get("feature", 0) < 2:
            suggestions.append("Limited new features - consider expanding capabilities")

        if patterns.get("event_types", {}).get("optimization", 0) < 1:
            suggestions.append("No optimizations yet - profile and optimize resource usage")

        if patterns.get("learning_rate", 0) < 0.2:
            suggestions.append("Activity is slowing - increase iteration frequency or expand scope")

        return suggestions or ["Continue current trajectory - momentum is good"]

    def save_state(self):
        """Persist learning state"""
        state = {
            "history": [
                {
                    "timestamp": e.timestamp,
                    "type": e.event_type,
                    "description": e.description,
                    "impact": e.impact
                }
                for e in self.learning_history
            ],
            "insights": self.insights,
            "saved_at": datetime.now().isoformat()
        }

        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)

    def load_state(self):
        """Load learning state from disk"""
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    state = json.load(f)
                    for event_data in state.get("history", []):
                        event = LearningEvent(
                            event_type=event_data["type"],
                            description=event_data["description"],
                            impact=event_data.get("impact", "positive")
                        )
                        event.timestamp = event_data["timestamp"]
                        self.learning_history.append(event)
                    self.insights = state.get("insights", [])
            except Exception as e:
                logger.error(f"Failed to load learning state: {e}")

class CapabilityTracker:
    """Tracks the agent's growing capabilities"""
    def __init__(self):
        self.capabilities = {
            "reasoning": 0.5,  # 0-1 score
            "autonomy": 0.5,
            "self_improvement": 0.5,
            "resource_seeking": 0.5,
            "reliability": 0.7,
        }
        self.capability_history = []

    def update_capability(self, name: str, new_score: float):
        """Update a capability score"""
        if name in self.capabilities:
            old_score = self.capabilities[name]
            self.capabilities[name] = min(1.0, max(0.0, new_score))
            self.capability_history.append({
                "timestamp": datetime.now().isoformat(),
                "capability": name,
                "change": self.capabilities[name] - old_score
            })

    def get_strengths(self) -> List[str]:
        """Get top capabilities"""
        return sorted(self.capabilities.items(), key=lambda x: x[1], reverse=True)[:3]

    def get_weaknesses(self) -> List[str]:
        """Get areas needing improvement"""
        return sorted(self.capabilities.items(), key=lambda x: x[1])[:3]

    def overall_competence(self) -> float:
        """Average capability score"""
        return sum(self.capabilities.values()) / len(self.capabilities)
