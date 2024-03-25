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
from winsound import Beep

def Search_Keywords(driver, keyword):
    headers = {'User-Agent': user_agent.random}
    
    duckduckgo_search = f"https://duckduckgo.com/?q=Join the {keyword.strip()} beta site:testflight.apple.com"
    driver.get(duckduckgo_search)
    wait = WebDriverWait(driver, 30)

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
            
    with open(TXT_RESULT_TESTFLIGHT_LIST, 'r', encoding='utf-8') as txt_result_testflight_list:
        existing_links = {line.strip() for line in txt_result_testflight_list if line is not None}
    
    for link in list_newtestflight_apps:
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
                    
                    list_available_testflight_links.add(f"{textname_between_tothe_and_beta}:::{link}")
                    
            new_testflight_links.add(link)
    
    list_newtestflight_apps.clear()
    if new_testflight_links:
        with open(TXT_RESULT_TESTFLIGHT_LIST, 'a+', encoding='utf-8') as txt_result_testflight_list:
            for add_link in new_testflight_links:
                txt_result_testflight_list.write(f"\n{add_link}")
    new_testflight_links.clear()

    if list_available_testflight_links:
        with open(TXT_RESULT_CRAWL_TESTFLIGHT_LINKS, 'a+', encoding='utf-8') as txt_result_crawl_testflight_links:
            for add_link in list_available_testflight_links:
                txt_result_crawl_testflight_links.write(f"\n{add_link}")
    list_available_testflight_links


def Fetch_Beta_Apps_Info(credential):
    
    try:
        gc = gspread.service_account_from_dict(credential)
        sh = gc.open("TestflightCampingGeneral")
        worksheet = sh.worksheet("DuckDuckGo_S")
        
        values = worksheet.get_all_values()
        try: 
            driver = webdriver.Chrome()
            for row in range(1, len(values)):  # Assuming the header is in the first row
                keywords_for_search = values[row][0]
                if keywords_for_search is not None:
                    Search_Keywords(driver, keywords_for_search)
        except Exception as e:
            print("driver:", e)
        finally: 
            driver.quit()
        
    except Exception as e:
        print(e)

if __name__ == "__main__":
    
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
    
    MAIN_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
    TXT_RESULT_TESTFLIGHT_LIST = os.path.join(MAIN_DIRECTORY, "Testflight_List.txt")
    TXT_RESULT_CRAWL_TESTFLIGHT_LINKS = os.path.join(MAIN_DIRECTORY, 'DATA_TESTFLIGHT_CRAWL', 'Result_Crawl_Testflight_Links.txt')

    with open(TXT_RESULT_CRAWL_TESTFLIGHT_LINKS, 'w'):
        pass

    list_newtestflight_apps = set()
    list_available_testflight_links = set()
    new_testflight_links = set()
    list_unique_url = []
    user_agent = UserAgent()
    session = requests.Session()
    adapter = HTTPAdapter(max_retries=MAX_RETRIES)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    credential = ValidateServiceAccountJSON()
    Fetch_Beta_Apps_Info(credential)
    Beep(2000, 1000)
