import sys
import os
import requests
import json
import aiohttp
import asyncio

# Add the parent directory (src) to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database

usernames = database.grab_all_usernames()

# Generates a graphql query, given the username as a variable for the request
def generate_user_contest_query(username: str):
    query = """
    query userContestRankingInfo($username: String!) {
        userContestRanking(username: $username) {
            rating
        }
        userContestRankingHistory(username: $username) {
            trendDirection
            rating
        }
    }
    """

    payload = {
        "query": query,
        "variables": {
            "username": username
        }
    }

    return payload


async def fetch_user_contest_history(session, url, headers, payload, username):
    async with session.post(url, headers=headers, data=json.dumps(payload)) as response:
        data = await response.json()
        return {"username": username, "data": data} # Return username associated with data to keep track


async def request_all_user_contest_history(batch_size: int):
    url = "https://leetcode.com/graphql/"
    headers={"Content-Type": "application/json"}


    # Generate all queries for users
    payloads = []
    payload_usernames = []
    for username in usernames:
        payload = generate_user_contest_query(username)
        payloads.append(payload)
        payload_usernames.append(username)


    responses = []
    async with aiohttp.ClientSession() as session:
        for i in range(7005, 7010, batch_size):
            print(f"Making request {i}")

            # 0 -> 9, 10 -> 19
            batch = payloads[i: i + batch_size]
            batch_usernames = payload_usernames[i: i + batch_size]

            # Go through the batch
            tasks = []
            for j, batch_payload in enumerate(batch):
                batch_username = batch_usernames[j]
                tasks.append(fetch_user_contest_history(session, url, headers, batch_payload, batch_username))

            batch_responses = await asyncio.gather(*tasks)
            responses.extend(batch_responses)

            # Sleep after every batch but the last one
            if i + batch_size < len(payloads):
                await asyncio.sleep(0.1)

    return responses


results = asyncio.run(request_all_user_contest_history(10))

for entry in results:
    username = entry['username']
    all_data = entry['data']

    all_contest_history = []
    if all_data['data']: # Check if entry exists
        current_rating = all_data['data']['userContestRanking']['rating']

        print(f"{username}'s current rating: {current_rating}")

        for history_data_point in all_data['data']['userContestRankingHistory']:
            curr_contest_rating = history_data_point['rating']
            all_contest_history.append(curr_contest_rating)

        # Only add the weekly contests to the array starting from back
        all_contest_history.reverse()
        weekly_contest_history = []
        weekly_contest_history.append(all_contest_history[0])
        
        iterator = 2
        while len(weekly_contest_history) <= 150:
            weekly_contest_history.append(all_contest_history[iterator])
            iterator += 1
            weekly_contest_history.append(all_contest_history[iterator])
            iterator += 2

        

        week = 436
        for contest in weekly_contest_history:
            print(f"Weekly Contest {week}: {contest}")
            week -= 1
        print("\n")
    
    
    # database.add_info(username, current_rating, contest_history)





# payload = generate_user_contest_query("coleprice")
# response = requests.post(
#     "https://leetcode.com/graphql/",
#     headers={"Content-Type": "application/json"},
#     data=json.dumps(payload)
# )

# if response.status_code == 200:
#     json_response = response.json();
#     print(json.dumps(json_response))