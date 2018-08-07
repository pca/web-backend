from django.conf import settings
from django.test import TestCase

from pca.models import DatabaseConfig

from wca.client import wca_client, recompute_rankings_job


class WCAClientTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        DatabaseConfig.objects.create(
            active_database='wca1',
            inactive_database='wca2',
        )
        wca_client.import_wca_test_database()

    def test_authorize_uri(self):
        authorize_uri = wca_client.authorize_uri()

        assert settings.WCA_OAUTH_URI in authorize_uri
        assert settings.WCA_CLIENT_ID in authorize_uri
        assert settings.WCA_REDIRECT_URI in authorize_uri

    def test_competitions(self):
        wca_client.redis_client.flushdb()

        competitions = wca_client.competitions()
        cached_competitions = wca_client.competitions()

        assert competitions is not None
        assert cached_competitions is not None

    def test_access_token_uri(self):
        code = '1234567890'
        access_token_uri = wca_client.access_token_uri(code)

        assert settings.WCA_OAUTH_URI in access_token_uri
        assert settings.WCA_CLIENT_ID in access_token_uri
        assert settings.WCA_CLIENT_SECRET in access_token_uri
        assert settings.WCA_REDIRECT_URI in access_token_uri
        assert code in access_token_uri

    def test_all_rankings(self):
        rankings = wca_client.all_rankings('national')

        assert rankings.get('single_222') is not None
        assert rankings.get('single_333') is not None
        assert rankings.get('single_444') is not None
        assert rankings.get('single_555') is not None
        assert rankings.get('average_222') is not None
        assert rankings.get('average_333') is not None
        assert rankings.get('average_444') is not None
        assert rankings.get('average_555') is not None

    def test_rankings(self):
        wca_client.redis_client.flushdb()

        rankings = wca_client.rankings('222', 'best', 'national')
        cached_rankings = wca_client.rankings('222', 'best', 'national')

        assert rankings is not None
        assert cached_rankings is not None

    def test_recompute_rankings(self):
        wca_client.redis_client.flushdb()

        wca_client.recompute_rankings('national')
        jobs = wca_client.redis_client.keys('rq:job:*')

        assert len(jobs) == 1

    def test_recompute_rankings_job(self):
        wca_client.redis_client.flushdb()

        recompute_rankings_job('national')
        keys = wca_client.redis_client.keys('*national*')

        assert len(keys) == 42
