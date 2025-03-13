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
    current_saturday = datetime.now().strftime('%Y-%m-%d')

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
                    'week': current_saturday,
                    'average': current_rating
                }
            }
        },
        upsert=True
    )

# for school, info in final_school_info.items():
    # print(f"{school}: {info[0]}, {info[1]}")
    # upsert_school(school, info[0], info[1])