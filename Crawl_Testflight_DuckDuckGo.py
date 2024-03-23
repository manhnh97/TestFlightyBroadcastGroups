from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import re
import time
import gspread
from copy_service_account_file import ValidateServiceAccountJSON #First time

EXISTING_LINKS_FILE = "Testflight_List.txt"
PATTERN = r'https?://testflight\.apple\.com/join/[a-zA-Z0-9]{8}'
LISTAPPSEARCH = "Result_ListAppSearch.txt"


def search_keywords(driver, list_keywords):
    
    keyword = f"Join the {list_keywords} beta site:testflight.apple.com"
    duckduckgo_search = f"https://duckduckgo.com/?q=Join the {keyword.strip()} beta site:testflight.apple.com"
    driver.get(duckduckgo_search)
    wait = WebDriverWait(driver, 60)

    def click_more_results():
        max_attempts = 10
        for _ in range(max_attempts):
            try:
                more_results_button = wait.until(EC.element_to_be_clickable((By.ID, "more-results")))
                more_results_button.click()
                time.sleep(1)
            except NoSuchElementException:
                print("No more results button found")
                break
    click_more_results()

    elements = driver.find_elements(By.CSS_SELECTOR, '[data-testid="result-extras-url-link"]')
    links_text = '\n'.join(element.get_attribute('href') for element in elements)
    with open(os.path.join(listappsearch_folder, LISTAPPSEARCH), 'a+') as file:
        file.write(links_text)


def fetch_beta_apps_info(credential):
    
    try:
        gc = gspread.service_account_from_dict(credential)
        sh = gc.open("TestflightCampingGeneral")
        worksheet = sh.worksheet("DuckDuckGo_S")
        
        values = worksheet.get_all_values()
        
        driver = webdriver.Chrome()
        for row in range(1, len(values) + 1):  # Assuming the header is in the first row
            keywords_for_search = values[row][0]
            search_keywords(driver, keywords_for_search)
                    
    except Exception:
        pass
    finally: 
        driver.quit()


def cleanlistappsearch():
    
    with open(EXISTING_LINKS_FILE, 'r', encoding='utf-8') as infile:
        existing_links = {line.strip() for line in infile}
        
    list_newtestflight_apps = set()
    for (dirpath, dirnames, filenames) in os.walk(listappsearch_folder):
        for filename in filenames:
            with open(os.path.join(dirpath, filename), 'r', encoding='utf-8') as outfile:
                for line in outfile:
                    testflight_link_search = re.search(PATTERN, line, re.IGNORECASE)
                    if testflight_link_search:
                        link = testflight_link_search.group(0)
                        if link not in existing_links:
                            list_newtestflight_apps.add(link)

    with open(os.path.join(dirpath, LISTAPPSEARCH), 'w', encoding='utf-8') as output_unique:
        for link in list_newtestflight_apps:
            output_unique.write(link + '\n')

if __name__ == "__main__":
    main_directory = os.path.dirname(os.path.abspath(__file__))
    listappsearch_folder = os.path.join(main_directory, 'Result_Keywords_Search')

    credential = ValidateServiceAccountJSON()
    fetch_beta_apps_info(credential)
    cleanlistappsearch()














