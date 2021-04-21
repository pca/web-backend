from django.utils.decorators import method_decorator
from drf_spectacular.extensions import OpenApiFilterExtension, OpenApiViewExtension
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.plumbing import get_doc
from drf_spectacular.utils import OpenApiExample, extend_schema

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


class RegionListAPIViewExtension(OpenApiViewExtension):
    target_class = "api.views.RegionListAPIView"

    def view_replacement(self):
        @method_decorator(
            extend_schema(tags=["locations"], examples=[region_list_example]),
            name="get",
        )
        class Decorated(self.target_class):
            pass

        return Decorated


class ZoneListAPIViewExtension(OpenApiViewExtension):
    target_class = "api.views.ZoneListAPIView"

    def view_replacement(self):
        @method_decorator(
            extend_schema(tags=["locations"], examples=[zone_list_example]),
            name="get",
        )
        class Decorated(self.target_class):
            pass

        return Decorated
