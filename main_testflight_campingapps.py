from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import re
import requests
from fake_useragent import UserAgent
from lxml import html
import warnings

TOKEN_CAMPINGAPPS_ID = '6675183376:AAFIHE7oDIHTb1vtOsZMLunu9oEcD0DwPTM'
BASE_URL_CAMPINGAPPS = f"https://api.telegram.org/bot{TOKEN_CAMPINGAPPS_ID}/sendMessage"

# Group TestflightCampingApps
GROUPS_TESTFLIGHT_CAMPINGAPPS_DASHBOARD = '-1002117624357'
GROUPS_TESTFLIGHT_CAMPINGAPPS_CHAT = '-1002011883262'

# Testflight_Mesasge
THREAD_CONTACT_M = '11'
GROUP_TESTFLIGHT_CONTACT_M = '-1002031575789'

MAX_RETRIES = 3
PATTERN_TESTFLIGHT = r'https?.*testflight\.apple\.com/join/[a-zA-Z0-9]{8}'
XPATH_STATUS = '//*[@class="beta-status"]/span/text()'
XPATH_TITLE = '/html/head/title/text()'
TITLE_REGEX = r'Join the (.+) beta - TestFlight - Apple'
user_agent = UserAgent()
warnings.filterwarnings('ignore', category=RuntimeWarning)

def Send_Message_Groups(hashtag, url):
    parameter = {
        "chat_id": GROUPS_TESTFLIGHT_CAMPINGAPPS_DASHBOARD,
        "text": f"{hashtag}\n\n{url}"
    }
    requests.get(BASE_URL_CAMPINGAPPS, data=parameter)

async def Start_Now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, \
            text="Hi sir, \
                \nThis is my bot and my group @testflightcampingapps. \
                \nThe bot support me post testflight apps soon. \
                \nIf you need contact to me. Please use /cc \"your message\". \
                \nHave a great day!")

async def Contact_M(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    username = update.message.chat.username
    message_contact_m = ' '.join(context.args)
    
    parameter = {
        "message_thread_id": THREAD_CONTACT_M,
        "chat_id": GROUP_TESTFLIGHT_CONTACT_M,
        "text": f"chat_id: {chat_id}\nusername: {username}\nmessage: {message_contact_m}"
    }
    requests.get(BASE_URL_CAMPINGAPPS, data=parameter)
    
async def Handle_TestflightApps_Private(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    headers = {'User-Agent': user_agent.random}
    if update.message and update.message.text:
        testflight_link = update.message.text
        if '#' in testflight_link:
            
            url = re.search(PATTERN_TESTFLIGHT, testflight_link).group(0)
            if url:
                r = requests.get(url, headers=headers)
                page = html.fromstring(r.text)
                title = re.findall(
                        TITLE_REGEX,
                        page.xpath(XPATH_TITLE)[0])[0]
                hashtags = re.findall(r"\b\w+\b", title)
                hashtag = " ".join(["#" + hashtag.upper() for hashtag in hashtags])
                
                Send_Message_Groups(hashtag, url)
            
        elif re.search(PATTERN_TESTFLIGHT, testflight_link):
            
            urls = re.findall(PATTERN_TESTFLIGHT, testflight_link)
            for url in urls:
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
                            Send_Message_Groups(hashtag, url)
                            
                except (requests.RequestException, IndexError) as e:
                    print("Error:", e)
                    await update.message.reply_text("An error occurred while processing the TestFlight link.")

def Handle_Entity_Links(url):
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
                Send_Message_Groups(hashtag, url)
    except (requests.RequestException, IndexError) as e:
        print("Error:", e)

async def Handle_TestflightApps_Entities(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    for entity in update.message.entities:
        if entity.type == 'text_link' and r'testflight.apple.com' in entity.url:
            testflight_link = entity.url
            Handle_Entity_Links(testflight_link)

app = ApplicationBuilder().token(TOKEN_CAMPINGAPPS_ID).build()

app.add_handler(CommandHandler('start', Start_Now, filters.ChatType.PRIVATE))
app.add_handler(CommandHandler('help', Start_Now, filters.ChatType.PRIVATE))
app.add_handler(CommandHandler('cc', Contact_M, filters.ChatType.PRIVATE))
app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE & filters.Regex(PATTERN_TESTFLIGHT), Handle_TestflightApps_Private))
app.add_handler(MessageHandler(filters.TEXT & (filters.Entity("url") | filters.Entity("text_link")) & filters.ChatType.PRIVATE, Handle_TestflightApps_Entities))

app.run_polling()