from app.modules.clients.repository import ClientRepository


class ClientService:
    def __init__(self, repository=None):
        self.repository = repository or ClientRepository()

    def list_clients(self):
        return self.repository.list_all()

    def get_client(self, client_id):
        return self.repository.get_by_id(client_id)

    def create_client(self, payload):
        return self.repository.create(payload)

    def update_client(self, client, payload):
        return self.repository.update(client, payload)

    def delete_client(self, client):
        return self.repository.delete(client)
