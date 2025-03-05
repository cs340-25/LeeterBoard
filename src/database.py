import os
from dotenv import load_dotenv

from typing import List, Dict, Tuple

from pymongo import MongoClient
from rapidfuzz.process import extractOne
from rapidfuzz import fuzz
# from rapidfuzz.distance import Levenshtein

from data.college_aliases import university_aliases


#load env vars
load_dotenv()
mongodb_uri = os.getenv("MONGODB_URI")

client = MongoClient(mongodb_uri)
# Grabs collection from db
leet_users = client.leeterboard.leet_users

def _serialize_users(users: List[dict]) -> List[dict]:
    for user in users:
        user['_id'] = str(user['_id'])
    return users


def get_users_by_school(school: str) -> List[dict]:
    users = list(leet_users.find({
        'school': school,
    }))

    return _serialize_users(users)




# Given an document in the db collection, update the school in the entry to the new value
def upsert_user(user: dict, matched_school: str) -> None:
    leet_users.update_one(
        {'username': user['username']},
        {'$set': {
            'school': matched_school
        }},
        upsert=True,
    )


# Opens file and stores university names in a map, as well as a list for fuzzy finding
school_names = {}
def open_file():
    with open('src/data/all-colleges.txt') as file:
        for line in file:
            school_name = line.rsplit(" (", 1)[0]
            school_name_lower = school_name.lower()
            
            school_names[school_name_lower] = school_name

open_file()
lowercase_university_names = list(school_names.keys())


# search all-colleges.txt for fuzzy matches
def standardize_school_name(school: str) -> str:
    # See if the user input was an alias first
    if school in university_aliases:
        school = university_aliases[school]

    # best match in lowercase_university_names, score, index (which we don't need)
    match, score, _ = extractOne(school, lowercase_university_names, scorer=fuzz.token_set_ratio)

    # If a match score of 80 is determined, add university name from list to database
    if score > 80:
        return school_names[match]
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
            updated_doc = leet_users.find_one({'username': user['username']})

            if updated_doc:
                # Making sure its actually deleting the doc
                print('doc not deleted')




# API FUNCTIONS FOR YOU TO CALL IN APP.PY


# Returns a list of tuples (university name, avg contest rating)
def calculate_university_averages() -> List[Tuple[float, str]]:
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
        avg = round(sum(ratings) / len(ratings), 2)
        avg_school_ratings.append((avg, school))

    avg_school_ratings.sort(reverse=True)
    return avg_school_ratings