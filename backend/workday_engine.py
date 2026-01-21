import json
import os
user = os.getenv("WORKDAY_USER")
password = os.getenv("WORKDAY_PASS")

def load_profile():
    with open('profile.json', 'r') as f:
        return json.load(f)

async def workday_handler(page, resume_path):
    profile = load_profile()
    creds = profile['workday_credentials']
    info = profile['personal_info']
    self_id = profile['self_id']

    # --- PHASE 1: LOGIN / ACCOUNT CREATION ---
    print("Starting Workday Login Flow...")
    await page.get_by_role("button", name="Sign In").click()
    
    # Check if we are on the login screen
    await page.get_by_label("Email Address").fill(creds['email'])
    await page.get_by_label("Password").fill(creds['password'])
    await page.get_by_role("button", name="Sign In", exact=True).click()
    await page.wait_for_timeout(3000)

    # Check for Account Existence
    if await page.get_by_text("Invalid credentials").is_visible():
        print("Account not found or password wrong. Attempting to create account...")
        await page.get_by_role("link", name="Create Account").click()
        await page.get_by_label("Email Address").fill(creds['email'])
        await page.get_by_label("Password").fill(creds['password'])
        await page.get_by_label("Confirm Password").fill(creds['password'])
        await page.get_by_label("I agree").check()
        await page.get_by_role("button", name="Create Account").click()
        await page.wait_for_timeout(3000)

    # --- PHASE 2: INITIATE APPLICATION ---
    if await page.get_by_role("button", name="Apply").is_visible():
        await page.get_by_role("button", name="Apply").click()
        await page.get_by_role("button", name="Apply Manually").click()

    # --- PHASE 3: THE MULTI-PAGE FILLER & SELF-ID ---
    print("Beginning Multi-Page Form Filler...")
    
    # We loop until the 'Review' page or a 'Submit' button appears
    while await page.get_by_text("Review", exact=True).is_hidden():
        
        # 1. Standard Info Fields
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
        # We look for common labels and use the profile.json mapping
        if await page.get_by_text("Voluntary Self-Identification").is_visible():
            print("Handling Self-Identification dropdowns...")
            
            # Gender Dropdown
            try:
                await page.get_by_label("Gender").select_option(label=self_id['gender'])
            except: pass

            # Hispanic/Latino Dropdown
            try:
                await page.get_by_label("Are you Hispanic or Latino?").select_option(label=self_id['hispanic_latino'])
            except: pass

            # Race Checkboxes or Dropdowns
            try:
                await page.get_by_label(self_id['race'], exact=False).check()
            except: pass

            # Veteran Status
            try:
                # Some Workdays use a custom menu, we click the box then the option
                await page.get_by_label("Veteran Status").click()
                await page.get_by_text(self_id['veteran_status']).click()
            except: pass

        # 4. Advance to Next Page
        continue_btn = page.get_by_role("button", name="Save and Continue")
        if await continue_btn.is_visible():
            await continue_btn.click()
            await page.wait_for_timeout(2000)
        else:
            break # Exit loop if no continue button found (might be at the end)

    print("Application filled. Ready for your final review!")

    # --- PHASE 4: FINAL REVIEW & REMOTE SUBMISSION ---
    # 1. Take a screenshot of the final 'Review' page
    screenshot_path = f"screenshots/{job_id}.png"
    await page.screenshot(path=screenshot_path)
    
    # 2. Upload to Supabase and update status to 'Pending'
    # (Use your save_job_to_cloud function here to update the status)
    print(f"Application filled. Waiting for remote approval for Job {job_id}...")

    # 3. The Listening Loop
    approved = False
    while not approved:
        # Check Supabase every 10 seconds
        job_status = await check_supabase_status(job_id) 
        
        if job_status == "Approved":
            await page.get_by_role("button", name="Submit").click()
            print("Successfully submitted via remote command!")
            approved = True
        elif job_status == "Rejected":
            print("Application cancelled by user.")
            break
            
        await asyncio.sleep(10) # Wait before checking again


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