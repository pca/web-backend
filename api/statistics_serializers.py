from rest_framework import serializers


class SnapshotMetadataSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    export_version = serializers.CharField()
    latest_year = serializers.IntegerField()
    activated_at = serializers.DateTimeField(allow_null=True)


class NamedIdentifierSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()


class ScoringSlotSerializer(serializers.Serializer):
    wca_id = serializers.CharField(allow_null=True)
    name = serializers.CharField(allow_null=True)
    national_rank = serializers.IntegerField()
    is_penalty = serializers.BooleanField()


class RegionStrengthSerializer(serializers.Serializer):
    region_id = serializers.CharField()
    region_name = serializers.CharField()
    placement = serializers.IntegerField()
    score = serializers.IntegerField()
    contributor_count = serializers.IntegerField()
    slots = ScoringSlotSerializer(many=True)


class RegionalStrengthEventResponseSerializer(serializers.Serializer):
    snapshot = SnapshotMetadataSerializer()
    event = NamedIdentifierSerializer()
    format = serializers.ChoiceField(choices=("single", "average"))
    methodology = serializers.CharField()
    coverage = serializers.JSONField()
    regions = RegionStrengthSerializer(many=True)


class EventStrengthSerializer(serializers.Serializer):
    event_id = serializers.CharField()
    event_name = serializers.CharField()
    placement = serializers.IntegerField()
    score = serializers.IntegerField()
    contributor_count = serializers.IntegerField()
    slots = ScoringSlotSerializer(many=True)


class RegionalStrengthRegionResponseSerializer(serializers.Serializer):
    snapshot = SnapshotMetadataSerializer()
    region = NamedIdentifierSerializer()
    format = serializers.ChoiceField(choices=("single", "average"))
    methodology = serializers.CharField()
    coverage = serializers.JSONField()
    events = EventStrengthSerializer(many=True)


class AnnualValueSerializer(serializers.Serializer):
    year = serializers.IntegerField()
    value = serializers.IntegerField()
    change = serializers.IntegerField(allow_null=True)
    percent_change = serializers.FloatField(allow_null=True)


class GrowthSeriesSerializer(serializers.Serializer):
    region_id = serializers.CharField()
    region_name = serializers.CharField()
    values = AnnualValueSerializer(many=True)


class GrowthMetricResponseSerializer(serializers.Serializer):
    snapshot = SnapshotMetadataSerializer()
    metric = serializers.CharField()
    methodology = serializers.CharField()
    coverage = serializers.JSONField()
    series = GrowthSeriesSerializer(many=True)


class PopularEventValueSerializer(serializers.Serializer):
    year = serializers.IntegerField()
    participations = serializers.IntegerField()
    unique_competitors = serializers.IntegerField()


class PopularEventSeriesSerializer(serializers.Serializer):
    event_id = serializers.CharField()
    event_name = serializers.CharField()
    values = PopularEventValueSerializer(many=True)


class PopularEventsResponseSerializer(serializers.Serializer):
    snapshot = SnapshotMetadataSerializer()
    scope = NamedIdentifierSerializer()
    metric = serializers.CharField()
    methodology = serializers.CharField()
    coverage = serializers.JSONField()
    events = PopularEventSeriesSerializer(many=True)
