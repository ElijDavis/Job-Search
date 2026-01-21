import json
import os
user = os.getenv("WORKDAY_USER")
password = os.getenv("WORKDAY_PASS")

def load_profile():
    # Looks for the json file in the same directory
    with open('profile.json', 'r') as f:
        return json.load(f)


async def workday_handler(page, profile, credentials):
    # 1. Attempt Login
    await page.get_by_role("button", name="Sign In").click()
    await page.get_by_label("Email Address").fill(credentials['email'])
    await page.get_by_label("Password").fill(credentials['password'])
    await page.get_by_role("button", name="Sign In").click()
    
    # 2. Check for Error (If account doesn't exist)
    if await page.get_by_text("Invalid credentials").is_visible():
        print("Account not found. Creating one...")
        await page.get_by_role("link", name="Create Account").click()
        await page.get_by_label("Email Address").fill(credentials['email'])
        await page.get_by_label("Password").fill(credentials['password'])
        await page.get_by_label("Confirm Password").fill(credentials['password'])
        await page.get_by_label("I agree").check()
        await page.get_by_role("button", name="Create Account").click()

    # 3. Start Application
    await page.get_by_role("button", name="Apply").click()
    await page.get_by_role("button", name="Apply Manually").click()


async def workday_handler(page, resume_path):
    profile = load_profile()
    creds = profile['workday_credentials']
    info = profile['personal_info']

    # --- Step 1: Login/Account Creation ---
    # (Using the logic we wrote previously)
    await page.get_by_label("Email Address").fill(creds['email'])
    await page.get_by_label("Password").fill(creds['password'])
    await page.get_by_role("button", name="Sign In").click()

    # --- Step 2: The Multi-Page Filler ---
    # Workday is a "Single Page App" that switches views. 
    # We use a loop to keep filling until we see the 'Review' page.
    
    while await page.get_by_text("Review").is_hidden():
        # Fill standard text boxes
        if await page.get_by_label("First Name").is_visible():
            await page.get_by_label("First Name").fill(info['first_name'])
            await page.get_by_label("Last Name").fill(info['last_name'])
            await page.get_by_label("Phone Number").fill(info['phone'])

        # Handle the Resume Upload specifically
        if await page.get_by_text("Upload", exact=False).is_visible():
            async with page.expect_file_chooser() as fc_info:
                await page.get_by_text("Upload").click()
            file_chooser = await fc_info.value
            await file_chooser.set_files(resume_path)

        # Click the 'Save and Continue' button to move to the next 'page'
        await page.get_by_role("button", name="Save and Continue").click()
        await page.wait_for_timeout(2000) # Give the next section time to load


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