import time
import requests
from collections import defaultdict

# Import connection to mongodb
import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Connect files to database (to use database function)
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database

load_dotenv()
mongodb_uri = os.getenv("MONGODB_URI")
client = MongoClient(mongodb_uri)
leet_users = client.leeterboard.leet_users

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

# max_page = find_max_page(444)
# print(max_page)



# STEP 2: Grab the users from all contest pages
def generate_url(contest_id: int, page: int) -> str:
    return f"https://leetcode.com/contest/api/ranking/weekly-contest-{contest_id}/?pagination={page}&region=global_v2"

def get_users_from_contest(contest: int):
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Mobile Safari/537.36",
        "Referer": "https://leetcode.com/contest/weekly-contest-437/ranking/1229/?region=global_v2",
        "Content-Type": "application/json"
    }

    all_urls = []
    contest_id = contest
    contest_max_pages = 20

    for page in range(1, contest_max_pages):
        all_urls.append(generate_url(contest_id, page))

    all_responses = []
    for url in all_urls:
        print("Requesting page...")
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            if data and data['user_num']:
                all_responses.append(data)
            else:
                print("failure")

    return all_responses
    
responses = get_users_from_contest(444)

# Filtering out users that countryCode is not United States
all_users = []
for data in responses:
    for user in data['total_rank']:
        if(user['country_code'] == 'US'):
            username = user['user_slug'].lower()
            all_users.append(username)




# STEP 3: Filter out users that are already in our DB
new_users = []
for username in all_users:
    result = leet_users.find_one({'username': username})

    if not result:
        new_users.append(username)


# STEP 4: Filter out users with no school on their LeetCode profile

# Generate the GraphQL Query to grab info from their profile
def generate_user_school_query(username: str) -> str:
    query = """
    query userPublicProfile($username: String!) {
        matchedUser(username: $username) {
            profile {
                school
                userAvatar
            }
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


# Generate the GraphQL Query to grab their current contest rating
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



def request_user_school(new_users):
    url = "https://leetcode.com/graphql/"
    headers={"Content-Type": "application/json"}

    users_info = []
    for user in new_users:
        profile_payload = generate_user_school_query(user)
        print(f"Making request for {user}")
        profile_response = requests.get(url=url, headers=headers, json=profile_payload)

        # Grab the user's profile info
        if profile_response.status_code == 200:
            profile_info = profile_response.json()
            if profile_info:
                school = profile_info['data']['matchedUser']['profile']['school']
                user_avatar = profile_info['data']['matchedUser']['profile']['userAvatar']
                country_code = "US"

                if school is not None and user_avatar is not None and country_code is not None:
                    # If we've secured the previous 3 data points, we should now grab the contest rating
                    rating_payload = generate_user_rating_query(user)
                    rating_response = requests.get(url=url, headers=headers, json=rating_payload)

                    if rating_response.status_code == 200:
                        rating_info = rating_response.json()
                        if rating_info:
                            rating = rating_info['data']['userContestRanking']['rating']

                            users_info.append((user, school, user_avatar, country_code, rating))
                    else:
                        print(f"Failed to Fetch User Contest Rating: {rating_response.status_code}")
        else:
            print(f"Failed to Fetch User Profile: {profile_response.status_code}")


    return users_info

# At this point we now have a list of users that:
# Are in the US
# Are not in out Database
# Have a school on their LeetCode profile

# So, now we need to run the rapidfuzz algorithm that can match their school to one of our standard names
# If we find a match, add this new user to the database
users_info = request_user_school(new_users)
for username, school, user_avatar, country_code, rating in users_info:
    school = school.lower().strip()
    matched_school = database.standardize_school_name(school)

    if matched_school:
        print(f"{username}:")
        print(f"  {matched_school}")
        print(f"  {user_avatar}")
        print(f"  {country_code}")
        print(f"  {rating}")
        print()

        # Add user + their information to DB
        database.upsert_user(username, matched_school, user_avatar, country_code, rating)


        # This is correctly adding the user to the database, but it crashes the site
        # because the site tries to pull field for every user that don't yet exist
        # for these new ones (userAvatar, etc.)
        # Figure out what fields are being pulled
    else:
        print("Not adding")





