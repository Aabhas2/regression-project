from selenium import webdriver
from selenium.webdriver.common.by import By 
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, NoSuchAttributeException
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
        value = re.findall(r'([\d.]+)',price_text)[0]
        if 'cr' in price_text:
            return float(value) * 10000000
        elif 'lac' in price_text or 'lakh' in price_text:
            return float(value) * 100000
        else:
            return float(value)
    except:
        return None 
    
def extract_area(area_text): 
    """"Extract numeric area value from area text"""
    try:
        if not area_text:
            return None 
        value = re.findall(r'[\d,]+\.?\d*', area_text)[0].replace(',','')
        if 'sqft' in area_text.lower() or 'sq ft' in area_text.lower(): 
            return float(value)
        elif 'sqm' in area_text.lower(): 
            return float(value) * 10.764 #convert sqm to sqft 
        elif 'sqyrd' in area_text.lower() or 'sq yrd' in area_text.lower(): 
            return float(value) * 9 # convert sq yard to sqft 
        else: 
            return float(value)
    except:
        return None 
    
def extract_bhk(title): 
    """Extract number of BHK from title"""
    try:
        if not title: 
            return None 
        match = re.search(r'(\d+)\s*bhk',title.lower())
        return int(match.group(1)) if match else None 
    except: 
        return None 
    
def clean_text(text): 
    """Clean and normalize text"""
    if not text: 
        return None 
    return ' '.join(text.strip().split())

# Configuration 
MAX_PROPERTIES = 10000 # Target number of properties 
MAX_RETRIES = 3 # Maximum number of retries for failed pages 
SAVE_INTERVAL = 500 # Save progress every 500 properties 
MAX_PAGES_PER_LOCATION = 100 # Max pages per location to avoid infinite loops 

# Configure webdriver 
options = webdriver.ChromeOptions() 
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--windo-size=1920,1080')
options.add_argument('--user-agent=Mozilla/5.0 (Winndows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36')
options.add_argument('--blink-settings=imagesEnabled=false')
prefs = {"profile.managed_default_content_settings.images": 2}
options.add_experimental_option("prefs",prefs) 
options.add_experimental_option("excludeSwitches",["enalbe-automation"])
options.add_experimental_option("useAutomationExtension", False)

