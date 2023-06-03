from trakt import Trakt
from dotenv import dotenv_values
from random import shuffle
import os.path
import json
import sys

secrets = dotenv_values(".env")

# Configure client
Trakt.configuration.defaults.app(
    id=secrets["TRAKT_APP_ID"]  # (e.g. "478" for https://trakt.tv/oauth/applications/478)
)

Trakt.configuration.defaults.client(
    id=secrets["API_ID"],
    secret=secrets["API_SECRET"]
)

# Load authorization from file if it exists
authorization_file = 'token.json'
if os.path.isfile(authorization_file):
    with open(authorization_file, 'r') as f:
        authorization = json.load(f)
else:
    authorization = None

# Request authentication if no authorization is found
if not authorization or not authorization.get('access_token'):
    print('Navigate to %s' % Trakt['oauth/pin'].url())
    pin = input('Pin: ')
    authorization = Trakt['oauth'].token_exchange(pin, 'urn:ietf:wg:oauth:2.0:oob')
    if not authorization or not authorization.get('access_token'):
        print('ERROR: Authentication failed')
        exit(1)
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
        # os.execv(sys.executable, ['python'] + sys.argv)
        exit(1)
    else:
        data = cached_data

if items is not None:
    # Print list items
    print('UNSHUFFLED:')
    print(*items[:2], sep='\n')
    print('...')
    print(*items[-2:], sep='\n') 

    data = {'movies': [{'ids': {item.pk[0]: item.pk[1]}} for item in items]}

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

    data = {'movies': [{'ids': {item.pk[0]: item.pk[1]}} for item in items]}


if data is not None:
    # Add shuffled items
    Trakt['users/sadmanca/lists/test'].add(data)

    # Cache data at end of program (if items is not NoneType)
    with open('data.json', 'w') as f:
        json.dump(data, f)