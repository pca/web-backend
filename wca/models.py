from django.db import models
from django.db.models.manager import BaseManager


class Continent(models.Model):
    id = models.CharField(primary_key=True, max_length=50)
    name = models.CharField(max_length=50)
    record_name = models.CharField(max_length=3, blank=True, null=True)
    latitude = models.IntegerField()
    longitude = models.IntegerField()
    zoom = models.IntegerField()


class Country(models.Model):
    id = models.CharField(primary_key=True, max_length=50)
    name = models.CharField(max_length=50)
    continent = models.ForeignKey(
        Continent,
        max_length=50,
        null=True,
        on_delete=models.DO_NOTHING,
    )
    iso2 = models.CharField(max_length=2, blank=True, null=True)


class Event(models.Model):
    id = models.CharField(primary_key=True, max_length=6)
    name = models.CharField(max_length=54)
    rank = models.IntegerField()
    format = models.CharField(max_length=10)
    cell_name = models.CharField(max_length=45)


class PersonQuerySet(models.QuerySet):
    def get(self, *args, **kwargs):
        """
        Perform the query and return a single object matching the given
        keyword arguments.
        """
        clone = self.filter(*args, **kwargs)

        if self.query.can_filter() and not self.query.distinct_fields:
            clone = clone.order_by()

        num = len(clone)

        if not num:
            raise self.model.DoesNotExist(
                "%s matching query does not exist." % self.model._meta.object_name
            )

        return clone._result_cache[num - 1]


class Person(models.Model):
    id = models.CharField(primary_key=True, max_length=10)
    subid = models.IntegerField()
    name = models.CharField(max_length=80, blank=True, null=True)
    country = models.ForeignKey(
        Country,
        max_length=50,
        null=True,
        on_delete=models.DO_NOTHING,
    )
    gender = models.CharField(max_length=1, blank=True, null=True)

    objects = BaseManager.from_queryset(PersonQuerySet)()

    class Meta:
        unique_together = (("id", "subid"),)
        base_manager_name = "objects"


class Competition(models.Model):
    id = models.CharField(primary_key=True, max_length=32)
    name = models.CharField(max_length=50)
    city_name = models.CharField(max_length=50)
    country = models.ForeignKey(
        Country,
        max_length=50,
        null=True,
        on_delete=models.DO_NOTHING,
    )
    information = models.TextField(blank=True, null=True)
    year = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField()
    day = models.PositiveSmallIntegerField()
    end_month = models.PositiveSmallIntegerField()
    end_day = models.PositiveSmallIntegerField()
    event_specs = models.CharField(max_length=256, blank=True, null=True)
    wca_delegate = models.TextField(blank=True, null=True)
    organizer = models.TextField(blank=True, null=True)
    venue = models.CharField(max_length=240, null=True)
    venue_address = models.CharField(max_length=120, blank=True, null=True)
    venue_details = models.CharField(max_length=120, blank=True, null=True)
    external_website = models.CharField(max_length=200, blank=True, null=True)
    cell_name = models.CharField(max_length=45)
    latitude = models.IntegerField(blank=True, null=True)
    longitude = models.IntegerField(blank=True, null=True)

    # Custom fields
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    events = models.ManyToManyField(Event)
    organizers = models.ManyToManyField(Person, related_name="organized_comps")
    delegates = models.ManyToManyField(Person, related_name="delegated_comps")


class Format(models.Model):
    id = models.CharField(primary_key=True, max_length=1)
    name = models.CharField(max_length=50)
    sort_by = models.CharField(max_length=255)
    sort_by_second = models.CharField(max_length=255)
    expected_solve_count = models.IntegerField()
    trim_fastest_n = models.IntegerField()
    trim_slowest_n = models.IntegerField()


class RanksAverage(models.Model):
    person = models.ForeignKey(
        Person,
        max_length=10,
        null=True,
        on_delete=models.DO_NOTHING,
    )
    event = models.ForeignKey(
        Event, max_length=6, null=True, on_delete=models.DO_NOTHING
    )
    best = models.IntegerField(null=True)
    world_rank = models.IntegerField()
    continent_rank = models.IntegerField()
    country_rank = models.IntegerField()


class RanksSingle(models.Model):
    person = models.ForeignKey(
        Person,
        max_length=10,
        null=True,
        on_delete=models.DO_NOTHING,
    )
    event = models.ForeignKey(
        Event, max_length=6, null=True, on_delete=models.DO_NOTHING
    )
    best = models.IntegerField(null=True)
    world_rank = models.IntegerField()
    continent_rank = models.IntegerField()
    country_rank = models.IntegerField()


class RoundType(models.Model):
    id = models.CharField(primary_key=True, max_length=1)
    rank = models.IntegerField()
    name = models.CharField(max_length=50)
    cell_name = models.CharField(max_length=45)
    final = models.IntegerField()


class Result(models.Model):
    competition = models.ForeignKey(
        Competition,
        max_length=32,
        null=True,
        on_delete=models.DO_NOTHING,
    )
    event = models.ForeignKey(
        Event, max_length=6, null=True, on_delete=models.DO_NOTHING
    )
    round_type = models.ForeignKey(
        RoundType,
        max_length=1,
        null=True,
        on_delete=models.DO_NOTHING,
    )
    pos = models.SmallIntegerField()
    best = models.IntegerField(db_index=True)
    average = models.IntegerField(db_index=True)
    person_name = models.CharField(max_length=80, blank=True, null=True)
    person = models.ForeignKey(
        Person,
        max_length=10,
        null=True,
        on_delete=models.DO_NOTHING,
    )
    country = models.ForeignKey(
        Country,
        max_length=50,
        blank=True,
        null=True,
        on_delete=models.DO_NOTHING,
    )
    format = models.ForeignKey(
        Format,
        max_length=1,
        null=True,
        on_delete=models.DO_NOTHING,
    )
    value1 = models.IntegerField()
    value2 = models.IntegerField()
    value3 = models.IntegerField()
    value4 = models.IntegerField()
    value5 = models.IntegerField()
    regional_single_record = models.CharField(max_length=3, blank=True, null=True)
    regional_average_record = models.CharField(max_length=3, blank=True, null=True)


class Scramble(models.Model):
    scramble_id = models.PositiveIntegerField()
    competition = models.ForeignKey(
        Competition,
        max_length=32,
        null=True,
        on_delete=models.DO_NOTHING,
    )
    event = models.ForeignKey(
        Event, max_length=6, null=True, on_delete=models.DO_NOTHING
    )
    round_type = models.ForeignKey(
        RoundType,
        max_length=1,
        null=True,
        on_delete=models.DO_NOTHING,
    )
    group_id = models.CharField(max_length=3)
    is_extra = models.IntegerField()
    scramble_num = models.IntegerField()
    scramble = models.TextField()


class Championship(models.Model):
    id = models.IntegerField(primary_key=True)
    competition = models.ForeignKey(
        Competition,
        max_length=191,
        null=True,
        on_delete=models.DO_NOTHING,
    )
    championship_type = models.CharField(max_length=191)
