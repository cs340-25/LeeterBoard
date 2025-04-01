import sys
import os
import asyncio
import aiohttp

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database
usernames = database.grab_all_usernames()

# Generate the individual query
def generate_user_rating_query(username: str):
    query = """
    query userContestRankingInfo($username: String!) {
        userContestRanking(username: $username) {
            rating
        }
    }
    """

    payload = {
        'query': query,
        'variables': {
            'username': username
        }
    }

    return payload


async def fetch_user_rating(session, url, headers, payload, username):
    async with session.post(url, headers=headers, json=payload) as response:
        content = await response.json()
        return {'username': username, 'content': content}


# Make all of the requests asynchronously
async def request_all_user_ratings(batch_size: int):
    url = "https://leetcode.com/graphql/"
    headers={"Content-Type": "application/json"}

    # Pre-generate all queries
    payloads = []
    payload_usernames = []
    for user in usernames:
        payload = generate_user_rating_query(user)
        payloads.append(payload)
        payload_usernames.append(user)

    print(len(payloads))

    # Make all requests
    all_responses = []
    async with aiohttp.ClientSession() as session:
        for i in range(3070, 3080, batch_size):
            print(f"Making request {i}")
            batch_payloads = payloads[i: i + batch_size] # Gives us the payloads for this batch
            batch_usernames = payload_usernames[i: i + batch_size] # Gives us usernames correlated with each payload

            # Loop through each payload in the batch
            batch_tasks = []
            for j, batch_payload in enumerate(batch_payloads):
                curr_username = batch_usernames[j]

                # Create the request
                curr_task = fetch_user_rating(session, url, headers, batch_payload, curr_username)
                batch_tasks.append(curr_task)

            # After loop, send out requests asynchronously
            batch_responses = await asyncio.gather(*batch_tasks)
            all_responses.extend(batch_responses)

            if i + batch_size < len(payloads):
                await asyncio.sleep(1)

    return all_responses


final_results = asyncio.run(request_all_user_ratings(10))

req = 1
for entry in final_results:
    print(req)
    req += 1

    username = entry['username']

    # Grab the field in which the 'rating' is contained in, this field will always be present, even if
    # rating is null for some reason
    user_contest_ranking_field = entry.get('content', {}).get('data', {}).get('userContestRanking')
    
    if username == 'deleted_user' or user_contest_ranking_field is None:
        # Delete this user from the database
        print(f"ERROR: {username} was deleted or did not have a contest rating -> Removing from DB")
        # REMOVE FROM DB
        database.delete_user(username)
    else:
        new_current_rating = user_contest_ranking_field['rating']
        database.update_user_rating(username, new_current_rating)

