from app.detectors.contextual_detector import ContextualDetector


class AddressDetector(ContextualDetector):
    name = "address"

    def detect(self, text, context):
        return [e for e in super().detect(text, context) if e.type.value == "ADDRESS"]
