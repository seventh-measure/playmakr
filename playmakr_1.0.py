import pandas as pd # Data Handling and Manipulation
import numpy as np # Math
import spotipy # Python Spotify Library
from spotipy.oauth2 import SpotifyOAuth # Spotify API Interactions
import configparser # For Getting Client ID and Secret

def spListConv(spList): # for handling Spotify's list formatting
    spList = spList.split(', ')
    return spList

def fetchUserPlaylists(): # retrieves users playlists and takes input to identify seed playlists
    spUserPlaylists = sp.current_user_playlists()
    userPlaylists = []

    for playlist in spUserPlaylists['items']:
        playlistData = {}
        playlistData['Name'] = playlist['name']
        playlistData['ID'] = playlist['id']
        
        userPlaylists.append(playlistData)
    return userPlaylists

def seedSelection(userPlaylists):
    for playlistData in userPlaylists:
        line = str(userPlaylists.index(playlistData))
        playlistName = playlistData['Name']
        print(line + " " + playlistName + '\n')
    seedIndex = input("Select seed playlists... \n")
    seedIndex = seedIndex.replace(" ", "").split(",")
    seeds = []
    for indice in seedIndex:
        if "-" in indice:
            start, end = map(int, indice.split("-"))
            seeds.extend(range(start, end +1))
        else:
            seeds.append(int(indice))
    seedPlaylists = [userPlaylists[i] for i in seeds]
    return seedPlaylists

def fetchSeedPlaylistTracks(seedPlaylists):
    for playlistData in seedPlaylists:
        playlistTrackIDs = []
        spTrackData = sp.playlist_tracks(playlistData['ID'], fields='items(track(id, artists(id)))')['items']
        for trackData in spTrackData:
            trackID = trackData['track']['id']
            playlistTrackIDs.append(trackID)
        playlistData['Track IDs'] = playlistTrackIDs
    return seedPlaylists

def fetchSeedAttributes(seedPlaylists):
    for playlistData in seedPlaylists:
        trackIDs = playlistData['Track IDs']
        seedAttributes = {
            'acousticness': [],
            'danceability': [],
            'energy': [],
            'instrumentalness': [],
            'speechiness': [],
            'tempo': [],
            'valence': []
        }
        seedArtistsGenres = {
            'artists': [],
            'genres': []
        }
        trackFeatureData = sp.audio_features(trackIDs)
        trackData = sp.tracks(trackIDs)
        trackArtistData = trackData['tracks']
        for data in trackFeatureData:
            seedAttributes['acousticness'].append(data['acousticness'])
            seedAttributes['danceability'].append(data['danceability'])
            seedAttributes['energy'].append(data['energy'])
            seedAttributes['instrumentalness'].append(data['instrumentalness'])
            seedAttributes['speechiness'].append(data['speechiness'])
            seedAttributes['tempo'].append(data['tempo'])
            seedAttributes['valence'].append(data['valence'])
        seedAttributes['acousticness'] = np.average(seedAttributes['acousticness'])
        seedAttributes['danceability'] = np.average(seedAttributes['danceability'])
        seedAttributes['energy'] = np.average(seedAttributes['energy'])
        seedAttributes['instrumentalness'] = np.average(seedAttributes['instrumentalness'])
        seedAttributes['speechiness'] = np.average(seedAttributes['speechiness'])
        seedAttributes['tempo'] = np.average(seedAttributes['tempo'])
        seedAttributes['valence'] = np.average(seedAttributes['valence'])
        playlistData['Attributes'] = seedAttributes
        for data in trackArtistData:
            artistID = data['artists'][0]['id']
            seedArtistsGenres['artists'].append(artistID)
            artistData = sp.artist(artistID)
            seedArtistsGenres['genres'].extend(artistData['genres'])
        seedArtistsGenres['genres'] = set(seedArtistsGenres['genres'])
        seedArtistsGenres['genres'] = list(seedArtistsGenres['genres'])
        seedArtistsGenres['artists'] = set(seedArtistsGenres['artists'])
        seedArtistsGenres['artists'] = list(seedArtistsGenres['artists'])
        playlistData['Artists'] = seedArtistsGenres['artists']
        playlistData['Genres'] = seedArtistsGenres['genres']
    return seedPlaylists
        


config = configparser.ConfigParser()
config.read('config.txt')
client_id = config['Section1']['client_id']
client_secret = config['Section1']['client_secret']
redirect_url = config['Section1']['redirect_url']
scope = "playlist-read-private, playlist-read-collaborative, user-library-read, playlist-modify-public, playlist-modify-private"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
	client_id=client_id, client_secret=client_secret, redirect_uri=redirect_url, 
	scope=scope))

playlistTest = fetchUserPlaylists()
seedtest = seedSelection(playlistTest)
seedPlaylists = fetchSeedPlaylistTracks(seedtest)
print(fetchSeedAttributes(seedPlaylists))