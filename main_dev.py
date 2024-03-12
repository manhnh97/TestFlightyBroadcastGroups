import re
import requests
import warnings
from lxml import html
from telegram import Update
from fake_useragent import UserAgent
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from Send_Message_Groups import Send_Message_Groups

TOKEN_REMINDSLOW_ID = '6717549493:AAEzYjWPhL0IQFQ1rnKEvEJ89lf3sbvxRGc'
BASE_URL_REDMINDSLOW = f"https://api.telegram.org/bot{TOKEN_REMINDSLOW_ID}/sendMessage"

TOKEN_CAMPINGAPPS_ID = '6675183376:AAFIHE7oDIHTb1vtOsZMLunu9oEcD0DwPTM'
BASE_URL_CAMPINGAPPS = f"https://api.telegram.org/bot{TOKEN_CAMPINGAPPS_ID}/sendMessage"

# Group TestflightCampingApps
GROUPS_TESTFLIGHT_M_DASHBOARD = '-1002099467699'
GROUPS_TESTFLIGHT_M_CHAT = '-1001883897634'
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

post_by_manhjisme = 863875519
CHOOSE_FILTER_PRIVATE = filters.ChatType.PRIVATE
CHOOSE_FILTER_SUPERGROUP = filters.ChatType.SUPERGROUP
Members_Bot = CHOOSE_FILTER_PRIVATE & filters.TEXT & filters.Chat(post_by_manhjisme)

MAX_RETRIES = 3
Testflight_Link_NoCode = 'https://testflight.apple.com/join/'
PATTERN_TESTFLIGHT_fulllink = r'https?.*testflight\.apple\.com/join/[a-zA-Z0-9]{8}'
PATTERN_TESTFLIGHT_code = '[a-zA-Z0-9]{8}'
XPATH_STATUS = '//*[@class="beta-status"]/span/text()'
XPATH_TITLE = '/html/head/title/text()'
TITLE_REGEX = r'Join the (.+) beta - TestFlight - Apple'
FULL_TEXTS = ['This beta is full.',
            "This beta isn't accepting any new testers right now."]
pattern_Available = r'To join the\s(.*?)\sbeta'

user_agent = UserAgent()
warnings.filterwarnings('ignore', category=RuntimeWarning)


