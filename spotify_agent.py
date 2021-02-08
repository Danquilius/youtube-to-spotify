from spotify_secrets import sp_client_id, sp_client_secret, sp_redirect_uri
from spotipy import Spotify, SpotifyOAuth


class SpotifyUser:
    """A Spotify User object that can create new playlists and add given tracks to it."""

    def __init__(self, user_scopes):
        self.client = Spotify(
            auth_manager=SpotifyOAuth(
                client_id=sp_client_id, client_secret=sp_client_secret, redirect_uri=sp_redirect_uri, scope=user_scopes
            )
        )
        self.user_id = self.client.current_user()["id"]

    def create_playlist(self):
        """Creates a Spotify playlist and returns its id."""

        playlist = self.client.user_playlist_create(self.user_id, "YouTube Music", public=False)

        print("\nPlaylist Created: YouTube Music")
        return playlist["id"]

    def get_track_ids(self, tracks_info):
        """Retrieves the spotify ID of all available tracks from the list of tracks provided."""

        track_ids = []

        for track in tracks_info:
            search_result = self.client.search(q="track:" + track["track"] + " artist:" + track["artist"], limit=1)

            # if the response in items exists, and it was not of length 0, add the id of that track to the list
            if len(search_result["tracks"]["items"]) > 0:
                track_ids.append(search_result["tracks"]["items"][0]["id"])

        return track_ids

    def add_tracks(self, tracks_info, playlist_id):
        """Adds tracks from the provided list of tracks into a playlist of the current user,
        filtered by the playlist ID."""

        ids = self.get_track_ids(tracks_info)
        self.client.user_playlist_add_tracks(self.user_id, playlist_id, ids)

        print(
            f"\nFrom your YouTube playlist, {len(ids)} out of {len(tracks_info)} "
            "tracks were successfully added to your Spotify 'YouTube Music' playlist."
            "\nDone."
        )
