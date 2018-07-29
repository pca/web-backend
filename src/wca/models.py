"""
WCA database export mapped in Django ORM.
"""
from django.db import models


class Competition(models.Model):
    name = models.CharField(max_length=50, db_column='name')
    city_name = models.CharField(max_length=50, db_column='cityName')
    country_id = models.CharField(max_length=50, db_column='countryId')
    information = models.TextField(null=True, blank=True, db_column='information')
    year = models.IntegerField(db_column='year')
    month = models.IntegerField(db_column='month')
    day = models.IntegerField(db_column='day')
    end_month = models.IntegerField(db_column='endMonth')
    end_day = models.IntegerField(db_column='endDay')
    event_specs = models.CharField(max_length=256, null=True, blank=True, db_column='eventSpecs')
    wca_delegate = models.TextField(null=True, blank=True, db_column='wcaDelegate')
    organiser = models.TextField(null=True, blank=True, db_column='organiser')
    venue = models.CharField(max_length=240, db_column='venue')
    venue_address = models.CharField(max_length=120, null=True, blank=True, db_column='venueAddress')
    venue_details = models.CharField(max_length=120, null=True, blank=True, db_column='venueDetails')
    external_website = models.CharField(max_length=200, null=True, blank=True, db_column='external_website')
    cell_name = models.CharField(max_length=45, db_column='cellName')
    latitude = models.IntegerField(null=True, blank=True, db_column='latitude')
    longitude = models.IntegerField(null=True, blank=True, db_column='longitude')

    class Meta:
        db_table = 'Competitions'
        managed = False


class Continent(models.Model):
    name = models.CharField(max_length=50, db_column='name')
    record_name = models.CharField(max_length=3, db_column='recordName')
    latitude = models.IntegerField(db_column='latitude')
    longitude = models.IntegerField(db_column='longitude')
    zoom = models.IntegerField(db_column='zoom')

    class Meta:
        db_table = 'Continents'
        managed = False


class Country(models.Model):
    name = models.CharField(max_length=50, db_column='name')
    continent_id = models.CharField(max_length=50, db_column='continentId')
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
    cell_name = models.CharField(max_length=45, db_column='cellName')

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
    country_id = models.CharField(max_length=50, db_column='countryId')
    gender = models.CharField(max_length=1, db_column='gender')

    class Meta:
        db_table = 'Persons'
        managed = False


class RanksAverage(models.Model):
    person_id = models.CharField(max_length=10, db_column='personId')
    event_id = models.CharField(max_length=6, db_column='eventId')
    best = models.IntegerField(db_column='best')
    world_rank = models.IntegerField(db_column='worldRank')
    continent_rank = models.IntegerField(db_column='continentRank')
    country_rank = models.IntegerField(db_column='countryRank')

    class Meta:
        db_table = 'RanksAverage'
        managed = False


class RanksSingle(models.Model):
    person_id = models.CharField(max_length=10, db_column='personId')
    event_id = models.CharField(max_length=6, db_column='eventId')
    best = models.IntegerField(db_column='best')
    world_rank = models.IntegerField(db_column='worldRank')
    continent_rank = models.IntegerField(db_column='continentRank')
    country_rank = models.IntegerField(db_column='countryRank')

    class Meta:
        db_table = 'RanksSingle'
        managed = False


class Result(models.Model):
    competition_id = models.CharField(max_length=32, db_column='competitionId')
    event_id = models.CharField(max_length=6, db_column='eventId')
    round_type_id = models.CharField(max_length=1, db_column='roundTypeId')
    pos = models.IntegerField(db_column='pos')
    best = models.IntegerField(db_column='best')
    average = models.IntegerField(db_column='average')
    person_name = models.CharField(max_length=80, null=True, blank=True, db_column='personName')
    person_id = models.CharField(max_length=10, db_column='personId')
    person_country_id = models.CharField(max_length=50, null=True, blank=True, db_column='personCountryId')
    format_id = models.CharField(max_length=1, db_column='formatId')
    value1 = models.IntegerField(db_column='value1')
    value2 = models.IntegerField(db_column='value2')
    value3 = models.IntegerField(db_column='value3')
    value4 = models.IntegerField(db_column='value4')
    value5 = models.IntegerField(db_column='value5')
    regional_single_record = models.CharField(max_length=3, null=True, blank=True, db_column='regionalSingleRecord')
    regional_average_record = models.CharField(max_length=3, null=True, blank=True, db_column='regionalAverageRecord')

    class Meta:
        db_table = 'Results'
        managed = False

    @classmethod
    def format_time(cls, time):
        defaults = {
            -1: 'DNF',
            -2: 'DNS',
        }

        time = int(time)  # Ensure data type

        if time > 0:
            ms = time % 100
            seconds = int(((time - ms) % 6000) / 100)
            minutes = int((time - (seconds * 100) - ms) / 6000)

            # Add 0 padding on the left if ms is 1 digit
            ms = '{:0>2}'.format(ms)

            if minutes:
                # Add 0 padding on the left  if seconds is 1 digit
                seconds = '{:0>2}'.format(seconds)

                return '{}:{}.{}'.format(minutes, seconds, ms)
            return '{}.{}'.format(seconds, ms)

        return defaults.get(time, 'ERR')

    def to_dict(self, rank_type):
        time = getattr(self, rank_type)
        time = Result.format_time(time)
        return {
            'competition_id': self.competition_id,
            'event': self.event_id,
            'time': time,
            'name': self.person_name,
            'wca_id': self.person_id,
        }


class RoundTypes(models.Model):
    rank = models.IntegerField()
    name = models.CharField(max_length=50)
    cell_name = models.CharField(max_length=45)
    final = models.IntegerField()

    class Meta:
        db_table = 'RoundTypes'
        managed = False


class Scramble(models.Model):
    scramble_id = models.IntegerField()
    competition_id = models.CharField(max_length=32)
    event_id = models.CharField(max_length=6)
    round_type_id = models.CharField(max_length=1)
    group_id = models.CharField(max_length=3)
    is_extra = models.IntegerField()
    scramble_num = models.IntegerField()
    scramble = models.CharField(max_length=500)

    class Meta:
        db_table = 'Scrambles'
        managed = False
