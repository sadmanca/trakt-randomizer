from trakt import Trakt
from dotenv import dotenv_values
from random import shuffle

secrets = dotenv_values(".env")

# Configure client
Trakt.configuration.defaults.app(
    id=secrets["TRAKT_APP_ID"]  # (e.g. "478" for https://trakt.tv/oauth/applications/478)
)

Trakt.configuration.defaults.client(
    id=secrets["API_ID"],
    secret=secrets["API_SECRET"]
)

# Request authentication
print('Navigate to %s' % Trakt['oauth/pin'].url())
pin = input('Pin: ')

# Exchange `pin` for an account authorization token
authorization = Trakt['oauth'].token_exchange(pin, 'urn:ietf:wg:oauth:2.0:oob')

if not authorization or not authorization.get('access_token'):
    print('ERROR: Authentication failed')
    exit(1)

# Configure client to use your account `authorization` by default
Trakt.configuration.defaults.oauth.from_response(authorization)

# ------------------------------------------------------

# Fetch list items
items = Trakt['users/sadmanca/lists/test'].items()

# Print list items
print('UNSHUFFLED:'), print(*items[:2], sep='\n'), print('...'), print(*items[-2:], sep='\n')

# remove unshuffled items
data = {'movies': [{'ids': {item.pk[0]: item.pk[1]}} for item in items]}
Trakt['users/sadmanca/lists/test'].remove(data)

print('-------------------')

shuffle(items)
print('SHUFFLED:'), print(*items[:2], sep='\n'), print('...'), print(*items[-2:], sep='\n')

# add shuffled items
data = {'movies': [{'ids': {item.pk[0]: item.pk[1]}} for item in items]}
Trakt['users/sadmanca/lists/test'].add(data)