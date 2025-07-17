import logging

class SafetyLogic:
    def __init__(self, policy=None):
        """
        :param policy: dict with custom weights or rules for evaluation
                       Example:
                       {
                         "weight_security": 0.5,
                         "weight_stability": 0.3,
                         "weight_risk": 0.2,
                         "max_acceptable_risk": 0.3
                       }
        """
        # Default weights and thresholds
        self.policy = policy or {
            "weight_security": 0.5,
            "weight_stability": 0.3,
            "weight_risk": 0.2,
            "max_acceptable_risk": 0.3
        }
        self.logger = logging.getLogger("SafetyLogic")
        logging.basicConfig(level=logging.INFO)

    def evaluate_method(self, method_info):
        """
        Evaluate a method dict containing:
        {
          "name": "method_name",
          "security": float [0..1],  # higher is better
          "stability": float [0..1], # higher is better
          "risk": float [0..1]       # higher is worse
        }
        Returns a score (higher is better)
        """
        sec = method_info.get("security", 0)
        stab = method_info.get("stability", 0)
        risk = method_info.get("risk", 1)  # risk default worst

        score = (
            sec * self.policy["weight_security"] +
            stab * self.policy["weight_stability"] -
            risk * self.policy["weight_risk"]
        )

        self.logger.debug(f"Evaluating method '{method_info.get('name')}', score: {score:.3f}")
        return score

    def is_method_safe(self, method_info):
        """Return True if risk is below max acceptable threshold."""
        risk = method_info.get("risk", 1)
        safe = risk <= self.policy["max_acceptable_risk"]
        self.logger.debug(f"Method '{method_info.get('name')}' safe: {safe} (risk={risk})")
        return safe

    def select_best_method(self, methods):
        """
        Given a list of method_info dicts, select the safest and highest scoring method.
        If no method is safe, return None.
        """
        safe_methods = [m for m in methods if self.is_method_safe(m)]
        if not safe_methods:
            self.logger.warning("No safe methods available under current policy.")
            return None

        best = max(safe_methods, key=self.evaluate_method)
        self.logger.info(f"Selected method '{best.get('name')}' with score {self.evaluate_method(best):.3f}")
        return best

    def recommend_actions(self, method_info):
        """
        Return recommendations or warnings based on method risk and scores.
        """
        risk = method_info.get("risk", 1)
        recs = []

        if risk > self.policy["max_acceptable_risk"]:
            recs.append(f"Method '{method_info.get('name')}' risk ({risk}) exceeds acceptable limit.")

        if method_info.get("security", 0) < 0.5:
            recs.append("Consider improving security measures.")

        if method_info.get("stability", 0) < 0.5:
            recs.append("Stability concerns: test thoroughly before deploying.")

        return recs