# Initialize driver with stealth mode 
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=options)
stealth(driver,
        languages=["en-US","en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True)

driver.set_page_load_timeout(30) 

# Initialize variables 
data = [] 
all_locations = [
    "new_delhi/new_delhi",
    "gurgaon/gurgaon",
    "noida/noida",
    "greater_noida/greater_noida",
    "faridabad/faridabad",
    "ghaziabad/ghaziabad"
]

print('\nStarting data collection...')
print(f"Target: {MAX_PROPERTIES} properties across {len(all_locations)} cities")

try:
    for location_idx, location in enumerate(all_locations):
        if len(data) >= MAX_PROPERTIES:
            break 
        print(f"\n{'='*20} LOCATION {location_idx+1}/{len(all_locations)}: {location.upper()} {'='*20}")
        base_url = f"https://housing.com/in/buy/{location}?page={{}}"

        page = 1 
        location_data_count = 0 


        while len(data) < MAX_PROPERTIES and page <= MAX_PAGES_PER_LOCATION and location_data_count < 2000: 
            current_url = base_url.format(page) 
        print(f"\n{'='*10} Page {page} {'='*10}")

        # Load the page
        try: 
            driver.get(current_url) 
            print(f"Loading page {page}...")
            time.sleep(2) # Wait for initial load 

            # Handle cookie consent if it appears 
            if page == 1: 
                try: 
                    cookie_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='cookie-consent-button']")))
                    cookie_button.click() 
                    print("Cookie conset handled.")
                except Exception: 
                    print("No cookie consent found or not clickable.")

            # Wait for property cards to load - target actual property articles 
            property_articles = WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "article[data-listingid]"))
            )
            print(f"Found {len(property_articles)} property articles on page {page}")

            # Process each property article 
            for i, article in enumerate(property_articles): 
                if len(data) >= MAX_PROPERTIES: 
                    break 
                try:
                    # Get listing ID 
                    listing_id = article.get_attribute('data-listingid')

                    # Extract all necessary information 
                    article_html = article.get_attribute('outerHTML')
                    soup = BeautifulSoup(article_html, 'html.parser')

                    # Debug: print first article's structure 
                    if i==0 and page==1: 
                        print("DEBUG: First article structure:")
                        print(f"Listing ID: {listing_id}")
                        all_text = soup.get_text() 
                        print("All text content:")
                        print(all_text[:500] + "...")

                    # Extract data using multiple strats 
                    title = None 
                    price = None 
                    area = None 
                    location = None 
                    bhk = None 

                    # Get all text from the article 
                    all_text = soup.get_text() 

                    # Strat 1: Find title in link tags 
                    title_links = soup.find_all("a")
                    for link in title_links: 
                        link_text = clean_text(link.get_text())
                        if link_text and len(link_text) > 10: 
                            title = link_text
                            break 

                    # Strat 2: Extract price using regex 
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

                    # Strat 3: Extract area using regex 
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

                    # Strat 4: Extract BHK 
                    bhk_match = re.search(r'(\d+)\s*BHK',all_text, re.IGNORECASE)
                    if bhk_match: 
                        bhk = int(bhk_match.group(1))

                    # Strat 5: Extract comprehensive property features 
                    # Basic location from current city 
                    city = location.split('/')[0].replace('_',' ').title() 

                    # detailed location/address 
                    location_patterns = [
                        r'(Sector\s+\d+[A-Z]*)',
                        r'(Greater\s+Noida)',
                        r'(Noida)',
                        r'(Gurgaon)',
                        r'(Delhi)',
                        r'(Faridabad)',
                        r'(Ghaziabad)',
                        r'(Phase\s+\d+)',
                        r'([A-Z][a-z]+\s+Vihar)',
                        r'([A-Z][a-z]+\s+Extension)',
                        r'([A-Z][a-z]+pur)',
                        r'([A-Z][a-z]+\s+Enclave)'
                    ]

                    for pattern in location_patterns: 
                        location_match = re.search(pattern, all_text, re.IGNORECASE)
                        if location_match: 
                            location = clean_text(location_match.group())
                            break 

                    # Extract additional features 
                    # Property type 
                    property_type = None 
                    type_patterns = [
                        r'(apartment|flat)',
                        r'(villa|bungalow)',
                        r'(house|kothi)',
                        r'(duplex)',
                        r'(penthouse)',
                        r'(studio)',
                        r'(plot|land)'
                    ]

                    for pattern in type_patterns: 
                        type_match = re.search(pattern, all_text, re.IGNORECASE)
                        if type_match: 
                            property_type = clean_text(type_match.group())
                            break 

                    # Bathrooms 
                    bathrooms = None 
                    bath_match = re.search(r'(\d+)\s*(bath|toilet)', all_text, re.IGNORECASE)
                    if bath_match: 
                        bathrooms = int(bath_match.group(1))

                    # Floor details 
                    floor = None 
                    total_floors = None 
                    floor_match = re.search(r'(\d+)(?:st|nd|rd|th)?\s*floor\s*out\s*of\s*(\d+)', all_text, re.IGNORECASE)
                    if floor_match: 
                        floor = int(floor_match.group(1))
                        total_floors = int(floor_match.group(2))
                    else: 
                        floor_match = re.search(r'(\d+)(?:st|nd|rd|th)?\s*floor', all_text, re.IGNORECASE)
                        if floor_match: 
                            floor = int(floor_match.group(1))

                    # Furnishing status 
                    furnishing = None 
                    if re.search(r'fully\s*furnished', all_text, re.IGNORECASE):
                        furnishing = 'Fully Furnished'
                    elif re.search(r'semi\s*furnished', all_text, re.IGNORECASE):
                        furnishing = 'Semi Furnished'
                    elif re.search(r'unfurnished', all_text, re.IGNORECASE):
                        furnishing = 'Unfurnished'

                    # Age of property 
                    age = None 
                    age_patterns = [
                        r'(\d+)\s*year[s]?\s*old',
                        r'ready\s*to\s*move',
                        r'under\s*construction',
                        r'new\s*launch'
                    ]
                    for pattern in age_patterns: 
                        age_match = re.search(pattern, all_text, re.IGNORECASE)
                        if age_match:
                            if 'year' in age_match.group():
                                age = int(re.findall(r'\d+', age_match.group())[0])
                            elif 'ready' in age_match.group().lower():
                                age = 'Ready to Move'
                            elif 'construction' in age_match.group().lower():
                                age = 'Under Construction'
                            elif 'launch' in age_match.group().lower():
                                age = 'New Launch'
                            break

                    # Parking 
                    parking = None 
                    if re.search(r'parking|garage', all_text, re.IGNORECASE):
                        park_match = re.search(r'(\d+)\s*parking', all_text, re.IGNORECASE)
                        if park_match:
                            parking = int(park_match.group(1))
                        else:
                            parking = 1

                    # Balcony 
                    balcony = None 
                    bal_match = re.search(r'(\d+)\s*balcon', all_text, re.IGNORECASE)
                    if bal_match:
                        balcony = int(bal_match.group(1))
                    elif re.search(r'balcony',all_text, re.IGNORECASE):
                        balcony = 1 

                    # Amenities (boolean flags) 
                    has_gym = bool(re.search(r'gym|fitness',all_text,re.IGNORECASE))
                    has_pool = bool(re.search(r'pool|swimming', all_text, re.IGNORECASE))
                    has_security = bool(re.search(r'security|guard', all_text, re.IGNORECASE))
                    has_lift = bool(re.search(r'lift|elevator', all_text, re.IGNORECASE))
                    has_power_backup = bool(re.search(r'power\s*backup|generator', all_text, re.IGNORECASE))
                    has_garden = bool(re.search(r'garden|park', all_text, re.IGNORECASE))
                    has_club = bool(re.search(r'club\s*house', all_text, re.IGNORECASE))


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
                        # Basic
                        "listing_id": listing_id,
                        "title": title,
                        "city": city,
                        "location": location,

                        # Price and area (raw and processed) 
                        "price_text": price, 
                        "area_text": area, 
                        "price": extract_price(price) if price else None, 
                        "area_sqft": extract_area(area) if area else None,

                        # Property features 
                        "bhk": bhk or extract_bhk(title) if title else None,
                        "bathrooms": bathrooms,
                        "property_type": property_type,

                        # Location and building features 
                        "floor": floor, 
                        "total_floors": total_floors,
                        "furnishing": furnishing,
                        "age": age, 
                        "parking": parking, 
                        "balcony": balcony, 

                        # Amenities (boolean features) 
                        "has_gym": has_gym,
                        "has_pool": has_pool,
                        "has_security": has_security,
                        "has_lift": has_lift,
                        "has_power_backup": has_power_backup,
                        "has_garden": has_garden,
                        "has_club": has_club,

                        # Derived features for modeling 
                        "price_per_sqft": extract_price(price) / extract_area(area) if (price and area and extract_price(price) and extract_area(area)) else None, 
                        "is_high_floor": floor > 5 if floor else None, 
                        "is_new_property": age == 'New Launch' or age == 'Under Construction' if age else None 
                    }

                    data.append(property_data)
                    location_data_count += 1 
                    print(f"Scraped ({len(data)}): {title[:50] if title else 'No Title'}... (ID: {listing_id})")

                    # Save progress periodically 
                    if len(data) % SAVE_INTERVAL == 0: 
                        temp_df = pd.DataFrame(data) 
                        temp_df.to_csv(f"housing_data_backup_{len(data)}.csv",index=False)
                        print(f"\n📁 Progress saved: {len(data)} properties collected")
 
                except Exception as e:
                    print(f"Error processing article {i+1}: {str(e)}")
                    if i < 3: 
                        import traceback
                        traceback.print_exc() 
                    continue

            # Move to next page within current location 
            page += 1 
            print(f"Location progress: {location_data_count} properties from {location}")
            time.sleep(random.uniform(2,5))

        except TimeoutException: 
            print(f"No properties found on page {page}. Moving to next page.")
            page += 1 
            continue 
        except Exception as e: 
            print(f"Error loading page {page}: {str(e)}")
            page += 1 
            continue 

