import os
from dotenv import load_dotenv
from pymongo import MongoClient

#load env vars
load_dotenv()
mongodb_uri = os.getenv("MONGODB_URI")

client = MongoClient(mongodb_uri)
# Grabs collection from db
university_avgs = client.leeterboard.university_avgs

# Gives each university their rank based on the mmr system
def assign_ranks():
    cursor = university_avgs.find(
        {},
        {'universityName': 1, 'currentAverage': 1}
    )

    for school in cursor:
        school_name = school['universityName']
        rating = school['currentAverage']

        rank_to_assign = ''
        if rating <= 1400:
            rank_to_assign = 'Bronze'
        elif rating <= 1500:
            rank_to_assign = 'Silver'
        elif rating <= 1550:
            rank_to_assign = 'Gold'
        elif rating <= 1600:
            rank_to_assign = 'Platinum'
        elif rating <= 1650:
            rank_to_assign = 'Diamond'
        elif rating <= 1700:
            rank_to_assign = 'Champion'
        elif rating <= 1750:
            rank_to_assign = 'Titan'
        elif rating > 1750:
            rank_to_assign = 'Immortal'
        
        university_avgs.update_one(
            {'universityName': school_name},
            {'$set': {'mmrRank': rank_to_assign}},
            upsert=True
        )

        print(f"Assigned {rank_to_assign} to {school_name} (Rating = {rating})")