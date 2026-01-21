import time
from scouter_logic import scout_google_jobs
from scouter import get_match_score, save_job_to_cloud
from resume_manager import get_all_resumes
from workday_engine import workday_handler
from playwright.async_api import async_playwright

async def run_automation():
    # 1. Load your resumes
    resumes = get_all_resumes("./resumes")
    
    # 2. Find jobs
    new_jobs = await scout_google_jobs("Software Engineer")

    for job in new_jobs:
        # 3. Brain: Find the best resume for this job
        best_resume = None
        highest_score = 0
        
        for name, text in resumes.items():
            score = get_match_score(job['job_description'], text)
            if score > highest_score:
                highest_score = score
                best_resume = name

        # 4. Action: If it's a good match, apply
        # ... previous scouter and matching code ...
        if highest_score >= 8:
            print(f"Applying with: {best_resume}")
            
            # Define the path to the specific resume file chosen by the AI
            resume_path = f"./resumes/{best_resume}"
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False) # Headless=False so you can watch it!
                page = await browser.new_page()
                
                await page.goto(job['job_url'])
                
                # Route to the correct engine
                if "myworkdayjobs.com" in job['job_url']:
                    await workday_handler(page, resume_path)
                
                print("Application ready for review. Please check the browser.")
                # We don't close the browser so you can hit the final 'Submit' button manually
                input("Press Enter to close the browser after you hit submit...")
            # Here is where you'd trigger your workday_engine.py logic
            # (We will connect this fully in the next step)
            # (The workday_handler function is already defined in workday_engine.py)

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_automation())