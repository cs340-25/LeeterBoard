import requests
import asyncio
import aiohttp
import json
import time

from pymongo import MongoClient


import os
from dotenv import load_dotenv
# Load csrftoken from env
csrftoken = os.getenv("CSRFTOKEN")

# # Load mongodb
# mongodb_uri = os.getenv("MONGODB_URI")
# client = MongoClient(mongodb_uri)
# leet_users = client.leeterboard.leet_users





# STEP 1: Binary search to find max page size of the Weekly Contest
def find_max_page(contest_id: int) -> int:
    left = 1
    right = 7500

    max_page = -1
    while(left <= right):
        mid = left + (right - left) // 2

        # Gives us permission to make the request (Avoid 403)
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Mobile Safari/537.36",
            "Referer": "https://leetcode.com/contest/weekly-contest-437/ranking/1229/?region=global_v2",
            "Content-Type": "application/json"
        }

        # Slight delay to avoid rate limiting
        time.sleep(0.25)

        response = requests.get(
            f"https://leetcode.com/contest/api/ranking/weekly-contest-{contest_id}/?pagination={mid}&region=global_v2",
            headers=headers
        )

        # Even if the page is too large, it should still return a 200, but with empty data
        if response.status_code == 200:
            data = response.json()
            if data and data['user_num']:
                # We have a valid page, update max_page, and search for a larger one
                max_page = mid
                left = mid + 1

                print(f"VALID... INCREASING MIN TO {mid}")
            else:
                # We have selected a page too large, search for a smaller one
                right = mid - 1
                print(f"INVALID.. SHRINKING MAX TO {mid}")

    return max_page






# STEP 2: Grab all users from the Weekly Contest

# Simply returns the proper url with the modified portions
def get_weekly_contest_url(contest_id: int, page: int) -> str:
    return f"https://leetcode.com/contest/api/ranking/weekly-contest-{contest_id}/?pagination={page}&region=global_v2"


# Makes the individual HTTP request and waits for the response body and parses it as JSON
async def fetch_contest_page(session, url, headers, cookies):
    async with session.get(url, headers=headers, cookies=cookies, ssl=False) as response:
        return await response.json()


# Performs all of the asynchronous requests
async def request_all_contest_pages(batch_size: int):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    }

    # Generate all URLs (1 per page)
    all_urls = []
    contest_number = 444
    contest_max_pages = 50

    # Add a delay from the last request in find_max_page()
    time.sleep(1)

    for page_number in range(1, contest_max_pages):
        all_urls.append(get_weekly_contest_url(contest_number, page_number))

    responses = []
    async with aiohttp.ClientSession() as session:
        # Process requests in batches
        # 0 -> 9, 10 -> 19, 20 -> 29k
        for i in range(0, 30, batch_size):
            print(f"Making request {i}")
            batch = all_urls[i:i + batch_size]
            
            # Go through the batch
            tasks = []
            for batch_url in batch:
                tasks.append(fetch_contest_page(session, batch_url, headers))
            
            # Send out all batched requests and store responses
            batch_responses = await asyncio.gather(*tasks)

            responses.extend(batch_responses)

            if i + batch_size < len(all_urls):
                await asyncio.sleep(1)

    return responses

# Results is the giant list of responses
results = asyncio.run(request_all_contest_pages(5))

all_new_users = []
for data in results:
    for user in data['total_rank']:
        if(user['country_code'] == 'US'):
            all_new_users.append(user['username'])

# Print all the new users
print(len(all_new_users))
    






# STEP 3: Filter out users that are already in our database
# for username in all_new_users:
#     username = username.lower()
#     # Check if the user exists
#     result = leet_users.find_one({'username': username})

#     if result:
#         print(f"{username} = FOUND")
#     else:
#         # Since the user's school was not included in their original request response, we need to
#         # make the graphQL query to grab their user profile -> if they have a school -> run the fuzzy finding algorithms
#         print(f"{username} = NOT FOUND")