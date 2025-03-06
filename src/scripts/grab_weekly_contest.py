import requests
import json
import asyncio
import aiohttp

# Simply returns the proper url with the modified portions
def get_weekly_contest_url(contest_id: int, page: int) -> str:
    return f"https://leetcode.com/contest/api/ranking/weekly-contest-{contest_id}/?pagination={page}&region=global_v2"


# Makes the individual HTTP request and waits for the response body and parses it as JSON
async def fetch_contest_page(session, url, cookies, headers):
    async with session.get(url, cookies=cookies, headers=headers, ssl=False) as response:
        return await response.json()


# Performs all of the asynchronous requests
async def request_all_contest_pages(batch_size: int):
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
            batch = all_urls[i:i + batch_size]
            
            # Go through the batch
            tasks = []
            for batch_url in batch:
                tasks.append(fetch_contest_page(session, batch_url, cookies, headers))
            
            # Send out all batched requests and store responses
            batch_responses = await asyncio.gather(*tasks)
            responses.extend(batch_responses)

            if i + batch_size < len(all_urls):
                print("Waiting between batches...")
                await asyncio.sleep(2.5)

    return responses

results = asyncio.run(request_all_contest_pages(10))

user_cnt = 0
for data in results:
    for user in data['total_rank']:
        if(user['country_code'] == 'US'):
            user_cnt +=1
            print(user['user_slug'])

