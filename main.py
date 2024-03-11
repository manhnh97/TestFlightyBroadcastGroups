from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import re
import requests
from fake_useragent import UserAgent
from lxml import html
import warnings

TOKEN_REMINDSLOW_ID = '6717549493:AAEzYjWPhL0IQFQ1rnKEvEJ89lf3sbvxRGc'
BASE_URL_REDMINDSLOW = f"https://api.telegram.org/bot{TOKEN_REMINDSLOW_ID}/sendMessage"

# Group TestflightCampingApps
GROUPS_TESTFLIGHT_CAMPINGAPPS_DASHBOARD = '-1002117624357'
GROUPS_TESTFLIGHT_CAMPINGAPPS_CHAT = '-1002011883262'
# Nghien
THREAD_NGHIEN_ID = '235212'
GROUP_TESTFLIGHT_NGHIEN_ID = '-1001236644871'
# Khong gian mang
THREAD_KGM = '32'
GROUP_TESTFLIGHT_KGM_ID = '-1001823403288'
# Testflight1110chat
GROUP_TESTFLIGHT_1110_ID = '-1002112742740'
# Testflight_Reviews
GROUP_TESTFLIGHT_REVIEWS_ID = '-1001170452834'
GROUPS_TESTFLIGHT_X_ID = '-1001363951322'
# Testflight_Mesasge
THREAD_CONTACT_M = '11'
GROUP_TESTFLIGHT_CONTACT_M = '-1002031575789'

MAX_RETRIES = 3
PATTERN_TESTFLIGHT = r'https?.*testflight\.apple\.com/join/[a-zA-Z0-9]{8}'
XPATH_STATUS = '//*[@class="beta-status"]/span/text()'
XPATH_TITLE = '/html/head/title/text()'
TITLE_REGEX = r'Join the (.+) beta - TestFlight - Apple'
pattern_Available = r'To join the\s(.*?)\sbeta'

user_agent = UserAgent()
warnings.filterwarnings('ignore', category=RuntimeWarning)

def Send_Message_Groups(hashtag, url):
    
    parameter = {
        "chat_id": GROUPS_TESTFLIGHT_CAMPINGAPPS_DASHBOARD,
        "text": f"{hashtag}\n\n{url}"
    }
    requests.get(BASE_URL_REDMINDSLOW, data=parameter)
    
    parameter = {
        "message_thread_id": THREAD_NGHIEN_ID,
        "chat_id": GROUP_TESTFLIGHT_NGHIEN_ID,
        "text": f"{hashtag}\n\n{url}"
    }
    requests.get(BASE_URL_REDMINDSLOW, data=parameter)

    parameter = {
        "chat_id": GROUP_TESTFLIGHT_1110_ID,
        "text": f"{hashtag}\n\n{url}"
    }
    requests.get(BASE_URL_REDMINDSLOW, data=parameter)
    
    parameter = {
        "chat_id": GROUPS_TESTFLIGHT_X_ID,
        "text": f"{hashtag}\n\n{url}"
    }
    requests.get(BASE_URL_REDMINDSLOW, data=parameter)
    
    parameter = {
        "message_thread_id": THREAD_KGM,
        "chat_id": GROUP_TESTFLIGHT_KGM_ID,
        "text": f"{hashtag}\n\n{url}"
    }
    requests.get(BASE_URL_REDMINDSLOW, data=parameter)

async def Start_Now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    await context.bot.send_message(chat_id=update.effective_chat.id, \
            text="Hi people, \
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
    requests.get(BASE_URL_REDMINDSLOW, data=parameter)
    
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

def Is_Available_Apps(url):
    headers = {'User-Agent': user_agent.random}
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            page = html.fromstring(r.text)
            span_text = page.xpath(XPATH_STATUS)[0]
            pattern_Available = r'To join the\s(.*?)\sbeta'
            text_matches = re.search(pattern_Available, span_text, re.IGNORECASE)

            return text_matches
    except (requests.RequestException, IndexError) as e:
        print("Error:", e)

async def Handle_TestflightApps_Entities(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    for entity in update.message.entities:
        if entity.type == 'text_link' and r'testflight.apple.com' in entity.url:
            testflight_link = entity.url
            Handle_Entity_Links(testflight_link)
app = ApplicationBuilder().token(TOKEN_REMINDSLOW_ID).build()

async def Handle_Testflight_Reviews_Group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_info = update.message.from_user.to_dict()
    message = update.message
    if message and message.text and user_info['is_bot'] == False:
        member_user = user_info['first_name']
        if re.search(r'ree?dee?m|code', message.text):
            await update.message.reply_text(f"Hi {member_user}, \
                                            \nWe have not Redeem Code, use Testflight Links, please. \
                                            \nPlease read: [Redeem Code](https://t.me/testflightR/70210)"
                                            , parse_mode=ParseMode.MARKDOWN)

# async def Handle_Testflight_Reviews_CheckApps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # pass

async def Start_Testflight_Reviews(update: Update, context: ContextTypes.DEFAULT_TYPE):
    member_user = update.message.from_user.to_dict()['first_name']
    await update.message.reply_text(f"Hi {member_user}, \
                \n- Use (/help | /start) for help, \
                \n- Use (/search | /s) to understand search apps \
                \n- Use (code | redeem) keywords to understand Redeem Code \
                \n- Updating...")

async def Search_Testflight_Reviews(update: Update, context: ContextTypes.DEFAULT_TYPE):
    member_user = update.message.from_user.to_dict()['first_name']
    await update.message.reply_text(f"- Hi {member_user}, \
                \nPlease use the search function to find apps. \
                \nExample: \
                \n- - Find Facebook => #FACEBOOK \
                \n- - Find Microsoft WORD => #MICROSOFT #WORD \
                \n- If an app is full, you need to wait until a slot opens up.\
                \n- We don’t create beta links and we do not control them.\
                \n- Repeatedly begging for apps will result in a ban.")

# Private bot
app.add_handler(CommandHandler(['start', 'help'], Start_Now, filters.ChatType.PRIVATE))
app.add_handler(CommandHandler('cc', Contact_M, filters.ChatType.PRIVATE))
app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE & filters.Regex(PATTERN_TESTFLIGHT), Handle_TestflightApps_Private))
app.add_handler(MessageHandler(filters.TEXT & (filters.Entity("url") | filters.Entity("text_link")) & filters.ChatType.PRIVATE, Handle_TestflightApps_Entities))

# Testflight_Reviews
CHOOSE_GROUP_TESTFLIGHT_REVIEWS = filters.ChatType.SUPERGROUP & filters.Chat(chat_id=int(GROUP_TESTFLIGHT_REVIEWS_ID))
app.add_handler(MessageHandler(filters.TEXT & (~ filters.COMMAND) & CHOOSE_GROUP_TESTFLIGHT_REVIEWS, Handle_Testflight_Reviews_Group))
# app.add_handler(CommandHandler(['check', 'c'], Handle_Testflight_Reviews_CheckApps, filters.ChatType.SUPERGROUP & (filters.Entity("url") | filters.Entity("text_link") | filters.Regex(r'[a-zA-Z0-9]{8}')) & filters.Chat(chat_id=int(GROUPS_TESTFLIGHT_CAMPINGAPPS_CHAT))))
app.add_handler(CommandHandler(['help', 'start'], Start_Testflight_Reviews, CHOOSE_GROUP_TESTFLIGHT_REVIEWS))
app.add_handler(CommandHandler(['search', 's'], Search_Testflight_Reviews, CHOOSE_GROUP_TESTFLIGHT_REVIEWS))


app.run_polling()