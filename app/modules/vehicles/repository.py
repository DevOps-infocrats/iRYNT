from app.extensions import db
from app.modules.vehicles.models import Vehicle


class VehicleRepository:
    def get_vehicle(self, vehicle_id):
        return Vehicle.query.filter_by(id=vehicle_id).first()

    def list_vehicles(self, company_id=None, circle_id=None, limit=20, offset=0):
        query = Vehicle.query.order_by(Vehicle.created_at.desc())
        if company_id:
            query = query.filter_by(company_id=company_id)
        if circle_id:
            query = query.filter_by(circle_id=circle_id)
        return query.limit(limit).offset(offset).all()

    def create_vehicle(self, payload):
        vehicle = Vehicle(**payload)
        db.session.add(vehicle)
        db.session.commit()
        return vehicle

    def update_vehicle(self, vehicle, payload):
        for key, value in payload.items():
            setattr(vehicle, key, value)
        db.session.commit()
        return vehicle

    def exists_vehicle_number(self, company_id, circle_id, client_id, project_id, subzone_id, vehicle_number, exclude_id=None):
        query = Vehicle.query.filter_by(
            company_id=company_id,
            circle_id=circle_id,
            client_id=client_id,
            project_id=project_id,
            subzone_id=subzone_id,
            vehicle_number=vehicle_number,
        )
        if exclude_id:
            query = query.filter(Vehicle.id != exclude_id)
        return db.session.query(query.exists()).scalar()

    def count_by_status(self):
        return db.session.query(Vehicle.status, db.func.count(Vehicle.id)).group_by(Vehicle.status).all()

