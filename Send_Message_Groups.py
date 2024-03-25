import re
import asyncio
import aiohttp
import requests
import warnings
from lxml import html
from telegram import Update
from fake_useragent import UserAgent
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN_REMINDSLOW_ID = '6717549493:AAEzYjWPhL0IQFQ1rnKEvEJ89lf3sbvxRGc'
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1210607511024177202/MqV1JFSHYhawyL6TIbaAMiiDRlQCueE4Xt-NkRBD0cSaGDNePaS1aEb8LjhMIukwg2xx"
BASE_URL_REDMINDSLOW = f"https://api.telegram.org/bot{TOKEN_REMINDSLOW_ID}/sendMessage"

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
# Testflight_Mesasge
THREAD_CONTACT_M = '11'
GROUP_TESTFLIGHT_CONTACT_M = '-1002031575789'

# Testflight_Reviews
GROUP_TESTFLIGHT_REVIEWS_ID = '-1001170452834'
GROUPS_TESTFLIGHT_X_ID = '-1001363951322'

post_by_personal = [863875519, 6325914189, 6775616554, 6168275376]
CHOOSE_FILTER_PRIVATE = filters.ChatType.PRIVATE
CHOOSE_FILTER_SUPERGROUP = filters.ChatType.SUPERGROUP
Members_Bot = CHOOSE_FILTER_PRIVATE & filters.TEXT & filters.Chat(post_by_personal)

MAX_RETRIES = 3
PATTERN_TESTFLIGHT_fulllink = r'https?.*testflight\.apple\.com/join/[a-zA-Z0-9]{8}'
XPATH_STATUS = '//*[@class="beta-status"]/span/text()'
XPATH_TITLE = '/html/head/title/text()'
TITLE_REGEX = r'Join the (.+) beta - TestFlight - Apple'

user_agent = UserAgent()
warnings.filterwarnings('ignore', category=RuntimeWarning)


async def Send_Message_Telegram(session, chat_id, text, message_thread_id=None):
    parameter = {
        "chat_id": chat_id,
        "text": text,
        "message_thread_id": message_thread_id
    }
    if parameter["chat_id"] is GROUP_TESTFLIGHT_NGHIEN_ID:
        parameter["message_thread_id"] = THREAD_NGHIEN_ID
    
    if parameter["chat_id"] is GROUP_TESTFLIGHT_KGM_ID:
        parameter["message_thread_id"] = THREAD_KGM
    
    async with session.post(BASE_URL_REDMINDSLOW, data=parameter) as response:
        pass

async def Send_Message_Discord(session, text):
    parameter = {"content": text}
    async with session.post(DISCORD_WEBHOOK_URL, json=parameter):
        pass

async def Send_Message_Groups(hashtag, url):
    async with aiohttp.ClientSession() as session:
        tasks = [
            Send_Message_Telegram(session, GROUPS_TESTFLIGHT_M_DASHBOARD, f"{hashtag}\n\n{url}"),
            Send_Message_Telegram(session, GROUP_TESTFLIGHT_NGHIEN_ID, f"{hashtag}\n\n{url}"),
            Send_Message_Telegram(session, GROUP_TESTFLIGHT_1110_ID, f"{hashtag}\n\n{url}"),
            Send_Message_Telegram(session, GROUPS_TESTFLIGHT_X_ID, f"{hashtag}\n\n{url}"),
            Send_Message_Telegram(session, GROUP_TESTFLIGHT_KGM_ID, f"{hashtag}\n\n{url}"),
            Send_Message_Discord(session, f"{hashtag}\n\n{url}"),
        ]
        await asyncio.gather(*tasks)


async def Send_Message_OnlyGroup(hashtag, url):
    tasks = [
        Send_Message_Telegram(GROUPS_TESTFLIGHT_M_DASHBOARD, f"{hashtag}\n\n{url}"),
    ]
    await asyncio.gather(*tasks)

async def Start_Now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    await context.bot.send_message(chat_id=update.effective_chat.id, \
            text="Hi people, \
                \nWelcome to my group @testflightcampingapps. \
                \nThe bot support me post testflight apps soon. \
                \nCan I help you? Contact me. Use /cc \"your message\", please. \
                \nHave a great day!")


