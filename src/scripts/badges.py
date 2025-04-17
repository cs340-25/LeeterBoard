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

# Rank-Threshold Based Badges
def rank_threshold_badges():
    """
    Awards the rank-threshold based badges (Summit Champion, Podium Elite, Vanguard 5, Prestige 10, Prime 25) 
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
        

# Star Ascendant
def star_ascendant():
    user_rating_changes = database.get_user_rating_changes()
    user_rating_changes.sort(reverse=True)

    for rating_change, username, _, school in user_rating_changes[:5]:
        print(f"{username} is on Trending Users with rating change of {rating_change}, so {school} has earned STAR ASCENDANT")
        university_avgs.update_one(
            {'universityName': school},
            {'$addToSet': {'badges': 'Star Ascendant'}},
            upsert=True
        )


# Trending Trailblazer
def trending_trailblazer():
    school_rating_changes = database.grab_university_info(5)
    school_rating_changes.sort(key=lambda x: x[3], reverse=True)

    for _, school_name, _, rating_change in school_rating_changes[:5]:
        print(f"{school_name} is on Trending Universities with a rating change of {rating_change}, so {school_name} has earned TRENDING TRAILBLAZER")
        university_avgs.update_one(
            {'universityName': school_name},
            {'$addToSet': {'badges': 'Trending Trailblazer'}},
            upsert=True
        )


# Rank-Change Based Badges
def rank_change_badges():
    cursor = university_avgs.find(
        {}
    )

    for school in cursor:
        if 'previousRankings' not in school or len(school['previousRankings']) <= 1: continue
        previous_rankings = school['previousRankings']

        # Momentum Mastery
        if len(previous_rankings) >= 3:
            # Check if rating improved over past 3 weeks
            valid = True
            start = len(previous_rankings) - 3
            for i in range(start + 1, len(previous_rankings)):
                current_rank = previous_rankings[i]
                previous_rank = previous_rankings[i - 1]

                # If the current rank is higher, that means they went down in rank
                if current_rank >= previous_rank:
                    valid = False
                    break;

            if valid:
                school_name = school['universityName']
                print(f"{school_name} increased rank over the course of 3 weeks, awarding Momentum Mastery badge")
                
                # Give the university the badge
                university_avgs.update_one(
                    {'universityName': school_name},
                    {'$addToSet': {'badges': 'Momentum Mastery'}},
                    upsert=True
                )


        # Rank Resurrection
        if len(previous_rankings) >= 3:
            previous_rankings = school['previousRankings']
            current_rank = school['currentRank']
            previous_rank = previous_rankings[-2]
            three_ranks_ago = previous_rankings[-3]

            # Three Ranks Ago = 58 -> Previous Rank = 60 -> Current Rank = 55

            # Check if the school first dropped, and then increased by 5+ spots AFTER that (hence resurrection)
            if three_ranks_ago < previous_rank and previous_rank - current_rank >= 5:
                school_name = school['universityName']
                print(f"{school_name}'s rank went from {previous_rank} to {current_rank}, awarding them 'Rank Resurrection'")

                university_avgs.update_one(
                    {'universityName': school_name},
                    {'$addToSet': {'badges': 'Rank Resurrection'}},
                    upsert=True
                )

        
        # Skyrocket Surge + Rapid Ascent
        if len(previous_rankings) >= 2:
            previous_rankings = school['previousRankings']
            current_rank = school['currentRank']
            previous_rank = previous_rankings[-2]

            # Skyrocket Surge
            # Check if the school increased by 10+ spots
            if previous_rank - current_rank >= 10:
                school_name = school['universityName']
                print(f"{school_name}'s rank went from {previous_rank} to {current_rank}, awarding them 'Skyrocket Surge'")

                university_avgs.update_one(
                    {'universityName': school_name},
                    {'$addToSet': {'badges': 'Skyrocket Surge'}},
                    upsert=True
                )

            # Rapid Ascent
            # Check if the school increased by 10+ spots
            if previous_rank - current_rank >= 5:
                school_name = school['universityName']
                print(f"{school_name}'s rank went from {previous_rank} to {current_rank}, awarding them 'Rapid Ascent'")

                university_avgs.update_one(
                    {'universityName': school_name},
                    {'$addToSet': {'badges': 'Rapid Ascent'}},
                    upsert=True
                )


# Ascension Streak
def ascension_streak():
    cursor = university_avgs.find(
        {},
        {'universityName': 1, 'weeklyAverages': 1}
    )


    for school in cursor:
        if 'weeklyAverages' in school and len(school['weeklyAverages']) <= 5: continue

        school_name = school['universityName']
        weekly_averages = school['weeklyAverages']
        start = len(weekly_averages) - 5

        valid = True
        for i in range(start + 1, len(weekly_averages)):
            curr_contest_rating = weekly_averages[i]['average']
            prev_contest_rating = weekly_averages[i - 1]['average']

            if curr_contest_rating <= prev_contest_rating:
                valid = False
                break

        if valid:
            # Add Badge to University
            print(f"{school_name} increased contest rating over the course of 5 weeks, awarding Ascension Streak Badge")
            university_avgs.update_one(
                {'universityName': school_name},
                {'$addToSet': {'badges': 'Ascension Streak'}},
                upsert=True
            )


# Rising Stars
def rising_stars():
    cursor = leet_users.find(
        {},
        {'school': 1, 'username': 1, 'currentRating': 1, 'previousRatings': 1}
    )


    university_qualified_students = defaultdict(int)
    for user in cursor:
        if 'previousRatings' not in user or len(user['previousRatings']) < 1: continue
        prev_ratings = user['previousRatings']

        curr_rating = user['currentRating']
        prev_rating = prev_ratings[-1]

        if curr_rating > prev_rating:
            school_name = user['school']
            university_qualified_students[school_name] += 1

    for school_name, qualified_users in university_qualified_students.items():
        # Universities who had 3 students increase their rating in 1 week
        if qualified_users >= 3:
            print(f"{school_name} had 3 students increase this week, awarding them Rising Stars badge")
            university_avgs.update_one(
                {'universityName': school_name},
                {'$addToSet': {'badges': 'Rising Stars'}},
                upsert=True
            )

rank_threshold_badges() # Summit Champion, Podium Elite, Vanguard 5, Prestige 10, Prime 25
top_gun() # Top Gun
talent_factory() # Talent Factory

star_ascendant() # Star Ascendant
trending_trailblazer() # Trending Trailblazer
rank_change_badges() # Momentum Mastery, Rank Resurrection, Skyrocket Surge, Rapid Ascent 
ascension_streak() # Ascension Streak
rising_stars() # Rising Stars