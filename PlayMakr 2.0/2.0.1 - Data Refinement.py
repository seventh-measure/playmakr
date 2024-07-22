import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import QuantileTransformer
from sklearn.cluster import KMeans
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import configparser

pd.set_option('max_colwidth', 400)

'''Notes
End Goal: An algorithm that takes a User's Spotify "Liked Songs" data, and from that generates a series of playlists.

Outline:
1. Gather and prepare data.
    1.1 spotify auth
    1.2 call API and input track_uri, artist_uri, artist_genres, and track attributes (e.g. valence, energy, danceability, and acousticness)
    1.3 prepare attribute data, normalization [quantiles? z-score?]
2. Quantizing genre data and genre similarity
    2.1 create a table of the form {artist_uri: [genres]}, matching each individual artist with their associated genre
    2.2 further populate missing artist-associated genre data for artists without [similar artists?]
    2.3 establish "metagenre" chunks that divide the entire genre space into more manageable subspaces, assume that genre between chunks is 0
    2.4 using track attributes, overlapping artists, and other means, calculate genre-to-genre similarity
3. Cluster songs using their attribute and genre data
    3.1 using metagenre divisions, go through chunks of tracks calculating similarities between
    3.2 with similarities calculated begin clustering tracks
4. Output clusters of tracks to User's Spotify
'''

# 1.1 - Spotify Authentication

# read config file to get 'client_id' and 'client_secret'
config = configparser.ConfigParser()
config.read('config.ini')
client_id = config['Section1']['client_id']
client_secret = config['Section1']['client_secret']
redirect_url = config['Section1']['redirect_url']
scope = "playlist-read-private, playlist-read-collaborative, user-library-read, playlist-modify-public, playlist-modify-private"

# setup authentication
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=client_id, client_secret=client_secret, redirect_uri=redirect_url, 
    scope=scope))

# simple test, returning a user's last liked song
"""
results = sp.current_user_saved_tracks(limit=1)
if results['items']:
    last_liked_track = results['items'][0]['track']
    print(f"Last liked track: {last_liked_track['name']} by {', '.join(artist['name'] for artist in last_liked_track['artists'])}")
"""

# 1.2 - Call API to gather track data

# prep data, and place into Dataframe
def fetch_user_tracks():
    i = 0
    tracks = []
    while True:
        tracks_chunk = sp.current_user_saved_tracks(limit=50, offset=i)
        if not tracks_chunk:
            break
        for item in tracks_chunk['items']:
            track = item['track']
            track_id = track['id']
            track_uri = track['uri']
            artist_uri = [artist['uri'] for artist in track['artists']]
            
            # Get audio features
            features = sp.audio_features(track_id)[0]
            if features:
                track_data = {
                    'track_uri': track_uri,
                    'artist_uri': artist_uri,
                    'valence': features.get('valence'),
                    'energy': features.get('energy'),
                    'danceability': features.get('danceability'),
                    'acousticness': features.get('acousticness')
                }
                tracks.append(track_data)
        break
        i += 50
    return tracks

track_data = fetch_user_tracks()

initial_track_df  = pd.DataFrame(track_data)
print(initial_track_df.head(10))