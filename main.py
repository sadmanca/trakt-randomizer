from trakt import Trakt
from dotenv import load_dotenv
from random import shuffle
import os
import json
import time

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
    return Trakt['users/sadmanca/lists/' + list_slug].items()

def fetch_cached_data(items):
    # Cache data if items is None
    if items is None:
        with open('data.json') as f:
            return json.load(f)

    return {}

def print_list_items(items, msg):
    if items is not None:
        print(msg)
        for item in items[:2]:
            print(f' {item}')
        print(' ...')
        for item in items[-2:]:
            print(f' {item}')

def format_data(items):
    return {
        'movies': [{'ids': {'imdb': item.pk[1]}} for item in items if item.pk[0] == 'imdb'],
        'shows':  [{'ids': {'tvdb': item.pk[1]}} for item in items if item.pk[0] == 'tvdb']
    }

def cache_data(data):
    # Cache data at end of program (if items is not NoneType)
    if data:
        with open('data.json', 'w') as f:
            json.dump(data, f)

def run(data, items):
    if items is not None:
        print_list_items(items, 'ORIGINAL:')
        data = format_data(items)

    # remove unshuffled items
    if data is not None:
        Trakt['users/sadmanca/lists/test'].remove(data)

    # Shuffle items
    if items is not None:
        shuffle(items)

        print('-------------------')
        print_list_items(items, 'SHUFFLED:')
        data = format_data(items)

    if data is not None:
        # Add shuffled items
        Trakt['users/sadmanca/lists/test'].add(data)

def main():
    load_dotenv()
    configure_client()
    authorization = load_authorization()
    authorization = refresh_token(authorization)
    authenticate(authorization)
    configure_authorization(authorization)
    items = fetch_list_items('test')
    data = fetch_cached_data(items)
    run(data, items)
    cache_data(data)

if __name__ == '__main__':
    main()