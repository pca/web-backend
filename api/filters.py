from rest_framework import exceptions, filters


class LimitFilter(filters.BaseFilterBackend):
    default_limit = 100

    def filter_queryset(self, request, queryset, view):
        limit = request.query_params.get("limit", self.default_limit)
        try:
            limit = int(limit)
        except ValueError:
            raise exceptions.ParseError("Invalid limit")
        return queryset[:limit]
