import json
import redis

from django.conf import settings
from django.db.models import Q

from wca.models import Result
from web.models import WCAProfile

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


def get_rankings(event_type='333', rank_type='best', area='national', area_filter=None, num=10):
    """
    Returns the top `num` records.
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
    key = '{}{}{}{}{}'.format(event_type, rank_type, area, area_filter, num)
    top_results_in_string = r.get(key)

    if top_results_in_string:
        return json.loads(top_results_in_string)

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

    results = Result.objects.filter(
        gt_query[rank_type],
        area_query
    ).order_by(rank_type)

    # Filter results by top ten and without repeating
    # person (Only the best record for 1 person)
    top_results = []
    personsIds = []

    for result in results:
        if len(top_results) == num:
            break
        if result.personId not in personsIds:
            personsIds.append(result.personId)
            top_results.append(result.to_dict())

    # Cache result
    top_results_in_string = json.dumps(top_results)
    r.set(key, top_results_in_string)

    return top_results
