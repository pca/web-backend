from django.utils.decorators import method_decorator
from drf_spectacular.extensions import OpenApiFilterExtension, OpenApiViewExtension
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.plumbing import get_doc
from drf_spectacular.utils import OpenApiExample, extend_schema

from . import app_settings

wca_login_request_example = OpenApiExample(
    "WCA login request example",
    value={
        "code": "OTQ5HFpRcpwBJPxGZgwc0Dc5LpnTUXxVVNHxe2QDdEl",
        "callback_url": app_settings.WCA_DEFAULT_CALLBACK_URL,
    },
    request_only=True,
)
wca_login_response_example = OpenApiExample(
    "WCA login response example",
    value={"key": "cjcsu60bc8fi4hw9s4lbhgnbtc4ls1xlyga99qe0"},
    response_only=True,
)

user_retrieve_example = OpenApiExample(
    "User retrieve example",
    value={
        "first_name": "Juan",
        "last_name": "dela Cruz",
        "wca_id": "2021DELA01",
        "region": "NCR",
        "region_updated_at": "2021-04-24T03:14:50.069Z",
        "created_at": "2021-04-24T03:14:50.069Z",
    },
    response_only=True,
)
region_list_example = OpenApiExample(
    "Region list example",
    value=[{"id": "NCR", "name": "NCR (Luzon - Metro Manila)"}],
    response_only=True,
)
zone_list_example = OpenApiExample(
    "Zone list example",
    value=[{"id": "luzon", "name": "Luzon"}],
    response_only=True,
)

news_list_example = OpenApiExample(
    "News list example",
    value=[
        {
            "from_name": "Philippine Cubers Association",
            "message": "Hello World!",
            "image": None,
            "permalink": (
                "https://www.facebook.com/182835918433029/posts/3709202639129655/"
            ),
            "created_at": "2021-04-24T02:29:17.921Z",
        }
    ],
    response_only=True,
)

wca_event_example = {
    "id": "333",
    "name": "3x3x3 Cube",
    "rank": "10",
    "format": "time",
    "cell_name": "3x3x3 Cube",
}
wca_event_list_example = OpenApiExample(
    "Event list example",
    value=[wca_event_example],
    response_only=True,
)
wca_person_retrieve_example = OpenApiExample(
    "Person retrieve example",
    value={
        "id": "2021DELA01",
        "name": "Juan dela Cruz",
        "country": "Philippines",
        "gender": "Male",
        "avatar": {
            "url": (
                "https://www.worldcubeassociation.org/assets/missing_avatar_thumb-"
                "f0ea801c804765a22892b57636af829edbef25260a65d90aaffbd7873bde74fc.png"
            ),
            "thumb_url": (
                "https://www.worldcubeassociation.org/assets/missing_avatar_thumb-"
                "f0ea801c804765a22892b57636af829edbef25260a65d90aaffbd7873bde74fc.png"
            ),
            "is_default": True,
        },
        "career": {
            "competition_count": 12,
            "solve_count": 60,
            "personal_records": {
                "333": {
                    "single": {
                        "best": "12.32",
                        "world_rank": 14912,
                        "continent_rank": 4105,
                        "country_rank": 341,
                    },
                    "average": {
                        "best": "14.02",
                        "world_rank": 15318,
                        "continent_rank": 5291,
                        "country_rank": 421,
                    },
                },
            },
            "records": {
                "national": 3,
                "continental": 0,
                "world": 0,
                "total": 3,
            },
            "medals": {"gold": 1, "silver": 2, "bronze": 0, "total": 3},
        },
    },
    response_only=True,
)
wca_result_list_example = OpenApiExample(
    "Result list example",
    value=[
        {
            "competition": {
                "id": "MC2021",
                "name": "Manila Cubing 2021",
            },
            "event": wca_event_example,
            "value": "6.51",
            "person_name": "Juan dela Cruz",
            "wca_id": "2021DELA01",
            "solves": {
                "solve1": "7.93",
                "solve2": "6.51",
                "solve3": "7.33",
                "solve4": "6.97",
                "solve5": "8.32",
            },
        }
    ],
    response_only=True,
)


