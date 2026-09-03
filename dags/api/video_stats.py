import requests
import json
from datetime import date

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
    


def extract_video_data(video_ids):
    extracted_data = []

    # we need a helper function to be able to add 50 video_ids comma separated in API request for URL

    def batch_list(video_id_list, batch_size):
        # yield helps return multiple batches one after the other
        for video_id in range(0, len(video_id_list), batch_size):
            yield video_id_list[video_id: video_id + batch_size]

    

    try:
        # getting a list of video_ids in batches of 50
        for batch in batch_list(video_ids, maxResults):
            # joining them separating them by a comma into a single string and using the video_ids_str in the url
            video_ids_str = ",".join(batch)
            
            url = f"https://youtube.googleapis.com/youtube/v3/videos?part=contentDetails&part=snippet&part=statistics&id={video_ids_str}&key={API_KEY}"

            # getting a json response - this will give a response for 50 videos
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            # for each item inside data['items'] - each item represents data for 1 video so we loop over each item to get specific data for each video
            for item in data.get("items", []):
                # assign variables to get smaller sections of the json
                video_id = item["id"]
                snippet = item["snippet"]
                contentDetails = item["contentDetails"]
                statistics = item["statistics"]
                
                # creating a video_data dictionary to get specific data for each video and appending into extracted data list
                video_data = {
                    "video_id": video_id,
                    "title": snippet["title"],
                    "publishedAt": snippet['publishedAt'],
                    "duration": contentDetails["duration"],
                    "viewCount": statistics.get("viewCount", None),
                    "likeCount": statistics.get("likeCount", None),
                    "commentCount": statistics.get("commentCount", None)            
                }

                extracted_data.append(video_data)
        # extracted data list will have dictionaries containing specific data for all videos
        return extracted_data
    
    except requests.exceptions.RequestException as e:
        raise e


def save_to_json(extracted_data):
    file_path = f"./data/YT_json_{date.today()}.json"

    with open(file_path, "w", encoding="utf-8") as json_outfile:
        json.dump(extracted_data, json_outfile, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    playListId = get_playList_id() 
    video_ids = get_video_ids(playListId)
    video_data = extract_video_data(video_ids)
    save_to_json(video_data)
    