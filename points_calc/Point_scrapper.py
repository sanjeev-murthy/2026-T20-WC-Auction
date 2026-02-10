import time
import pandas as pd
from io import StringIO
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException

# ==========================================
# CONFIGURATION SECTION
# ==========================================

# 1. YOUR LOGIN DETAILS (Optional: leave blank to log in manually)
LOGIN_URL = "https://www.cricbattle.com/Account/LoginRegister"
TARGET_URL = "https://fantasycricket.cricbattle.com/MyFantasy/Player-Scores-Breakdown?LeagueModel=SalaryCap&LeagueId=675295"

# 2. MATCH DROPDOWN SETTINGS
# IMPORTANT: You must replace 'ddlMatches' with the actual ID from the website.
# Right-click the match dropdown on the site -> Inspect -> Look for id="...".
MATCH_DROPDOWN_ID = "ddlMatch"  

# 3. CHOOSE YOUR MODE
# Options: "ALL" (runs every match in the dropdown) 
#          "SELECTED" (runs only the specific matches listed below)
MODE = "ALL" 

# 4. IF MODE IS "SELECTED", LIST THE MATCH NAMES HERE
# These must match the text in the dropdown exactly (e.g., "Match 1", "CSK vs MI").
SELECTED_MATCHES = [
    "Match 1",
    "Match 5",
    "Final"
]

# ==========================================
# MAIN SCRIPT
# ==========================================

def scrape_matches():
    # Setup Browser
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        # --- LOGIN PHASE ---
        driver.get(LOGIN_URL)
        print("\n" + "="*50)
        print("ACTION REQUIRED: Please log in manually in the browser.")
        input("Press ENTER here once you are logged in...")
        print("="*50 + "\n")

        # --- NAVIGATION PHASE ---
        print(f"Navigating to: {TARGET_URL}")
        driver.get(TARGET_URL)
        time.sleep(5)  # Wait for initial load

        # --- DROPDOWN DISCOVERY ---
        try:
            # Find the dropdown element
            select_element = driver.find_element(By.ID, MATCH_DROPDOWN_ID)
            dropdown = Select(select_element)
            
            # Get all available options from the dropdown
            all_options = dropdown.options
            print(f"Found dropdown with {len(all_options)} options.")
            
        except NoSuchElementException:
            print(f"ERROR: Could not find dropdown with ID '{MATCH_DROPDOWN_ID}'.")
            print("Please check the ID by right-clicking the dropdown on the site and hitting 'Inspect'.")
            return

        # --- ITERATION PHASE ---
        # Prepare a list to store all data
        master_data = []

        for option in all_options:
            match_name = option.text.strip()
            
            # SKIP LOGIC: Decides whether to process this match based on your MODE
            if match_name == "" or "Select" in match_name:
                continue  # Skip placeholder options like "Select Match"

            if MODE == "SELECTED" and match_name not in SELECTED_MATCHES:
                continue # Skip if not in your list
            
            print(f"Processing: {match_name}...")

            # 1. Click the option
            dropdown.select_by_visible_text(match_name)
            
            # 2. Wait for the table to reload (AJAX)
            time.sleep(4) 
            
            # 3. Scrape the table
            try:
                page_html = driver.page_source
                tables = pd.read_html(StringIO(page_html))
                
                if tables:
                    # Assume largest table is the data table
                    df = max(tables, key=len)
                    df['Match_Name'] = match_name # Add column to identify the match
                    master_data.append(df)
                    print(f"  -> Extracted {len(df)} rows.")

                    # Save per-match CSV
                    safe_name = "".join(ch if ch.isalnum() or ch in (" ", "-", "_") else "_" for ch in match_name).strip()
                    per_match_filename = f"match_scores_{safe_name}.csv"
                    df.to_csv(per_match_filename, index=False)
                    print(f"  -> Saved match file: {per_match_filename}")
                else:
                    print("  -> No table found for this match.")
                    
            except Exception as e:
                print(f"  -> Error reading table: {e}")

        # --- SAVING PHASE ---
        if master_data:
            print("\nConsolidating data...")
            final_df = pd.concat(master_data, ignore_index=True)
            
            filename = "all_matches_scores.csv"
            final_df.to_csv(filename, index=False)
            print(f"SUCCESS! Saved {len(final_df)} total rows to '{filename}'")
        else:
            print("No data was extracted. Check your match names or dropdown ID.")

    except Exception as e:
        print(f"Critical Error: {e}")

    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_matches()
