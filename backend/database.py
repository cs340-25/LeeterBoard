from typing import List

from pymongo import MongoClient

client = MongoClient('mongodb+srv://colepricecollege:5Hn7WKdqFZa91UwT@cluster0.s3baj.mongodb.net/')
leet_users = client.leeterboard.leet_users


def upsert_user(user: dict) -> None:
    user['username'] = user['username'].lower()
    leet_users.update_one(
        {'username': user['username']},
        {'$set': {
            'contestRating': user['currentRating'],
            'username': user['username'],
            'userAvatar': user['userAvatar'],
            'school': user['school'],
        }},
        upsert=True,
    )


def get_users_by_school(school: str) -> List[dict]:
    return list(leet_users.find({
        'school': school,
    }))