except Exception as e: 
    print(f"\nFatal error during scraping: {str(e)}")

finally: 
    print(f"\nFinished scraping process:")
    print(f"Total pages processed: {page-1}")
    print(f"Total properties collected: {len(data)}")

    if data: 
        df = pd.DataFrame(data) 

        # Convert numeric columns 
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df['area_sqft'] = pd.to_numeric(df['area_sqft'], errors='coerce')

        # Calculate price per sqft 
        df['price_per_sqft'] = df['price'] / df['area_sqft']

        # Reorder columns for better analysis 
        desired_order = [
            # Identifiers
            'listing_id', 'title', 'city', 'location',
            # Target and key features
            'price', 'price_per_sqft', 'area_sqft', 'bhk', 'bathrooms',
            # Property characteristics
            'property_type', 'floor', 'total_floors', 'furnishing', 'age', 'parking', 'balcony',
            # Amenities
            'has_gym', 'has_pool', 'has_security', 'has_lift', 'has_power_backup', 'has_garden', 'has_club',
            # Derived features
            'is_high_floor', 'is_new_property',
            # Raw text data
            'price_text', 'area_text'
        ]
        remaining_cols = [col for col in df.columns if col not in desired_order]
        final_order = desired_order + remaining_cols

        df = df[final_order]

        # Save to csv 
        output_file = 'housing_data.csv'
        df.to_csv(output_file, index=False)
        print(f"\n✅ Successfully created {output_file}")

        # Print comprehensive statistics 
        print("\n" + "="*50)
        print("COMPREHENSIVE DATASET STATISTICS")
        print("="*50)
        print(f"Total Properties: {len(df)}")
        print(f"Cities Covered: {df['city'].nunique()}")
        print(f"Unique Locations: {df['location'].nunique()}")
        print("\n💰 PRICE STATISTICS:")
        print(f"Average Price: ₹{df['price'].mean():,.0f}")
        print(f"Median Price: ₹{df['price'].median():,.0f}")
        print(f"Price Range: ₹{df['price'].min():,.0f} - ₹{df['price'].max():,.0f}")
        print(f"Average Price/sq ft: ₹{df['price_per_sqft'].mean():,.0f}")
        print("\n🏠 PROPERTY FEATURES:")
        print(f"Average Area: {df['area_sqft'].mean():,.0f} sq ft")
        print(f"BHK Distribution:\n{df['bhk'].value_counts().sort_index()}")
        print(f"\nProperty Types:\n{df['property_type'].value_counts()}")
        print(f"\nFurnishing Status:\n{df['furnishing'].value_counts()}")
        print(f"\n🏙️ CITY-WISE DISTRIBUTION:")
        print(df['city'].value_counts())
        print(f"\n🎯 FEATURE COVERAGE:")
        feature_coverage = (df.notna().sum() / len(df) * 100).sort_values(ascending=False)
        for feature in ['price','area_sqft','bhk','bathrooms','floor','parking']:
            if feature in feature_coverage: 
                print(f"{feature} {feature_coverage[feature]:.1f}% coverage")

        print("\nDataset Preview:")
        print(df[['title', 'bhk', 'price', 'area_sqft', 'location']].head())

        print("\nMissing Values Summary:")
        print(df.isnull().sum())
    else: 
        print("❌ No data was scraped, so no CSV file was created.")
    driver.quit()
    