from spotify_agent import SpotifyUser
import youtube_response


yt_scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
sp_scopes = "playlist-modify-private"

yt_client = youtube_response.get_auth_youtube_client(yt_scopes)
yt_playlists = youtube_response.get_playlists(yt_client)
yt_playlist = youtube_response.select_playlist(yt_playlists)
yt_tracks = youtube_response.get_tracks(yt_client, yt_playlist)

sp = SpotifyUser(sp_scopes)
sp_playlist_id = sp.create_playlist()
sp.add_tracks(yt_tracks, sp_playlist_id)
