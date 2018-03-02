"""
WCA database export mapped in Django ORM.
"""
from django.db import models

from web.models import WCAProfile


class Competition(models.Model):
    name = models.CharField(max_length=50, db_column='name')
    cityName = models.CharField(max_length=50, db_column='cityName')
    countryId = models.CharField(max_length=50, db_column='countryId')
    information = models.TextField(null=True, blank=True, db_column='information')
    year = models.IntegerField(db_column='year')
    month = models.IntegerField(db_column='month')
    day = models.IntegerField(db_column='day')
    endMonth = models.IntegerField(db_column='endMonth')
    endDay = models.IntegerField(db_column='endDay')
    eventSpecs = models.CharField(max_length=256, null=True, blank=True, db_column='eventSpecs')
    wcaDelegate = models.TextField(null=True, blank=True, db_column='wcaDelegate')
    organiser = models.TextField(null=True, blank=True, db_column='organiser')
    venue = models.CharField(max_length=240, db_column='venue')
    venueAddress = models.CharField(max_length=120, null=True, blank=True, db_column='venueAddress')
    venueDetails = models.CharField(max_length=120, null=True, blank=True, db_column='venueDetails')
    external_website = models.CharField(max_length=200, null=True, blank=True, db_column='external_website')
    cellName = models.CharField(max_length=45, db_column='cellName')
    latitude = models.IntegerField(null=True, blank=True, db_column='latitude')
    longitude = models.IntegerField(null=True, blank=True, db_column='longitude')

    class Meta:
        db_table = 'Competitions'
        managed = False


class Continent(models.Model):
    name = models.CharField(max_length=50, db_column='name')
    recordName = models.CharField(max_length=3, db_column='recordName')
    latitude = models.IntegerField(db_column='latitude')
    longitude = models.IntegerField(db_column='longitude')
    zoom = models.IntegerField(db_column='zoom')

    class Meta:
        db_table = 'Continents'
        managed = False


class Country(models.Model):
    name = models.CharField(max_length=50, db_column='name')
    continentId = models.CharField(max_length=50, db_column='continentId')
    latitude = models.IntegerField(db_column='latitude')
    longitude = models.IntegerField(db_column='longitude')
    zoom = models.IntegerField(db_column='zoom')
    iso2 = models.CharField(max_length=2, null=True, blank=True, db_column='iso2')

    class Meta:
        db_table = 'Countries'
        managed = False


class Event(models.Model):
    name = models.CharField(max_length=54, db_column='name')
    rank = models.IntegerField(db_column='rank')
    format = models.CharField(max_length=10, db_column='format')
    cellName = models.CharField(max_length=45, db_column='cellName')

    class Meta:
        db_table = 'Events'
        managed = False


class Format(models.Model):
    name = models.CharField(max_length=50, db_column='name')
    sort_by = models.CharField(max_length=255, db_column='sort_by')
    sort_by_second = models.CharField(max_length=255, db_column='sort_by_second')
    expected_solve_count = models.IntegerField(db_column='expected_solve_count')
    trim_fastest_n = models.IntegerField(db_column='trim_fastest_n')
    trim_slowest_n = models.IntegerField(db_column='trim_slowest_n')

    class Meta:
        db_table = 'Formats'
        managed = False


class Person(models.Model):
    subid = models.IntegerField(db_column='subid')
    name = models.CharField(max_length=80, db_column='name')
    countryId = models.CharField(max_length=50, db_column='countryId')
    gender = models.CharField(max_length=1, db_column='gender')

    class Meta:
        db_table = 'Persons'
        managed = False


class RanksAverage(models.Model):
    personId = models.CharField(max_length=10, db_column='personId')
    eventId = models.CharField(max_length=6, db_column='eventId')
    best = models.IntegerField(db_column='best')
    worldRank = models.IntegerField(db_column='worldRank')
    continentRank = models.IntegerField(db_column='continentRank')
    countryRank = models.IntegerField(db_column='countryRank')

    class Meta:
        db_table = 'RanksAverage'
        managed = False


class RanksSingle(models.Model):
    personId = models.CharField(max_length=10, db_column='personId')
    eventId = models.CharField(max_length=6, db_column='eventId')
    best = models.IntegerField(db_column='best')
    worldRank = models.IntegerField(db_column='worldRank')
    continentRank = models.IntegerField(db_column='continentRank')
    countryRank = models.IntegerField(db_column='countryRank')

    class Meta:
        db_table = 'RanksSingle'
        managed = False


class Result(models.Model):
    competitionId = models.CharField(max_length=32, db_column='competitionId')
    eventId = models.CharField(max_length=6, db_column='eventId')
    roundTypeId = models.CharField(max_length=1, db_column='roundTypeId')
    pos = models.IntegerField(db_column='pos')
    best = models.IntegerField(db_column='best')
    average = models.IntegerField(db_column='average')
    personName = models.CharField(max_length=80, null=True, blank=True, db_column='personName')
    personId = models.CharField(max_length=10, db_column='personId')
    personCountryId = models.CharField(max_length=50, null=True, blank=True, db_column='personCountryId')
    formatId = models.CharField(max_length=1, db_column='formatId')
    value1 = models.IntegerField(db_column='value1')
    value2 = models.IntegerField(db_column='value2')
    value3 = models.IntegerField(db_column='value3')
    value4 = models.IntegerField(db_column='value4')
    value5 = models.IntegerField(db_column='value5')
    regionalSingleRecord = models.CharField(max_length=3, null=True, blank=True, db_column='regionalSingleRecord')
    regionalAverageRecord = models.CharField(max_length=3, null=True, blank=True, db_column='regionalAverageRecord')

    class Meta:
        db_table = 'Results'
        managed = False

    def to_dict(self):
        return {
            'competitionId': self.competitionId,
            'eventId': self.eventId,
            'roundTypeId': self.roundTypeId,
            'pos': self.pos,
            'best': self.best,
            'average': self.average,
            'personName': self.personName,
            'personId': self.personId,
            'personCountryId': self.personCountryId,
            'formatId': self.formatId,
            'value1': self.value1,
            'value2': self.value2,
            'value3': self.value3,
            'value4': self.value4,
            'value5': self.value5,
            'regionalSingleRecord': self.regionalSingleRecord,
            'regionalAverageRecord': self.regionalAverageRecord,
        }


class RoundTypes(models.Model):
    rank = models.IntegerField()
    name = models.CharField(max_length=50)
    cellName = models.CharField(max_length=45)
    final = models.IntegerField()

    class Meta:
        db_table = 'RoundTypes'
        managed = False


class Scramble(models.Model):
    scrambleId = models.IntegerField()
    competitionId = models.CharField(max_length=32)
    eventId = models.CharField(max_length=6)
    roundTypeId = models.CharField(max_length=1)
    groupId = models.CharField(max_length=3)
    isExtra = models.IntegerField()
    scrambleNum = models.IntegerField()
    scramble = models.CharField(max_length=500)

    class Meta:
        db_table = 'Scrambles'
        managed = False
