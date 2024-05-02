import pandas as pd
import numpy as np
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import configparser
import time

def sp_list_conv(sp_list):
    return sp_list.split(', ')

def fetch_user_playlists():
    sp_user_playlists = sp.current_user_playlists()
    user_playlists = []

    for playlist in sp_user_playlists['items']:
        playlist_data = {
            'name': playlist['name'],
            'id': playlist['id']
        }
        user_playlists.append(playlist_data)

    return user_playlists

def seed_selection(user_playlists):
    for i, playlist_data in enumerate(user_playlists):
        print(f"{i} {playlist_data['name']}")

    seed_indices = input("Select seed playlists (comma-separated or range with hyphen): ").replace(" ", "").split(",")
    seeds = []

    for indice in seed_indices:
        if "-" in indice:
            start, end = map(int, indice.split("-"))
            seeds.extend(range(start, end + 1))
        else:
            seeds.append(int(indice))

    seed_playlists = [user_playlists[i] for i in seeds]
    
    print(f"Selected seed playlists: {[playlist['name'] for playlist in seed_playlists]}")
    
    return seed_playlists

def fetch_seed_playlist_tracks(seed_playlists):
    for playlist_data in seed_playlists:
        playlist_track_ids = []
        sp_track_data = sp.playlist_tracks(playlist_data['id'], fields='items(track(id, artists(id)))')['items']

        for track_data in sp_track_data:
            track_id = track_data['track']['id']
            playlist_track_ids.append(track_id)

        playlist_data['track_ids'] = playlist_track_ids
    
    return seed_playlists

def fetch_seed_attributes(seed_playlists):
    for playlist_data in seed_playlists:
        print(playlist_data['name'])
        track_ids = playlist_data['track_ids']
        seed_attributes = {
            'acousticness': [],
            'danceability': [],
            'energy': [],
            'instrumentalness': [],
            'speechiness': [],
            'tempo': [],
            'valence': []
        }
        
        seed_artists_genres = {
            'artists': [],
            'genres': []
        }

        print("track feature data fetching")
        track_feature_data = sp.audio_features(track_ids)
        print("track data fetching")
        track_data = sp.tracks(track_ids)
        print("track artist data fetching")
        track_artist_data = track_data['tracks']

        for data in track_feature_data:
            seed_attributes['acousticness'].append(data['acousticness'])
            seed_attributes['danceability'].append(data['danceability'])
            seed_attributes['energy'].append(data['energy'])
            seed_attributes['instrumentalness'].append(data['instrumentalness'])
            seed_attributes['speechiness'].append(data['speechiness'])
            seed_attributes['tempo'].append(data['tempo'])
            seed_attributes['valence'].append(data['valence'])

        for data in track_artist_data:
            artist_id = data['artists'][0]['id']
            seed_artists_genres['artists'].append(artist_id)
            artist_data = sp.artist(artist_id)
            seed_artists_genres['genres'].extend(artist_data['genres'])

        seed_attributes = {key: np.average(val) for key, val in seed_attributes.items()}
        seed_artists_genres['genres'] = list(set(seed_artists_genres['genres']))
        seed_artists_genres['artists'] = list(set(seed_artists_genres['artists']))

        playlist_data['attributes'] = seed_attributes
        playlist_data['artists'] = seed_artists_genres['artists']
        playlist_data['genres'] = seed_artists_genres['genres']
    
    return seed_playlists

def fetch_user_songs(offset):
    current_chunk = sp.current_user_saved_tracks(limit=50, offset=offset)
    simplified_chunk = [{
        'id': item['track']['id'],
        'artist_id': item['track']['artists'][0]['id']
    } for item in current_chunk['items'] if not item['track']['is_local']]

    return simplified_chunk

def fetch_chunk_attributes(simplified_chunk):
    chunk_track_ids = [track['id'] for track in simplified_chunk]
    chunk_artist_ids = [track['artist_id'] for track in simplified_chunk]
    
    chunk_attributes = sp.audio_features(chunk_track_ids)
    chunk_artist_info = sp.artists(chunk_artist_ids)
    
    attribute_maps = {
        'acousticness': [],
        'danceability': [],
        'energy': [],
        'instrumentalness': [],
        'speechiness': [],
        'tempo': [],
        'valence': []
    }

    genre_map = {}

    for attribute_data in chunk_attributes:
        for key, val in attribute_data.items():
            if key in attribute_maps:
                attribute_maps[key].append(val)

    for artist_data in chunk_artist_info['artists']:
        genre_map[artist_data['id']] = artist_data['genres'] if artist_data['genres'] else []

    for track in simplified_chunk:
        for key, val in attribute_maps.items():
            track[key] = np.average(val) if val else None
        
        track['genres'] = genre_map.get(track['artist_id'], [])

    return simplified_chunk

