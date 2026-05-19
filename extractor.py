import asyncio
import json
import logging
from playwright.async_api import async_playwright

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def scrape_google_maps_reviews(url: str, max_reviews: int = 50):
    reviews_data = []
    seen_review_ids = set() # THE FIX: A memory bank to prevent duplicates

    async with async_playwright() as p:
        logging.info("Launching actual Google Chrome with Persistent Context...")
        
        context = await p.chromium.launch_persistent_context(
            user_data_dir="./chrome_profile", 
            channel="chrome", # <--- ADD THIS LINE
            headless=False,
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            locale='id-ID'
        )
        
        page = context.pages[0] 
        logging.info(f"Navigating to URL: {url}")
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            await page.wait_for_selector('h1', state='attached', timeout=15000)
            await page.wait_for_timeout(2000) 
            
            logging.info("Looking for the Reviews tab or Star Rating to click...")
            
            tab_locator = page.locator('button[role="tab"]:has-text("Ulasan"), button[role="tab"]:has-text("Reviews")').first
            stars_locator = page.locator('button[aria-label*="ulasan"], button[aria-label*="reviews"], div.F7nice').first

            clicked = False
            
            if await tab_locator.is_visible():
                logging.info("Target 1 found: Clicking the Reviews tab...")
                await tab_locator.click(force=True)
                clicked = True
            elif await stars_locator.is_visible():
                logging.info("Target 2 found: Clicking the Star Ratings text...")
                await stars_locator.click(force=True)
                clicked = True
            
            if not clicked:
                logging.warning("No explicit buttons found. Proceeding to brute-force scroll...")

            logging.info("Focusing sidebar and sending PageDown events to trigger network loads...")
            try:
                await page.locator('h1').click(force=True) 
                for _ in range(5):
                    await page.keyboard.press("PageDown")
                    await page.wait_for_timeout(800) 
            except Exception as scroll_err:
                logging.warning(f"Could not perform keyboard scroll: {scroll_err}")

            await page.wait_for_timeout(3000) 
            
            review_card_selector = 'div[data-review-id], div.jftiEf'
            await page.wait_for_selector(review_card_selector, timeout=15000)
            
        except Exception as e:
            logging.error(f"Failed to load the review feed for {url}: {e}")
            logging.info("Taking a screenshot of the crash...")
            await page.screenshot(path="timeout_crash_scene.png") 
            await context.close()
            return []

        logging.info("Reviews loaded! Starting extraction loop...")
        
        empty_scroll_attempts = 0 # Tracks if we've hit the bottom of the feed
        
        while len(reviews_data) < max_reviews:
            review_elements = await page.locator(review_card_selector).all()
            added_new_this_loop = False
            
            for element in review_elements:
                if len(reviews_data) >= max_reviews:
                    break
                    
                try:
                    # THE DUPLICATION FIX: Grab the unique ID for this specific review
                    review_id = await element.get_attribute('data-review-id')
                    
                    # If Google obfuscates the ID, fallback to using the raw text as the unique identifier
                    if not review_id:
                        text_element = element.locator('span.wiI7pd')
                        review_id = await text_element.inner_text() if await text_element.count() > 0 else None

                    # If we've already parsed this ID, skip to the next loop immediately
                    if not review_id or review_id in seen_review_ids:
                        continue 

                    more_btn = element.locator('button:has-text("More"), button:has-text("Lainnya")')
                    if await more_btn.count() > 0:
                        await more_btn.first.click()
                        await page.wait_for_timeout(500)

                    name_element = element.locator('div.d4r55')
                    name = await name_element.inner_text() if await name_element.count() > 0 else "Unknown"
                    
                    rating_element = element.locator('span[aria-label*="stars"], span[aria-label*="bintang"]')
                    rating_text = await rating_element.get_attribute('aria-label') if await rating_element.count() > 0 else ""
                    rating = int(rating_text.split(' ')[0]) if rating_text else None
                    
                    text_element = element.locator('span.wiI7pd')
                    text = await text_element.inner_text() if await text_element.count() > 0 else ""
                    
                    if text.strip():
                        # Save the ID to our memory bank so we never scrape it again
                        seen_review_ids.add(review_id)
                        reviews_data.append({
                            "author": name,
                            "rating": rating,
                            "text": text.replace('\n', ' ').strip()
                        })
                        added_new_this_loop = True
                except Exception as e:
                    logging.warning(f"Failed to parse a review block: {e}")

            logging.info(f"Collected {len(reviews_data)}/{max_reviews} unique reviews...")
            
            if len(reviews_data) >= max_reviews:
                break
                
            # If we scrolled but didn't find any new IDs, we might be at the end
            if not added_new_this_loop:
                empty_scroll_attempts += 1
                if empty_scroll_attempts >= 3:
                    logging.info("No new unique reviews found after multiple scrolls. Reached the end of the feed.")
                    break
            else:
                empty_scroll_attempts = 0 # Reset the counter if we found new data
                
            try:
                last_review = page.locator(review_card_selector).last
                await last_review.hover()
                await page.mouse.wheel(0, 5000) # Slightly lighter scroll to ensure we don't skip cards
                await page.wait_for_timeout(3000) 
            except Exception as e:
                logging.info(f"Could not scroll further. {e}")
                break

        await context.close()
        
    return reviews_data