async def Contact_M(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    if update.message:
        member_user = update.message.from_user.to_dict()
        await update.message.reply_text(f"Thanks {member_user['first_name']}, \
                                        \nYour message is important to me and I will respond as soon as possible.")
        
        message_contact_m = ' '.join(context.args) 
        if 'username' not in member_user:
            member_user['username'] = None
            
        parameter = {
            "message_thread_id": THREAD_CONTACT_M,
            "chat_id": GROUP_TESTFLIGHT_CONTACT_M,
            "text": f"chat_id: {member_user['id']}\nusername: {member_user['username']}\nmessage: {message_contact_m}"
        }
        requests.post(BASE_URL_REDMINDSLOW, data=parameter)


async def Handle_Entity_Links(url):
    
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
            await Send_Message_Groups(hashtag, url)
            
    except (requests.RequestException, IndexError) as e:
        print("Error: Handle Entity Links:", e)


async def Handle_TestflightApps_Private(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    if update.message and update.message.text:
        testflight_link = update.message.text
        if '#' in testflight_link and len(testflight_link) > 0:
            
            url = re.search(PATTERN_TESTFLIGHT_fulllink, testflight_link).group(0)
            await Handle_Entity_Links(url)
            
        elif re.search(PATTERN_TESTFLIGHT_fulllink, testflight_link) and len(testflight_link) > 0:
            
            urls = re.findall(PATTERN_TESTFLIGHT_fulllink, testflight_link)
            for url in urls:
                await Handle_Entity_Links(url)


async def Handle_TestflightApps_Entities(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    for entity in update.message.entities:
        if re.search(PATTERN_TESTFLIGHT_fulllink, entity.url) and len(entity.url) > 0:
            testflight_link = entity.url
            await Handle_Entity_Links(testflight_link)

async def Start_Testflight_Mchat_Group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    if update.message:
        member_user = update.message.from_user.to_dict()['first_name']
        await update.message.reply_text(f"Hi {member_user}, \
                    \n- Use (/help or /start) for help. \
                    \n- What is TestFlight? [From NghienMac with love](https://nghienmac.nghienplus.net/1001-cau-hoi-ve-testflight). \
                    \n1. How to search apps? [On PC](https://t.me/testflightm/1015) | [On Phone](https://t.me/testflightR/71287). \
                    \n2. How to.post Redeem Code? [Read more...](https://t.me/testflightR/70210). \
                    \n- Updating...", parse_mode=ParseMode.MARKDOWN)

async def Handle_Testflight_Mchat_Group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    user_info = update.message.from_user.to_dict()
    if update.message:
        message = update.message
        if message and message.text and (user_info['is_bot'] == False and user_info['first_name'] != 'Telegram'):
            member_user = user_info['first_name']
            if re.search(r'ree?dee?m|code', (message.text).lower()):
                await update.message.reply_text(f"Hi {member_user}, \
                                                \nWe have not Redeem Code, use only Testflight Links." \
                                                    , parse_mode=ParseMode.MARKDOWN)
                                                # \nPlease read: [Redeem Code](https://t.me/testflightR/70210)"


async def Start_Testflight_Reviews_Group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    if update.message:
        member_user = update.message.from_user.to_dict()['first_name']
        await update.message.reply_text(f"Hi {member_user}, \
                    \n- Use (/help or /start) for help. \
                    \n- What is TestFlight? [From NghienMac with love](https://nghienmac.nghienplus.net/1001-cau-hoi-ve-testflight). \
                    \n1. How to search apps? [On PC](https://t.me/testflightR/71288) | [On Phone](https://t.me/testflightR/71287). \
                    \n2. How to.post Redeem Code? [Read more...](https://t.me/testflightR/70210). \
                    \n- Updating...", parse_mode=ParseMode.MARKDOWN)


async def Handle_Testflight_Reviews_Group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    user_info = update.message.from_user.to_dict()
    if update.message:
        message = update.message
        if message and message.text and (user_info['is_bot'] == False and user_info['first_name'] != 'Telegram'):
            member_user = user_info['first_name']
            if re.search(r'ree?dee?m|code', (message.text).lower()):
                await update.message.reply_text(f"Hi {member_user}, \
                                                \nWe have not Redeem Code, use only Testflight Links. \
                                                \nPlease read: [Redeem Code](https://t.me/testflightR/70210" \
                                                    , parse_mode=ParseMode.MARKDOWN)


async def Report_Testflight_Groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    user_info = update.message.from_user.to_dict()
    if update.message and (user_info['is_bot'] == False and user_info['first_name'] != 'Telegram'):
        await update.message.reply_text(f"Thanks {user_info['first_name']}, \
                                        \n\[URGENT] [manhjisme](tg://user?id=863875519)", parse_mode=ParseMode.MARKDOWN)

app = ApplicationBuilder().token(TOKEN_REMINDSLOW_ID).build()
# Testflight_Bot_Private
app.add_handler(CommandHandler(['start', 'help'], Start_Now, CHOOSE_FILTER_PRIVATE))
app.add_handler(CommandHandler('cc', Contact_M, CHOOSE_FILTER_PRIVATE))

app.add_handler(MessageHandler(Members_Bot & filters.Regex(PATTERN_TESTFLIGHT_fulllink), Handle_TestflightApps_Private))
app.add_handler(MessageHandler(Members_Bot & (filters.Entity("url") | filters.Entity("text_link")), Handle_TestflightApps_Entities))

# TestflightM Chat group
CHOOSE_GROUP_TESTFLIGHT_M = CHOOSE_FILTER_SUPERGROUP & filters.Chat(chat_id=int(GROUPS_TESTFLIGHT_M_CHAT))
app.add_handler(MessageHandler(filters.TEXT & (~ filters.COMMAND) & CHOOSE_GROUP_TESTFLIGHT_M, Handle_Testflight_Mchat_Group))
app.add_handler(CommandHandler(['help', 'start'], Start_Testflight_Mchat_Group, CHOOSE_GROUP_TESTFLIGHT_M))

# Testflight Reviews group
CHOOSE_GROUP_TESTFLIGHT_REVIEWS = CHOOSE_FILTER_SUPERGROUP & filters.Chat(chat_id=int(GROUP_TESTFLIGHT_REVIEWS_ID))
app.add_handler(MessageHandler(filters.TEXT & (~ filters.COMMAND) & CHOOSE_GROUP_TESTFLIGHT_REVIEWS, Handle_Testflight_Reviews_Group))
app.add_handler(CommandHandler(['help', 'start'], Start_Testflight_Reviews_Group, CHOOSE_GROUP_TESTFLIGHT_REVIEWS))

# Testflight MyAdmin Groups
app.add_handler(CommandHandler('report', Report_Testflight_Groups, CHOOSE_FILTER_SUPERGROUP))

app.run_polling()