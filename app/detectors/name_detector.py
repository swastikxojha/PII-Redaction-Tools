from app.detectors.contextual_detector import ContextualDetector


class NameDetector(ContextualDetector):
    """Compatibility wrapper exposing person/relative-name detection as a dedicated detector."""

    name = "name"

    def detect(self, text, context):
        return [e for e in super().detect(text, context) if e.type.value in {"PERSON", "RELATIVE_NAME"}]
