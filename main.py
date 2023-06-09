from trakt import Trakt
from dotenv import load_dotenv
from random import shuffle
from urllib.parse import urlparse
import os
import json
import time

import logging
logging.basicConfig(level=logging.INFO)
handler = logging.FileHandler('test.log', encoding='utf-8')
handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
logging.getLogger().addHandler(handler)

json_string = ""

def configure_client():
    Trakt.configuration.defaults.app(
        id=os.environ.get('TRAKT_APP_ID')
    )

    Trakt.configuration.defaults.client(
        id=os.environ.get('TRAKT_APP_API_ID'),
        secret=os.environ.get('TRAKT_APP_API_SECRET')
    )

def load_authorization():
    try:
        json_string = os.environ.get('AUTHORIZATION_TOKEN')
        authorization = json.loads(json_string)
    except json.JSONDecodeError:
        authorization = None

    return authorization

def refresh_token(authorization):
    expires_at = authorization['created_at'] + authorization['expires_in']
    if time.time() > expires_at:
        if Trakt['oauth'].token_refresh(authorization['refresh_token']):
            authorization = Trakt['oauth'].token_exchange(authorization['refresh_token'])
            authorization['created_at'] = time.time()
            with open('.env', 'w') as f:
                json_string = json.dumps(authorization)
                f.write(f'AUTHORIZATION_TOKEN={json_string}')

    return authorization

def authenticate(authorization):
    if not authorization or not authorization.get('access_token'):
        print('Navigate to %s' % Trakt['oauth/pin'].url())
        pin = input('Pin: ')
        authorization = Trakt['oauth'].token_exchange(pin, 'urn:ietf:wg:oauth:2.0:oob')
        
        if not authorization or not authorization.get('access_token'):
            print('ERROR: Authentication failed')
            exit(1)
        authorization['created_at'] = time.time()
        with open('.env', 'w') as f:
            json_string = json.dumps(authorization)
            f.write(f'AUTHORIZATION_TOKEN={json_string}')

    return authorization

# Configure client to use your account `authorization` by default
def configure_authorization(authorization):
    if authorization and 'access_token' in authorization:
        Trakt.configuration.defaults.oauth.from_response(authorization)

# ------------------------------------------------------

# Fetch list items
def fetch_list_items(list_slug):
    items = Trakt[list_slug].items()
    if items is not None:
        return items
    else:
        print('ERROR: Could not fetch list items')
        exit(1)

def write_to_log(items, msg):
    if items is not None:
        logging.info(msg)
        for item in items[:2]:
            logging.info(f'    {item}')
        logging.info('    ...')
        for item in items[-2:]:
            logging.info(f'    {item}')

def format_data(items):
    items = items[:1000] # Trakt limit for number of items in a personal list w/o VIP
    return {
        'movies': [{'ids': {'imdb': item.pk[1]}} for item in items if item.pk[0] == 'imdb'],
        'shows':  [{'ids': {'tvdb': item.pk[1]}} for item in items if item.pk[0] == 'tvdb']
    }

def run(list_slug):
    items = fetch_list_items(list_slug)

    if items is not None:
        logging.info(list_slug)
        write_to_log(items, 'ORIGINAL:')
        data = format_data(items)

        # remove unshuffled items
        Trakt[list_slug].remove(data)
        time.sleep(1)

        shuffle(items)

        write_to_log(items, 'SHUFFLED:')
        data = format_data(items)

        # Add shuffled items
        Trakt[list_slug].add(data)
        time.sleep(1)

def copy_run(others_list_slug, self_list_slug, randomize=False):
    self_items = fetch_list_items(self_list_slug)
    others_items = fetch_list_items(others_list_slug)

    if others_items is not None and self_items is not None:
        logging.info(self_list_slug)
        write_to_log(self_items, 'ORIGINAL:')
        
        data = format_data(self_items)
        Trakt[self_list_slug].remove(data)
        time.sleep(1)

        logging.info(others_list_slug)
        if randomize:
            shuffle(others_items)
            write_to_log(others_items, 'NEW, SHUFFLED:')
        else:
            write_to_log(others_items, 'NEW, NOT SHUFFLED:')

        # Add shuffled items
        data = format_data(others_items)
        Trakt[self_list_slug].add(data)
        time.sleep(1)

def multi_run(url_list):
    self_urls = []
    others_dict = {}
    current_key = None

    for line in url_list.split('\n'):
        line = line.strip()
        if line.startswith('#'):
            continue
        elif line.startswith('[self]'):
            current_key = 'self'
            continue
        elif line.startswith('[others]'):
            current_key = 'others'
            continue
        if line:
            urls = line.split(', ')
            if current_key == 'self':
                self_urls.extend(urls)
            elif current_key == 'others' and len(urls) == 2:
                others_dict[urls[0]] = urls[1]

    for url in self_urls:
        run(urlparse(url).path[1:])

    for key, value in others_dict.items():
        copy_run(urlparse(key).path[1:], urlparse(value).path[1:], randomize=True)

def main():
    load_dotenv()
    configure_client()
    authorization = load_authorization()
    authorization = refresh_token(authorization)
    authenticate(authorization)
    configure_authorization(authorization)
    url_list = os.environ.get('URL_LIST')
    multi_run(url_list)
    logging.info('----------------------------------------')

if __name__ == '__main__':
    main()