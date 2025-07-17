import logging
from NHS_111 import NHS111Client  # Assuming this module exists as discussed earlier
from typing import Optional

class HealthReporter:
    """
    Reports user symptom info to NHS 111 ITK SOAP endpoints.
    Ensures minimum necessary data sharing and logs actions.
    """

    def __init__(self, nhs_client: NHS111Client, user_consent: bool):
        """
        :param nhs_client: An initialized NHS111Client instance for SOAP communication.
        :param user_consent: Boolean confirming user consent for data transmission.
        """
        self.nhs_client = nhs_client
        self.user_consent = user_consent
        logging.info("HealthReporter initialized. Consent given: %s", self.user_consent)

    def report_symptom(self, patient_info: dict, referral_info: dict) -> Optional[dict]:
        """
        Sends referral alert to NHS 111 if user consent is granted.
        :param patient_info: Minimal patient identifying info (id, name).
        :param referral_info: Summary of referral reason or symptom.
        :return: NHS 111 response dict or None on failure/no consent.
        """
        if not self.user_consent:
            logging.warning("User consent not given. Aborting NHS 111 report.")
            return None

        cda_xml = self.nhs_client.build_cda_payload(patient_info, referral_info)
        logging.info("Built CDA payload for referral.")

        response = self.nhs_client.send_referral(cda_xml)
        if response is None:
            logging.error("Failed to send referral to NHS 111.")
            return None

        logging.info("Referral sent successfully. NHS response: %s", response)
        return response

    def revoke_consent(self):
        """
        Handle user withdrawing consent to report data.
        Further reports should not be sent.
        """
        self.user_consent = False
        logging.info("User consent revoked. Reporting disabled.")

    def update_consent(self, consent: bool):
        """
        Update consent status.
        """
        self.user_consent = consent
        logging.info("User consent updated to: %s", consent)