def calc_fit_score(chunk, seed_playlists):
    for track in chunk:
        track['fit_scores'] = []

        for playlist in seed_playlists:
            acousticness_diff = abs(track['acousticness'] - playlist['attributes']['acousticness'])
            danceability_diff = abs(track['danceability'] - playlist['attributes']['danceability'])
            energy_diff = abs(track['energy'] - playlist['attributes']['energy'])
            instrumentalness_diff = abs(track['instrumentalness'] - playlist['attributes']['instrumentalness'])
            speechiness_diff = abs(track['speechiness'] - playlist['attributes']['speechiness'])
            tempo_diff = abs(track['tempo'] - playlist['attributes']['tempo'])
            valence_diff = abs(track['valence'] - playlist['attributes']['valence'])

            audio_fit = 1 - ((acousticness_diff + danceability_diff + energy_diff + instrumentalness_diff + speechiness_diff + (tempo_diff / 100) + valence_diff) / 7)

            genre_intersection = set(track['genres']).intersection(set(playlist['genres']))
            genre_intersection_count = len(genre_intersection)
            genre_fit = genre_intersection_count / len(playlist['genres']) if len(playlist['genres']) > 0 else 0

            artist_fit = 1 if track['artist_id'] in playlist['artists'] else 0

            fit_score = (audio_fit + genre_fit + artist_fit) / 3
            track['fit_scores'].append({playlist['id']: fit_score})

def sort_chunk(calc_chunk):
    track_map = {}

    for track in calc_chunk:
        fit_scores = {list(fit_score.keys())[0]: list(fit_score.values())[0] for fit_score in track['fit_scores']}
        best_seed = max(fit_scores, key=fit_scores.get)
        
        if best_seed not in track_map:
            track_map[best_seed] = []
        
        track_map[best_seed].append(track['id'])

    return track_map

def add_tracks_to_playlists(track_map):
    for playlist_id, track_ids in track_map.items():
        track_uris = [f"spotify:track:{track_id}" for track_id in track_ids]
        batch_size = 20
        num_batches = (len(track_uris) + batch_size - 1) // batch_size  # Calculate number of batches
        for i in range(num_batches):
            start_idx = i * batch_size
            end_idx = min((i + 1) * batch_size, len(track_uris))
            batch = track_uris[start_idx:end_idx]
            sp.playlist_add_items(playlist_id=playlist_id, items=batch)
            time.sleep(3)


config = configparser.ConfigParser()
config.read('config.txt')
client_id = config['Section1']['client_id']
client_secret = config['Section1']['client_secret']
redirect_url = config['Section1']['redirect_url']
scope = "playlist-read-private, playlist-read-collaborative, user-library-read, playlist-modify-public, playlist-modify-private"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=client_id, client_secret=client_secret, redirect_uri=redirect_url, 
    scope=scope))

# Fetching user playlists
print("Fetching user playlists...")
user_playlists = fetch_user_playlists()

# Selecting seed playlists
print("\nSelecting seed playlists...")
seed_playlists = seed_selection(user_playlists)

# Fetching tracks from seed playlists
print("\nFetching tracks from seed playlists...")
seed_playlists = fetch_seed_playlist_tracks(seed_playlists)

# Fetching attributes for seed playlists
print("\nFetching attributes for seed playlists...")
seed_playlists = fetch_seed_attributes(seed_playlists)

# Fetching user songs
print("\nFetching user songs...")
offset = 0
user_song_attributes = []

while True:
    print(f"Fetching songs from offset {offset}...")
    current_chunk = fetch_user_songs(offset)
    
    if not current_chunk:
        break

    chunk_attributes = fetch_chunk_attributes(current_chunk)
    user_song_attributes.extend(chunk_attributes)
    offset += 50

# Calculating fit scores
print("\nCalculating fit scores...")
calc_fit_score(user_song_attributes, seed_playlists)

# Sorting tracks
print("\nSorting tracks...")
track_map = sort_chunk(user_song_attributes)

# Adding tracks to playlists
print("\nAdding tracks to playlists...")
add_tracks_to_playlists(track_map)

print("\nAll processes completed successfully!")
# 3,4,5,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,23