from trakt import Trakt
from dotenv import load_dotenv
from random import shuffle
import os
import json
import time

load_dotenv()

# Configure client
Trakt.configuration.defaults.app(
    id=os.environ.get('TRAKT_APP_ID')  # (e.g. "478" for https://trakt.tv/oauth/applications/478)
)

Trakt.configuration.defaults.client(
    id=os.environ.get('TRAKT_APP_API_ID'),
    secret=os.environ.get('TRAKT_APP_API_SECRET')
)

# Load authorization from file if it exists
authorization_file = 'token.json'
if os.path.isfile(authorization_file):
    with open(authorization_file, 'r') as f:
        try:
            authorization = json.load(f)
        except json.JSONDecodeError:
            authorization = None
else:
    authorization = None

# Calculate expiration time
if authorization and 'created_at' in authorization and 'expires_in' in authorization:
    expires_at = authorization['created_at'] + authorization['expires_in']
else:
    expires_at = 0

# Refresh token if it has expired
if authorization and time.time() > expires_at:
    if Trakt['oauth'].token_refresh(authorization['refresh_token']):
        authorization = Trakt['oauth'].token_exchange(authorization['refresh_token'])
        authorization['created_at'] = time.time()
        with open(authorization_file, 'w') as f:
            json.dump(authorization, f)
else:
    # Use cached authorization if it exists
    if authorization and 'access_token' in authorization:
        Trakt.configuration.defaults.oauth.from_response(authorization)
    else:
        # Request authentication if no authorization is found or refresh fails
        print('Navigate to %s' % Trakt['oauth/pin'].url())
        pin = input('Pin: ')
        authorization = Trakt['oauth'].token_exchange(pin, 'urn:ietf:wg:oauth:2.0:oob')
        
        if not authorization or not authorization.get('access_token'):
            print('ERROR: Authentication failed')
            exit(1)
        authorization['created_at'] = time.time()
        with open(authorization_file, 'w') as f:
            json.dump(authorization, f)

# Configure client to use your account `authorization` by default
Trakt.configuration.defaults.oauth.from_response(authorization)

# ------------------------------------------------------

# Fetch list items
list_test = Trakt['users/sadmanca/lists/test'].get()
items = list_test.items()

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