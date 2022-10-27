# download my personal playlist from youtube music

# I have no idea where copilot stole this from

from multiprocessing import Process
import os
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# read the api key from .env file
API_KEY = os.getenv('API_KEY')
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
save_location = 'D:/Music'

# log in to youtube music
def login():
    credentials = None
    # get the credentials from the file
    if os.path.exists('token.pickle'):
        print('Loading Credentials From File...')
        with open('token.pickle', 'rb') as token:
            credentials = pickle.load(token)

    # if there are no valid credentials available, then either refresh the token or log in.
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            print('Refreshing Access Token...')
            credentials.refresh(Request())
        else:
            print('Fetching New Tokens...')
            flow = InstalledAppFlow.from_client_secrets_file(
                os.path.join(os.path.dirname(__file__), 'client_secret.json'),
                scopes=[
                    'https://www.googleapis.com/auth/youtube.readonly'
                ]
            )

            flow.run_local_server(port=5000, prompt='consent',
                                authorization_prompt_message='')
            credentials = flow.credentials

            # Save the credentials for the next run
            with open('token.pickle', 'wb') as f:
                print('Saving Credentials for Future Use...')
                pickle.dump(credentials, f)

    return credentials

# build the youtube music api
def build_youtube_music_api(credentials):
    youtube = build(
        'youtube', 'v3', credentials=credentials)
    return youtube

# get all playlists from youtube music
def get_playlists(youtube):
    request = youtube.playlists().list(
        part="snippet,contentDetails",
        maxResults=50,
        mine=True
    )
    response = request.execute()
    return response

# get all songs from a playlist
def get_songs_from_playlist(youtube, playlist_id):
    # use pagination to get all songs from a playlist
    songs = []
    next_page_token = None
    while True:
        request = youtube.playlistItems().list(
            part="snippet,contentDetails",
            maxResults=50,
            playlistId=playlist_id,
            pageToken=next_page_token
        )
        response = request.execute()
        songs += response['items']
        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break
    return songs

# download a song from youtube music
def download_song(song, save_location):
    # download using yt-dlp with best quality and save to the save_location in mp3 format

    song_name = song['snippet']['title']
    song_id = song['contentDetails']['videoId']

    # provide path to yt-dlp.exe
    path = "D:\\Users\zolix\\Downloads\\ffmpeg-2022-10-27-git-00b03331a0-full_build\\bin"
    os.system(f'yt-dlp -f bestaudio --extract-audio --audio-format mp3 --audio-quality 0 --output "{save_location}/{song_name}.%(ext)s" --ffmpeg-location "{path}" https://www.youtube.com/watch?v={song_id}')

# download all songs from a playlist
def download_playlist(youtube, playlist_id, save_location):
    songs = get_songs_from_playlist(youtube, playlist_id)
    for song in songs:
        download_song(song, save_location)

# download all songs from a playlist from url
def download_playlist_from_url(youtube, url, save_location):
    playlist_id = url.split('list=')[1]
    download_playlist(youtube, playlist_id, save_location)

# download all songs from all playlists
def download_all_playlists(youtube, save_location):
    processes = []

    while True:
        # ask the user if they want to download playlist from url
        print('Do you want to download a playlist from a url? (y/n)', end=' ')
        choice = input()
        if choice == 'y':
            print('Enter the url of the playlist')
            url = input()
            processes.append(Process(target=download_playlist_from_url, args=(youtube, url, save_location)))
        else:
            break

    # ask the user if they want to download liked songs
    print('Do you want to download liked songs? (y/n)', end=' ')
    choice = input()
    if choice == 'y':
        processes.append(Process(target=download_playlist, args=(youtube, 'LM', save_location)))

    playlists = get_playlists(youtube) 
    print('Do you want to download playlists? (y/n)', end=' ')
    choice = input()
    if choice == 'y':  
        # download all songs from all playlists
        for playlist in playlists['items']:
            processes.append(Process(target=download_playlist, args=(youtube, playlist['id'], save_location)))
    else:
        print('Do you want to select playlists to download? (y/n)', end=' ')
        choice = input()
        if choice == 'y':
            for playlist in playlists['items']:
                print(f"Download {playlist['snippet']['title']}? (y/n)", end=' ')
                choice = input()
                if choice == 'y':
                    processes.append(Process(target=download_playlist, args=(youtube, playlist['id'], save_location)))

    for process in processes:
        process.start()

# main function
def main():
    credentials = login()
    youtube = build_youtube_music_api(credentials)
    download_all_playlists(youtube, save_location)

if __name__ == '__main__':
    main()
