import json
import os
import asyncio

from scouter import upload_screenshot, check_supabase_status, supabase
user = os.getenv("WORKDAY_USER")
password = os.getenv("WORKDAY_PASS")

def load_profile():
    with open('profile.json', 'r') as f:
        return json.load(f)

async def workday_handler(page, resume_path, job_id):
    profile = load_profile()
    creds = profile['workday_credentials']
    info = profile['personal_info']
    self_id = profile['self_id']
    job_status = await check_supabase_status(job_id)

    # --- PHASE 1: LOGIN / ACCOUNT CREATION ---
    print("Starting Workday Login Flow...")
    try:
        # Some Workdays have a "Sign In" button on the landing page
        signin_btn = page.get_by_role("button", name="Sign In")
        if await signin_btn.is_visible():
            await signin_btn.click()
        
        await page.get_by_label("Email Address").fill(creds['email'])
        await page.get_by_label("Password").fill(creds['password'])
        await page.get_by_role("button", name="Sign In", exact=True).click()
        await page.wait_for_timeout(3000)

        # Handle Account Creation if Login Fails
        if await page.get_by_text("Invalid credentials").is_visible():
            print("Account not found. Attempting to create one...")
            await page.get_by_role("link", name="Create Account").click()
            await page.get_by_label("Email Address").fill(creds['email'])
            await page.get_by_label("Password").fill(creds['password'])
            await page.get_by_label("Confirm Password").fill(creds['password'])
            await page.get_by_label("I agree").check()
            await page.get_by_role("button", name="Create Account").click()
            await page.wait_for_timeout(3000)
    except Exception as e:
        print(f"Login/Auth phase encountered an issue: {e}")

    # --- PHASE 2: INITIATE APPLICATION ---
    if await page.get_by_role("button", name="Apply").is_visible():
        await page.get_by_role("button", name="Apply").click()
        await page.get_by_role("button", name="Apply Manually").click()

    # --- PHASE 3: THE MULTI-PAGE FILLER & SELF-ID ---
    print("Beginning Multi-Page Form Filler...")
    
    # We loop until the 'Review' page appears
    while await page.get_by_text("Review", exact=True).is_hidden():
        
        # 1. Standard Info Fields (Contact, Address, etc.)
        if await page.get_by_label("First Name").is_visible():
            await page.get_by_label("First Name").fill(info['first_name'])
            await page.get_by_label("Last Name").fill(info['last_name'])
            await page.get_by_label("Phone Number").fill(info['phone'])

        # 2. Resume Upload
        if await page.get_by_text("Upload", exact=False).is_visible():
            async with page.expect_file_chooser() as fc_info:
                await page.get_by_text("Upload").click()
            file_chooser = await fc_info.value
            await file_chooser.set_files(resume_path)

        # 3. SELF-ID REFINEMENT (The Dropdowns)
        if await page.get_by_text("Voluntary Self-Identification").is_visible():
            print("Handling Self-Identification dropdowns...")
            try:
                await page.get_by_label("Gender").select_option(label=self_id['gender'])
                await page.get_by_label("Are you Hispanic or Latino?").select_option(label=self_id['hispanic_latino'])
                await page.get_by_label(self_id['race'], exact=False).check()
                
                # Custom click for Veteran status menu
                await page.get_by_label("Veteran Status").click()
                await page.get_by_text(self_id['veteran_status']).click()
            except Exception as e:
                print(f"Self-ID Field missing or skipped: {e}")

        # 4. Advance to Next Page
        continue_btn = page.get_by_role("button", name="Save and Continue")
        if await continue_btn.is_visible():
            await continue_btn.click()
            # Wait for the next section to animate/load
            await page.wait_for_timeout(2500)
        else:
            # If no continue button, we might have hit the Review page
            break 

    # --- PHASE 4: FINAL REVIEW & REMOTE SUBMISSION ---
    # --- PHASE 4: STATE-BASED ACTIONS (REPLACED) ---
        print(f"Application reach Review stage. Current status: {job_status}")
        
        # CASE A: First time seeing this job (Scouting phase)
        if job_status in ["Found", "Pending Approval", None]:
            print(f"Preparing preview for remote approval: Job {job_id}")
            
            # Take a screenshot so you can see it on your phone
            os.makedirs("screenshots", exist_ok=True)
            screenshot_path = f"screenshots/{job_id}.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            
            # This function (in scouter.py) uploads the image and sets status to 'Pending Approval'
            await upload_screenshot(job_id, screenshot_path)
            
            print("Preview uploaded to Android app. Closing browser to wait for your command.")
            return # STOP HERE. This frees up the bot to scout the next job.

        # CASE B: You clicked 'Approve' on your phone
        elif job_status == "Approved":
            print(f"Remote Approval confirmed for Job {job_id}. Finalizing submission...")
            
            # Look for the final Submit button
            submit_btn = page.get_by_role("button", name="Submit")
            if await submit_btn.is_visible():
                await submit_btn.click()
                # Give Workday a few seconds to show the 'Congratulations' page
                await page.wait_for_timeout(5000) 
                
                # Final Database Update so it disappears from your 'Pending' list on Android
                supabase.table("jobs").update({"status": "Applied"}).eq("id", job_id).execute()
                print(f"✅ Job {job_id} successfully submitted!")
            else:
                print("❌ Submit button not found. You might need to check this one manually.")

        # CASE C: You clicked 'Reject' on your phone
        elif job_status == "Rejected":
            print(f"Job {job_id} was rejected via mobile. Skipping.")


async def fill_workday_sections(page, profile):
    # List of section headers Workday usually uses
    sections = ["Contact Information", "Experience", "Education", "Languages", "Skills"]
    
    for section in sections:
        print(f"Filling section: {section}")
        
        # 1. Automatic Field Filler (matches labels to your profile)
        await fill_basic_info(page, profile) 
        
        # 2. Click the 'Save and Continue' button
        # Workday buttons often use 'data-automation-id' which is great for bots
        continue_button = page.locator('button:has-text("Save and Continue")')
        await continue_button.click()
        
        # 3. Wait for the next page to load
        await page.wait_for_timeout(2000)

async def fill_basic_info(page, profile):
    # This is where the 'Smart Filling' we discussed earlier happens
    # It tries to find 'Address', 'Phone', etc., on whatever page is visible
    if await page.get_by_label("Address").is_visible():
        await page.get_by_label("Address").fill(profile['address'])