from app.modules.circles.models import Circle
from app.extensions import db


class CircleRepository:
    def get_by_id(self, circle_id):
        return Circle.query.get(circle_id)

    def list_all(self):
        return Circle.query.order_by(Circle.circle_name).all()

    def find_by_field(self, field_name, value, company_id=None, exclude_id=None):
        if not value:
            return None
        query = Circle.query.filter(getattr(Circle, field_name) == value)
        if company_id:
            query = query.filter(Circle.company_id == company_id)
        if exclude_id:
            query = query.filter(Circle.id != exclude_id)
        return query.first()

    def exists_by_field(self, field_name, value, company_id=None, exclude_id=None):
        return self.find_by_field(field_name, value, company_id, exclude_id) is not None

    def create(self, data):
        circle = Circle(**data)
        db.session.add(circle)
        db.session.commit()
        return circle

    def update(self, circle, data):
        for key, value in data.items():
            setattr(circle, key, value)
        db.session.commit()
        return circle

    def delete(self, circle):
        db.session.delete(circle)
        db.session.commit()
# auto-generated placeholder
