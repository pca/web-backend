import requests

from bs4 import BeautifulSoup


def scrape_competition(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    competition_data = {}
    title = ''

    dataset = soup.find_all('dl', 'dl-horizontal')

    for data in dataset:
        elements = data.findAll(['dt', 'dd'])

        for index, element in enumerate(elements):
            if index % 2 == 0:
                title = element.string
            else:
                if title == 'Venue':
                    if element.find('a'):
                        competition_data['venue'] = {
                            'link': element.p.a.get('href'),
                            'text': element.p.a.string,
                        }
                    else:
                        competition_data['venue'] = {
                            'link': None,
                            'text': element.p.string,
                        }
                elif title == 'Address':
                    competition_data['venue']['address'] = {
                        'map': element.a.get('href'),
                        'text': element.a.string,
                    }
                elif title == 'Details':
                    competition_data['venue']['details'] = element.p.string
                elif title == 'Registration period':
                    opening, closing = element.p.findAll('span')
                    competition_data['registration_period'] = {
                        'opening': opening.get('data-utc-time'),
                        'closing': closing.get('data-utc-time'),
                    }

    return competition_data
