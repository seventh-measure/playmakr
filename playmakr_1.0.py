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
        
def fetchUserSongs(offset): # fetches chunks of tracks (50 at a time) from User's liked songs
    currentChunk = sp.current_user_saved_tracks(limit=50, offset=offset)
    simplifiedChunk = [{
        'id': item['track']['id'],
        'artist_id': item['track']['artists'][0]['id']
    } for item in currentChunk['items']]
    return simplifiedChunk

def fetchChunkAttributes(simplifiedChunk): # adds relevant attribute information to each track in a chunk
    chunkTrackIDs = [track['id'] for track in simplifiedChunk]
    chunkArtistIDs = [track['artist_id'] for track in simplifiedChunk]
    chunkAttributes = sp.audio_features(chunkTrackIDs)
    chunkArtistInfo = sp.artists(chunkArtistIDs)

    acousticnessMap = {item['id']: item['acousticness'] for item in chunkAttributes}
    danceabilityMap = {item['id']: item['danceability'] for item in chunkAttributes}
    energyMap = {item['id']: item['energy'] for item in chunkAttributes}
    instrumentalnessMap = {item['id']: item['instrumentalness'] for item in chunkAttributes}
    speechinessMap = {item['id']: item['speechiness'] for item in chunkAttributes}
    tempoMap = {item['id']: item['tempo'] for item in chunkAttributes}
    valenceMap = {item['id']: item['valence'] for item in chunkAttributes}

    genreMap = {artist['id']: artist['genres'] if artist['genres'] else [] for artist in chunkArtistInfo['artists']}

    for track in simplifiedChunk:
        track['acousticness'] = acousticnessMap.get(track['id'], [])
        track['danceability'] = danceabilityMap.get(track['id'], [])
        track['energy'] = energyMap.get(track['id'], [])
        track['instrumentalness'] = instrumentalnessMap.get(track['id'], [])
        track['speechiness'] = speechinessMap.get(track['id'], [])
        track['tempo'] = tempoMap.get(track['id'], [])
        track['valence'] = valenceMap.get(track['id'], [])
        track['genres'] = genreMap.get(track['artist_id'], [])
    
    return simplifiedChunk

def calcFitScore(chunk, seedPlaylists): # with track chunks now having all relevant data, simple functions determine each tracks best fit based on each parameter
    for track in chunk:
        track['fit scores'] = []
        for playlist in seedPlaylists:
            playlistID = playlist['ID']

            acoSubScore = abs(track['acousticness'] - playlist['Attributes']['acousticness'])
            danSubScore = abs(track['danceability'] - playlist['Attributes']['danceability'])
            eneSubScore = abs(track['energy'] - playlist['Attributes']['energy'])
            insSubScore = abs(track['instrumentalness'] - playlist['Attributes']['instrumentalness'])
            speSubScore = abs(track['speechiness'] - playlist['Attributes']['speechiness'])
            temSubScore = abs(track['tempo'] - playlist['Attributes']['tempo'])
            valSubScore = abs(track['valence'] - playlist['Attributes']['valence'])

            audioFit = (acoSubScore + danSubScore + eneSubScore + insSubScore + speSubScore + (temSubScore/100) + valSubScore)/7

            genreIntersection = set(track['genres']).intersection(set(playlist['Genres']))
            genreIntersectionCount = len(genreIntersection)

            genreSubScore = (genreIntersectionCount/(len(playlist['Genres'])))

            if track['artist_id'] in playlist['Artists']:
                artistSubScore = 1
            else:
                artistSubScore = 0
            
            fitScore = (audioFit + genreSubScore + artistSubScore)/3
            track['fit scores'].append({playlistID: fitScore})
    return chunk


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
seeds = fetchSeedAttributes(seedPlaylists)
chunk = fetchChunkAttributes(fetchUserSongs(0))
print(calcFitScore(chunk, seeds))