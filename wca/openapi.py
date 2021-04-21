from drf_spectacular.utils import OpenApiExample


# wca.Event
event_example = OpenApiExample(
    "Event example",
    value={
        "id": "333",
        "name": "3x3x3 Cube",
        "rank": "10",
        "format": "time",
        "cell_name": "3x3x3 Cube",
    },
    response_only=True,
)

# wca.Competition
competition_example = OpenApiExample(
    "Competition example",
    value={
        "id": "MC2012",
        "name": "Manila Cubing 2021",
    },
    response_only=True,
)

result_solves_example_value = {
    "solve1": "7.93",
    "solve2": "6.51",
    "solve3": "7.33",
    "solve4": "6.97",
    "solve5": "8.32",
}

# wca.Result
result_example = OpenApiExample(
    "Result example",
    value=[
        {
            "competition": competition_example.value,
            "event": event_example.value,
            "value": "6.51",
            "person_name": "Juan dela Cruz",
            "wca_id": "2021DELA01",
            "solves": result_solves_example_value,
        }
    ],
)

# wca.Person
person_example = OpenApiExample(
    "Person example",
    value={
        "id": "2021DELA01",
        "name": "Juan dela Cruz",
        "country": "Philippines",
        "gender": "Male",
        "avatar": None,
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
