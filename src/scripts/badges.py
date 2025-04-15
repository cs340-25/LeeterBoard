import sys
import os
from dotenv import load_dotenv

from collections import defaultdict

from pymongo import MongoClient

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database


#load env vars
load_dotenv()
mongodb_uri = os.getenv("MONGODB_URI")

client = MongoClient(mongodb_uri)
# Grabs collection from db
university_avgs = client.leeterboard.university_avgs
leet_users = client.leeterboard.leet_users

# Rank-Based Badges
def rank_badges():
    """
    Awards the rank-based badges (Summit Champion, Podium Elite, Vanguard 5, Prestige 10, Prime 25) 
    to schools that have reached the respective rank threshold for each badge
    """
    cursor = university_avgs.find(
        {},
        {'universityName': 1, 'currentRank': 1}
    )

    for school in cursor:
        school_name = school['universityName']
        rank = school['currentRank']

        if rank == -1: continue

        if rank == 1:
            university_avgs.update_one(
                {'universityName': school_name},
                {'$addToSet': {'badges': 'Summit Champion'}},
                upsert = True
            )

        if rank <= 3:
            university_avgs.update_one(
                {'universityName': school_name},
                {'$addToSet': {'badges': 'Podium Elite'}},
                upsert = True
            )

        if rank <= 5:
            university_avgs.update_one(
                {'universityName': school_name},
                {'$addToSet': {'badges': 'Vanguard 5'}},
                upsert = True
            )

        if rank <= 10:
            university_avgs.update_one(
                {'universityName': school_name},
                {'$addToSet': {'badges': 'Prestige 10'}},
                upsert = True
            )

        if rank <= 25:
            university_avgs.update_one(
                {'universityName': school_name},
                {'$addToSet': {'badges': 'Prime 25'}},
                upsert = True
            )
    
    print('ASSIGNED RANK BADGES')
    return


# Top Gun
def top_gun():
    """
    Awards the 'Top Gun' badge to schools that have/had the #1 student site-wide
    in their university
    """
    cursor = leet_users.find(
        {},
        {'username': 1, 'currentRating': 1, 'school': 1}
    )

    best_rating = -1
    best_user = ""
    best_school = ""
    for user in cursor:
        rating = user['currentRating']
        username = user['username']
        school = user['school']


        if rating > best_rating:
            best_user = username
            best_rating = rating
            best_school = school

    print(f"{best_user}: {best_rating} -> {best_school}")
    university_avgs.update_one(
        {'universityName': best_school},
        {'$addToSet': {'badges': 'Top Gun'}},
        upsert=True
    )
    

# Talent Factory
def talent_factory():
    """
    Awards the 'Talent Factory' badge to schools with 5+ users having 1750+ rating
    """
    cursor = leet_users.find(
        {},
        {'school': 1, 'currentRating': 1}
    )

    school_qualified_cnt = defaultdict(int)
    for user in cursor:
        school = user['school']
        rating = user['currentRating']

        if not school or rating is None:
            continue

        if rating >= 1750:
            school_qualified_cnt[school] += 1
    

    for school, qualified_users in school_qualified_cnt.items():
        if qualified_users >= 5:
            # Give school the badge
            print(f"{school} has {qualified_users} students >= 1750 rating, EARN TALENT FACTORY BADGE")
            university_avgs.update_one(
                {'universityName': school},
                {'$addToSet': {'badges': 'Talent Factory'}},
                upsert=True
            )



def crown_snatcher():
    """
    Awards the 'Crown Snatcher' badge to schools who have stolen the rank 1 spot
    For this function to work in all cases, when we calculate the ranks for universities,
    we need to set 'beenRankOne' back to false if a university is no longer rank 1, so
    universities who lost the rank 1 spot at some point in the past still have the chance
    to earn it back, as well as this mythic badge
    """
    cursor = university_avgs.find(
        {},
        {'universityName': 1, 'currentRank': 1, 'beenRankOne': 1}
    )

    for school in cursor:
        name = school['universityName']
        rank = school['currentRank']
        been_rank_one = school['beenRankOne']

        if rank == 1 and been_rank_one == False:
            # Update beenRankOne to True
            university_avgs.update_one(
                {'universityName': name},
                {'$set': {'beenRankOne': True}}
            )
            print(f"{name} has earned CROWN SNATCHER")
        

def fix_prev_ratings():
    cursor = university_avgs.find(
        {}
    )

    for school in cursor:
        name = school['universityName']
        current_rank = school['currentRank']
        prev_rank = school['previousRank']

        university_avgs.update_one(
            {'universityName': name},
            {'$unset': {'previousRank': ""}}
        )

        university_avgs.update_one(
            {'universityName': name},
            {'$push': {
                'previousRankings': {
                    '$each': [prev_rank, current_rank]
                }
            }},
            upsert=True
        )

# Star Ascendant
def star_ascendant():
    user_rating_changes = database.get_user_rating_changes()
    user_rating_changes.sort(reverse=True)

    for rating_change, username, _, school in user_rating_changes[:5]:
        print(f"{username} is on Trending Users with rating {rating_change}, so {school} has earned STAR ASCENDANT")
        university_avgs.update_one(
            {'universityName': school},
            {'$addToSet': {'badges': 'Star Ascendant'}},
            upsert=True
        )


def fix():
    cursor = university_avgs.find(
        {},
    )

    for school in cursor:
        last_rank = school['previousRankings'][-2]
        name = school['universityName']

        university_avgs.update_one(
            {'universityName': name},
            {
                '$set': {'currentRank': last_rank},
                '$pop': {'previousRankings': 1}
            }
        )

fix()