def Send_Message_Groups(hashtag, url):
    
    parameter = {
        "chat_id": GROUPS_TESTFLIGHT_M_DASHBOARD,
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


def Send_Message_OnlyGroup(hashtag, url):
    parameter = {
    "chat_id": GROUPS_TESTFLIGHT_M_DASHBOARD,
    "text": f"{hashtag}\n\n{url}"
    }
    requests.get(BASE_URL_REDMINDSLOW, data=parameter)


async def Start_Now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    await context.bot.send_message(chat_id=update.effective_chat.id, \
            text="Hi people, \
                \nThis is my bot and my group @testflightcampingapps. \
                \nThe bot support me post testflight apps soon. \
                \nCan I help you? Contact me. Use /cc \"your message\", please. \
                \nHave a great day!")


async def Contact_M(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    if update.message:
        member_user = update.message.from_user.to_dict()
        await update.message.reply_text(f"Thank {member_user['first_name']} for your message. \
                                        \nYour message is important to (Us/Me) and (I/We) will respond as soon as possible.")
        
        message_contact_m = ' '.join(context.args) 
        parameter = {
            "message_thread_id": THREAD_CONTACT_M,
            "chat_id": GROUP_TESTFLIGHT_CONTACT_M,
            "text": f"chat_id: {member_user['id']}\nusername: {member_user['username']}\nmessage: {message_contact_m}"
        }
        requests.get(BASE_URL_REDMINDSLOW, data=parameter)


async def Handle_TestflightApps_Private(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        testflight_link = update.message.text
        if '#' in testflight_link:
            
            url = re.search(PATTERN_TESTFLIGHT_fulllink, testflight_link).group(0)
            Handle_Entity_Links(url)
            
        elif re.search(PATTERN_TESTFLIGHT_fulllink, testflight_link):
            
            urls = re.findall(PATTERN_TESTFLIGHT_fulllink, testflight_link)
            for url in urls:
                Handle_Entity_Links(url)


def Handle_Entity_Links(url):
    headers = {'User-Agent': user_agent.random}
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            page = html.fromstring(r.text)
            title = re.findall(
                    TITLE_REGEX,
                    page.xpath(XPATH_TITLE)[0])[0]
            textname_between_tothe_and_beta = title.strip()
            hashtags = re.findall(r"\b\w+\b", textname_between_tothe_and_beta)
            hashtag = " ".join(["#" + hashtag.upper() for hashtag in hashtags])
            return hashtag, url
            # Send_Message_Groups(hashtag, url)
    except (requests.RequestException, IndexError) as e:
        print("Error: Handle Entity Links:", e)


async def Handle_TestflightApps_Entities(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    for entity in update.message.entities:
        if entity.type == 'text_link' and r'testflight.apple.com' in entity.url:
            testflight_link = entity.url
            Handle_Entity_Links(testflight_link)


async def Handle_Testflight_Reviews_Group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    if update.message:
        user_info = update.message.from_user.to_dict()
        message = update.message
        if message and message.text and user_info['is_bot'] == False:
            member_user = user_info['first_name']
            if re.search(r'ree?dee?m|code', message.text):
                await update.message.reply_text(f"Hi {member_user}, \
                                                \nWe have not Redeem Code, use only Testflight Links. \
                                                \nPlease read: [Redeem Code](https://t.me/testflightR/70210)"
                                                , parse_mode=ParseMode.MARKDOWN)

async def Handle_Request_Testflight_Reviews_Group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    # print(update.message.text)
    if update.message.text:
        member_user = update.message.from_user.to_dict()
        message_request = context.args
        for message in message_request:
            urls = re.search(f"({PATTERN_TESTFLIGHT_fulllink}|{PATTERN_TESTFLIGHT_code})", message)
            if urls:
                url = urls.group(1)
                if len(url) == 8:
                    result = Handle_Entity_Links(Testflight_Link_NoCode+url)
                else:
                    result = Handle_Entity_Links(url)    
            reply_request_member = f"Your request"
        await update.message.reply_text(f"Thank {member_user['first_name']} for your message. \
                                        # \nYour message is important to (Us/Me) and (I/We) will respond as soon as possible.")
        
    
        # for url in urls:
        #     if len(url) == 8:
        #         print(url)
        # if update.message:
        #     message_contact_m = ' '.join(context.args)
        
        
    
    

async def Start_Testflight_Reviews(update: Update):
    
    if update.message:
        member_user = update.message.from_user.to_dict()['first_name']
        await update.message.reply_text(f"Hi {member_user}, \
                    \n- Use (/help or /start) for help. \
                    \n- How to search apps? [On PC](https://t.me/testflightR/71288) | [On Phone](https://t.me/testflightR/71287). \
                    \n- How to get Redeem Code? [Read more...](https://t.me/testflightR/70210). \
                    \n- Use (/request) to request testflight apps in queue. \
                    \n- Updating...", parse_mode=ParseMode.MARKDOWN)


app = ApplicationBuilder().token(TOKEN_CAMPINGAPPS_ID).build()
# Testflight_Bot_Private
app.add_handler(CommandHandler(['start', 'help'], Start_Now, CHOOSE_FILTER_PRIVATE))
app.add_handler(CommandHandler('cc', Contact_M, CHOOSE_FILTER_PRIVATE))

app.add_handler(MessageHandler(Members_Bot & filters.Regex(PATTERN_TESTFLIGHT_fulllink), Handle_TestflightApps_Private))
app.add_handler(MessageHandler(Members_Bot & (filters.Entity("url") | filters.Entity("text_link")), Handle_TestflightApps_Entities))

# Testflight_Reviews group
CHOOSE_GROUP_TESTFLIGHT_REVIEWS = CHOOSE_FILTER_SUPERGROUP & filters.Chat(chat_id=int(GROUPS_TESTFLIGHT_M_CHAT))
app.add_handler(MessageHandler(filters.TEXT & (~ filters.COMMAND) & CHOOSE_GROUP_TESTFLIGHT_REVIEWS, Handle_Testflight_Reviews_Group))
app.add_handler(CommandHandler(['help', 'start'], Start_Testflight_Reviews, CHOOSE_GROUP_TESTFLIGHT_REVIEWS))
app.add_handler(CommandHandler(['r','request'], Handle_Request_Testflight_Reviews_Group, CHOOSE_GROUP_TESTFLIGHT_REVIEWS))

app.run_polling()