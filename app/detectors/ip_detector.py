from app.detectors.regex_detector import StructuredRegexDetector


class IPDetector(StructuredRegexDetector):
    name = "ip"

    def detect(self, text, context):
        return [e for e in super().detect(text, context) if e.type.value == "IP_ADDRESS"]
