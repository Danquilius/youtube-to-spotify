from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import pickle
import youtube_dl


def get_auth_youtube_client(scopes):
    """Uses OAuth to obtain access tokens for the current user
    so they can be granted access into the YouTube Data API."""

    credentials = None

    # if we have a token.pickle file, get its credentials
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as f:
            print("Acquiring Most Recently Used Access Tokens...")
            credentials = pickle.load(f)

    # refresh expired tokens or get new tokens if there are no credentials present
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            print("Refreshing Expired Access Tokens...")
            credentials.refresh(Request())
        else:
            print("Fetching New Access Tokens...")
            flow = InstalledAppFlow.from_client_secrets_file("client_secrets.json", scopes)
            credentials = flow.run_console()

            with open("token.pickle", "wb") as f:
                print("Saving Credentials In a Token File For Future Use...")
                pickle.dump(credentials, f)

    # returns a YouTube client service that allows access to user playlists, videos, etc.
    return build("youtube", "v3", credentials=credentials)


def get_playlists(yt_build):
    """Retreives all the YouTube playlists of the current user."""

    playlist_options = dict()

    my_playlists = yt_build.playlists().list(part="snippet", mine=True).execute()

    while True:
        for playlist in range(len(my_playlists["items"])):
            # print out the index and title of each playlist respectively
            print(f"{playlist}: {my_playlists['items'][playlist]['snippet']['title']}")

            # get all the videos and their information from each playlist and store it in the dictionary
            playlist_id = my_playlists["items"][playlist]["id"]
            playlist_videos = yt_build.playlistItems().list(part="contentDetails", playlistId=playlist_id).execute()

            playlist_options[playlist] = [playlist_id, playlist_videos]

        nextToken = my_playlists.get("nextPageToken")

        # if there is no succeeding response page, end the loop. Otherwise, keep extracting more playlists
        if nextToken is None:
            break
        else:
            my_playlists = yt_build.playlists().list(part="id", mine=True, pageToken=nextToken).execute()

    liked_videos = yt_build.videos().list(part="id", myRating="like").execute()

    # if there are liked videos, then there is a playlist consisting of all liked videos and add it to the dictionary
    if liked_videos["pageInfo"]["totalResults"] > 0:
        playlist_options[len(playlist_options)] = [liked_videos]
        print(f"{len(playlist_options) - 1}: Liked Videos")

    return playlist_options


def select_playlist(playlists):
    """Asks the user to select a YouTube playlist to be transferred to Spotify."""

    print("Select one of the above YouTube playlists on your account:")

    while True:
        try:
            chosen_playlist_num = int(input())
        except ValueError:
            print("Invalid Entry! Select a number associated with your chosen playlist")
        else:
            if chosen_playlist_num >= 0 and chosen_playlist_num <= len(playlists) - 1:
                break
            else:
                print("Invalid Entry! This number doesn't have an associated playlist")

    return playlists[chosen_playlist_num]


def get_track_info(playlist, video_info):
    """Extracts the name and artist of the track in the YouTube video
    from the playlist and the video information provided."""

    # the length is greater than 1 when it is not a Liked Videos list and has a playlist ID
    if len(playlist) > 1:
        video_id = video_info["contentDetails"]["videoId"]
    else:
        video_id = video_info["id"]

    video_url = f"https://www.youtube.com/watch?v={video_id}"

    try:
        video = youtube_dl.YoutubeDL().extract_info(video_url, download=False)

        track_name = video["track"]
        artist_name = video["artist"]
    # avoids videos that are unavailable, private, or inaccessible for whatever reason
    except Exception:
        print("Video Not Available...")
        return {"track": None, "artist": None}
    else:
        # returns the information of the singular track, including its name and artist
        return {"track": track_name, "artist": artist_name}


def clean_tracks(raw_tracks):
    """Processes the list of tracks, and returns a new list that
    only contains the tracks that have available information."""

    cleaned_tracks = []

    for track in raw_tracks:
        if track["track"] is not None and track["artist"] is not None:
            cleaned_tracks.append(track)

    return cleaned_tracks


def get_tracks(yt_build, playlist):
    """Extracts the available name and artist of all tracks in the videos of the YouTube playlist provided."""

    tracks = []

    while True:
        # calls a helper function to add tracks from the current response page to a list
        for item in playlist[-1]["items"]:
            tracks.append(get_track_info(playlist, item))

        nextToken = playlist[-1].get("nextPageToken")

        # if there is no succeeding response page, end the loop.
        if nextToken is None:
            break
        # otherwise, keep extracting more videos from either the Liked Videos or a different playlist in question
        else:
            if len(playlist) > 1:
                playlist_id = playlist[0]

                playlist = [
                    playlist_id,
                    (
                        yt_build.playlistItems()
                        .list(part="contentDetails", playlistId=playlist_id, pageToken=nextToken)
                        .execute()
                    ),
                ]
            else:
                playlist = [yt_build.videos().list(part="id", myRating="like", pageToken=nextToken).execute()]

    # calls a helper function to remove any unavailable track information from the list so it's cleaned.
    return clean_tracks(tracks)
