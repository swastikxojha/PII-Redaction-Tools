from app.detectors.regex_detector import StructuredRegexDetector


class EmailDetector(StructuredRegexDetector):
    name = "email"

    def detect(self, text, context):
        return [e for e in super().detect(text, context) if e.type.value == "EMAIL"]
