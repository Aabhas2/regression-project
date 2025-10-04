from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, NoSuchElementException
from selenium_stealth import stealth
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import json
import random

def extract_price(price_text):
    """Extract numeric price value from price text"""
    try:
        if not price_text:
            return None
        price_text = price_text.replace(',', '').lower()
        value = re.findall(r'([\d.]+)', price_text)[0]
        if 'cr' in price_text:
            return float(value) * 10000000
        elif 'lac' in price_text or 'lakh' in price_text:
            return float(value) * 100000
        else:
            return float(value)
    except:
        return None

def extract_area(area_text):
    """Extract numeric area value from area text"""
    try:
        if not area_text:
            return None
        value = re.findall(r'([\d,]+\.?\d*)', area_text)[0].replace(',', '')
        if 'sqft' in area_text.lower() or 'sq ft' in area_text.lower():
            return float(value)
        elif 'sqm' in area_text.lower():
            return float(value) * 10.764  # Convert sqm to sqft
        elif 'sqyrd' in area_text.lower() or 'sq yrd' in area_text.lower():
            return float(value) * 9  # Convert sq yard to sq ft
        else:
            return float(value)
    except:
        return None

def extract_bhk(title):
    """Extract number of BHK from title"""
    try:
        if not title:
            return None
        match = re.search(r'(\d+)\s*bhk', title.lower())
        return int(match.group(1)) if match else None
    except:
        return None



def extract_age(text):
    """Extract property age from text"""
    try:
        if not text:
            return None
        if 'new construction' in text.lower() or 'under construction' in text.lower():
            return 0
        elif 'ready to move' in text.lower():
            return 1
        age_match = re.search(r'(\d+)\s*year[s]?\s*old', text.lower())
        if age_match:
            return int(age_match.group(1))
        return None
    except:
        return None

def clean_text(text):
    """Clean and normalize text"""
    if not text:
        return None
    return ' '.join(text.strip().split())

# Configuration
MAX_PROPERTIES = 12000  # Target number of properties 
MAX_RETRIES = 3  # Maximum number of retries for failed pages
SAVE_INTERVAL = 500  # Save data every N properties to prevent data loss

# Configure webdriver
options = webdriver.ChromeOptions()
# options.add_argument('--headless')  # Uncomment to run in headless mode
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--window-size=1920,1080')
options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36')
options.add_argument("--blink-settings=imagesEnabled=false")
prefs = {"profile.managed_default_content_settings.images": 2}
options.add_experimental_option("prefs", prefs)
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

# Initialize driver with stealth mode
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True)

driver.set_page_load_timeout(30)

# Initialize variables
data = []
page = 1
max_pages = 500  # Maximum number of pages to scrape (increased for 10K+ properties)
processed_listings = set()  # Track processed listings to avoid duplicates

print('\nStarting data collection...')
print(f"Target: {MAX_PROPERTIES} properties")

