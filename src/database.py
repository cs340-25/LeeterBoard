import os
from dotenv import load_dotenv

from typing import List, Set, Dict

from pymongo import MongoClient
from rapidfuzz import process, fuzz


#load env vars
load_dotenv()
mongodb_uri = os.getenv("MONGODB_URI")

client = MongoClient(mongodb_uri)
leet_users = client.leeterboard.leet_users


def _serialize_users(users: List[dict]) -> List[dict]:
    for user in users:
        user['_id'] = str(user['_id'])
    return users


def upsert_user(user: dict) -> None:
    user['username'] = user['username'].lower()
    user['contestRating'] = float(user['contestRating'])
    leet_users.update_one(
        {'username': user['username']},
        {'$set': {
            'contestRating': user['contestRating'],
            'username': user['username'],
            'userAvatar': user['userAvatar'],
            'school': user['school'],
        }},
        upsert=True,
    )


def get_users_by_school(school: str) -> List[dict]:
    users = list(leet_users.find({
        'school': school,
    }))

    return _serialize_users(users)






# University list for matching to original [lower matching name, original name]
school_dict = {}

# Open file of all colleges
with open('src/data/all-colleges.txt', 'r', encoding='utf-8') as f:
    for line in f:
        original_name = line.rsplit(" (", 1)[0]
        matching_name = original_name.lower()
        school_dict[matching_name] = original_name

# Lowercase list for fuzzy matching
school_list_lower = list(school_dict.keys())

def standardize_school_name(school: str) -> str:
    school_input = school.lower().strip()
    # This calculates a similarity score that assigns match to the best match in 'school_list_lower'
    match, score, _ = process.extractOne(school_input, school_list_lower, scorer=fuzz.ratio)
    
    if score > 80:
        return school_dict[match]
    else:
        return None



# Grabs all schools' contest rating averages
def grab_all_school_ratings() -> Dict[str, List[float]]:
    cursor = leet_users.find(
        {
            'school': {
                '$ne': None,
                '$regex': 'University'
            }
        },
        {'school': 1, 'contestRating': 1, '_id': 0}
    )

    school_ratings = {}
    for entry in cursor:
        original_school = entry['school']
        standardized_school = standardize_school_name(original_school)

        if standardized_school is None: continue

        rating = entry['contestRating']

        if standardized_school not in school_ratings:
            school_ratings[standardized_school] = []

        school_ratings[standardized_school].append(rating)

    return school_ratings