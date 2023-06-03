from trakt import Trakt
from dotenv import load_dotenv
from random import shuffle
import os
import json
import time

load_dotenv()

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

def main():
    configure_client()
    authorization = load_authorization()
    authorization = refresh_token(authorization)
    authenticate(authorization)
    configure_authorization(authorization)
    items = fetch_list_items('test')

    # Cache data if items is NoneType
    data = None
    if items is None:
        with open('data.json', 'r') as f:
            cached_data = json.load(f)

        if cached_data is None:
            print('ERROR: No cached data found')
            exit(1)
        else:
            data = cached_data

    if items is not None:
        # Print list items
        print('UNSHUFFLED:')
        print(*items[:2], sep='\n')
        print('...')
        print(*items[-2:], sep='\n') 

        data = {
            'movies': [{'ids': {'imdb': item.pk[1]}} for item in items if item.pk[0] == 'imdb'],
            'shows':  [{'ids': {'tvdb': item.pk[1]}} for item in items if item.pk[0] == 'tvdb']
        }

    # remove unshuffled items
    if data is not None:
        Trakt['users/sadmanca/lists/test'].remove(data)

    # Shuffle items
    if items is not None:
        shuffle(items)

        print('-------------------')
        print('SHUFFLED:')
        print(*items[:2], sep='\n')
        print('...')
        print(*items[-2:], sep='\n')

        data = {
            'movies': [{'ids': {'imdb': item.pk[1]}} for item in items if item.pk[0] == 'imdb'],
            'shows':  [{'ids': {'tvdb': item.pk[1]}} for item in items if item.pk[0] == 'tvdb']
        }

    if data is not None:
        # Add shuffled items
        Trakt['users/sadmanca/lists/test'].add(data)

        # Cache data at end of program (if items is not NoneType)
        with open('data.json', 'w') as f:
            json.dump(data, f)

if __name__ == '__main__':
    main()