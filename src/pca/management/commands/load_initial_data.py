import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth.models import Group

from wagtail.core.models import Site, Page


class Command(BaseCommand):
    def handle(self, **options):
        fixtures_dir = os.path.join(settings.BASE_DIR, 'pca', 'fixtures')
        fixture_file = os.path.join(fixtures_dir, 'initial_data.json')

        # Wagtail creates default Site, Page, and auth Group instances during install, but we already have
        # them in the data load. Remove the auto-generated ones.
        if Site.objects.filter(hostname='localhost').exists():
            Site.objects.get(hostname='localhost').delete()

        if Page.objects.filter(title='Welcome to your new Wagtail site!').exists():
            Page.objects.get(title='Welcome to your new Wagtail site!').delete()

        Group.objects.all().delete()

        call_command('loaddata', fixture_file, verbosity=0)
        print('Your data is loaded!')
