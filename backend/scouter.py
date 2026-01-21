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

############################################################################# workday integration helpers

async def upload_screenshot(job_id, file_path):
    """Uploads the form preview to Supabase Storage and returns the public URL."""
    file_name = f"{job_id}.png"
    
    with open(file_path, 'rb') as f:
        # 1. Upload the file to the 'screenshots' bucket
        supabase.storage.from_("screenshots").upload(
            path=file_name,
            file=f,
            file_options={"content-type": "image/png", "upsert": "true"}
        )
    
    # 2. Get the public URL so your Android app can display it
    response = supabase.storage.from_("screenshots").get_public_url(file_name)
    
    # 3. Update the database record with this URL and change status to 'Pending'
    supabase.table("jobs").update({
        "screenshot_url": response,
        "status": "Pending Approval"
    }).eq("id", job_id).execute()
    
    return response

async def check_supabase_status(job_id):
    """Checks the database to see if the user has clicked 'Approve' on the mobile app."""
    response = supabase.table("jobs").select("status").eq("id", job_id).execute()
    
    if response.data:
        return response.data[0]['status']
    return None