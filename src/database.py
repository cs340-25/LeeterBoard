import os
from dotenv import load_dotenv

from typing import List, Dict, Tuple
from collections import defaultdict

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
university_avgs = client.leeterboard.university_avgs



# Delete a user by username in the db
def delete_user(username: str) -> None:
    leet_users.delete_one({'username': username})


# Given an document in the db collection, update the school in the entry to the new value
# User in weekly_script.py to add a new users weekly per contest
def upsert_user(username: str, matched_school: str, user_avatar: str, country_code: str, rating: float) -> None:
    leet_users.update_one(
        {'username': username},
        {'$set': {
            'school': matched_school,
            'userAvatar': user_avatar,
            'country_code': country_code,
            'currentRating': rating,
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



# API FUNCTIONS FOR YOU TO CALL IN APP.PY

# This function takes each user's currentRating and calculates the updated average
# Returns a list of tuples (university name, avg contest rating)
def grab_university_info(min_students: int = 0) -> List[Tuple[float, str, int, float]]:
    cursor = university_avgs.find()

    school_info = []
    for school in cursor:
        school_name = school['universityName']
        student_count = school['studentCount']

        # Make sure that the university has previousRankings and weeklyAverages >= 2 length
        if len(school['previousRankings']) < 2 or len(school['weeklyAverages']) < 2: continue

        current_avg_rating = school['currentAverage']
        prev_avg_rating = school['weeklyAverages'][-2]['average'] # Grabs the second to last
        rating_change = current_avg_rating - prev_avg_rating

        if student_count >= min_students:
            school_info.append((current_avg_rating, school_name, student_count, rating_change))

    return school_info


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


    # Do not return users that do not have a previousRatings array with len < 1
    valid_users = []
    for user in users:
        # Factor out users that do not have 1 item in their previousRatings Array
        prev_ratings = user.get('previousRatings', [])
        # Check if it doesn't exist or it has length less than 1
        if not prev_ratings:
            continue

        # Calculate weekly rating change
        current_rating = user['currentRating']
        prev_current_rating = user['previousRatings'][-1]
        user['ratingChange'] = current_rating - prev_current_rating
        valid_users.append(user)

    return valid_users


# Returns a list of every user (not just by school) associated with their rating change
def get_user_rating_changes() -> List[Tuple[(float, str, str)]]:
    cursor = leet_users.find(
        {},
        {'username': 1, 'currentRating': 1, 'previousRatings': 1, 'userAvatar': 1, 'school': 1}
    )

    user_rating_changes = []
    for user in cursor:
        # Factor out users that do not have 1 item in their previousRatings Array
        prev_ratings = user.get('previousRatings', [])
        # Check if it doesn't exist or it has length less than 1
        if not prev_ratings:
            continue

        username = user['username']
        user_avatar = user['userAvatar']
        school = user['school']
        current_rating = user['currentRating']
        prev_rating = user['previousRatings'][-1]
        rating_change = current_rating - prev_rating

        user_rating_changes.append((rating_change, username, user_avatar, school))

    return user_rating_changes


def grab_all_schools_only() -> List[str]:
    schools = set()
    cursor = leet_users.find(
        {},
        {'school': 1}
    )

    for entry in cursor:
        schools.add(entry['school'])

    return list(schools)


def grab_students_per_school():
    school_students = defaultdict(int)
    cursor = leet_users.find(
        {},
        {'school': 1}
    )

    for entry in cursor:
        school_students[entry['school']] += 1
        
    return school_students


def calculate_school_prev_avg() -> List[Tuple[(str, float)]]:
    all_school_prev_ratings = defaultdict(list)
    cursor = leet_users.find(
        {},
        {'school': 1, 'previousRatings': 1}
    )

    for entry in cursor:
        prev_rating = entry['previousRatings'][-1]
        school = entry['school']

        all_school_prev_ratings[school].append(prev_rating)

    school_prev_ratings = []
    for school, ratings in all_school_prev_ratings.items():
        prev_avg_rating = sum(ratings) / len(ratings)
        school_prev_ratings.append((school, prev_avg_rating))
    
    return school_prev_ratings


def calculate_school_curr_avg() -> List[Tuple[(str, float)]]:
    all_school_curr_ratings = defaultdict(list)
    cursor = leet_users.find(
        {},
        {'school': 1, 'currentRating': 1}
    )

    for entry in cursor:
        curr_rating = entry['currentRating']
        school = entry['school']

        all_school_curr_ratings[school].append(curr_rating)

    school_curr_ratings = []
    for school, ratings in all_school_curr_ratings.items():
        curr_avg_rating = sum(ratings) / len(ratings)
        school_curr_ratings.append((school, curr_avg_rating))
    
    return school_curr_ratings


# Grabs all the schools weekly averages for the graphs
def get_school_weekly_averages() -> Dict[str, List[Tuple[str, float]]]:
    cursor = university_avgs.find(
        {},
        {'universityName': 1, 'weeklyAverages': 1}
    )

    school_weekly_averages = defaultdict(list)
    for school in cursor:
        school_name = school['universityName']
        weekly_averages = school['weeklyAverages']
        for rating in weekly_averages:
            school_weekly_averages[school_name].append(rating)
        
    return school_weekly_averages



def grab_homepage_universities(filter) -> List[Tuple[int, int, float, str, int, float]]:
    cursor = university_avgs.find()

    school_info = []
    for school in cursor:
        # If a school has curr and prev rank parameters set to -1, this just means that
        # they have < 5 students
        if 'previousRankings' not in school: continue
        previous_rankings = school['previousRankings']
        if len(previous_rankings) <= 1: continue

        previous_rank = previous_rankings[-2]
        current_rank = school['currentRank']
        # print(f"{school['universityName']}")
        # print(f"curr: {current_rank}, prev: {previous_rank}")
        # print()

        # We are passing in a parameter (filter)
        # True = filter out schools that have -1 in both rank fields (current + previous)
            # This means that the school has less than 5 students (aka not factored into the weekly ranking calculation script)
        # False = do not filter out (aka include all schools) [for universities page]
        if filter:
            if previous_rank != -1 and current_rank != -1:
                school_name = school['universityName']
                student_count = school['studentCount']

                # Calculate average contest rating change (weekly)
                current_avg_rating = school['currentAverage']
                prev_avg_rating = school['weeklyAverages'][-2]['average'] # Grabs the second to last
                rating_change = current_avg_rating - prev_avg_rating

                school_info.append((current_rank, previous_rank, current_avg_rating, school_name, student_count, rating_change))
        else:
            school_name = school['universityName']
            student_count = school['studentCount']

            # Calculate average contest rating change (weekly)
            current_avg_rating = school['currentAverage']
            prev_avg_rating = school['weeklyAverages'][-2]['average'] # Grabs the second to last
            rating_change = current_avg_rating - prev_avg_rating

            school_info.append((current_rank, previous_rank, current_avg_rating, school_name, student_count, rating_change))
            # print(f"{school_name} went {rank_change} from {previous_rank} to {current_rank}")

    return school_info


def get_university_ranks() -> Dict[str, int]:
    cursor = university_avgs.find(
        {},
        {'universityName': 1, 'currentRank': 1, 'previousRankings': 1}
    )

    school_rankings = defaultdict(int)
    for school in cursor:
        school_name = school['universityName']
        current_rank = school['currentRank']

        if 'previousRankings' in school and len(school['previousRankings']) >= 2:
            school_rankings[school_name] = current_rank
        else:
            school_rankings[school_name] = -1
    
    return school_rankings



# Get the information for one university's profile
def get_school_profile_info(school_name: str):
    school_info = university_avgs.find_one(
        {'universityName': school_name},
    )

    if not school_info:
        return None

    school_name = school_info['universityName']
    # print(school_name)
    students = school_info['studentCount']
    curr_rating = school_info['currentAverage']
    prev_rating = school_info['weeklyAverages'][-2]['average']
    rating_change = curr_rating - prev_rating
    rank = school_info['currentRank']

    return (school_name, students, curr_rating, rating_change, rank)


# Grabs and Calculates the information for "University Highlights"
def get_university_highlights(school_name: str) -> Tuple[(str, str, float, float, float)]:
    cursor = leet_users.find(
        {'school': school_name},
    )

    # MOST IMPROVED (current rating - first ever rating on site)
    most_improved = "none"
    most_improved_pts = -1


    # TOP PERFORMER
    top_performer = "none"
    top_performer_rating = -1


    # RATING RANGE
    min_rating = float('inf')
    max_rating = float('-inf')
    for user in cursor:
        curr_rating = user['currentRating']

        # MOST IMPROVED
        # Factor out users that do not have 1 item in their previousRatings Array
        prev_ratings = user.get('previousRatings', [])
        # Check if it doesn't exist or it has length less than 1
        if not prev_ratings:
            continue
        else:
            first_rating = user['previousRatings'][0]
            improved = curr_rating - first_rating
            if improved > most_improved_pts:
                most_improved_pts = improved
                most_improved = user['username']


        min_rating = min(min_rating, curr_rating)

        if curr_rating > max_rating:
            max_rating = curr_rating
            top_performer = user['username']
            top_performer_rating = curr_rating

    # print(f"MOST IMPROVED: {most_improved}")
    # print(f"{min_rating} -> {max_rating}")
    # print(f"TOP PERFORMER: {top_performer}")



    # HISTORICAL PEAK
    school_info = university_avgs.find_one(
        {'universityName': school_name}
    )

    historical_peak = -1
    for entry in school_info['weeklyAverages']:
        rating = entry['average']
        historical_peak = max(historical_peak, rating)

    # print(f"HISTORICAL PEAK: {historical_peak}")


    return (top_performer, top_performer_rating, most_improved, most_improved_pts, min_rating, max_rating, historical_peak)



def get_university_badges(school_name: str):
    school = university_avgs.find_one(
        {'universityName': school_name},
        {'badges': 1}
    )

    return school.get('badges', [])
    

def get_university_rank(school_name: str):
    school = university_avgs.find_one(
        {'universityName': school_name},
        {'mmrRank': 1}
    )

    return school.get('mmrRank', 'NONE')



