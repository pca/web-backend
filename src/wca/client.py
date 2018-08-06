import json
import requests
import shutil
import subprocess
import zipfile

import django_rq as q
import redis
from django.conf import settings
from django.db import connections
from django.db.models import Q

from wca.models import Result
from pca.models import WCAProfile, DatabaseConfig


class WCAClient:
    """
    A class wrapper for WCA-related operations.

    Event glossary:
        bf - Blindfolded
        fm - Fewest Moves
        ft - With Feet
        mbf - Multi-Blind
        mbo - Multi-Blind old style
        oh - One-Handed
        minx - Megaminx
        magic - Rubik's Magic
        mmagic - Master Magic
    """
    events = [
        '222', '333', '333bf', '333fm', '333ft', '333mbf', '333mbo',
        '333oh', '444', '444bf', '555', '555bf', '666', '777', 'clock',
        'magic', 'minx', 'mmagic', 'pyram', 'skewb', 'sq1',
    ]

    def __init__(self):
        self.redis_client = redis.StrictRedis.from_url(settings.REDIS_URL)

    def authorize_uri(self):
        """
        Returns the WCA authorize URI.
        """
        authorize_uri = (
            '{}authorize/'.format(settings.WCA_OAUTH_URI) +
            '?client_id={}'.format(settings.WCA_CLIENT_ID) +
            '&redirect_uri={}'.format(settings.WCA_REDIRECT_URI) +
            '&response_type=code&scope='
        )
        return authorize_uri

    def access_token_uri(self, code):
        """
        Returns the WCA access token URI.
        """
        access_token_uri = (
            '{}token/'.format(settings.WCA_OAUTH_URI) +
            '?client_id={}'.format(settings.WCA_CLIENT_ID) +
            '&client_secret={}'.format(settings.WCA_CLIENT_SECRET) +
            '&redirect_uri={}'.format(settings.WCA_REDIRECT_URI) +
            '&code={}'.format(code) +
            '&grant_type=authorization_code'
        )
        return access_token_uri

    def get_profile(self, code):
        access_token_uri = self.access_token_uri(code)
        response = requests.post(access_token_uri)
        access_token = response.json().get('access_token')

        response = requests.get(settings.WCA_API_URI + 'me', headers={
            'Authorization': 'Bearer {}'.format(access_token),
        })
        profile = response.json()
        return profile.get('me')

    def competitions(self):
        """
        Returns the list of all competitions in the Philippines.
        """
        # Try to fetch data from cache
        competitions = self.redis_client.get('competitions')

        if competitions:
            return json.loads(competitions)

        # Fetch competitions from the WCA API
        response = requests.get('https://www.worldcubeassociation.org/api/v0/search/competitions?q=philippines')
        competitions = response.json()['result']

        # Cache the result for 10 minutes (600 seconds)
        self.redis_client.set('competitions', json.dumps(competitions), 600)

        return competitions

    def all_rankings(self, level, query=None, limit=10):
        """
        Returns ranking list of all available events.

        Args:
            level: Level can be `national`, `regional`, or `cityprovincial`
            query: Can be a region code or cityprovincial code
            limit: The number of results
        """
        all_rankings = {}

        for event in self.events:
            best_rankings = self.rankings(event, 'best', level, query=query, limit=limit)
            average_rankings = self.rankings(event, 'average', level, query=query, limit=limit)
            all_rankings['single_{}'.format(event)] = best_rankings
            all_rankings['average_{}'.format(event)] = average_rankings

        return all_rankings

    def rankings(self, event, rank_type, level, query=None, limit=10):
        """
        Lists the top `limit` records/rankings of a specific `event`,
        `rank_type`. and rank `level`.

        Args:
            event: The type of event to rank
            rank_type: Rank type can be either be `best` (single) or `average`
            level: Level can be `national`, `regional`, or `cityprovincial`
            query: Can be a region code or cityprovincial code
            limit: The number of results
        """
        # Try to fetch result from cache
        key = '{}{}{}{}{}'.format(event, rank_type, level, query, limit)
        top_results_in_string = self.redis_client.get(key)

        if top_results_in_string:
            return json.loads(top_results_in_string)

        results = self._query_records(event, rank_type, level, query=query)
        top_results = self._sanitize_results(results, rank_type, limit=limit)

        # Cache result
        top_results_in_string = json.dumps(top_results)
        self.redis_client.set(key, top_results_in_string)

        return top_results

    def recompute_rankings(self, level, query=None, limit=10):
        """
        Enqueues a recomputation job as the queries from the live and
        active databases are long and resource-intensive.
        """
        q.enqueue(self._recompute_rankings_job, level, query=query, limit=limit)

    def _get_db_config(self):
        """
        Returns the latest WCA database configuration.
        """
        db_config = self.redis_client.get('db_config')

        if not db_config:
            db_config = DatabaseConfig.db().to_dict()
            self.redis_client.set('db_config', json.dumps(db_config))
            return db_config

        return json.loads(db_config)

    def _query_records(self, event, rank_type, level, query=None):
        """
        Fetch the records/rankings of a specific `event`, `rank_type`,
        and rank `level` from the live and active WCA and PCA database.

        Args:
            event: The type of event to rank
            rank_type: Rank type can be either be `best` (single) or `average`
            level: Level can be `national`, `regional`, or `cityprovincial`
            query: Can be a region code or cityprovincial code
        """
        # Default query for national rankings
        db_query = Q(person_country_id='Philippines', event_id=event)

        if level != 'national':
            # Additional query for non-national rankings
            profile_query_options = {
                'regional': Q(user__pcaprofile__region=query),
                'cityprovincial': Q(user__pcaprofile__city_province=query),
            }
            profiles = WCAProfile.objects.filter(profile_query_options[level])
            # Prepare WCA IDs of registered profiles
            wca_ids = [p.wca_id for p in profiles if p.wca_id]
            db_query &= Q(person_id__in=wca_ids)

        # Additional query for the rank/result type
        rank_type_query_options = {
            'best': Q(best__gt=0),
            'average': Q(average__gt=0),
        }
        db_query &= rank_type_query_options[rank_type]

        # Fetch from the active wca database
        active_db = self._get_db_config()['active']
        return Result.objects.using(active_db).filter(db_query).order_by(rank_type)

    def _sanitize_results(self, records, rank_type, limit=10):
        """
        Limit results by top `limit` and without repeating
        person (Only the best record for 1 person).

        Args:
            records: The QuerySet queried from the database
            rank_type: Rank type can be either be `best` (single) or `average`
            limit: The number of results
        """
        top_results = []
        persons_ids = []
        rank_order = 1

        for result in records:
            if len(top_results) == limit:
                break

            if result.person_id not in persons_ids:
                persons_ids.append(result.person_id)
                data = result.to_dict(rank_type)
                data['rank'] = rank_order
                rank_order += 1
                top_results.append(data)

        return top_results

    def _recompute_rankings_job(self, level, query=None, limit=10):
        """
        Recomputes all the rankings by querying the live and active
        databases and storing it in the cache.

        Args:
            level: Level can be `national`, `regional`, or `cityprovincial`
            query: Can be a region code or cityprovincial code
            limit: The number of results
        """
        for event in self.events:
            # Singles
            single_records = self._query_records(event, 'best', level, query=query)
            single_records = self._sanitize_results(single_records, 'best', limit=limit)
            key = '{}{}{}{}{}'.format(event, 'best', level, query, limit)
            self.redis_client.set(key, json.dumps(single_records))

            # Average
            average_records = self._query_records(event, 'average', level, query=query)
            average_records = self._sanitize_results(average_records, 'average', limit=limit)
            key = '{}{}{}{}{}'.format(event, 'average', level, query, limit)
            self.redis_client.set(key, json.dumps(average_records))

    def _get_inactive_connection(self):
        db_config = self._get_db_config()
        return connections[db_config['inactive']]

    def _download_wca_dump(self):
        zip_location = '/data/WCA_export.sql.zip'

        response = requests.get(settings.WCA_EXPORT_URL, stream=True)
        with open(zip_location, 'wb') as f:
            shutil.copyfileobj(response.raw, f)

        # Extract zip file
        with zipfile.ZipFile(zip_location, 'r') as zip_ref:
            zip_ref.extractall('/data/')

    def _import_wca_dump(self, test=False):
        # Import the database dump to the inactive table
        connection = self._get_inactive_connection()
        db_django_config = connection.settings_dict
        sql_location = '/data/WCA_export.sql'

        if test:
            sql_location = '/data/WCA_lite.sql'

        proc = subprocess.Popen(
            [
                'mysql',
                '-u', db_django_config['USER'],
                '--password={}'.format(db_django_config['PASSWORD']),
                '-h', db_django_config['HOST'],
                db_django_config['NAME'],
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            encoding='utf8',
        )
        f = open(sql_location, 'r')
        out, err = proc.communicate(f.read())

    def _switch_wca_database(self):
        db_config = self._get_db_config()
        db = DatabaseConfig.db()
        db.active_database = db_config['inactive']
        db.inactive_database = db_config['active']
        db.save()

        return db.active_database

    def sync_wca_database(self, download_latest=True, test=False):
        """
        Downloads the latest WCA database dump, imports it in the
        inactive wca database, switches the wca databases after the import.
        Switching means replacing the active database with the inactive one
        and vice versa.
        """
        # TODO: Schedule this method every 1am
        connection = self._get_inactive_connection()

        if download_latest and not test:
            self._download_wca_dump()

        self._import_wca_dump(test=test)

        # Create missing primary key (id) on Results table
        if not test:
            with connection.cursor() as cursor:
                cursor.execute('ALTER TABLE Results ADD COLUMN `id` int(10) UNSIGNED PRIMARY KEY AUTO_INCREMENT')

        self._switch_wca_database()

        # Delete cached database config
        self.redis_client.delete('db_config')


wca_client = WCAClient()