class CustomAutoSchema(AutoSchema):
    def get_summary(self):
        docstring = self.get_docstring()
        summary, _ = self.split_summary_from_docstring(docstring)
        return summary

    def get_docstring(self):
        action_or_method = getattr(
            self.view, getattr(self.view, "action", self.method.lower()), None
        )
        view_doc = get_doc(self.view.__class__)
        action_doc = get_doc(action_or_method)
        return action_doc or view_doc

    def split_summary_from_docstring(self, docstring):
        # OpenAPI 3.0 spec doesn't specify max length but 2.0 says summary
        # should be under 120 characters
        summary_max_len = 120
        summary = None
        description = docstring

        # https://www.python.org/dev/peps/pep-0257/#multi-line-docstrings
        sections = docstring.split("\n\n", 1)

        if len(sections) == 1:
            summary = docstring.strip()
            description = None

        if len(sections) == 2:
            sections[0] = sections[0].strip()

            if len(sections[0]) < summary_max_len:
                summary, description = sections
                description = description.strip()

        return summary, description


class LimitFilterExtension(OpenApiFilterExtension):
    target_class = "api.filters.LimitFilter"

    def get_schema_operation_parameters(self, auto_schema, *args, **kwargs):
        return [
            {
                "name": "limit",
                "required": False,
                "in": "query",
                "description": "Limits the result count.",
                "schema": {
                    "type": "string",
                },
            }
        ]


class OpenApiViewExamplesExtension(OpenApiViewExtension):
    extend_schema_kwargs = {}
    examples = []
    method = "get"

    def view_replacement(self):
        @method_decorator(
            extend_schema(examples=self.examples, **self.extend_schema_kwargs),
            name=self.method,
        )
        class Decorated(self.target_class):
            pass

        return Decorated


class WCALoginViewExtension(OpenApiViewExamplesExtension):
    target_class = "api.views.WCALoginView"
    examples = [wca_login_request_example, wca_login_response_example]
    method = "post"


class UserRetrieveAPIView(OpenApiViewExamplesExtension):
    target_class = "api.views.UserRetrieveAPIView"
    examples = [user_retrieve_example]
    method = "get"


class RegionListAPIViewExtension(OpenApiViewExamplesExtension):
    target_class = "api.views.RegionListAPIView"
    extend_schema_kwargs = {"tags": ["locations"]}
    examples = [region_list_example]
    method = "get"


class ZoneListAPIViewExtension(OpenApiViewExamplesExtension):
    target_class = "api.views.ZoneListAPIView"
    extend_schema_kwargs = {"tags": ["locations"]}
    examples = [zone_list_example]
    method = "get"


class EventListAPIViewExtension(OpenApiViewExamplesExtension):
    target_class = "api.views.EventListAPIView"
    examples = [wca_event_list_example]
    method = "get"


class NationalRankingSingleAPIView(OpenApiViewExamplesExtension):
    target_class = "api.views.NationalRankingSingleAPIView"
    examples = [wca_result_list_example]
    method = "get"


class NationalRankingAverageAPIView(OpenApiViewExamplesExtension):
    target_class = "api.views.NationalRankingAverageAPIView"
    examples = [wca_result_list_example]
    method = "get"


class RegionalRankingSingleAPIView(OpenApiViewExamplesExtension):
    target_class = "api.views.RegionalRankingSingleAPIView"
    examples = [wca_result_list_example]
    method = "get"


class RegionalRankingAverageAPIView(OpenApiViewExamplesExtension):
    target_class = "api.views.RegionalRankingAverageAPIView"
    examples = [wca_result_list_example]
    method = "get"


class ZonalRankingSingleAPIView(OpenApiViewExamplesExtension):
    target_class = "api.views.ZonalRankingSingleAPIView"
    examples = [wca_result_list_example]
    method = "get"


class ZonalRankingAverageAPIView(OpenApiViewExamplesExtension):
    target_class = "api.views.ZonalRankingAverageAPIView"
    examples = [wca_result_list_example]
    method = "get"


class PersonRetrieveAPIView(OpenApiViewExamplesExtension):
    target_class = "api.views.PersonRetrieveAPIView"
    examples = [wca_person_retrieve_example]
    method = "get"


class NewsListAPIViewExtension(OpenApiViewExamplesExtension):
    target_class = "api.views.NewsListAPIView"
    examples = [news_list_example]
    method = "get"
