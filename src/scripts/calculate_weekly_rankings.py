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



# Calculates weekly rankings for all universities (with >= 5 students)
def calculate_weekly_rankings():
    cursor = university_avgs.find(
        {},
        {'universityName': 1, 'currentAverage': 1, 'studentCount': 1, 'weeklyAverages': 1}
    )

    school_averages = []
    for school in cursor:
        school_name = school['universityName']
        student_count = school['studentCount']
        school_avg = school['currentAverage']

        # Do not factor in schools with < 5 students into our rankings
        # Do not factor in schools without 2 previous weekly averages into our rankings
        if student_count < 5 or len(school['weeklyAverages']) < 2:
            print(f"Skipping {school_name} -> STUDENTS: {student_count}")

            university_avgs.update_one(
                {'universityName': school_name},
                {
                    '$set': {
                        'currentRank': -1,
                        'beenRankOne': False # Set beenRankOne to false for badge calculation purposes
                    },
                    '$push': {
                        'previousRankings': -1
                    }
                },
                upsert=True
            )
            continue

        # Student count > 5, factor into rankings
        school_averages.append((school_name, school_avg))

    # Sort by contest rating (descending order)
    sorted_school_avg = sorted(school_averages, key=lambda x: x[1], reverse=True)

    school_rankings = []
    for i, (school_name, _) in enumerate(sorted_school_avg):
        rank = i + 1
        print(f"{rank}: {school_name}")
        # For each rank:
            # Add current rank in DB to 'weeklyRankings'
            # Update 'currentRank' to new rank

        doc = university_avgs.find_one({'universityName': school_name})

        # If currentRanking does not exist, set it for the first time using rank
        # Otherwise, use the existing currentRanking in the document to push to weeklyRankings
        if doc and 'currentRank' in doc:
            previous_ranking = doc['currentRank']
        else:
            previous_ranking = -1
        
        
        # CHECK FOR CROWN SNATCHER BADGE HERE.. before we update the weekly rank
        been_rank_one = school.get('beenRankOne', False)  # Use .get() with default value False
        if rank == 1 and been_rank_one == False:
            # Update beenRankOne to True
            university_avgs.update_one(
                {'universityName': school_name},
                {'$set': {'beenRankOne': True}}
            )
            print(f"{school_name} has earned CROWN SNATCHER")


        
        # Update the university's currentRanking and previousRankings in the collection
        if rank == 1:
            university_avgs.update_one(
                {'universityName': school_name},
                {
                    '$set': {
                        'currentRank': rank,
                        'beenRankOne': True,
                    },
                    '$push': {
                        'previousRankings': rank
                    }
                },
                upsert=True
            )
        else:
            university_avgs.update_one(
                {'universityName': school_name},
                {
                    '$set': {
                        'currentRank': rank,
                        'beenRankOne': False,
                    },
                    '$push': {
                        'previousRankings': rank
                    }
                },
                upsert=True
            )

        print(f"{school_name}: set previousRank to {previous_ranking} and currentRank to {rank}")


calculate_weekly_rankings()