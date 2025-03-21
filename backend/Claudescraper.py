import os
import json
import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from openai import OpenAI
from IPython.display import display, Markdown

class WebsiteCrawler:
    def __init__(self, url, timeout=30, chrome_path=None):
        """Initialize a website crawler with Selenium"""
        self.url = url
        self.timeout = timeout
        self.chrome_path = chrome_path
        self.page_source = None
        self.driver = None
        self.setup_driver()
        
    def setup_driver(self):
        """Set up the Chrome WebDriver with anti-detection measures"""
        options = Options()
        
        # Anti-detection measures
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-extensions')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Additional options
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # Use custom Chrome path if provided
        if self.chrome_path:
            service = Service(executable_path=self.chrome_path)
            self.driver = webdriver.Chrome(service=service, options=options)
        else:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
        # Modify navigator properties to avoid detection
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def crawl(self):
        """Navigate to the URL and get the page source"""
        try:
            self.driver.get(self.url)
            
            # Wait for the page to load
            time.sleep(random.uniform(2, 5))
            
            # Add some human-like scrolling
            self.driver.execute_script("window.scrollBy(0, 300);")
            time.sleep(random.uniform(1, 3))
            self.driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(random.uniform(1, 3))
            
            # Get the page source
            self.page_source = self.driver.page_source
            return self.page_source
            
        except Exception as e:
            print(f"Error crawling {self.url}: {e}")
            return None
        finally:
            if self.driver:
                self.driver.quit()
    
    def get_page_source(self):
        """Return the page source"""
        if not self.page_source:
            self.crawl()
        return self.page_source

def messages_for(web_crawler):
    """Create messages for the OpenAI API based on the crawled web page"""
    page_source = web_crawler.get_page_source()
    
    if not page_source:
        return [{"role": "user", "content": "The page couldn't be crawled. Please provide guidance on troubleshooting web scraping issues."}]
    
    # Create system message with instructions for the model
    system_message = {
        "role": "system", 
        "content": """You are a specialized job listing extractor. Your task is to analyze the HTML content 
        of job listing pages and extract structured information about each job posting.
        
        For each job posting, extract the following fields if available:
        1. Job Title
        2. Company Name
        3. Location (including remote status if mentioned)
        4. Salary (if available)
        5. Job Description (a brief summary)
        6. Application Link
        7. Required Skills/Qualifications (top 3-5)
        8. Job Type (Full-time, Part-time, Contract, etc.)
        9. Date Posted
        
        Return the data in a structured JSON format. For example:
        {
            "jobs": [
                {
                    "title": "Senior Software Engineer",
                    "company": "Tech Company Inc.",
                    "location": "New York, NY (Remote Available)",
                    "salary": "$120,000 - $150,000",
                    "description": "Brief summary of job responsibilities...",
                    "application_link": "https://example.com/apply",
                    "skills": ["Python", "JavaScript", "AWS"],
                    "job_type": "Full-time",
                    "date_posted": "2023-03-15"
                },
                {...}
            ]
        }
        
        If certain fields are not available, use "Not specified" as the value.
        If the page does not contain job listings or you can't identify any, respond with:
        {"jobs": [], "error": "No job listings found or unable to parse the page."}
        """
    }
    
    # Create user message with the HTML content
    # Limit content length to avoid token limits
    max_length = 15000  # Adjust based on model token limits
    truncated_html = page_source[:max_length]
    
    user_message = {
        "role": "user",
        "content": f"Extract job listings from this HTML content:\n\n{truncated_html}\n\nIf the HTML is truncated, focus on extracting what you can see."
    }
    
    return [system_message, user_message]

