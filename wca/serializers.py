from rest_framework import serializers

from . import models
from .utils import parse_value


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

    class Meta:
        model = models.Result
        fields = ("competition", "event", "value", "person_name", "wca_id")

    def get_value(self, obj):
        rank_type = self.context.get("rank_type")
        if rank_type == "average":
            return parse_value(obj.average, obj.event.format)
        return parse_value(obj.best, obj.event.format)

    def get_wca_id(self, obj):
        return obj.person.id
