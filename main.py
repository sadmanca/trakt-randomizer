from trakt import Trakt
from dotenv import load_dotenv
from random import shuffle
from urllib.parse import urlparse
import os
import json
import time

import logging
logging.basicConfig(format='%(asctime)s %(message)s', filename='test.log', level=logging.INFO)

AUTHORIZATION_FILE = 'token.json'

def configure_client():
    Trakt.configuration.defaults.app(
        id=os.environ.get('TRAKT_APP_ID')
    )

    Trakt.configuration.defaults.client(
        id=os.environ.get('TRAKT_APP_API_ID'),
        secret=os.environ.get('TRAKT_APP_API_SECRET')
    )

def load_authorization():
    if os.path.isfile(AUTHORIZATION_FILE):
        with open(AUTHORIZATION_FILE, 'r') as f:
            try:
                authorization = json.load(f)
            except json.JSONDecodeError:
                authorization = None
    else:
        authorization = None

    return authorization

def refresh_token(authorization):
    expires_at = authorization['created_at'] + authorization['expires_in']
    if time.time() > expires_at:
        if Trakt['oauth'].token_refresh(authorization['refresh_token']):
            authorization = Trakt['oauth'].token_exchange(authorization['refresh_token'])
            authorization['created_at'] = time.time()
            with open(AUTHORIZATION_FILE, 'w') as f:
                json.dump(authorization, f)

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
        with open(AUTHORIZATION_FILE, 'w') as f:
            json.dump(authorization, f)

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

def multi_run(url_list):
    url_dict = {}

    with open(url_list, 'r') as f:
        current_section = None
        for line in f:
            line = line.strip()
            if line.startswith('[') and line.endswith(']'):
                current_section = line[1:-1]
                url_dict[current_section] = []
            elif line:
                url_dict[current_section].append(urlparse(line).path[1:])
    
    self_urls = url_dict['self']
    for url in self_urls:
        print(url)
        run(url)

def main():
    load_dotenv()
    configure_client()
    authorization = load_authorization()
    authorization = refresh_token(authorization)
    authenticate(authorization)
    configure_authorization(authorization)
    multi_run('url_list.txt')
    logging.info('----------------------------------------')

if __name__ == '__main__':
    main()