import json
import requests
import subprocess
from datetime import datetime

import django_rq as q
import redis
from django.conf import settings
from django.db import connections
from django.db.models import Q

from wca.models import Result
from wca.scrapers import scrape_competition
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

    def get_competition_data(self):
        # Try to fetch data from cache
        competitions = self.redis_client.get('competitions')

        if competitions:
            competitions = json.loads(competitions)
        else:
            # Fetch competitions from the WCA API
            response = requests.get('https://www.worldcubeassociation.org/api/v0/search/competitions?q=philippines')
            competitions = response.json()['result']

        # Try to fetch additional data from cache
        additional_competitions_data = self.redis_client.get('additional_competitions_data')

        if additional_competitions_data:
            additional_competitions_data = json.loads(additional_competitions_data)
            has_new_entry = False

            for competition in competitions:
                if competition['id'] not in additional_competitions_data.keys():
                    data = scrape_competition(competition['url'])
                    competition['additional_data'] = data
                    additional_competitions_data[competition['id']] = data
                    has_new_entry = True

            if has_new_entry:
                self.redis_client.set(
                    'additional_competitions_data',
                    json.dumps(additional_competitions_data),
                )
        else:
            additional_competitions_data = {}

            for competition in competitions:
                data = scrape_competition(competition['url'])
                competition['additional_data'] = data
                additional_competitions_data[competition['id']] = data

            self.redis_client.set(
                'additional_competitions_data',
                json.dumps(additional_competitions_data),
            )

        return competitions

    def competitions(self):
        """
        Returns the list of all competitions in the Philippines.
        """
        competitions = self.get_competition_data()

        # Cache the result for 10 minutes (600 seconds)
        self.redis_client.set('competitions', json.dumps(competitions), 600)

        return competitions

    def upcoming_competitions(self):
        """
        Returns the list of upcoming competitions in the Philippines.
        """
        competitions = self.competitions()
        upcoming_competitions = []

        # Filter upcoming competitions
        for competition in competitions:
            start_date = datetime.strptime(competition['start_date'], '%Y-%m-%d')

            if start_date > datetime.today():
                end_date = datetime.strptime(competition['end_date'], '%Y-%m-%d')
                competition['start_date'] = start_date.strftime('%B %d, %Y')
                competition['end_date'] = end_date.strftime('%B %d, %Y')
                upcoming_competitions.insert(0, competition)

        return upcoming_competitions

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
        q.enqueue(recompute_rankings_job, level, query=query, limit=limit)

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

    def _get_inactive_connection(self):
        db_config = self._get_db_config()
        return connections[db_config['inactive']]

    def _import_wca_test_dump(self, test=False):
        # Import the database dump to the inactive table
        connection = self._get_inactive_connection()
        db_django_config = connection.settings_dict
        sql_location = '/app/data/WCA_lite.sql'

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

    def import_wca_test_database(self):
        """
        Imports the WCA_lite test database dump.
        Note: Should only be used in test cases using test databases.
        """
        # connection = self._get_inactive_connection()

        self._import_wca_test_dump()

        # Create missing primary key (id) on Results table
        # XXX: Temporarily not needed as the test dump already contains `id` column
        # with connection.cursor() as cursor:
        #     cursor.execute('ALTER TABLE Results ADD COLUMN `id` int(10) UNSIGNED PRIMARY KEY AUTO_INCREMENT')

        self._switch_wca_database()

        # Delete cached database config
        self.redis_client.delete('db_config')


wca_client = WCAClient()


def recompute_rankings_job(level, query=None, limit=10):
    """
    Recomputes all the rankings by querying the live and active
    databases and storing it in the cache.

    Args:
        level: Level can be `national`, `regional`, or `cityprovincial`
        query: Can be a region code or cityprovincial code
        limit: The number of results
    """
    for event in wca_client.events:
        # Singles
        single_records = wca_client._query_records(event, 'best', level, query=query)
        single_records = wca_client._sanitize_results(single_records, 'best', limit=limit)
        key = '{}{}{}{}{}'.format(event, 'best', level, query, limit)
        wca_client.redis_client.set(key, json.dumps(single_records))

        # Average
        average_records = wca_client._query_records(event, 'average', level, query=query)
        average_records = wca_client._sanitize_results(average_records, 'average', limit=limit)
        key = '{}{}{}{}{}'.format(event, 'average', level, query, limit)
        wca_client.redis_client.set(key, json.dumps(average_records))