class JobScraper:
    def __init__(self, api_key=None):
        """Initialize the GPT-powered job scraper with OpenAI API key"""
        # Use provided API key or get from environment
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Provide it when initializing JobScraper or set OPENAI_API_KEY environment variable.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.jobs_data = []
    
    def scrape_jobs(self, job_title, location, sources=None):
        """Scrape job listings for the given job title and location"""
        if sources is None:
            sources = ["indeed", "linkedin", "glassdoor"]
        
        for source in sources:
            if source.lower() == "indeed":
                self._scrape_indeed(job_title, location)
            elif source.lower() == "linkedin":
                self._scrape_linkedin(job_title, location)
            elif source.lower() == "glassdoor":
                self._scrape_glassdoor(job_title, location)
            else:
                print(f"Unsupported source: {source}")
        
        return self.jobs_data
    
    def _scrape_indeed(self, job_title, location, pages=2):
        """Scrape job listings from Indeed"""
        print(f"Scraping Indeed for {job_title} in {location}...")
        formatted_title = job_title.replace(" ", "+")
        formatted_location = location.replace(" ", "+")
        
        for page in range(pages):
            start = page * 10  # Indeed uses increments of 10 for pagination
            url = f"https://www.indeed.com/jobs?q={formatted_title}&l={formatted_location}&start={start}"
            
            # Create a WebsiteCrawler instance
            web = WebsiteCrawler(url, 30)
            
            # Call OpenAI API
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages_for(web),
                    temperature=0.2,  # Low temperature for consistent outputs
                    max_tokens=4000   # Adjust based on your needs
                )
                
                job_results = response.choices[0].message.content
                
                # Process the results
                try:
                    job_data = json.loads(job_results)
                    if "jobs" in job_data and job_data["jobs"]:
                        # Add source information to each job
                        for job in job_data["jobs"]:
                            job["source"] = "Indeed"
                        
                        # Extend our jobs data
                        self.jobs_data.extend(job_data["jobs"])
                        print(f"Found {len(job_data['jobs'])} jobs on Indeed (page {page+1})")
                    else:
                        print(f"No jobs found on Indeed (page {page+1}) or unable to parse.")
                except json.JSONDecodeError:
                    print(f"Failed to parse OpenAI response as JSON: {job_results[:100]}...")
                
                # Introduce delay to avoid rate limits
                if page < pages - 1:
                    delay = random.uniform(5, 10)
                    print(f"Waiting {delay:.1f} seconds before next page...")
                    time.sleep(delay)
                    
            except Exception as e:
                print(f"Error with OpenAI API call for Indeed: {e}")
    
    def _scrape_linkedin(self, job_title, location, pages=2):
        """Scrape job listings from LinkedIn"""
        print(f"Scraping LinkedIn for {job_title} in {location}...")
        formatted_title = job_title.replace(" ", "%20")
        formatted_location = location.replace(" ", "%20")
        
        for page in range(pages):
            start = page * 25  # LinkedIn uses increments of 25 for pagination
            url = f"https://www.linkedin.com/jobs/search/?keywords={formatted_title}&location={formatted_location}&start={start}"
            
            # Create a WebsiteCrawler instance
            web = WebsiteCrawler(url, 30)
            
            # Call OpenAI API
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages_for(web),
                    temperature=0.2,
                    max_tokens=4000
                )
                
                job_results = response.choices[0].message.content
                
                # Process the results
                try:
                    job_data = json.loads(job_results)
                    if "jobs" in job_data and job_data["jobs"]:
                        # Add source information to each job
                        for job in job_data["jobs"]:
                            job["source"] = "LinkedIn"
                        
                        # Extend our jobs data
                        self.jobs_data.extend(job_data["jobs"])
                        print(f"Found {len(job_data['jobs'])} jobs on LinkedIn (page {page+1})")
                    else:
                        print(f"No jobs found on LinkedIn (page {page+1}) or unable to parse.")
                except json.JSONDecodeError:
                    print(f"Failed to parse OpenAI response as JSON: {job_results[:100]}...")
                
                # Introduce delay to avoid rate limits
                if page < pages - 1:
                    delay = random.uniform(5, 10)
                    print(f"Waiting {delay:.1f} seconds before next page...")
                    time.sleep(delay)
                    
            except Exception as e:
                print(f"Error with OpenAI API call for LinkedIn: {e}")
    
    def _scrape_glassdoor(self, job_title, location, pages=2):
        """Scrape job listings from Glassdoor"""
        print(f"Scraping Glassdoor for {job_title} in {location}...")
        formatted_title = job_title.replace(" ", "-")
        formatted_location = location.replace(" ", "-").replace(",", "")
        
        for page in range(pages):
            # Glassdoor URLs are a bit different
            url = f"https://www.glassdoor.com/Job/{formatted_location}-{formatted_title}-jobs-SRCH_IL.0,{len(formatted_location)}_IN{len(formatted_location)}_KO{len(formatted_location)+1},{len(formatted_location)+1+len(formatted_title)}_IP{page+1}.htm"
            
            # Create a WebsiteCrawler instance
            web = WebsiteCrawler(url, 30)
            
            # Call OpenAI API
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages_for(web),
                    temperature=0.2,
                    max_tokens=4000
                )
                
                job_results = response.choices[0].message.content
                
                # Process the results
                try:
                    job_data = json.loads(job_results)
                    if "jobs" in job_data and job_data["jobs"]:
                        # Add source information to each job
                        for job in job_data["jobs"]:
                            job["source"] = "Glassdoor"
                        
                        # Extend our jobs data
                        self.jobs_data.extend(job_data["jobs"])
                        print(f"Found {len(job_data['jobs'])} jobs on Glassdoor (page {page+1})")
                    else:
                        print(f"No jobs found on Glassdoor (page {page+1}) or unable to parse.")
                except json.JSONDecodeError:
                    print(f"Failed to parse OpenAI response as JSON: {job_results[:100]}...")
                
                # Introduce delay to avoid rate limits
                if page < pages - 1:
                    delay = random.uniform(5, 10)
                    print(f"Waiting {delay:.1f} seconds before next page...")
                    time.sleep(delay)
                    
            except Exception as e:
                print(f"Error with OpenAI API call for Glassdoor: {e}")
    
    def filter_jobs(self, keywords=None, locations=None, remote=False, min_salary=None):
        """Filter jobs based on criteria"""
        filtered_jobs = self.jobs_data.copy()
        
        if keywords:
            filtered_jobs = [job for job in filtered_jobs if 
                            any(keyword.lower() in job.get('title', '').lower() or 
                               keyword.lower() in job.get('description', '').lower() or
                               (job.get('skills') and any(keyword.lower() in skill.lower() for skill in job.get('skills', [])))
                               for keyword in keywords)]
        
        if locations:
            filtered_jobs = [job for job in filtered_jobs if 
                            any(location.lower() in job.get('location', '').lower() 
                               for location in locations)]
        
        if remote:
            remote_keywords = ['remote', 'work from home', 'wfh', 'virtual']
            filtered_jobs = [job for job in filtered_jobs if 
                            any(keyword in job.get('location', '').lower() or
                               keyword in job.get('title', '').lower() or
                               keyword in job.get('description', '').lower()
                               for keyword in remote_keywords)]
        
        if min_salary:
            # This is a simple implementation; actual salary parsing would be more complex
            def extract_salary_value(salary_str):
                import re
                if not salary_str or salary_str == "Not specified":
                    return 0
                # Try to extract numeric values from salary string
                numbers = re.findall(r'\d+[,\d]*', salary_str)
                if numbers:
                    # Remove commas and convert to float
                    return float(numbers[0].replace(',', ''))
                return 0
            
            filtered_jobs = [job for job in filtered_jobs if extract_salary_value(job.get('salary', '')) >= min_salary]
        
        return filtered_jobs
    
    def save_to_csv(self, filename="gpt_jobs_data.csv"):
        """Save job data to CSV file"""
        if not self.jobs_data:
            print("No jobs data to save.")
            return
        
        try:
            # Convert jobs data to DataFrame
            df = pd.DataFrame(self.jobs_data)
            
            # Convert skills list to string if present
            if 'skills' in df.columns:
                df['skills'] = df['skills'].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)
            
            # Save to CSV
            df.to_csv(filename, index=False)
            print(f"Successfully saved {len(self.jobs_data)} jobs to {filename}")
            
        except Exception as e:
            print(f"Error saving to CSV: {e}")
    
    def save_to_json(self, filename="gpt_jobs_data.json"):
        """Save job data to JSON file"""
        if not self.jobs_data:
            print("No jobs data to save.")
            return
        
        try:
            with open(filename, 'w', encoding='utf-8') as jsonfile:
                json.dump(self.jobs_data, jsonfile, indent=4)
            
            print(f"Successfully saved {len(self.jobs_data)} jobs to {filename}")
            
        except Exception as e:
            print(f"Error saving to JSON: {e}")
    
    def display_jobs_summary(self):
        """Display a summary of the jobs data"""
        if not self.jobs_data:
            return display(Markdown("No jobs data available."))
        
        summary = f"# Job Search Results\n\n"
        summary += f"## Total Jobs Found: {len(self.jobs_data)}\n\n"
        
        # Source distribution
        sources = {}
        for job in self.jobs_data:
            source = job.get('source', 'Unknown')
            if source in sources:
                sources[source] += 1
            else:
                sources[source] = 1
        
        summary += "## Source Distribution\n"
        for source, count in sources.items():
            summary += f"- {source}: {count} jobs\n"
        
        # Sample of jobs
        summary += "\n## Sample Job Listings\n"
        for i, job in enumerate(self.jobs_data[:5]):  # Show first 5 jobs
            summary += f"### {i+1}. {job.get('title', 'Unknown Title')}\n"
            summary += f"**Company:** {job.get('company', 'Not specified')}\n\n"
            summary += f"**Location:** {job.get('location', 'Not specified')}\n\n"
            summary += f"**Salary:** {job.get('salary', 'Not specified')}\n\n"
            if job.get('skills'):
                if isinstance(job['skills'], list):
                    summary += f"**Skills:** {', '.join(job['skills'])}\n\n"
                else:
                    summary += f"**Skills:** {job.get('skills')}\n\n"
            summary += f"**Link:** {job.get('application_link', 'Not available')}\n\n"
            summary += "---\n\n"
        
        return display(Markdown(summary))

# Example usage
if __name__ == "__main__":
    # Initialize the scraper with your OpenAI API key
    # Either set OPENAI_API_KEY environment variable or pass it directly
    scraper = JobScraper()
    
    # Specify job title and location
    job_title = "data scientist"
    location = "New York"
    
    # Scrape from chosen sources
    scraper.scrape_jobs(job_title, location, sources=["indeed", "linkedin"])
    
    # Filter jobs (example)
    filtered_jobs = scraper.filter_jobs(
        keywords=["python", "machine learning"],
        remote=True
    )
    
    # Save results
    scraper.save_to_csv()
    scraper.save_to_json()
    
    # Display summary
    scraper.display_jobs_summary()