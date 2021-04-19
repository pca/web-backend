from rest_framework import serializers

from . import api, models
from .utils import parse_solves, parse_value


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Event
        fields = "__all__"


class CompetitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Competition
        fields = ("id", "name")


class ResultSerializer(serializers.ModelSerializer):
    competition = CompetitionSerializer()
    event = EventSerializer()
    value = serializers.SerializerMethodField()
    wca_id = serializers.SerializerMethodField()
    solves = serializers.SerializerMethodField()

    class Meta:
        model = models.Result
        fields = ("competition", "event", "value", "person_name", "wca_id", "solves")

    def get_value(self, obj):
        rank_type = self.context.get("rank_type")
        if rank_type == "average":
            return parse_value(obj.average, obj.event.format, rank_type=rank_type)
        return parse_value(obj.best, obj.event.format, rank_type=rank_type)

    def get_wca_id(self, obj):
        return obj.person.id

    def get_solves(self, obj):
        rank_type = self.context.get("rank_type")
        return parse_solves(obj, rank_type)


class PersonSerializer(serializers.ModelSerializer):
    gender = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    career = serializers.SerializerMethodField()

    class Meta:
        model = models.Person
        fields = (
            "id",
            "name",
            "country",
            "gender",
            "avatar",
            "career",
        )

    def get_gender(self, obj):
        return obj.get_gender_display()

    def get_avatar(self, obj):
        return api.get_avatar(obj)

    def get_career(self, obj):
        return api.get_career_details(obj)
