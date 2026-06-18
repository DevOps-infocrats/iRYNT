from app.modules.clients.models import Client


class ClientSchema:
    @staticmethod
    def dump(client: Client):
        if not client:
            return None
        return client.to_dict()
