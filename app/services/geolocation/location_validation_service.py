class LocationValidationService:
    DEFAULT_MAX_ACCURACY_METERS = 100

    def __init__(self, max_accuracy_meters=None):
        self.max_accuracy_meters = max_accuracy_meters or self.DEFAULT_MAX_ACCURACY_METERS

    def normalize_coordinate(self, value):
        if value in (None, ''):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def normalize_accuracy(self, value):
        if value in (None, ''):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def validate_accuracy(self, accuracy):
        if accuracy is None:
            return False
        return accuracy <= self.max_accuracy_meters

    def parse_payload(self, payload):
        latitude = self.normalize_coordinate(payload.get('latitude'))
        longitude = self.normalize_coordinate(payload.get('longitude'))
        accuracy = self.normalize_accuracy(payload.get('accuracy'))

        return {
            'latitude': latitude,
            'longitude': longitude,
            'accuracy': accuracy,
            'has_location': latitude is not None and longitude is not None,
            'is_accuracy_acceptable': self.validate_accuracy(accuracy),
        }

