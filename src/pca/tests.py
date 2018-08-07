from django.test import TestCase

from pca.client import pca_client


class PCAClientTestCase(TestCase):
    def test_create_user(self):
        wca_profile_data = {
            'id': 1,
            'wca_id': None,
            'name': 'Juan Dela Cruz',
            'gender': 'm',
            'country_iso2': 'PH',
            'delegate_status': None,
            'avatar': {
                'url': 'https://www.worldcubeassociation.org/assets/missing_avatar_thumb-f0ea801c804765a22892b57636af829edbef25260a65d90aaffbd7873bde74fc.png',
                'thumb_url': 'https://www.worldcubeassociation.org/assets/missing_avatar_thumb-f0ea801c804765a22892b57636af829edbef25260a65d90aaffbd7873bde74fc.png',
                'is_default': True,
            },
            'created_at': '2017-01-12T07:53:16.000Z',
            'updated_at': '2018-07-29T14:08:47.000Z',
        }

        wca_profile = pca_client.create_user(wca_profile_data)

        assert wca_profile is not None
        assert wca_profile.user is not None
        assert wca_profile.wca_pk == wca_profile_data['id']
