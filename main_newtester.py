import os
import re
import requests
from lxml import html
from time import sleep
from random import choice
from fake_useragent import UserAgent
from requests.adapters import HTTPAdapter
from requests.exceptions import ConnectTimeout



def ListProxies():
    list_proxies = []
    response = requests.get(URL_PROXIES)
    proxy_data = response.json().get('proxies', [])
    if response.status_code == 200:
        listCountry = ['VN']
        for proxies in proxy_data:
            ip_data = proxies.get('ip_data', {})
            countryCode = ip_data.get('countryCode')
            if countryCode in listCountry:
                list_proxies.append((proxies['protocol'], proxies['proxy']))
    return list_proxies

def fetch_beta_apps_info(data_proxy):
    var_newtesters = []
    with open(TXT_RESULT_NEWTESTERS_BETA_APPS, 'r', encoding='utf-8') as txt_result_newtesters_testflight_file:
        urls = list(set(txt_result_newtesters_testflight_file.read().split()))
        user_agent = UserAgent()
        session = requests.Session()
        adapter = HTTPAdapter(max_retries=MAX_RETRIES)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        headers = {'User-Agent': user_agent.random}
        protocol, proxy = choice(data_proxy)
        
        try:
            while urls:
                url_testflight = urls.pop(0).strip()
                try:
                    r = session.get(url_testflight, headers=headers, proxies={protocol: proxy})
                except (ConnectTimeout, ConnectionError) as e:
                    urls.append(url_testflight)
                    headers = {'User-Agent': user_agent.random}
                    protocol, proxy = choice(data_proxy)
                    continue
                if r.status_code == 429:
                    urls.append(url_testflight)
                    headers = {'User-Agent': user_agent.random}
                    protocol, proxy = choice(data_proxy)
                    retry_after = int(r.headers.get('Retry-After', MAX_RETRIES))
                    sleep(retry_after)
                    continue
                
                if r.status_code == 200:
                    page = html.fromstring(r.text)
                    status_elements = page.xpath(XPATH_STATUS)
                    title_elements = page.xpath(XPATH_TITLE)
                    
                    if status_elements and title_elements:
                        status = status_elements[0]
                        title = title_elements[0]
                        
                        free_slots = status not in FULL_TEXTS
                        
                        if free_slots:
                            title_match = re.findall(TITLE_REGEX, title)
                            if title_match:
                                hashtags = re.findall(r"\b\w+\b", title_match[0].strip())
                                hashtag = " ".join(["#" + tag.upper() for tag in hashtags])
                                parameter = {
                                    "chat_id": GROUP_TESTFLIGHT_CAMPINGAPPS_ID,
                                    "text": f"{hashtag}\n{url_testflight}\nOpening for New Testers"
                                }
                                requests.post(BASE_URL_REMINDSLOW, data=parameter)
                    
                    matches = re.findall(PATTERN_CODE, url_testflight.strip())

                    var_newtesters.extend(matches)
        except (ConnectTimeout, TimeoutError, OSError) as e:
            print(f"Connection error: {e}")
            headers = {'User-Agent': user_agent.random}
            protocol, proxy = choice(data_proxy)
            urls.append(url_testflight)
            pass
        finally:
            session.close()
            return var_newtesters

def update_testflight_list(var_newtesters):

    var_newtesters = set(var_newtesters)
    testflight_list = []
    
    with open(TXT_RESULT_TESTFLIGHT_LIST, 'r', encoding='utf-8') as f1:
        for line in f1:
            matches = re.findall(PATTERN_CODE,line.strip())
            testflight_list.extend(matches)
    
    updated_lines_f1 = [line for line in var_newtesters if line not in testflight_list]
    
    with open(TXT_RESULT_TESTFLIGHT_LIST, 'a+', encoding='utf-8') as f1:
        for line in updated_lines_f1:
            f1.write(f'\nhttps://testflight.apple.com/join/{line}')

if __name__ == "__main__":
    URL_PROXIES = "https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&proxy_format=ipport&format=json"
    
    MAIN_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
    
    TXT_RESULT_TESTFLIGHT_LIST = os.path.join(MAIN_DIRECTORY, "Testflight_List.txt")
    TXT_RESULT_NEWTESTERS_BETA_APPS = os.path.join(MAIN_DIRECTORY, "DATA_TESTFLIGHT_NEWTESTERS", "Result_Testflight_NewTesters_BetaApps.md")

    TOKEN_REMINDSLOW_ID = '6717549493:AAEzYjWPhL0IQFQ1rnKEvEJ89lf3sbvxRGc'
    BASE_URL_REMINDSLOW = f"https://api.telegram.org/bot{TOKEN_REMINDSLOW_ID}/sendMessage"
    GROUP_TESTFLIGHT_CAMPINGAPPS_ID = '-1002052388225'

    PATTERN_CODE = r'[a-zA-Z0-9]{8}\/?$'
    XPATH_STATUS = '//*[@class="beta-status"]/span/text()'
    XPATH_TITLE = '/html/head/title/text()'
    TITLE_REGEX = r'Join the (.+) beta - TestFlight - Apple'
    FULL_TEXTS = ['This beta is full.',
                "This beta isn't accepting any new testers right now."]
    MAX_RETRIES = 5
    
    data_proxy = ListProxies()
    var_newtesters = fetch_beta_apps_info(data_proxy)
    update_testflight_list(var_newtesters)