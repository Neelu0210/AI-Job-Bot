from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import csv

# Set up the Selenium WebDriver (Ensure you have the right ChromeDriver installed)
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Run Chrome in headless mode (no UI)
driver = webdriver.Chrome(options=options)

# Open Indeed Job Search
job_title = "Product Manager"
location = "Remote"
url = f"https://www.indeed.com/jobs?q={job_title}&l={location}"
driver.get(url)

time.sleep(3)  # Wait for page to load

# Find job elements
jobs = driver.find_elements(By.CLASS_NAME, "job_seen_beacon")

print(job_list)  # Print scraped job data before writing to CSV
# Open a CSV file to save the results
with open("jobs.csv", "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Title", "Company", "Location", "Link"])

    for job in jobs:
        try:
            title = job.find_element(By.CLASS_NAME, "jobTitle").text
            company = job.find_element(By.CLASS_NAME, "companyName").text
            location = job.find_element(By.CLASS_NAME, "companyLocation").text
            link = job.find_element(By.TAG_NAME, "a").get_attribute("href")

            writer.writerow([title, company, location, link])
        except Exception as e:
            print("Error:", e)

driver.quit()
print("✅ Job scraping complete! Check jobs.csv")


