import requests
import json

import os
from dotenv import load_dotenv

load_dotenv("./.env")

API_KEY = os.getenv("API_KEY")

CHANNEL_HANDLE = "MrBeast"

maxResults = 50

def get_playList_id():
    
    try:

        url = f"https://youtube.googleapis.com/youtube/v3/channels?part=contentDetails&forHandle={CHANNEL_HANDLE}&key={API_KEY}"

        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        # print(json.dumps(data, indent=4))
        channel_items = data["items"][0]
        channel_playlistId = channel_items["contentDetails"]["relatedPlaylists"]["uploads"]
        # print(channel_playlistId)

        return channel_playlistId
    except requests.exceptions.RequestException as e:
        raise e
        



def get_video_ids(playListId):

    video_ids = []

    base_url = f"https://youtube.googleapis.com/youtube/v3/playlistItems?part=contentDetails&maxResults={maxResults}&playlistId={playListId}&key={API_KEY}"

    pageToken = None

    try:
        # runnning the while True: loop as long as there is a nextPageToken
        while True:
            url = base_url
            # if there is a pageToken, add it to the url (initially it is none)
            if pageToken:
                url += f"&pageToken={pageToken}"

            # getting response using the new url with pageToken
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            # using a for loop to append each video_id to video_ids list
            for item in data.get("items", []):
                video_id = item["contentDetails"]["videoId"]
                video_ids.append(video_id)
            
            # updaing pageToken to nextPageToken to make sure loop stops when there is no next page and gets out of while True: loop
            pageToken = data.get("nextPageToken")
            
            # if pageToken is None, break out of the loop
            if not pageToken:
                break
        
        return video_ids
        

    except requests.exceptions.RequestException as e:
        raise e

if __name__ == "__main__":
    playListId = get_playList_id() 
    get_video_ids(playListId)
    