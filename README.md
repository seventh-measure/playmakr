# playmakr
A Python-based, Spotify playlist making program

## Rough Outline
_as of February, 2024_

1. Identify "Seed Playlists"
   1.1 Spotipy Authentication
   1.2 Fetch user's playlists' IDs
   1.3 Have user identify seed playlists

2. Define Seed Playlist Attributes
   2.1 Fetch and organize seed playlist data (e.g., Names, IDs, tracks)
   2.2 Calculate each playlist's overall attributes based on the underlying tracks' attributes*
   2.3 Prepare the playlists to interpret the incoming tracks

3. Process User's Unsorted Tracks
   3.1 In chunks, due to Spotify's rate-limiting, fetch each track's collection of metadata
   3.2 Compare the relevant track attributes with each playlist's attributes and identify the best fit
   3.3 Compile each list of new tracks underneath their respective playlists

4. Upload Playlists to User's Account
   4.1 Divide the playlist data into chunks
   4.2 Update each seed playlist with its new list of songs

* A lot of math still to be written out. I have some ideas based on past iterations of this project. My goal is to create some set of functions that will adapt the values for various attributes coming in into a feasible scale by which to judge the individual track values. While some of the metadata is easy and quantative, other, more qualitative information, like genres, will require a more abstract method of comparison.
