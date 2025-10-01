       # for i in range(processed_count, len(listings)): 
        #     try:
        #         listing = listings[i]

        #         listing_id = listing.get_attribute('id').replace('cardid', '') 

        #         if listing_id in processed_ids: 
        #             continue 
        #         processed_ids.add(listing_id)

        #         title = clean_text(listing.find_element(By.CSS_SELECTOR, ".mb-srp__card--title").text)
        #         price = clean_text(listing.find_element(By.CSS_SELECTOR, ".mb-srp__card__price--amount").text)
        #         area  = clean_text(listing.find_element(By.CSS_SELECTOR, ".mb-srp__card__summary--value").text)

        #         json_info = {}
        #         try:
        #             script_tag = listing.find_element(By.CSS_SELECTOR, 'script[type="application/ld+json"]')
        #             json_text = script_tag.get_attribute('innerHTML')
        #             json_info = json.loads(json_text)
        #         except Exception as e:
        #             # Fallback: 
        #             for obj in json_ld_data:
        #                 if isinstance(obj,dict) and obj.get("url") and title.split()[0] in obj.get("url", ""):
        #                     json_info = obj
        #                     break
                
        #         # Get optional fields like locality
        #         locality = None
        #         try: 
        #             locality = clean_text(listing.find_element(By.CSS_SELECTOR, ".mb-srp__card__society--name").text)
        #         except Exception: pass 

        #         # Get all other details from the summary list
        #         additional_info = {} 
        #         try: 
        #             details = listing.find_elements(By.CSS_SELECTOR, ".mb-srp__card__summary__list--item")
        #             additional_info = {
        #                 # Use the correct child class names for label and value
        #                 clean_text(d.find_element(By.CSS_SELECTOR, ".mb-srp__card__summary--label").text): 
        #                 clean_text(d.find_element(By.CSS_SELECTOR, ".mb-srp__card__summary--value").text)
        #                 for d in details
        #             }
        #         except Exception: pass
                
        #         # Create the data dictionary
        #         property_data = {
        #             "listing_id": listing_id,
        #             "title": title,
        #             "url": json_info.get("url"), # Get URL from JSON
        #             "price_text": price, 
        #             "area_text": area,
        #             "price": extract_price(price),
        #             "area_sqft": extract_area(area),
        #             "bhk": extract_bhk(title),
        #             "property_type": json_info.get('@type'),
        #             "latitude": json_info.get("geo", {}).get("latitude"),
        #             "longitude": json_info.get("geo", {}).get("longitude"),
        #             "locality": locality,
        #             "address": json_info.get("address", {}).get("addressLocality"),
        #             "is_new": 1 if additional_info.get("Transaction") == "New Property" else 0,
        #         }

        #         # Add all extra details (Bathrooms, Furnishing, etc.) from the website directly
        #         property_data.update(additional_info)
                
        #         data.append(property_data)
        #         new_listings += 1 
        #         if len(data) % 200 == 0:
        #             pd.DataFrame(data).to_csv('raw_partial.csv',index=False)
        #             print(f"Saved {len(data)} listings to raw_partial.csv")
        #         print(f"--> Successfully scraped: {title[:70]}...")
        #     except StaleElementReferenceException: 
        #         print(f"Listing {i} went stale, skipping this one.")
        #         continue
        #     except Exception as e: 
        #         print(f"Error processing listing #{i+1}: {str(e)}")
        #         continue
