import asyncio
from playwright.async_api import async_playwright
#from playwright_stealth import stealth
from playwright_stealth import stealth_async

async def scout_google_jobs(search_query):
    async with async_playwright() as p:
        # 1. Launch Browser
        browser = await p.chromium.launch(headless=True, args=[
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage", # Prevents memory crashes in small containers
            "--disable-gpu"
        ]) # Set to True once it's working
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await stealth_async(page) # Apply stealth to avoid blocks

        # 2. Go directly to Google Jobs
        formatted_query = search_query.replace(" ", "+")
        url = f"https://www.google.com/search?q={formatted_query}&ibp=htl;jobs"
        await page.goto(url)
        await page.wait_for_timeout(3000) # Wait for load

        # 3. Locate the job cards
        # In Google Jobs, each job is an <li> element inside a specific list
        job_listings = await page.query_selector_all('li')

        found_jobs = []

        for job in job_listings[:10]: # Let's just look at the first 10 for now
            await job.click() # Click to load details on the right
            await page.wait_for_timeout(1000)

            title = await page.inner_text('h2.KL3o9e') # Selector for Job Title
            company = await page.inner_text('div.nS3V7e') # Selector for Company
            
            # Find all Apply links
            links = await page.query_selector_all('a[href]')
            apply_url = ""
            
            for link in links:
                href = await link.get_attribute('href')
                # SUBVERTER LOGIC: Filter out the middleman
                if "linkedin" not in href and "indeed" not in href and "google" not in href:
                    apply_url = href
                    break
            
            if apply_url:
                found_jobs.append({
                    "company_name": company,
                    "job_title": title,
                    "job_url": apply_url,
                    "status": "Found"
                })
                print(f"🎯 Found Direct Match: {title} at {company}")

        await browser.close()
        return found_jobs

# To run it:
# asyncio.run(scout_google_jobs("Software Engineer New York"))