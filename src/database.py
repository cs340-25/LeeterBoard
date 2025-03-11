import os
from dotenv import load_dotenv

from typing import List, Dict, Tuple

from pymongo import MongoClient
from rapidfuzz.process import extractOne
from rapidfuzz import fuzz
from rapidfuzz.distance import Levenshtein

from data.college_aliases import university_aliases
from data.college_map import university_names


#load env vars
load_dotenv()
mongodb_uri = os.getenv("MONGODB_URI")

client = MongoClient(mongodb_uri)
# Grabs collection from db
leet_users = client.leeterboard.leet_users



# Delete a user by username in the db
def delete_user(username: str) -> None:
    leet_users.delete_one({'username': username})


# Given an document in the db collection, update the school in the entry to the new value
def upsert_user(user: dict, matched_school: str) -> None:
    leet_users.update_one(
        {'username': user['username']},
        {'$set': {
            'school': matched_school
        }},
        upsert=True,
    )


# After the user's new current rating is fetched every saturday, this stores their previous
# current rating in an array of previous ratings and updates their current rating to the new one
def update_user_rating(username: str, new_current_rating: float) -> None:
    leet_users.update_one(
        {'username': username},
        [
            {'$set': {
                'previousRatings': {
                    '$cond': {
                        'if': {'$isArray': '$previousRatings'},
                        'then': {'$concatArrays': ['$previousRatings', ['$currentRating']]},
                        'else': ['$currentRating']
                    }
                },
                'currentRating': new_current_rating
            }}
        ]
    )




# Takes the keys from college_map for fuzzy matching comparison
lowercase_university_names = list(university_names.keys())

# search all-colleges.txt for fuzzy matches
def standardize_school_name(school: str) -> str:
    if len(school) <= 7: return None

    # See if the user input was an alias first
    if school in university_aliases:
        school = university_aliases[school]

    # best match in lowercase_university_names, score, index (which we don't need)
    match, score, _ = extractOne(school, lowercase_university_names, scorer=Levenshtein.normalized_similarity)

    # If a match score of 80 is determined, add university name from list to database
    if score > 0.80:
        return university_names[match]
    else:
        return None


# Grabs all schools from db and updates their info
def standardize_db_universities():
    # Grabs document from leet_users collection
    cursor = leet_users.find()

    # Iterating through each document in the collection
    for user in cursor:
        # Grab original school name in db
        original_school = user['school']

        # Try to match it with a standard one from list
        standardized_school = standardize_school_name(original_school)

        if standardized_school is not None: # Match found
            # Replace the user's original school with the updated name in the db
            upsert_user(user, standardized_school)
        else: # No match found
            # Remove user from db
            leet_users.delete_one({'username': user['username']})






# API FUNCTIONS FOR YOU TO CALL IN APP.PY

# This function takes each user's currentRating and calculates the updated average
# Returns a list of tuples (university name, avg contest rating)
def calculate_university_info() -> List[Tuple[float, str, float]]:
    all_school_current_ratings = {}
    all_school_prev_ratings = {}
    cursor = leet_users.find()

    for user in cursor:
        school = user['school']
        prev_rating = user['previousRatings'][-1]
        current_rating = user['currentRating']

        # Add current rating to school previous ratings map
        if school not in all_school_prev_ratings:
            all_school_prev_ratings[school] = []

        all_school_prev_ratings[school].append(prev_rating)

        # Add current rating to school current ratings map
        if school not in all_school_current_ratings:
            all_school_current_ratings[school] = []

        all_school_current_ratings[school].append(current_rating)


    school_info = []
    for school, ratings in all_school_current_ratings.items():
        # ONLY calculate its rating averages if there are at least 5 people in the university
        if len(ratings) >= 5:
            # Calculate the average rating change as well by getting the previous_ratings_avg as well
            current_ratings_avg = sum(ratings) / len(ratings)
            prev_ratings_avg = sum(all_school_prev_ratings[school]) / len(all_school_prev_ratings[school])
            rating_change = current_ratings_avg - prev_ratings_avg
            
            school_info.append((current_ratings_avg, school, rating_change))

    return school_info


def grab_all_usernames() -> List[str]:
    cursor = leet_users.find()

    usernames = []
    for user in cursor:
        usernames.append(user['username'])

    return usernames


# We need to make this function also return a value that is the user's rating change
def get_users_by_school(school: str) -> List[dict]:
    users = list(leet_users.find({
        'school': school,
    }))


    for user in users:
        # Grab their current rating
        current_rating = user['currentRating']
        prev_current_rating = user['previousRatings'][-1]
        user['ratingChange'] = current_rating - prev_current_rating

    return users


# Returns a list of every user (not just by school) associated with their rating change
def get_user_rating_changes() -> List[Tuple[(float, str)]]:
    cursor = leet_users.find(
        {},
        {'username': 1, 'currentRating': 1, 'previousRatings': 1}
    )

    user_rating_changes = []
    for user in cursor:
        username = user['username']
        current_rating = user['currentRating']
        prev_rating = user['previousRatings'][-1]
        rating_change = current_rating - prev_rating

        user_rating_changes.append((rating_change, username))

    return user_rating_changes

        
