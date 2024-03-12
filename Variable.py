
def Variable_Token_Bot():
    TOKEN_REMINDSLOW_ID = '6717549493:AAEzYjWPhL0IQFQ1rnKEvEJ89lf3sbvxRGc'
    BASE_URL_REDMINDSLOW = f"https://api.telegram.org/bot{TOKEN_REMINDSLOW_ID}/sendMessage"

    TOKEN_CAMPINGAPPS_ID = '6675183376:AAFIHE7oDIHTb1vtOsZMLunu9oEcD0DwPTM'
    BASE_URL_CAMPINGAPPS = f"https://api.telegram.org/bot{TOKEN_CAMPINGAPPS_ID}/sendMessage"

def Variable_Channels_Groups():
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

    CHOOSE_FILTER_PRIVATE = filters.ChatType.PRIVATE
    CHOOSE_FILTER_SUPERGROUP = filters.ChatType.SUPERGROUP

def Variable_Config():
    MAX_RETRIES = 3
    PATTERN_TESTFLIGHT = r'https?.*testflight\.apple\.com/join/[a-zA-Z0-9]{8}'
    XPATH_STATUS = '//*[@class="beta-status"]/span/text()'
    XPATH_TITLE = '/html/head/title/text()'
    TITLE_REGEX = r'Join the (.+) beta - TestFlight - Apple'
    FULL_TEXTS = ['This beta is full.',
                "This beta isn't accepting any new testers right now."]
    pattern_Available = r'To join the\s(.*?)\sbeta'
