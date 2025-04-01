import sys
import os
from dotenv import load_dotenv
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database

from collections import defaultdict
from datetime import datetime, timedelta
from pymongo import MongoClient

#load env vars
load_dotenv()
mongodb_uri = os.getenv("MONGODB_URI")

client = MongoClient(mongodb_uri)
# Grabs collection from db
university_avgs = client.leeterboard.university_avgs



def get_second_previous_saturday():
    """
    Returns the Saturday before the previous Saturday from the current date in 'YYYY-MM-DD' format.
    
    Returns:
        str: Second previous Saturday in 'YYYY-MM-DD' format.
    """
    # Get current date
    current_date = datetime.now()
    
    # Calculate days to go back to reach previous Saturday
    # weekday() returns 0-6 where 0 is Monday and 5 is Saturday
    days_since_saturday = (current_date.weekday() + 2) % 7
    
    # If today is Saturday, we want last Saturday, so add 7
    if days_since_saturday == 0:
        days_since_saturday = 7
    
    # Calculate the previous Saturday
    previous_saturday = current_date - timedelta(days=days_since_saturday)
    
    # Now go back 7 more days to get the Saturday before that
    second_previous_saturday = previous_saturday - timedelta(days=7)
    
    # Return the formatted date
    return second_previous_saturday.strftime('%Y-%m-%d')



# For a school we have school: (current rating, students, weekly_ratings[rating 1 (date), rating 2 (date)])
final_school_info = defaultdict(list)

# Get the student # for each school
school_students = database.grab_students_per_school()
for school, students in school_students.items():
    final_school_info[school].append(students)

# Get the avg
school_curr_avgs = database.calculate_school_curr_avg()
for school, curr_weekly_avg in school_curr_avgs:
    final_school_info[school].append(curr_weekly_avg)


# Updates 3 fields, but pushes new current weekly school average to array for graph plotting
def upsert_school(school_name, student_count, current_rating):
    # current_saturday = datetime.now().strftime('%Y-%m-%d')
    previous_saturday = get_second_previous_saturday()

    university_avgs.update_one(
        {'universityName': school_name},
        {
            '$set': {
                'universityName': school_name,
                'studentCount': student_count,
                'currentAverage': current_rating
            },
            '$push': {
                'weeklyAverages': {
                    'week': previous_saturday,
                    'average': current_rating
                }
            }
        },
        upsert=True
    )

cur = 0
for school, info in final_school_info.items():
    print(cur)
    cur += 1
    # print(f"{school}: {info[0]}, {info[1]}")
    upsert_school(school, info[0], info[1])