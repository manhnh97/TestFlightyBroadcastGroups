from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import re
import requests
from fake_useragent import UserAgent
from lxml import html
import warnings

TOKEN_REMINDSLOW_ID = '6717549493:AAEzYjWPhL0IQFQ1rnKEvEJ89lf3sbvxRGc'
BASE_URL_REDMINDSLOW = f"https://api.telegram.org/bot{TOKEN_REMINDSLOW_ID}/sendMessage"

# GROUP_TESTFLIGHT_PERSONAL_ID = '-1001999506419'
# Nghien
THREAD_NGHIEN_ID = '235212'
GROUP_TESTFLIGHT_NGHIEN_ID = '-1001236644871'
# Khong gian mang
THREAD_KGM = '32'
GROUP_TESTFLIGHT_KGM_ID = '-1001823403288'
# Testflight1110chat
# THREAD_KGM = '32'
GROUP_TESTFLIGHT_1110_ID = '-1002077327541'

MAX_RETRIES = 3
XPATH_STATUS = '//*[@class="beta-status"]/span/text()'

async def handle_testflightapps(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    testflight_link = update.message.text
    
    warnings.filterwarnings('ignore', category=RuntimeWarning)
    PATTERN = r'https?://testflight\.apple\.com/join/[a-zA-Z0-9]{8}'

    if '#' in testflight_link:
        # await update.message.reply_text(testflight_link)
        parameter = {
            "message_thread_id": THREAD_NGHIEN_ID,
            "chat_id": GROUP_TESTFLIGHT_NGHIEN_ID,
            "text": testflight_link
        }
        r = requests.get(BASE_URL_REDMINDSLOW, data=parameter)

        parameter = {
            "message_thread_id": THREAD_KGM,
            "chat_id": GROUP_TESTFLIGHT_KGM_ID,
            "text": testflight_link
        }
        r = requests.get(BASE_URL_REDMINDSLOW, data=parameter)
        
        parameter = {
            # "message_thread_id": THREAD_KGM,
            "chat_id": GROUP_TESTFLIGHT_1110_ID,
            "text": testflight_link
        }
        r = requests.get(BASE_URL_REDMINDSLOW, data=parameter)
    elif re.search(PATTERN, testflight_link):
        # Define the pattern to match TestFlight links
        # Find all TestFlight links in the message
        urls = re.findall(PATTERN, testflight_link)

        for url in urls:
            user_agent = UserAgent()
            headers = {'User-Agent': user_agent.random}

            try:
                r = requests.get(url, headers=headers)
                if r.status_code == 200:
                    page = html.fromstring(r.text)
                    span_text = page.xpath(XPATH_STATUS)[0]
                    pattern_Available = r'To join the\s(.*?)\sbeta'
                    text_matches = re.search(pattern_Available, span_text, re.IGNORECASE)

                    if text_matches:
                        textname_between_tothe_and_beta = text_matches.group(1).strip()
                        hashtags = re.findall(r"\b\w+\b", textname_between_tothe_and_beta)
                        hashtag = " ".join(["#" + hashtag.upper() for hashtag in hashtags])
                        # await update.message.reply_text(f"{hashtag}\n\n{url}")
                        
                        parameter = {
                            "message_thread_id": THREAD_NGHIEN_ID,
                            "chat_id": GROUP_TESTFLIGHT_NGHIEN_ID,
                            "text": f"{hashtag}\n\n{url}"
                        }
                        r = requests.get(BASE_URL_REDMINDSLOW, data=parameter)

                        parameter = {
                            "message_thread_id": THREAD_KGM,
                            "chat_id": GROUP_TESTFLIGHT_KGM_ID,
                            "text": f"{hashtag}\n\n{url}"
                        }
                        r = requests.get(BASE_URL_REDMINDSLOW, data=parameter)
                        
                        parameter = {
                            # "message_thread_id": THREAD_KGM,
                            "chat_id": GROUP_TESTFLIGHT_1110_ID,
                            "text": f"{hashtag}\n\n{url}"
                        }
                        r = requests.get(BASE_URL_REDMINDSLOW, data=parameter)

            except (requests.RequestException, IndexError) as e:
                print("Error:", e)
                await update.message.reply_text("An error occurred while processing the TestFlight link.")
        else:
            update.message.reply_text("The provided message does not contain a TestFlight link")

app = ApplicationBuilder().token(TOKEN_REMINDSLOW_ID).build()

app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r".*testflight\.apple\.com.*"), handle_testflightapps))

app.run_polling()