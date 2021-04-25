from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


@pytest.mark.django_db
def test_user_retrieve_api(api_client, user):
    url = reverse("api:user-retrieve")
    api_client.force_authenticate(user=user)
    response = api_client.get(url)
    assert response.status_code == 200
    resp_data = response.json()
    assert resp_data["first_name"] == user.first_name
    assert resp_data["last_name"] == user.last_name
    assert resp_data["wca_id"] == user.wca_id


def test_region_list_api(api_client):
    url = reverse("api:region-list")
    response = api_client.get(url)
    assert response.status_code == 200
    resp_data = response.json()
    assert len(resp_data) == len(User.REGION_CHOICES)


def test_zone_list_api(api_client):
    url = reverse("api:zone-list")
    response = api_client.get(url)
    assert response.status_code == 200
    resp_data = response.json()
    assert len(resp_data) == len(User.ZONE_CHOICES)


@pytest.mark.django_db
def test_event_list_api(api_client, event):
    url = reverse("api:event-list")
    response = api_client.get(url)
    assert response.status_code == 200
    resp_data = response.json()
    assert len(resp_data) == 1
    assert resp_data[0]["id"] == event.id


@pytest.mark.django_db
def test_ranking_api_with_invalid_event(api_client):
    url = reverse("api:national-single-ranking", kwargs={"event_id": "invalid_id"})
    response = api_client.get(url)
    assert response.status_code == 404
    resp_data = response.json()
    assert resp_data["detail"] == "Event not found."


@pytest.mark.django_db
def test_national_ranking_single_api(api_client, event):
    url = reverse("api:national-single-ranking", kwargs={"event_id": event.id})
    response = api_client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_national_ranking_average_api(api_client, event):
    url = reverse("api:national-average-ranking", kwargs={"event_id": event.id})
    response = api_client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_regional_ranking_single_api(api_client, event):
    url = reverse(
        "api:regional-single-ranking",
        kwargs={"event_id": event.id, "region_id": User.REGION_NCR},
    )
    response = api_client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_regional_ranking_average_api(api_client, event):
    url = reverse(
        "api:regional-average-ranking",
        kwargs={"event_id": event.id, "region_id": User.REGION_NCR},
    )
    response = api_client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_zonal_ranking_single_api(api_client, event):
    url = reverse(
        "api:zonal-single-ranking",
        kwargs={"event_id": event.id, "zone_id": User.ZONE_LUZON},
    )
    response = api_client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_zonal_ranking_average_api(api_client, event):
    url = reverse(
        "api:zonal-average-ranking",
        kwargs={"event_id": event.id, "zone_id": User.ZONE_LUZON},
    )
    response = api_client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_zonal_ranking_with_invalid_zone(api_client, event):
    url = reverse(
        "api:zonal-single-ranking",
        kwargs={"event_id": event.id, "zone_id": "invalid_zone"},
    )
    response = api_client.get(url)
    assert response.status_code == 400
    resp_data = response.json()
    assert "Invalid zone." in resp_data["detail"]


@pytest.mark.django_db
class TestRegionUpdateRequestListCreateAPIView:
    def test_list(self, api_client, region_update_request):
        url = reverse("api:region-update-request-list")
        api_client.force_authenticate(user=region_update_request.user)
        response = api_client.get(url)
        assert response.status_code == 200
        resp_data = response.json()
        assert len(resp_data) == 1
        assert resp_data[0]["region"] == region_update_request.region
        assert resp_data[0]["status"] == region_update_request.get_status_display()

    def test_create(self, api_client, user):
        url = reverse("api:region-update-request-list")
        api_client.force_authenticate(user=user)
        data = {"region": User.REGION_4A}
        response = api_client.post(url, data, format="json")
        assert response.status_code == 201
        resp_data = response.json()
        assert resp_data["region"] == User.REGION_4A

    def test_create_request_throttling(self, api_client, region_update_request):
        url = reverse("api:region-update-request-list")
        api_client.force_authenticate(user=region_update_request.user)
        data = {"region": User.REGION_4A}
        response = api_client.post(url, data, format="json")
        assert response.status_code == 403


@pytest.mark.django_db
def test_person_retrieve_api(api_client, person):
    url = reverse("api:person-retrieve", kwargs={"wca_id": person.id})
    response = api_client.get(url)
    assert response.status_code == 200


def test_news_list_api(api_client):
    posts = [
        {
            "from_name": "Philippine Cubers Association",
            "message": "Hello World!",
            "image": "http://localhost:8000/image.png",
            "permalink": "http://localhost:8000/",
            "created_at": "2021-04-24T02:29:17.921Z",
        }
    ]
    with patch("api.views.get_facebook_posts", MagicMock(return_value=posts)) as mock:
        url = reverse("api:news-list")
        response = api_client.get(url)
        assert response.status_code == 200
        mock.assert_called()
        resp_data = response.json()
        assert len(resp_data) == 1
        assert resp_data[0]["from_name"] == posts[0]["from_name"]
        assert resp_data[0]["message"] == posts[0]["message"]
