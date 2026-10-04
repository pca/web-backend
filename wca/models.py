from django.db import models
from django.db.models.manager import BaseManager


class Continent(models.Model):
    id = models.CharField(primary_key=True, max_length=50)
    name = models.CharField(max_length=50)
    record_name = models.CharField(max_length=3, blank=True, null=True)
    # The WCA v2 public export no longer includes map-display coordinates.
    # Keep the fields for compatibility with existing data, but allow new
    # imports to leave them empty.
    latitude = models.IntegerField(blank=True, null=True)
    longitude = models.IntegerField(blank=True, null=True)
    zoom = models.IntegerField(blank=True, null=True)


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
    GENDER_MALE = "m"
    GENDER_FEMALE = "f"
    GENDER_CHOICES = (
        (GENDER_MALE, "Male"),
        (GENDER_FEMALE, "Female"),
    )

    id = models.CharField(primary_key=True, max_length=10)
    subid = models.IntegerField()
    name = models.CharField(max_length=80, blank=True, null=True)
    country = models.ForeignKey(
        Country,
        max_length=50,
        null=True,
        on_delete=models.DO_NOTHING,
    )
    gender = models.CharField(
        max_length=1, choices=GENDER_CHOICES, blank=True, null=True
    )

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


class BoundaryDataset(models.Model):
    """Provenance for the boundary snapshot used by regional classification."""

    version = models.CharField(max_length=80, primary_key=True)
    source_url = models.URLField(max_length=500)
    retrieved_on = models.DateField()
    coordinate_system = models.CharField(max_length=32, default="EPSG:4326")
    license = models.CharField(max_length=240)
    attribution = models.CharField(max_length=500, blank=True)
    processing_notes = models.TextField()
    checksum_sha256 = models.CharField(max_length=64, db_index=True)
    feature_count = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)


class CompetitionRegionAssignment(models.Model):
    STATUS_ASSIGNED = "assigned"
    STATUS_MISSING_COORDINATES = "missing_coordinates"
    STATUS_INVALID_COORDINATES = "invalid_coordinates"
    STATUS_OUTSIDE_BOUNDARY = "outside_boundary"
    STATUS_BOUNDARY = "boundary"
    STATUS_OVERLAPPING_REGIONS = "overlapping_regions"
    STATUS_CHOICES = (
        (STATUS_ASSIGNED, "Assigned"),
        (STATUS_MISSING_COORDINATES, "Missing coordinates"),
        (STATUS_INVALID_COORDINATES, "Invalid coordinates"),
        (STATUS_OUTSIDE_BOUNDARY, "Outside boundary"),
        (STATUS_BOUNDARY, "On boundary"),
        (STATUS_OVERLAPPING_REGIONS, "Overlapping regions"),
    )

    competition = models.OneToOneField(
        Competition,
        related_name="region_assignment",
        on_delete=models.CASCADE,
    )
    boundary_dataset = models.ForeignKey(
        BoundaryDataset,
        related_name="competition_assignments",
        on_delete=models.PROTECT,
    )
    region_code = models.CharField(max_length=2, blank=True, null=True, db_index=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, db_index=True)
    classified_latitude = models.IntegerField(blank=True, null=True)
    classified_longitude = models.IntegerField(blank=True, null=True)
    classified_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(
                fields=("boundary_dataset", "status"),
                name="wca_assign_dataset_status_idx",
            ),
            models.Index(
                fields=("boundary_dataset", "region_code"),
                name="wca_assign_dataset_region_idx",
            ),
        ]


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

    class Meta:
        indexes = [
            models.Index(
                fields=("event", "country_rank", "person"),
                name="wca_rankavg_event_rank_idx",
            )
        ]


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

    class Meta:
        indexes = [
            models.Index(
                fields=("event", "country_rank", "person"),
                name="wca_ranksingle_event_rank_idx",
            )
        ]


class RoundType(models.Model):
    id = models.CharField(primary_key=True, max_length=1)
    rank = models.IntegerField()
    name = models.CharField(max_length=50)
    cell_name = models.CharField(max_length=45)
    final = models.IntegerField()


class Result(models.Model):
    # Stable identifier introduced by the WCA v2 export.  It lets the importer
    # join the separate result_attempts file without keeping every attempt in
    # memory.  Null remains allowed for rows imported before v2.
    wca_result_id = models.PositiveBigIntegerField(
        blank=True,
        null=True,
        unique=True,
    )
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

    class Meta:
        indexes = [
            models.Index(
                fields=("person", "competition"),
                name="wca_result_person_comp_idx",
            ),
            models.Index(
                fields=("competition", "event", "person"),
                name="wca_result_comp_event_person",
            ),
            models.Index(
                fields=("person", "event", "country", "best", "id"),
                name="wca_res_person_evt_best_idx",
            ),
            models.Index(
                fields=("event", "country", "best", "person"),
                name="wca_res_evt_ctry_best_person",
            ),
            models.Index(
                fields=("person", "event", "country", "average", "id"),
                name="wca_res_person_evt_avg_idx",
            ),
            models.Index(
                fields=("event", "country", "average", "person"),
                name="wca_res_evt_ctry_avg_person",
            ),
        ]


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
