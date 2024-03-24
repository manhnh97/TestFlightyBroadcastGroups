import os
import re
import gspread
import requests
from lxml import html
from time import sleep
from selenium import webdriver
from fake_useragent import UserAgent
from requests.adapters import HTTPAdapter
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from copy_service_account_file import ValidateServiceAccountJSON #First time

URL_PROXIES = "https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&proxy_format=ipport&format=json"

# Group TestflightCampingApps
GROUPS_TESTFLIGHT_M_DASHBOARD = '-1002099467699'
GROUPS_TESTFLIGHT_M_CHAT = '-1001883897634'
GROUPS_TESTFLIGHT_X_ID = '-1001363951322'

TOKEN_REMINDSLOW_ID = '6717549493:AAEzYjWPhL0IQFQ1rnKEvEJ89lf3sbvxRGc'
BASE_URL_REDMINDSLOW = f"https://api.telegram.org/bot{TOKEN_REMINDSLOW_ID}/sendMessage"

TOKEN_CAMPINGAPPS_ID = '6675183376:AAFIHE7oDIHTb1vtOsZMLunu9oEcD0DwPTM'
BASE_URL_CAMPINGAPPS = f"https://api.telegram.org/bot{TOKEN_CAMPINGAPPS_ID}/sendMessage"


XPATH_TITLE = '/html/head/title/text()'
TITLE_REGEX = r'Join the (.+) beta - TestFlight - Apple'
XPATH_STATUS = '//*[@class="beta-status"]/span/text()'
FULL_TEXTS = 'This beta is full.'
EXPIRED_TEXT = "This beta isn't accepting any new testers right now."
PATTERN_AVAILABLE = r'To join the\s(.*?)\sbeta'

EXISTING_LINKS_FILE = "Testflight_List.txt"
LISTAPPSEARCH = "Result_ListAppSearch.txt"
PATTERN_TESTFLIGHT_LINKS = r'https?://testflight\.apple\.com/join/[a-zA-Z0-9]{8}'

MAX_RETRIES = 5

def Search_Keywords(driver, list_keywords):
    headers = {'User-Agent': user_agent.random}
    
    keyword = f"Join the {list_keywords} beta site:testflight.apple.com"
    duckduckgo_search = f"https://duckduckgo.com/?q=Join the {keyword.strip()} beta site:testflight.apple.com"
    driver.get(duckduckgo_search)
    wait = WebDriverWait(driver, 60)

    def Click_More_Results():
        max_attempts = 15
        for _ in range(max_attempts):
            try:
                more_results_button = wait.until(EC.element_to_be_clickable((By.ID, "more-results")))
                more_results_button.click()
                sleep(1)
            except NoSuchElementException:
                print("No more results button found")
                break
    Click_More_Results()

    elements = driver.find_elements(By.CSS_SELECTOR, '[data-testid="result-extras-url-link"]')
    
    for element in elements:
        testflight_links = re.search(PATTERN_TESTFLIGHT_LINKS, element.get_attribute('href'))
        if testflight_links:
            url = testflight_links.group(0)
            list_newtestflight_apps.add(url)
            
    with open(testflight_list_file, 'r', encoding='utf-8') as infile:
        existing_links = {line.strip() for line in infile if line is not None}
        
    for count, link in enumerate(list_newtestflight_apps, 1):
        if link not in existing_links:
            r = session.get(link, headers=headers)
            if r.status_code == 429:
                headers = {'User-Agent': user_agent.random}
                retry_after = int(r.headers.get('Retry-After', MAX_RETRIES))
                sleep(retry_after)
            
            if r.status_code == 200:
                page = html.fromstring(r.text)
                span_text = page.xpath(XPATH_STATUS)[0]
                text_matches = re.search(PATTERN_AVAILABLE, span_text, re.IGNORECASE)
                if text_matches:
                    textname_between_tothe_and_beta = text_matches.group(1).strip()
                    hashtags = re.findall(r"\b\w+\b", textname_between_tothe_and_beta)
                    hashtag = " ".join(["#" + hashtag.upper() for hashtag in hashtags])
                    parameter = {
                        "chat_id": GROUPS_TESTFLIGHT_X_ID,
                        "text": f"{hashtag}\n\n{link}"
                    }
                    requests.post(BASE_URL_REDMINDSLOW, data=parameter)
                    if count % 5 == 0:
                        sleep(1)
            new_testflight_links.add(link)
    
    list_newtestflight_apps.clear()
    if new_testflight_links:
        with open(testflight_list_file, 'a+', encoding='utf-8') as infile:
            for add_link in new_testflight_links:
                infile.write(f"\n{add_link}")
    new_testflight_links.clear()
    
    if count >= 10:
        r.close()
        session.close()

def Fetch_Beta_Apps_Info(credential):
    
    try:
        gc = gspread.service_account_from_dict(credential)
        sh = gc.open("TestflightCampingGeneral")
        worksheet = sh.worksheet("DuckDuckGo_S")
        
        values = worksheet.get_all_values()
        
        driver = webdriver.Chrome()
        for row in range(len(values)):  # Assuming the header is in the first row
            keywords_for_search = values[row][0]
            if keywords_for_search is not None:
                Search_Keywords(driver, keywords_for_search)
        
    except Exception as e:
        print(e)
    finally: 
        driver.quit()

if __name__ == "__main__":
    main_directory = os.path.dirname(os.path.abspath(__file__))
    listappsearch_folder = os.path.join(main_directory, 'Result_Keywords_Search')
    testflight_list_file = os.path.join(main_directory, EXISTING_LINKS_FILE)

    list_newtestflight_apps = set()
    new_testflight_links = set()
    list_unique_url = []
    user_agent = UserAgent()
    session = requests.Session()
    adapter = HTTPAdapter(max_retries=MAX_RETRIES)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    credential = ValidateServiceAccountJSON()
    Fetch_Beta_Apps_Info(credential)

