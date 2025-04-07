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
def upsert_user(user: dict, matched_school: str) -> None:
    leet_users.update_one(
        {'username': user['username']},
        {'$set': {
            'school': matched_school
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






# API FUNCTIONS FOR YOU TO CALL IN APP.PY

# This function takes each user's currentRating and calculates the updated average
# Returns a list of tuples (university name, avg contest rating)
def grab_university_info(min_students: int = 0) -> List[Tuple[float, str, int, float]]:
    cursor = university_avgs.find()

    school_info = []
    for school in cursor:
        school_name = school['universityName']
        student_count = school['studentCount']
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


    for user in users:
        # Grab their current rating
        current_rating = user['currentRating']
        prev_current_rating = user['previousRatings'][-1]
        user['ratingChange'] = current_rating - prev_current_rating

    return users


# Returns a list of every user (not just by school) associated with their rating change
def get_user_rating_changes() -> List[Tuple[(float, str, str)]]:
    cursor = leet_users.find(
        {},
        {'username': 1, 'currentRating': 1, 'previousRatings': 1, 'userAvatar': 1}
    )

    user_rating_changes = []
    for user in cursor:
        username = user['username']
        user_avatar = user['userAvatar']
        current_rating = user['currentRating']
        prev_rating = user['previousRatings'][-1]
        rating_change = current_rating - prev_rating

        user_rating_changes.append((rating_change, username, user_avatar))

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



def grab_homepage_universities() -> List[Tuple[int, int, float, str, int, float]]:
    cursor = university_avgs.find()

    school_info = []
    for school in cursor:
        # This function will only return a list of schools with a current rank and previous rank
        # So, previousRank != 0 and currentRank != 0
        previous_rank = school['previousRank']
        current_rank = school['currentRank']

        if previous_rank != -1 and current_rank != -1:
            school_name = school['universityName']
            student_count = school['studentCount']

            # Calculate average contest rating change (weekly)
            current_avg_rating = school['currentAverage']
            prev_avg_rating = school['weeklyAverages'][-2]['average'] # Grabs the second to last
            rating_change = current_avg_rating - prev_avg_rating

            school_info.append((current_rank, previous_rank, current_avg_rating, school_name, student_count, rating_change))
            # print(f"{school_name} went {rank_change} from {previous_rank} to {current_rank}")

    return school_info