from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import pandas as pd

# Set up ChromeDriver
driver = webdriver.Chrome()

# Open Indeed job search page
URL = "https://www.indeed.com/jobs?q=Software+Engineer&l=Remote"
driver.get(URL)

time.sleep(3)  # Wait for page to load

# Scrape job details
jobs = []
job_cards = driver.find_elements(By.CLASS_NAME, "job_seen_beacon")

for job in job_cards:
    try:
        title = job.find_element(By.CLASS_NAME, "jobTitle").text
    except:
        title = "N/A"

    try:
        company = job.find_element(By.CLASS_NAME, "companyName").text
    except:
        company = "N/A"

    try:
        location = job.find_element(By.CLASS_NAME, "companyLocation").text
    except:
        location = "N/A"

    jobs.append([title, company, location])

# Save to CSV
df = pd.DataFrame(jobs, columns=["Title", "Company", "Location"])
df.to_csv("jobs.csv", index=False, encoding="utf-8")

print("✅ Job data saved to jobs.csv")

# Close browser
driver.quit()
