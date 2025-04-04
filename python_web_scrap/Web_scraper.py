import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import logging
from urllib.parse import urlparse
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# List of company websites
company_websites = [
    "https://www.dupont.com",
    "https://www.bASF.com",
    "https://www.glanbianutritionals.com",
    "https://www.iff.com",
    "https://www.amway.com"
]

# Keywords to search for in the website content
keywords = ["probiotic", "gut health", "fortification", "cognitive health", "nutrition", "women's health", "digestive health", "microbiome", "fermentation"]

# Country name list for broader detection
country_keywords = [
    "USA", "United States", "India", "Germany", "France", "UK", "United Kingdom",
    "China", "Japan", "Canada", "Australia", "Netherlands", "Italy", "Spain", "Brazil"
]

# Setup Selenium WebDriver
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--log-level=3")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def extract_company_name(url):
    parsed_url = urlparse(url)
    domain_parts = parsed_url.netloc.split(".")
    if len(domain_parts) > 2:
        return domain_parts[1].capitalize()
    return domain_parts[0].capitalize()

def classify_category(text):
    if any(x in text for x in ["beverage", "cereal", "milk", "dairy", "food", "drink", "bakery"]):
        return "Food & Beverages"
    elif any(x in text for x in ["pharma", "nutra", "capsule", "tablet", "sachet", "drug", "healthcare", "medicine"]):
        return "Pharmaceuticals"
    elif any(x in text for x in ["formulation", "finished product", "OTC", "formulated"]):
        return "Formulations"
    elif any(x in text for x in ["biotech", "biosciences", "laboratory", "diagnostic", "clinical"]):
        return "Biotechnology"
    elif any(x in text for x in ["ingredients", "supply chain", "additives", "chemical"]):
        return "Ingredients / Raw Materials"
    elif any(x in text for x in ["nutritionals", "nutrients", "nutritional solutions"]):
        return "Nutritional Solutions"
    elif any(x in text for x in ["supplements", "vitamins", "minerals"]):
        return "Supplements"
    elif any(x in text for x in ["personal care", "skincare", "cosmetics"]):
        return "Personal Care"
    else:
        return "Unknown"

def classify_health_segment(text):
    if "gut health" in text or "digestive health" in text:
        return "Gut Health"
    elif "women's health" in text:
        return "Women's Health"
    elif "cognitive health" in text or "mental wellness" in text:
        return "Cognitive Health"
    elif "sports nutrition" in text:
        return "Sports Nutrition"
    else:
        return "General Health"

def detect_roles(text):
    roles = {
        "Manufacturer": any(re.search(kw, text) for kw in ["manufacturing", "production", "plant capacity", "GMP certified", "facility"]),
        "Researcher": any(re.search(kw, text) for kw in ["research", "clinical trials", "r&d", "scientific", "study"]),
        "Distributor": any(re.search(kw, text) for kw in ["distributor", "supply", "raw material", "wholesale"])
    }
    return {k: "Yes" if v else "No" for k, v in roles.items()}

def is_website_relevant(text):
    return any(kw in text for kw in keywords)

def extract_contact_email(text):
    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
    return emails[0] if emails else "No email found"

def extract_phone_number(text):
    phone_numbers = re.findall(r'\b\+?[0-9][0-9(). \-]{8,}[0-9]\b', text)
    return phone_numbers[0] if phone_numbers else "No phone number found"

def extract_country(text):
    for country in country_keywords:
        if country.lower() in text:
            return country
    return "Unknown"

def scrape_website(url):
    logging.info(f"Scraping {url}")
    try:
        driver.get(url)
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        text = soup.get_text().lower()

        found_keywords = [kw for kw in keywords if kw in text]
        category = classify_category(text)
        health_segment = classify_health_segment(text)
        roles = detect_roles(text)
        company_name = extract_company_name(url)
        relevance = "Relevant" if is_website_relevant(text) else "Not Relevant"
        contact_email = extract_contact_email(text)
        phone_number = extract_phone_number(text)
        country = extract_country(text)

        return {
            "Company Name": company_name,
            "Website": url,
            "Keywords Found": ", ".join(found_keywords) if found_keywords else "No relevant keywords found",
            "Category": category,
            "Health Segment": health_segment,
            "Relevance": relevance,
            "Contact Email": contact_email,
            "Phone Number": phone_number,
            "Country": country,
            "Manufacturer": roles["Manufacturer"],
            "Researcher": roles["Researcher"],
            "Distributor": roles["Distributor"],
            "Status": "Success"
        }
    except Exception as e:
        logging.error(f"Error scraping {url}: {e}")
        return {
            "Company Name": extract_company_name(url),
            "Website": url,
            "Keywords Found": f"Error: {e}",
            "Category": "Error",
            "Health Segment": "Error",
            "Relevance": "Error",
            "Contact Email": "Error",
            "Phone Number": "Error",
            "Country": "Error",
            "Manufacturer": "Error",
            "Researcher": "Error",
            "Distributor": "Error",
            "Status": "Failed"
        }

# Scrape each website and collect results
scraped_data = [scrape_website(website) for website in company_websites]

# Convert results to DataFrame
df = pd.DataFrame(scraped_data)

# Save to Excel
excel_filename = "scraped_probiotics_data.xlsx"
df.to_excel(excel_filename, index=False)

# Close WebDriver
driver.quit()

logging.info(f"Scraping completed. Data saved to {excel_filename}")
print(f"Scraping completed. Data saved to {excel_filename}")
