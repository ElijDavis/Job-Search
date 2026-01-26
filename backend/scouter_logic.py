import requests
import os
from dotenv import load_dotenv

load_dotenv()

def scout_google_jobs(search_query):
    print(f"📡 API Scouting for: {search_query}")
    
    url = "https://jsearch.p.rapidapi.com/search"
    
    # We want jobs from the last 24 hours to keep them fresh
    querystring = {
        "query": search_query,
        "page": "1",
        "num_pages": "1",
        "date_posted": "today" 
    }

    headers = {
        "X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY"),
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }

    try:
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status() 
        data = response.json()
        
        raw_jobs = data.get('data', [])
        found_jobs = []

        for job in raw_jobs:
            apply_link = job.get('job_apply_link')
            
            # We specifically look for Workday links to ensure our engine can handle them
            if apply_link and "myworkdayjobs" in apply_link:
                found_jobs.append({
                    "company_name": job.get('employer_name'),
                    "job_title": job.get('job_title'),
                    "job_description": job.get('job_description'),
                    "job_url": apply_link,
                    "status": "Found"
                })
                print(f"🎯 Found Workday Match: {job.get('job_title')} at {job.get('employer_name')}")

        print(f"✅ Total Workday jobs found: {len(found_jobs)}")
        return found_jobs

    except Exception as e:
        print(f"❌ API Scouting Failed: {e}")
        return []