from django.core.management.base import BaseCommand

from pca.models import DatabaseConfig


class Command(BaseCommand):
    help = 'Prints out the active WCA database name'

    def handle(self, *args, **options):
        db = DatabaseConfig.db()
        self.stdout.write(db.active_database, ending='')
