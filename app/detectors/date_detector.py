from app.detectors.contextual_detector import ContextualDetector


class DateDetector(ContextualDetector):
    name = "dob"

    def detect(self, text, context):
        return [e for e in super().detect(text, context) if e.type.value == "DOB"]
