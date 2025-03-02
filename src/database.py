import os
from dotenv import load_dotenv

from typing import List, Set, Dict

from pymongo import MongoClient


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





# Grabs all schools
def grab_all_school_ratings() -> Dict[str, List[float]]:
    cursor = leet_users.find(
        {
            'school': { '$ne': None }
        },
        {'school': 1, 'contestRating': 1, '_id': 0}
    )

    school_ratings = {}
    for entry in cursor:
        school = entry['school']
        rating = entry['contestRating']

        if school not in school_ratings:
            school_ratings[school] = []

        school_ratings[school].append(rating)

    return school_ratings