try:
    base_url = "https://housing.com/in/buy/new_delhi/new_delhi?page={}"
    
    while len(data) < MAX_PROPERTIES and page <= max_pages:
        current_url = base_url.format(page)
        print(f"\n{'='*10} Page {page} {'='*10}")
        
        # Load the page
        try:
            driver.get(current_url)
            print(f"Loading page {page}...")
            time.sleep(2)  # Wait for initial load
            
            # Handle cookie consent if it appears
            if page == 1:
                try:
                    cookie_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='cookie-consent-button']"))
                    )
                    cookie_button.click()
                    print("Cookie consent handled.")
                except Exception:
                    print("No cookie consent found or not clickable.")
            
            property_articles = WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "article[data-listingid]"))
            )
            print(f"Found {len(property_articles)} property articles on page {page}")
            
            # Process each property article
            for i, article in enumerate(property_articles):
                if len(data) >= MAX_PROPERTIES:
                    break
                
                try:
                    # Get the listing ID
                    listing_id = article.get_attribute('data-listingid')
                    
                    # Skip if already processed
                    if listing_id in processed_listings:
                        continue
                    processed_listings.add(listing_id)
                    
                    # Extract all necessary information
                    article_html = article.get_attribute('outerHTML')
                    soup = BeautifulSoup(article_html, 'html.parser')

                    # Debug: Print first article's structure
                    if i == 0 and page == 1:
                        print("DEBUG: First article structure:")
                        print(f"Listing ID: {listing_id}")
                        all_text = soup.get_text()
                        print("All text content:")
                        print(all_text[:500] + "...")

                    # Extract data using multiple strategies
                    title = None
                    price = None
                    area = None
                    location = None
                    bhk = None
                    age = None
                    parking = None

                    # Get all text from the article
                    all_text = soup.get_text()
                    
                    # Find title in link tags
                    title_links = soup.find_all("a")
                    for link in title_links:
                        link_text = clean_text(link.get_text())
                        if link_text and len(link_text) > 10:  # Likely a property title
                            title = link_text
                            break
                    
                    # Extract price using regex
                    price_patterns = [
                        r'₹\s*([\d.,]+)\s*(Lac|Lakh|Cr|Crore)',
                        r'([\d.,]+)\s*(Lac|Lakh|Cr|Crore)',
                        r'₹\s*([\d.,]+)'
                    ]
                    
                    for pattern in price_patterns:
                        price_match = re.search(pattern, all_text, re.IGNORECASE)
                        if price_match:
                            price = clean_text(price_match.group())
                            break
                    
                    # Extract area using regex
                    area_patterns = [
                        r'([\d.,]+)\s*(sq\.?\s*ft|sqft|sq\s*feet)',
                        r'([\d.,]+)\s*(sq\.?\s*m|sqm)',
                        r'([\d.,]+)\s*ft'
                    ]
                    
                    for pattern in area_patterns:
                        area_match = re.search(pattern, all_text, re.IGNORECASE)
                        if area_match:
                            area = clean_text(area_match.group())
                            break
                    
                    # Extract BHK
                    bhk_match = re.search(r'(\d+)\s*BHK', all_text, re.IGNORECASE)
                    if bhk_match:
                        bhk = int(bhk_match.group(1))
                    
                    # Try to find location/address
                    location_patterns = [
                        r'(Sector\s+\d+[A-Z]*)',
                        r'(Greater\s+Noida)',
                        r'(Noida)',
                        r'(Gurgaon)',
                        r'(Delhi)',
                        r'(Faridabad)',
                        r'(Ghaziabad)'
                    ]
                    
                    for pattern in location_patterns:
                        location_match = re.search(pattern, all_text, re.IGNORECASE)
                        if location_match:
                            location = clean_text(location_match.group())
                            break
                    
                    # Extract additional features for regression
                    age = extract_age(all_text)
                    
                    # Extract parking information
                    parking_match = re.search(r'(\d+)\s*(parking|car)', all_text, re.IGNORECASE)
                    if parking_match:
                        parking = int(parking_match.group(1))
                    elif 'parking' in all_text.lower():
                        parking = 1

                    # Debug output for first few cards
                    if i < 5:
                        print(f"DEBUG Article {i+1} (ID: {listing_id}): Title='{title}', Price='{price}', Area='{area}', BHK={bhk}")
                    
                    # Skip if essential data is missing
                    if not title and not price:
                        if i < 5:
                            print(f"DEBUG: Skipping article {i+1} - missing essential data")
                        continue

                    # Create comprehensive property data dictionary
                    property_data = {
                        "listing_id": listing_id,
                        "title": title,
                        "price_text": price,
                        "area_text": area,
                        "location": location,
                        "price": extract_price(price) if price else None,
                        "area_sqft": extract_area(area) if area else None,
                        "bhk": bhk or extract_bhk(title) if title else None,
                        "age_years": age,
                        "parking": parking,
                        "page_scraped": page
                    }
                    
                    data.append(property_data)
                    print(f"Scraped ({len(data)}): {title[:50] if title else 'No Title'}... (ID: {listing_id})")
                    
                    # Save progress periodically to prevent data loss
                    if len(data) % SAVE_INTERVAL == 0:
                        temp_df = pd.DataFrame(data)
                        temp_df.to_csv(f'housing_data_backup_{len(data)}.csv', index=False)
                        print(f"\n📁 Backup saved: housing_data_backup_{len(data)}.csv")
                            
                except Exception as e:
                    print(f"Error processing article {i+1}: {str(e)}")
                    if i < 3:  # Debug 
                        import traceback
                        traceback.print_exc()
                    continue
            
            # Move to next page
            page += 1
            time.sleep(random.uniform(2, 5))  # Increased random delay
            
        except TimeoutException:
            print(f"No properties found on page {page}. Moving to next page.")
            page += 1
            continue
        except Exception as e:
            print(f"Error loading page {page}: {str(e)}")
            page += 1  # Skip problematic page
            continue
            
except Exception as e:
    print(f"\nFatal error during scraping: {str(e)}")

finally:
    print(f"\nFinished scraping process:")
    print(f"Total pages processed: {page-1}")
    print(f"Total properties collected: {len(data)}")
    
    if data:
        # Create DataFrame and clean data
        df = pd.DataFrame(data)
        
        # Convert numeric columns
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df['area_sqft'] = pd.to_numeric(df['area_sqft'], errors='coerce')
        
        # Calculate price per sqft
        df['price_per_sqft'] = df['price'] / df['area_sqft']
        
        # Reorder columns for regression model
        desired_order = ['listing_id', 'title', 'price', 'bhk', 'area_sqft', 
                        'age_years', 'parking', 'location', 'price_per_sqft']
        remaining_cols = [col for col in df.columns if col not in desired_order]
        final_order = desired_order + remaining_cols
        
        df = df[final_order]
        
        # Save to CSV
        output_file = 'housing_data.csv'
        df.to_csv(output_file, index=False)
        print(f"\n✅ Successfully created {output_file}")
        
        # Print statistics
        print("\nDataset Statistics:")
        print(f"Total Properties: {len(df)}")
        print(f"Unique Listings: {df['listing_id'].nunique()}")
        print(f"Average Price: ₹{df['price'].mean():,.2f}")
        print(f"Average Area: {df['area_sqft'].mean():,.2f} sq ft")
        print(f"Average Price/sq ft: ₹{df['price_per_sqft'].mean():,.2f}")
        print(f"\nBHK Distribution:\n{df['bhk'].value_counts().sort_index()}")
        print(f"\nLocation Distribution:\n{df['location'].value_counts().head(10)}")
        print(f"\nFeature Completeness:")
        completeness = (df.notna().sum() / len(df) * 100).round(1)
        for col in ['price', 'bhk', 'area_sqft', 'age_years', 'parking', 'location']:
            if col in completeness:
                print(f"{col}: {completeness[col]}%")
        
        print("\nDataset Preview:")
        print(df[['title', 'bhk', 'price', 'area_sqft', 'location']].head())
        
        print("\nMissing Values Summary:")
        print(df.isnull().sum())
    else:
        print("❌ No data was scraped, so no CSV file was created.")

    driver.quit()