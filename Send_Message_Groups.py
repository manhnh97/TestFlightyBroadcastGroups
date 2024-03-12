import requests

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