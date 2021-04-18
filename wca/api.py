from django.contrib.auth import get_user_model
from django.db.models import Count, Q

from . import utils
from .models import Event, Person, RanksAverage, RanksSingle, Result

User = get_user_model()


def get_avatar(person: Person) -> dict:
    user = User.objects.filter(wca_id=person.id).first()
    if user:
        return user.socialaccount.extra_data.get("avatar")


def get_competition_count(person: Person) -> int:
    return Result.objects.filter(person=person).distinct("competition").count()


def get_solve_count(person: Person) -> int:
    annotations = dict(
        solves1=Count("result", filter=Q(result__value1__gt=0)),
        solves2=Count("result", filter=Q(result__value2__gt=0)),
        solves3=Count("result", filter=Q(result__value3__gt=0)),
        solves4=Count("result", filter=Q(result__value4__gt=0)),
        solves5=Count("result", filter=Q(result__value5__gt=0)),
    )
    person = Person.objects.filter(id=person.id).annotate(**annotations).first()
    return sum(
        [person.solves1, person.solves2, person.solves3, person.solves4, person.solves5]
    )


def _get_ranks_result(rank, rank_type):
    return {
        "best": utils.parse_value(rank.best, rank.event.format, rank_type=rank_type),
        "world_rank": rank.world_rank,
        "continent_rank": rank.continent_rank,
        "country_rank": rank.country_rank,
    }


def get_personal_records(person: Person) -> list:
    records = []
    events = Event.objects.order_by("rank")
    for event in events:
        single = RanksSingle.objects.filter(person=person, event=event).first()
        average = RanksAverage.objects.filter(person=person, event=event).first()
        event_record = {}
        if single:
            event_record["single"] = _get_ranks_result(single, rank_type="single")
        if average:
            event_record["average"] = _get_ranks_result(average, rank_type="average")
        if event_record:
            event_record["event"] = event.id
            records.append(event_record)
    return records


def get_records(person: Person) -> dict:
    annotations = dict(
        nr_single=Count("result", filter=Q(result__regional_single_record="NR")),
        nr_average=Count("result", filter=Q(result__regional_average_record="NR")),
        wr_single=Count("result", filter=Q(result__regional_single_record="WR")),
        wr_average=Count("result", filter=Q(result__regional_average_record="WR")),
        continent_single=Count(
            "result",
            filter=Q(
                ~Q(result__regional_single_record=None),
                ~Q(result__regional_single_record__in=["NR", "WR"]),
            ),
        ),
        continent_average=Count(
            "result",
            filter=Q(
                ~Q(result__regional_average_record=None),
                ~Q(result__regional_average_record__in=["NR", "WR"]),
            ),
        ),
    )
    person = Person.objects.filter(id=person.id).annotate(**annotations).first()
    national = person.nr_single + person.nr_average
    world = person.wr_single + person.wr_average
    continent = person.continent_single + person.continent_average
    return {
        "national": national,
        "continental": continent,
        "world": world,
        "total": national + continent + world,
    }


def get_medals(person: Person) -> dict:
    finals = dict(result__round_type__final=1, result__best__gt=0)
    annotations = dict(
        gold=Count("result", filter=Q(**finals, result__pos=1)),
        silver=Count("result", filter=Q(**finals, result__pos=2)),
        bronze=Count("result", filter=Q(**finals, result__pos=3)),
    )
    person = Person.objects.filter(id=person.id).annotate(**annotations).first()
    return {
        "gold": person.gold,
        "silver": person.silver,
        "bronze": person.bronze,
        "total": person.gold + person.silver + person.bronze,
    }
