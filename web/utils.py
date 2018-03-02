import json
import redis

import django_rq as q
from django.conf import settings
from django.db.models import Q

from wca.models import Result
from web.models import WCAProfile
from web.constants import EVENTS

r = redis.StrictRedis(host='redis', port=6379, db=0)


def wca_authorize_uri():
    authorize_uri = settings.WCA_OAUTH_URI + 'authorize/'
    authorize_uri += '?client_id=' + settings.WCA_CLIENT_ID
    authorize_uri += '&redirect_uri=' + settings.WCA_CALLBACK
    authorize_uri += '&response_type=code&scope='
    return authorize_uri


def wca_access_token_uri(code):
    access_token_uri = settings.WCA_OAUTH_URI + 'token/'
    access_token_uri += '?client_id=' + settings.WCA_CLIENT_ID
    access_token_uri += '&client_secret=' + settings.WCA_CLIENT_SECRET
    access_token_uri += '&redirect_uri=' + settings.WCA_CALLBACK
    access_token_uri += '&code=' + code
    access_token_uri += '&grant_type=authorization_code'
    return access_token_uri


def get_all_rankings(area='regional', area_filter=None):
    all_rankings = {}
    for event in EVENTS:
        best_rankings = get_rankings(event_type=event, rank_type='best', area=area, area_filter=area_filter)
        average_rankings = get_rankings(event_type=event, rank_type='average', area=area, area_filter=area_filter)
        all_rankings['single_{}'.format(event)] = best_rankings
        all_rankings['average_{}'.format(event)] = average_rankings
    return all_rankings


def get_rankings(event_type='333', rank_type='best', area='national', area_filter=None, limit=10):
    """
    Returns the top `limit` records.
    rank_type can be 'best' or 'average'.
    area can be `national`, `regional`, or `cityprovincial'.
    area_filter are choice valies defined in web.constants
    event_type can be:
    - 222 (2x2x2 Cube)
    - 333 (Rubik's Cube)
    - 333bf (3x3x3 Blindfolded)
    - 333fm (3x3x3 Fewest Moves)
    - 333ft (3x3x3 With Feet)
    - 333mbf (3x3x3 Multi-Blind)
    - 333mbo (Rubik's Cube: Multi blind old style)
    - 333oh (3x3x3 One-Handed)
    - 444 (4x4x4 Cube)
    - 444bf (4x4x4 Blindfolded)
    - 555 (5x5x5 Cube)
    - 555bf (5x5x5 Blindfolded)
    - 666 (6x6x6 Cube)
    - 777 (7x7x7 Cube)
    - clock (Rubik's Clock)
    - magic (Rubik's Magic)
    - minx (Megaminx)
    - mmagic (Master Magic)
    - pyram (Pyraminx)
    - skewb (Skewb)
    - sq1 (Square-1)
    """

    # Try to fetch result from cache
    key = '{}{}{}{}{}'.format(event_type, rank_type, area, area_filter, limit)
    top_results_in_string = r.get(key)

    if top_results_in_string:
        return json.loads(top_results_in_string)

    results = query_records(
        event_type=event_type,
        rank_type=rank_type,
        area=area,
        area_filter=area_filter,
    )
    top_results = limit_records(results, limit=limit)

    # Cache result
    top_results_in_string = json.dumps(top_results)
    r.set(key, top_results_in_string)

    return top_results


def query_records(event_type='333', rank_type='best', area='national', area_filter=None):
    # Get results
    gt_query = {
        'best': Q(best__gt=0),
        'average': Q(average__gt=0),
    }

    # Default query for national rankings
    area_query = Q(
        personCountryId='Philippines',
        eventId=event_type,
    )

    if area == 'regional':
        profiles = WCAProfile.objects.filter(user__pcaprofile__region=area_filter)
        wca_ids = [p.wca_id for p in profiles if p.wca_id]  # Get WCA IDs of registered profiles
        area_query &= Q(personId__in=wca_ids)
    elif area == 'cityprovincial':
        profiles = WCAProfile.objects.filter(user__pcaprofile__city_province=area_filter)
        wca_ids = [p.wca_id for p in profiles if p.wca_id]  # Get WCA IDs of registered profiles
        area_query &= Q(personId__in=wca_ids)

    return Result.objects.filter(
        gt_query[rank_type],
        area_query
    ).order_by(rank_type)


def limit_records(records, limit=10):
    # Limit results by top `limit` and without repeating
    # person (Only the best record for 1 person)
    top_results = []
    personsIds = []

    for result in records:
        if len(top_results) == limit:
            break
        if result.personId not in personsIds:
            personsIds.append(result.personId)
            top_results.append(result.to_dict())

    return top_results


def recompute_rankings(area='national', area_filter=None, limit=10):
    for event in EVENTS:
        # Singles
        single_records = query_records(event_type=event, rank_type='best', area=area, area_filter=area_filter)
        single_records = limit_records(single_records, limit=limit)
        key = '{}{}{}{}{}'.format(event, 'best', area, area_filter, limit)
        r.set(key, json.dumps(single_records))
        # Average
        average_records = query_records(event_type=event, rank_type='average', area=area, area_filter=area_filter)
        average_records = limit_records(average_records, limit=limit)
        key = '{}{}{}{}{}'.format(event, 'average', area, area_filter, limit)
        r.set(key, json.dumps(average_records))


def enqueue_ranking_computation(area='national', area_filter=None, limit=10):
    q.enqueue(recompute_rankings, area, area_filter, limit)
