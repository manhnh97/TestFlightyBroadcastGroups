import requests
from requests.exceptions import ConnectTimeout
from requests.adapters import HTTPAdapter
from fake_useragent import UserAgent
import re
from random import choice
from time import sleep
import os
from lxml import html

# Constants
URL_PROXIES = "https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&proxy_format=ipport&format=json"

# Group TestflightCampingApps
GROUPS_TESTFLIGHT_M_DASHBOARD = '-1002099467699'
GROUPS_TESTFLIGHT_M_CHAT = '-1001883897634'

GROUP_TESTFLIGHT_EXPLORER_ID = '-1002031117480'

TOKEN_CAMPINGAPPS_ID = '6675183376:AAFIHE7oDIHTb1vtOsZMLunu9oEcD0DwPTM'
BASE_URL_CAMPINGAPPS = f"https://api.telegram.org/bot{TOKEN_CAMPINGAPPS_ID}/sendMessage"

XPATH_TITLE = '/html/head/title/text()'
TITLE_REGEX = r'Join the (.+) beta - TestFlight - Apple'
XPATH_STATUS = '//*[@class="beta-status"]/span/text()'
FULL_TEXTS = 'This beta is full.'
EXPIRED_TEXT = "This beta isn't accepting any new testers right now."
PATTERN_AVAILABLE = r'To join the\s(.*?)\sbeta'

EXISTING_LINKS_FILE = "Testflight_List.txt"
MAX_RETRIES = 5
list_newtestflight_apps = set()

def ListProxies():
    list_proxies = []
    response = requests.get(URL_PROXIES)
    proxy_data = response.json().get('proxies', [])  # Use get() with a default value of an empty list
    if response.status_code == 200:
        listCountry = ['VN', 'US']
        for proxies in proxy_data:
            ip_data = proxies.get('ip_data', {})  # Use get() to handle missing 'ip_data' key
            countryCode = ip_data.get('countryCode')
            if countryCode in listCountry:
                list_proxies.append((proxies['protocol'], proxies['proxy']))
    return list_proxies

def fetch_beta_apps_info(main_directory, data_proxy):

    listappsearch_file = os.path.join(main_directory, 'Result_Keywords_Search', 'Result_ListAppSearch.txt')
    try:
        with open(listappsearch_file, 'r', encoding='utf-8') as infile:
            try:
                user_agent = UserAgent()
                session = requests.Session()
                adapter = HTTPAdapter(max_retries=MAX_RETRIES)
                session.mount('http://', adapter)
                session.mount('https://', adapter)
                headers = {'User-Agent': user_agent.random}
                
                protocol, proxy = choice(data_proxy)
                
                for count, url in enumerate(infile, 1):
                    r = session.get(url, headers=headers, proxies={protocol: proxy})
                    
                    if r.status_code == 429:
                        headers = {'User-Agent': user_agent.random}
                        protocol, proxy = choice(data_proxy)
                        retry_after = int(r.headers.get('Retry-After', MAX_RETRIES))
                        sleep(retry_after)
                        continue
                    
                    if r.status_code == 200:
                        page = html.fromstring(r.text)
                        span_text = page.xpath(XPATH_STATUS)[0]
                        text_matches = re.search(PATTERN_AVAILABLE, span_text, re.IGNORECASE)
                        if text_matches:
                            textname_between_tothe_and_beta = text_matches.group(1).strip()
                            hashtags = re.findall(r"\b\w+\b", textname_between_tothe_and_beta)
                            hashtag = " ".join(["#" + hashtag.upper() for hashtag in hashtags])
                            parameter = {
                                "chat_id": GROUPS_TESTFLIGHT_M_DASHBOARD,
                                "text": f"{hashtag}\n\n{url}"
                            }
                            requests.post(BASE_URL_CAMPINGAPPS, data=parameter)
                        list_newtestflight_apps.add(url)
                    if count % 10:
                        sleep(1)
                            
            except (ConnectTimeout, AttributeError, IndexError) as e:
                print("2", e)
            finally:
                session.close()
    except Exception as e:
        print("1" ,e)

    testflight_list = os.path.join(main_directory, 'Testflight_List.txt')
    # Read existing links into a set
    with open(testflight_list, 'a+', encoding='utf-8') as output_unique:
        output_unique.write('\n')
        for link in list_newtestflight_apps:
            output_unique.write(link)
        
if __name__ == "__main__":
    main_directory = os.path.dirname(os.path.abspath(__file__))
    data_proxy = ListProxies()
    fetch_beta_apps_info(main_directory, data_proxy)