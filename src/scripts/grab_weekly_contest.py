import requests
import json
import asyncio
import aiohttp

# Simply returns the proper url with the modified portions
def get_weekly_contest_url(contest_id: int, page: int) -> str:
    return f"https://leetcode.com/contest/api/ranking/weekly-contest-{contest_id}/?pagination={page}&region=global_v2"


# Makes the individual HTTP request and waits for the response body and parses it as JSON
async def fetch_contest_page(session, url, headers):
    async with session.get(url, headers=headers, ssl=False) as response:
        return await response.json()


# Performs all of the asynchronous requests
async def request_all_contest_pages(batch_size: int):
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Mobile Safari/537.36",
        "Referer": "https://leetcode.com/contest/weekly-contest-437/ranking/1229/?region=global_v2",
        "x-csrftoken": "8bg8dnJkupMC9wgGkgkuXkpoND0D4pooy8qrEWc93k4O64npnl4JJ6mioYgoX1JK",
        "Content-Type": "application/json"
    }

    # Generate all URLs (1 per page)
    all_urls = []
    contest_number = 440
    contest_max_pages = 1264
    for page_number in range(1, contest_max_pages):
        all_urls.append(get_weekly_contest_url(contest_number, page_number))

    responses = []
    async with aiohttp.ClientSession() as session:
        # Process requests in batches
        # 0 -> 9, 10 -> 19, 20 -> 29k
        for i in range(0, len(all_urls), batch_size):
            print(f"Making request {i}")
            batch = all_urls[i:i + batch_size]
            
            # Go through the batch
            tasks = []
            for batch_url in batch:
                tasks.append(fetch_contest_page(session, batch_url, headers))
            
            # Send out all batched requests and store responses
            batch_responses = await asyncio.gather(*tasks)
            responses.extend(batch_responses)

            if i + batch_size < len(all_urls):
                await asyncio.sleep(1)

    return responses

results = asyncio.run(request_all_contest_pages(10))

all_new_users = []
for data in results:
    for user in data['total_rank']:
        if(user['country_code'] == 'US'):
            all_new_users.append(user)
    

# Now, we want to see how many of these users have a school
# Now, see if the user in already in our database
    # If not, we need to create a new document for them in the database
    # Run the fuzzy matching script to find the best school match for them

# Now that our database contains all of the new users found this week, we can
# safely run the script to pull the new weekly ratings for each user in our database


# With this information, we will be able to have all of the data we need for what is currently on the site




# WORKING ON THIS NOW (created weekly script + mongodb collection)
# However, we need to find a way to calculate weekly averages across all universities for the graphs
# We may want to create a new collection for each of these universities and store their past weekly averages there
# Could potentially just run the calculate_university_info() function once weekly and then whatever that returns will
# be the updated data point for that week, but obviously all of the operations before this will occur before this
# in real time as well
