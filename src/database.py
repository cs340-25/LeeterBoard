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
def calculate_university_averages() -> List[Tuple[float, str, float]]:
    all_school_ratings = {}
    cursor = leet_users.find()

    for user in cursor:
        school = user['school']
        current_rating = user['currentRating']

        if school not in all_school_ratings:
            all_school_ratings[school] = []

        all_school_ratings[school].append(current_rating)

    avg_school_ratings = []
    for school, ratings in all_school_ratings.items():
        # ONLY calculate its rating averages if there are at least 5 people in the university
        if len(ratings) >= 5:
            # Since we are already calculating the current average rating, we only need
            # to calculate the previous average rating for our rating_change value
            prev_ratings_avg = calculate_university_prev_rating_avg(school)
            current_ratings_avg = sum(ratings) / len(ratings)
            rating_change = current_ratings_avg - prev_ratings_avg

            avg_school_ratings.append((current_ratings_avg, school, rating_change))

    avg_school_ratings.sort(reverse=True)
    return avg_school_ratings


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


def calculate_university_prev_rating_avg(school: str) -> float:
    users = list(leet_users.find({
        'school': school,
    }))

    prev_ratings_sum = 0
    for user in users:
        prev_ratings_sum += user['previousRatings'][-1]

    return prev_ratings_sum / len(users)