async def main():
    # Replace with the URL from your screenshot testing
    target_urls = [
        "https://www.google.com/maps/place/TOMORO+COFFEE+-+Sesetan/@-8.6376254,115.2291566,12.5z/data=!4m8!3m7!1s0x2dd2419b879f2bd9:0x13aa3d0da3333020!8m2!3d-8.6793134!4d115.2150307!9m1!1b1!16s%2Fg%2F11vc1h_v81?entry=ttu&g_ep=EgoyMDI2MDUxNy4wIKXMDSoASAFQAw%3D%3D",
        "https://www.google.com/maps/place/TOMORO+COFFEE+-+Teuku+Umar+Barat/@-8.6737258,115.1423324,12z/data=!4m8!3m7!1s0x2dd2410000e6b91b:0x884d7c98af589665!8m2!3d-8.6817233!4d115.1906366!9m1!1b1!16s%2Fg%2F11w1zc_9_q?entry=ttu&g_ep=EgoyMDI2MDUxNy4wIKXMDSoASAFQAw%3D%3D",
        "https://www.google.com/maps/place/TOMORO+COFFEE+-+Seminyak/@-8.6737258,115.1423324,12z/data=!4m7!3m6!1s0x2dd2477be65e945b:0x8ce8e9b56c937232!8m2!3d-8.6834161!4d115.1665955!15sCg10b21vcm8gY29mZmVlWg8iDXRvbW9ybyBjb2ZmZWWSAQtjb2ZmZWVfc2hvcOABAA!16s%2Fg%2F11y22ck5cz?entry=tts&g_ep=EgoyMDI2MDUxNy4wIPu8ASoASAFQAw%3D%3D&skid=2f68e3d4-de7c-43a5-9ebf-82546579515f",
        "https://www.google.com/maps/place/TOMORO+COFFEE+-+Monang+Maning/@-8.6737258,115.1423324,12z/data=!4m7!3m6!1s0x2dd2416d7f0b7c45:0xb102bdf50b0db62e!8m2!3d-8.6661799!4d115.1985339!15sCg10b21vcm8gY29mZmVlWg8iDXRvbW9ybyBjb2ZmZWWSAQtjb2ZmZWVfc2hvcOABAA!16s%2Fg%2F11l5bw2c68?entry=tts&g_ep=EgoyMDI2MDUxNy4wIPu8ASoASAFQAw%3D%3D&skid=6d3da06b-365d-4e21-9ab6-89a10b12b10e",
        "https://www.google.com/maps/place/TOMORO+COFFEE+-+Merdeka+Renon/@-8.6737258,115.1423324,12z/data=!4m7!3m6!1s0x2dd24191f23a5c95:0x7c4a790729ba933e!8m2!3d-8.6669206!4d115.2387385!15sCg10b21vcm8gY29mZmVlWg8iDXRvbW9ybyBjb2ZmZWWSAQtjb2ZmZWVfc2hvcOABAA!16s%2Fg%2F11l66_x2h0?entry=tts&g_ep=EgoyMDI2MDUxNy4wIPu8ASoASAFQAw%3D%3D&skid=40d91ebb-474f-4cd4-ace3-a11d50f364d5",
        "https://www.google.com/maps/place/TOMORO+COFFEE+-+Universitas+Warmadewa/@-8.6737258,115.1423324,12z/data=!4m8!3m7!1s0x2dd241002c0bbc31:0x51c7c15815518631!8m2!3d-8.657372!4d115.2421643!9m1!1b1!16s%2Fg%2F11vqnpcbh8?entry=ttu&g_ep=EgoyMDI2MDUxNy4wIKXMDSoASAFQAw%3D%3D",
        "https://www.google.com/maps/place/TOMORO+COFFEE+-+SPBU+Jimbaran/@-8.6737258,115.1423324,12z/data=!4m7!3m6!1s0x2dd2450057d70233:0xf367783f32008d!8m2!3d-8.7979104!4d115.1611825!15sCg10b21vcm8gY29mZmVlWg8iDXRvbW9ybyBjb2ZmZWWSAQtjb2ZmZWVfc2hvcOABAA!16s%2Fg%2F11w1zcsk_f?entry=tts&g_ep=EgoyMDI2MDUxNy4wIPu8ASoASAFQAw%3D%3D&skid=1a825a91-5e12-4e0a-b302-daf08e93d59e",
        "https://www.google.com/maps/place/TOMORO+COFFEE+-+Waribang/@-8.6737258,115.1423324,12z/data=!4m7!3m6!1s0x2dd2412d63a55d79:0xc6e6b4c6823a0403!8m2!3d-8.6518647!4d115.2504578!15sCg10b21vcm8gY29mZmVlWg8iDXRvbW9ybyBjb2ZmZWWSAQRjYWZl4AEA!16s%2Fg%2F11z51p_kfv?entry=tts&g_ep=EgoyMDI2MDUxNy4wIPu8ASoASAFQAw%3D%3D&skid=17167736-cc15-4963-8651-717ee65638ee",
        "https://www.google.com/maps/place/Tomoro+Coffee+-+Nusa+Indah/@-8.6737258,115.1423324,12z/data=!4m7!3m6!1s0x2dd24110475e1471:0xadf94594f66803a3!8m2!3d-8.6490011!4d115.2334864!15sCg10b21vcm8gY29mZmVlWg8iDXRvbW9ybyBjb2ZmZWWSAQRjYWZl4AEA!16s%2Fg%2F11x0flt8v1?entry=tts&g_ep=EgoyMDI2MDUxNy4wIPu8ASoASAFQAw%3D%3D&skid=d62cdef7-ce3d-46ab-b68e-61f3c0a184ef",
        "https://www.google.com/maps/place/Tomoro+Coffee+-+Batubulan/@-8.6737258,115.1423324,12z/data=!4m7!3m6!1s0x2dd23ffe065eeb27:0x5225b6cb3e4312fb!8m2!3d-8.6309051!4d115.2594548!15sCg10b21vcm8gY29mZmVlkgELY29mZmVlX3Nob3DgAQA!16s%2Fg%2F11z5ffvy5g?entry=tts&g_ep=EgoyMDI2MDUxNy4wIPu8ASoASAFQAw%3D%3D&skid=c499c378-702e-4242-8ff9-4edca6c740a7",
        "https://www.google.com/maps/place/TOMORO+COFFEE+-+Gatot+Subroto/@-8.6737258,115.1423324,12z/data=!4m7!3m6!1s0x2dd23f076ffe38e3:0x9a114a8af1d8afa0!8m2!3d-8.6360305!4d115.2175944!15sCg10b21vcm8gY29mZmVlWg8iDXRvbW9ybyBjb2ZmZWWSAQtjb2ZmZWVfc2hvcOABAA!16s%2Fg%2F11l1ys9_dd?entry=tts&g_ep=EgoyMDI2MDUxNy4wIPu8ASoASAFQAw%3D%3D&skid=53e38a32-58a9-4677-9580-3917935ed753",
        "https://www.google.com/maps/place/TOMORO+COFFEE+-+Padang+Luwih/@-8.6737258,115.1423324,12z/data=!4m7!3m6!1s0x2dd239c2253b7219:0xab3e7fda5bfb9005!8m2!3d-8.6317777!4d115.1759707!15sCg10b21vcm8gY29mZmVlWg8iDXRvbW9ybyBjb2ZmZWWSAQtjb2ZmZWVfc2hvcOABAA!16s%2Fg%2F11vb_93my7?entry=tts&g_ep=EgoyMDI2MDUxNy4wIPu8ASoASAFQAw%3D%3D&skid=18640c37-4fbc-471a-beca-4df0bdafff46",
        "https://www.google.com/maps/place/Tomoro+Coffee+-+Antasura/@-8.6737258,115.1423324,12z/data=!4m7!3m6!1s0x2dd23f532ee062f9:0xce84e4d8f60a744!8m2!3d-8.613501!4d115.2219015!15sCg10b21vcm8gY29mZmVlWg8iDXRvbW9ybyBjb2ZmZWWSAQRjYWZl4AEA!16s%2Fg%2F11zjxz5lyn?entry=tts&g_ep=EgoyMDI2MDUxNy4wIPu8ASoASAFQAw%3D%3D&skid=37626b11-c554-4bdd-8107-fce8f9445b25",
        "https://www.google.com/maps/place/Tomoro+Coffee+-+Cokroaminoto/@-8.6737258,115.1423324,12z/data=!4m7!3m6!1s0x2dd23f0055d32105:0x43c2c9e9cb28d109!8m2!3d-8.6125882!4d115.1922096!15sCg10b21vcm8gY29mZmVlWg8iDXRvbW9ybyBjb2ZmZWWSAQtjb2ZmZWVfc2hvcOABAA!16s%2Fg%2F11y8j6_6y0?entry=tts&g_ep=EgoyMDI2MDUxNy4wIPu8ASoASAFQAw%3D%3D&skid=8a6ac45e-a0ef-48f2-92ab-223c4b31982c",
        "https://www.google.com/maps/place/TOMORO+COFFEE+-+Tabanan/@-8.5514853,115.059557,12z/data=!4m7!3m6!1s0x2dd23b0006fac1c9:0xd7de735b43754488!8m2!3d-8.5514792!4d115.1296087!15sCg10b21vcm8gY29mZmVlkgELY29mZmVlX3Nob3DgAQA!16s%2Fg%2F11n532bykr?entry=tts&g_ep=EgoyMDI2MDUxNy4wIPu8ASoASAFQAw%3D%3D&skid=e073e46f-fac1-4504-80a8-c23858236349",
        "https://www.google.com/maps/place/TOMORO+COFFEE+-+Rumah+Sakit+Ari+Canti/@-8.5991607,115.215988,10.75z/data=!4m7!3m6!1s0x2dd23dab00368d2f:0x43f5980d795f84fb!8m2!3d-8.5521769!4d115.2728283!15sCg10b21vcm8gY29mZmVlWg8iDXRvbW9ybyBjb2ZmZWWSAQtjb2ZmZWVfc2hvcOABAA!16s%2Fg%2F11y1k21kyg?entry=tts&g_ep=EgoyMDI2MDUxNy4wIPu8ASoASAFQAw%3D%3D&skid=5cf25edb-c24d-47e9-bbbb-cff109e45c9c",
        "https://www.google.com/maps/place/Tomoro+Coffee+-+Ubud/@-8.5991607,115.215988,10.75z/data=!4m7!3m6!1s0x2dd23d0027546413:0x61ae4a5054656e57!8m2!3d-8.5071332!4d115.2633354!15sCg10b21vcm8gY29mZmVlWg8iDXRvbW9ybyBjb2ZmZWWSAQtjb2ZmZWVfc2hvcOABAA!16s%2Fg%2F11yzvxclc8?entry=tts&g_ep=EgoyMDI2MDUxNy4wIPu8ASoASAFQAw%3D%3D&skid=394f3119-b501-415b-b41d-9a23a9e07c2a",
        "https://www.google.com/maps/place/TOMORO+COFFEE+-+Gianyar/@-8.5991607,115.215988,10.75z/data=!4m7!3m6!1s0x2dd21797ac1a43cf:0x2179f15036da6f70!8m2!3d-8.54093!4d115.3176454!15sCg10b21vcm8gY29mZmVlWg8iDXRvbW9ybyBjb2ZmZWWSAQtjb2ZmZWVfc2hvcOABAA!16s%2Fg%2F11l66zv9_f?entry=tts&g_ep=EgoyMDI2MDUxNy4wIPu8ASoASAFQAw%3D%3D&skid=67fff0a3-7bb9-4010-af22-509245a265fe",
        "https://www.google.com/maps/place/Tomoro+Coffee+-+Klungkung/@-8.5991607,115.215988,10z/data=!4m6!3m5!1s0x2dd2110006679c93:0x715f3922665d199a!8m2!3d-8.5428265!4d115.4025991!16s%2Fg%2F11mzx7d_4t?entry=ttu&g_ep=EgoyMDI2MDUxNy4wIKXMDSoASAFQAw%3D%3D",
        "https://www.google.com/maps/place/Tomoro+Coffee+-+Singaraja/@-8.1486736,115.0590143,13.75z/data=!4m7!3m6!1s0x2dd19b00624e84f5:0xa7c8afd65510e927!8m2!3d-8.1164878!4d115.0867015!15sCg10b21vcm8gY29mZmVlWg8iDXRvbW9ybyBjb2ZmZWWSAQtjb2ZmZWVfc2hvcOABAA!16s%2Fg%2F11x37437tk?entry=tts&g_ep=EgoyMDI2MDUxNy4wIPu8ASoASAFQAw%3D%3D&skid=cab7f0fe-ec9f-441d-bb3a-44d4df52fbe7"
    ]
    
    all_extracted_reviews = []
    
    for url in target_urls:
        logging.info(f"Starting extraction for: {url}")
        extracted = await scrape_google_maps_reviews(url, max_reviews=50) 
        all_extracted_reviews.extend(extracted)
    
    with open('tomoro_reviews.jsonl', 'w', encoding='utf-8') as f:
        for item in all_extracted_reviews:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
            
    logging.info(f"Successfully saved {len(all_extracted_reviews)} total UNIQUE reviews.")

if __name__ == "__main__":
    asyncio.run(main())