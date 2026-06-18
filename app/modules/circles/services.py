from app.modules.circles.repository import CircleRepository


class CircleService:
    def __init__(self, repository=None):
        self.repository = repository or CircleRepository()

    def list_circles(self):
        return self.repository.list_all()

    def get_circle(self, circle_id):
        return self.repository.get_by_id(circle_id)

    def create_circle(self, payload):
        return self.repository.create(payload)

    def update_circle(self, circle, payload):
        return self.repository.update(circle, payload)

    def delete_circle(self, circle):
        return self.repository.delete(circle)
# auto-generated placeholder
