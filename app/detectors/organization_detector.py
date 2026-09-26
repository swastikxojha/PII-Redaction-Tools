from app.detectors.contextual_detector import ContextualDetector


class OrganizationDetector(ContextualDetector):
    name = "organization"

    def detect(self, text, context):
        return [e for e in super().detect(text, context) if e.type.value == "COMPANY"]
