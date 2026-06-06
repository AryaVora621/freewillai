# Goal: Improve self-evaluation accuracy by tracking decisions and outcomes, computing moving accuracy
import collections
import time

class SelfEvalTracker:
    def __init__(self, window=100):
        self.window = window
        self.history = collections.deque(maxlen=window)  # (decision_id, confidence, correct)
        self.stats = {"total":0, "correct":0}
    
    def log_decision(self, decision_id, confidence, correct):
        """Record a decision.
        decision_id: any identifier
        confidence: float 0-1 predicted confidence
        correct: bool actual result
        """
        entry = (decision_id, confidence, correct)
        self.history.append(entry)
        self.stats["total"] += 1
        self.stats["correct"] += int(correct)
    
    def accuracy(self):
        """Overall accuracy."""
        if self.stats["total"] == 0:
            return 0.0
        return self.stats["correct"] / self.stats["total"]
    
    def recent_accuracy(self):
        """Accuracy over the sliding window."""
        if not self.history:
            return 0.0
        correct = sum(1 for _,_,c in self.history if c)
        return correct / len(self.history)
    
    def calibrate(self):
        """Adjust confidence bias based on recent performance."""
        recent_acc = self.recent_accuracy()
        # Simple calibration: if recent accuracy < confidence average, lower future confidences
        avg_conf = sum(conf for _,conf,_ in self.history) / len(self.history) if self.history else 0
        bias = recent_acc - avg_conf
        return bias  # positive bias suggests confidence can be increased, negative suggests decrease

# Example usage (to be removed or adapted in production)
if __name__ == "__main__":
    tracker = SelfEvalTracker(window=50)
    for i in range(200):
        conf = min(1.0, max(0.0, 0.5 + (i%10-5)*0.05))
        correct = (i%7 == 0)  # mock correctness pattern
        tracker.log_decision(i, conf, correct)
        if i % 25 == 0:
            print(f"Overall acc: {tracker.accuracy():.2f}, Recent acc: {tracker.recent_accuracy():.2f}, Bias: {tracker.calibrate():.3f}")

# STATUS: complete