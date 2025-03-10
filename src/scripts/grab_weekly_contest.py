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
    contest_number = 437
    contest_max_pages = 1197
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

user_cnt = 0
for data in results:
    for user in data['total_rank']:
        if(user['country_code'] == 'US'):
            user_cnt +=1
            print(user['user_slug'])

