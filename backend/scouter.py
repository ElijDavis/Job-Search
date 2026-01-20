import os
from openai import OpenAI
from dotenv import load_dotenv
from supabase import create_client
############################################################# openai integration

# Initialize OpenAI client
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_match_score(job_description, my_resume):
    prompt = f"""
    Compare this job description with my resume. 
    Rate the match from 1 to 10. 
    Return ONLY the number.
    
    Resume: {my_resume}
    Job: {job_description}
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini", # Cheaper and faster for matching
        messages=[{"role": "user", "content": prompt}]
    )
    return int(response.choices[0].message.content.strip())


############################################################# supabase integration

# Initialize Supabase
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

def save_job_to_cloud(job_data):
    """
    job_data should be a dictionary like:
    {'company_name': 'Apple', 'job_title': 'Engineer', 'match_score': 9, ...}
    """
    try:
        response = supabase.table("jobs").insert(job_data).execute()
        print("Success! Job saved to Supabase.")
        return response
    except Exception as e:
        print(f"Cloud save failed: {e}")

# --- INTEGRATION EXAMPLE ---
# 1. Get score from AI
# score = get_match_score(job_desc, my_resume)

# 2. Save it automatically
# save_job_to_cloud({
#    "company_name": "Hershey",
#    "job_title": "Data Analyst",
#    "match_score": score,
#    "job_url": "https://careers.hershey.com/job123"
# })