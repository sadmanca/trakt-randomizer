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

# Fetch watched items
# for key, movie in Trakt['sync/watched'].movies().items():
#     print('%s (%s)' % (movie.title, movie.year))

# items = Trakt['users/sadmanca/lists/Test'].items('sadmanca', 'Test')

# Fetch list items
items = Trakt['users/sadmanca/lists/test'].items()

# Print list items
print('Unshuffled:')
for item in items:
    print(item)

data = {'movies': [{'ids': {item.pk[0]: item.pk[1]}} for item in items]}

Trakt['users/sadmanca/lists/test'].remove(data)

print('-------------------')

print('Shuffled:')
shuffle(items)
for item in items:
    print(item)

# for item in items:
#     print(str(item.index) + ": " + item.pk[0] + " - " + item.pk[1])

data = {'movies': [{'ids': {item.pk[0]: item.pk[1]}} for item in items]}

Trakt['users/sadmanca/lists/test'].add(data)

print('-------------------')

# updated_items = Trakt['users/sadmanca/lists/test'].items()

# print('Updated after shuffle:')
# for item in updated_items:
#     print(item)

# {
#     'movies': [
#         {'ids': {'tmdb': '76341'}},
#         {'ids': {'tmdb': '257091'}},
#         {'ids': {'tmdb': '287424'}}
#     ]
# }

# 17: imdb - tt1881002

# for item in items:
#     print(str(item.index) + ": " + item.pk[0] + " - " + item.pk[1])

# Trakt['users/sadmanca/lists/test'].remove({
#     'movies': [
#         {'ids': {'tmdb': '287424'}}
#     ]
# })

""" 
# Convert items to list of dictionaries
item_dicts = []
for item in items:
    if hasattr(item, 'movie') and isinstance(item.movie, Trakt['movies'].Movie):
        item_dict = {
            'type': 'movie',
            'movie': item.movie.to_dict(),
            'ids': item.ids.to_dict(),
            'rank': item.rank,
            'notes': item.notes,
            'listed_at': item.listed_at.isoformat(),
            'updated_at': item.updated_at.isoformat()
        }
    elif hasattr(item, 'show') and isinstance(item.show, Trakt['shows'].Show):
        item_dict = {
            'type': 'show',
            'show': item.show.to_dict(),
            'episode': item.episode.to_dict() if item.episode else None,
            'ids': item.ids.to_dict(),
            'rank': item.rank,
            'notes': item.notes,
            'listed_at': item.listed_at.isoformat(),
            'updated_at': item.updated_at.isoformat()
        }
    elif hasattr(item, 'person') and isinstance(item.person, Trakt['people'].Person):
        item_dict = {
            'type': 'person',
            'person': item.person.to_dict(),
            'ids': item.ids.to_dict(),
            'rank': item.rank,
            'notes': item.notes,
            'listed_at': item.listed_at.isoformat(),
            'updated_at': item.updated_at.isoformat()
        }
    else:
        raise ValueError('Unknown item type')

    item_dicts.append(item_dict)

Trakt['users/sadmanca/lists/test'].update(item_dicts)

updated_items = Trakt['users/sadmanca/lists/test'].items()

print('Updated after shuffle:')
for item in updated_items:
    print(item)
"""