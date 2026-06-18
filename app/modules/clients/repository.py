from app.extensions import db
from app.modules.clients.models import Client


class ClientRepository:
    def get_by_id(self, client_id):
        return Client.query.get(client_id)

    def list_all(self):
        return Client.query.order_by(Client.client_name).all()

    def find_by_field(self, field_name, value, company_id=None, exclude_id=None):
        if not value:
            return None
        query = Client.query.filter(getattr(Client, field_name) == value)
        if company_id:
            query = query.filter(Client.company_id == company_id)
        if exclude_id:
            query = query.filter(Client.id != exclude_id)
        return query.first()

    def exists_by_field(self, field_name, value, company_id=None, exclude_id=None):
        return self.find_by_field(field_name, value, company_id, exclude_id) is not None

    def create(self, data):
        client = Client(**data)
        db.session.add(client)
        db.session.commit()
        return client

    def update(self, client, data):
        for key, value in data.items():
            setattr(client, key, value)
        db.session.commit()
        return client

    def delete(self, client):
        db.session.delete(client)
        db.session.commit()
