import pandas as pd # Data Handling and Manipulation
import numpy as np # Math
import spotipy # Python Spotify Library
from spotipy.oauth2 import SpotifyOAuth # Spotify API Interactions
import configparser # For Getting Client ID and Secret

def spListConv(spList):
    spList = spList.split(', ')
    return spList

class seedPlaylist:
    def __init__(self, title, playlistID):
        self.title = title
        self.playlistID = playlistID
        self.trackIDs = []
        
        self.genres = []
        self.aBar = None # acousticness
        self.dBar = None # danceability
        self.eBar = None # energy
        self.iBar = None # instrumentalness
        self.sBar = None # speechiness
        self.tBar = None # tempo
        self.vBar = None # valence
        
    def fetchTrackInfo(self, playlistID):
        self.trackIDs.append(sp.playlist_tracks(playlistID, fields='items(track(id))')['items'])

        for trackID in self.trackIDs:
            
            

        




config = configparser.ConfigParser()
config.read('config.txt')
client_id = config['Section1']['client_id']
client_secret = config['Section1']['client_secret']
redirect_url = config['Section1']['redirect_url']
scope = "playlist-read-private, playlist-read-collaborative, user-library-read, playlist-modify-public, playlist-modify-private"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
	client_id=client_id, client_secret=client_secret, redirect_uri=redirect_url, 
	scope=scope))

