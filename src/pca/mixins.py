from pca.client import PCAClient
from wca.client import WCAClient


class ClientMixin:
    """
    Client Mixin object delivers the wca_client and pca_client to every views
    """
    def __init__(self):
        self.wca_client = WCAClient()
        self.pca_client = PCAClient(self.wca_client)
