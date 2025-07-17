import logging
import threading
import time
from typing import Callable, Optional

class HealthMonitor:
    """
    Passive and active health symptom monitor.
    Collects and processes user symptom data in compliance with GDPR.
    """

    def __init__(self, consent_given: bool):
        """
        :param consent_given: User must explicitly consent before monitoring starts.
        """
        self.consent_given = consent_given
        self.symptom_callbacks = []  # functions to call on new symptom detected
        self._monitoring = False
        self._symptom_data = []
        self._lock = threading.Lock()
        logging.info("HealthMonitor initialized. Consent given: %s", consent_given)

    def register_symptom_callback(self, callback: Callable[[dict], None]):
        """
        Register a callback to be notified when new symptom data is available.
        Callback receives a dictionary with symptom info.
        """
        self.symptom_callbacks.append(callback)

    def add_symptom(self, symptom_info: dict):
        """
        Add symptom data (from user input or sensors).
        Only stores data if consent is given.
        """
        if not self.consent_given:
            logging.warning("Attempted to add symptom data without consent.")
            return
        with self._lock:
            self._symptom_data.append(symptom_info)
            logging.info("Symptom added: %s", symptom_info)
        # Notify all registered callbacks asynchronously
        for cb in self.symptom_callbacks:
            try:
                cb(symptom_info)
            except Exception as e:
                logging.error("Error in symptom callback: %s", e)

    def start_passive_monitoring(self):
        """
        Starts a background thread simulating passive monitoring.
        Replace with actual sensor or data stream integration.
        """
        if not self.consent_given:
            logging.error("Cannot start monitoring without user consent.")
            return
        self._monitoring = True
        threading.Thread(target=self._passive_monitor_loop, daemon=True).start()
        logging.info("Passive health monitoring started.")

    def stop_passive_monitoring(self):
        self._monitoring = False
        logging.info("Passive health monitoring stopped.")

    def _passive_monitor_loop(self):
        """
        Dummy passive monitoring loop. Replace with real data collection.
        """
        while self._monitoring:
            # Example: every 30 seconds, check something or simulate symptom
            time.sleep(30)
            # Simulated data
            symptom = {"symptom": "mild headache", "timestamp": time.time()}
            self.add_symptom(symptom)

    def get_all_symptoms(self) -> list:
        """
        Return all stored symptoms. Could be anonymized or filtered as needed.
        """
        with self._lock:
            return list(self._symptom_data)

    def clear_symptom_data(self):
        """
        GDPR right to erasure.
        Clears all stored symptom data immediately.
        """
        with self._lock:
            self._symptom_data.clear()
        logging.info("All symptom data cleared per user request.")
