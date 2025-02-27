import json
from typing import List


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
    


def main():
    print('temp')
    users = read_users_json('../data/users.json')
    print(users[-1:])

if __name__ == '__main__':
    main()