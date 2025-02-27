import json
from typing import List

import database


def read_users_json(filename: str) -> List[dict]:
    """
    Example return:
        [
            {
                'currentRating': '3702.788', 
                'username': 'fjzzq2002', 
                'userAvatar': 'https://assets.leetcode.com/users/default_avatar.jpg', 
                'school': None
            }
        ]
    """
    with open(filename, 'r') as f:
        users = json.load(f)
        
    return users


def upsert_users_to_mongodb(users: List[dict]) -> None:
    total = len(users)
    for i, user in enumerate(users):
        database.upsert_user(user)
        print(f'upserted user {i + 1} / {total}')


def main():
    print('reading json file')
    users = read_users_json('./src/data/users.json')
    print('json file read')
    print('upserting users to mongodb')
    upsert_users_to_mongodb(users)
    print('done')

if __name__ == '__main__':
    main()