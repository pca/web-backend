from django.core.management.base import BaseCommand

from wca.client import wca_client


class Command(BaseCommand):
    help = 'Toggles the inactive db as the active one'

    def handle(self, *args, **options):
        active_db = wca_client._switch_wca_database()
        self.stdout.write('{} is now the active db'.format(active_db), ending='')
