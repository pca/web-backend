import requests

from pca.models import WCAProfile, PCAProfile, User


class PCAClient:
    """
    A class wrapper for PCA-related operations.
    """

    def __init__(self, wca_client):
    	self.wca_client = wca_client

    def get_wca_profile(self, host, code):
        access_token_uri = self.wca_client.access_token_uri(host, code)
        response = requests.post(access_token_uri)
        access_token = response.json().get('access_token')

        response = requests.get(settings.WCA_API_URI + 'me', headers={
            'Authorization': 'Bearer {}'.format(access_token),
        })
        profile = response.json()
        return profile.get('me')

    def create_user(self, profile_data):
        user = User.objects.create_user(
            username=str(profile_data['id']),  # Default username is wca_pk
            password=get_random_string(64),  # Generate random password
        )

        wca_profile = WCAProfile.objects.create(
            user=user,
            wca_pk=profile_data['id'],
            wca_id=profile_data['wca_id'],
            name=profile_data['name'],
            gender=profile_data['gender'],
            country_iso2=profile_data['country_iso2'],
            delegate_status=profile_data['delegate_status'],
            avatar_url=profile_data['avatar']['url'],
            avatar_thumb_url=profile_data['avatar']['thumb_url'],
            is_default_avatar=profile_data['avatar']['is_default'],
            wca_created_at=profile_data['created_at'],
            wca_updated_at=profile_data['updated_at'],
        )

        PCAProfile.objects.create(user=user)

        return wca_profile
