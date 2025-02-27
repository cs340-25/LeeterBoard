import os
from dotenv import load_dotenv

from typing import List

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