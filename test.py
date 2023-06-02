data = {'movies': []}

data['movies'].append({'ids': {'tmdb': '76341'}})

movie_ids = ['76341', '257091', '287424']

for movie_id in movie_ids:
    data['movies'].append({'ids': {'tmdb': movie_id}})

print(data)