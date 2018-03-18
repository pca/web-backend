import json
import requests
import shutil
import subprocess
import zipfile

import django_rq as q
import redis
from django.conf import settings
from django.db.models import Q

from wca.models import Result
from web.models import WCAProfile, DatabaseConfig
from web.constants import EVENTS

r = redis.StrictRedis.from_url(settings.REDIS_URL)


class WCAClient:
    """
    A class wrapper for WCA-related operations.
    """
    events = [
        '222',  # (2x2x2 Cube)
        '333',  # (Rubik's Cube)
        '333bf',  # (3x3x3 Blindfolded)
        '333fm',  # (3x3x3 Fewest Moves)
        '333ft',  # (3x3x3 With Feet)
        '333mbf',  # (3x3x3 Multi-Blind)
        '333mbo',  # (Rubik's Cube: Multi blind old style)
        '333oh',  # (3x3x3 One-Handed)
        '444',  # (4x4x4 Cube)
        '444bf',  # (4x4x4 Blindfolded)
        '555',  # (5x5x5 Cube)
        '555bf',  # (5x5x5 Blindfolded)
        '666',  # (6x6x6 Cube)
        '777',  # (7x7x7 Cube)
        'clock',  # (Rubik's Clock)
        'magic',  # (Rubik's Magic)
        'minx',  # (Megaminx)
        'mmagic',  # (Master Magic)
        'pyram',  # (Pyraminx)
        'skewb',  # (Skewb)
        'sq1',  # (Square-1)
    ]

    def wca_authorize_uri(self, host):
        redirect_uri = 'http://{}{}'.format(host, settings.WCA_CALLBACK_PATH)
        authorize_uri = (
            '{}authorize/'.format(settings.WCA_OAUTH_URI) +
            '?client_id={}'.format(settings.WCA_CLIENT_ID) +
            '&redirect_uri={}'.format(redirect_uri) +
            '&response_type=code=&scope='
        )
        return authorize_uri

    def wca_access_token_uri(self, host, code):
        redirect_uri = 'http://{}{}'.format(host, settings.WCA_CALLBACK_PATH)
        access_token_uri = (
            '{}token/'.format(settings.WCA_OAUTH_URI) +
            '?client_id={}'.format(settings.WCA_CLIENT_ID) +
            '&client_secret={}'.format(settings.WCA_CLIENT_SECRET) +
            '&redirect_uri={}'.format(redirect_uri) +
            '&code={}'.format(code) +
            '&grant_type=authorization_code'
        )
        return access_token_uri

    def rankings(self, event_type='333', rank_type='best', area='national', area_filter=None, limit=10):
        # Try to fetch result from cache
        key = '{}{}{}{}{}'.format(event_type, rank_type, area, area_filter, limit)
        top_results_in_string = r.get(key)

        if top_results_in_string:
            return json.loads(top_results_in_string)

        results = self._query_records(
            event_type=event_type,
            rank_type=rank_type,
            area=area,
            area_filter=area_filter,
        )
        top_results = self._sanitize_results(results, limit=limit)

        # Cache result
        top_results_in_string = json.dumps(top_results)
        r.set(key, top_results_in_string)

        return top_results

    def _query_records(self, event_type='333', rank_type='best', area='national', area_filter=None):
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

        # Fetch from the active wca database
        active_db = self.get_db_config()['active']
        return Result.objects.using(active_db).filter(
            gt_query[rank_type],
            area_query
        ).order_by(rank_type)

    def _sanitize_results(self, records, limit=10):
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

    def _get_db_config(self):
        db_config = r.get('db_config')
        if not db_config:
            db_config = DatabaseConfig.db().to_dict()
            r.set('db_config', json.dumps(db_config))
            return db_config
        return json.loads(db_config)

    def recompute_rankings(self, area='national', area_filter=None, limit=10):
        for event in EVENTS:
            # Singles
            single_records = self._query_records(event_type=event, rank_type='best', area=area, area_filter=area_filter)
            single_records = self._sanitize_results(single_records, limit=limit)
            key = '{}{}{}{}{}'.format(event, 'best', area, area_filter, limit)
            r.set(key, json.dumps(single_records))
            # Average
            average_records = self._query_records(event_type=event, rank_type='average', area=area, area_filter=area_filter)
            average_records = self._sanitize_results(average_records, limit=limit)
            key = '{}{}{}{}{}'.format(event, 'average', area, area_filter, limit)
            r.set(key, json.dumps(average_records))

    def enqueue_ranking_computation(self, area='national', area_filter=None, limit=10):
        q.enqueue(self.recompute_rankings, area, area_filter, limit)

    def sync_wca_database(self):
        # TODO: Schedule this method every 1am
        data_location = 'data/'
        zip_location = data_location + 'WCA_export.sql.zip'
        sql_location = data_location + 'WCA_export.sql'

        # Download the latest database dump
        r = requests.get(settings.WCA_EXPORT_URL, stream=True)
        with open(zip_location, 'wb') as f:
            shutil.copyfileobj(r.raw, f)

        # Extract zip file
        zip_ref = zipfile.ZipFile(zip_location, 'r')
        zip_ref.extractall(data_location)
        zip_ref.close()

        # Import the database dump to the inactive table
        db_config = self.get_db_config()
        db_django_config = settings.DATABASES[db_config['inactive']]
        proc = subprocess.Popen(
            [
                'mysql',
                '-u', db_django_config['USER'],
                '--password={}'.format(db_django_config['PASSWORD']),
                '-h', db_django_config['HOST'],
                db_config['inactive'],
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            encoding='utf8',
        )
        f = open(sql_location, 'r')
        out, err = proc.communicate(f.read())

        # TODO: Create missing primary key (id) on Results table

        # Update database config
        db = DatabaseConfig.db()
        db.active_database = db_config['inactive']
        db.inactive_database = db_config['active']
        db.save()

        # Delete cached database config
        r.delete('db_config')
