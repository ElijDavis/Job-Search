import asyncio
import os
from scouter_logic import scout_google_jobs
from scouter import get_match_score, save_job_to_cloud, supabase, check_supabase_status
from resume_manager import get_all_resumes
from workday_engine import workday_handler
from playwright.async_api import async_playwright

async def process_approvals():
    """Checks Supabase for any jobs the user Approved on their phone."""
    print("Checking for your approvals...")
    # Fetch jobs that ARE 'Approved' but NOT yet 'Applied'
    response = supabase.table("jobs").select("*").eq("status", "Approved").execute()
    approved_jobs = response.data

    if not approved_jobs:
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        for job in approved_jobs:
            print(f"🚀 Processing Approval for: {job['company_name']}")
            page = await browser.new_page()
            try:
                # Use the stored resume path or a default one
                resume_path = "./resumes/Elijah - Resume.pdf" 
                await page.goto(job['job_url'])
                
                if "myworkdayjobs.com" in job['job_url']:
                    # Re-run the handler to finish the 'Submit' step
                    await workday_handler(page, resume_path, job['id'])
                    
                # Update status to 'Applied' so we don't do it again
                supabase.table("jobs").update({"status": "Applied"}).eq("id", job['id']).execute()
            except Exception as e:
                print(f"Failed to finish approved job {job['id']}: {e}")
            finally:
                await page.close()
        await browser.close()

async def run_automation():
    while True:
        # --- TASK 1: CHECK FOR MOBILE APPROVALS (Run this frequently) ---
        await process_approvals()

        # --- TASK 2: SCOUT FOR NEW JOBS (Run this occasionally) ---
        print("--- Starting scouting cycle ---")
        resumes = get_all_resumes("./resumes")
        """new_jobs = await scout_google_jobs("Software Engineer")

        if new_jobs:
            for job in new_jobs:
                # ... [Keep your existing Match Score logic here] ...
                if highest_score >= 8:
                    # Save with 'Found' status first
                    job_id = save_job_to_cloud(job, highest_score)
                    
                    # Optional: Automatically trigger the screenshot/preview 
                    # by calling the first half of workday_handler here
                    # which sets status to 'Pending Approval'
        """
        # --- Inside run_automation() ---
        print("Scouting for new 'Software Engineer' roles...")
        new_jobs = scout_google_jobs("Software Engineer")

        # ADD THIS:
        print(f"DEBUG: Found {len(new_jobs) if new_jobs else 0} raw jobs on Google.")

        if new_jobs:
            for job in new_jobs:
                print(f"DEBUG: Checking job: {job['job_title']} at {job['company_name']}")
                
                highest_score = 0
                for name, text in resumes.items():
                    score = get_match_score(job['job_description'], text)
                    print(f"DEBUG: AI Score for {name}: {score}/10") # ADD THIS
                    
                    if score > highest_score:
                        highest_score = score
                        best_resume = name

                if highest_score >= 8:
                    print(f"✅ MATCH! Saving {job['job_title']} to Supabase...")
                    # ... existing save logic ...
                else:
                    print(f"❌ REJECTED: Score {highest_score} is below threshold.")
        
        print("Cycle finished. Waiting 5 minutes before checking approvals again...")
        await asyncio.sleep(300) # Check for approvals every 5 mins

if __name__ == "__main__":
    asyncio.run(run_automation())