import os
from json import load

def ValidateServiceAccountJSON():
    main_directory = os.path.dirname(os.path.abspath(__file__))
    service_account_file = os.path.join(main_directory, 'gspread', 'service_account_camping_general.json')

    # Load service account credentials from the JSON key file
    with open(service_account_file) as f:
        credentials = load(f)
    return credentials

def ValidateServiceAccountCampingAppsJSON():
    main_directory = os.path.dirname(os.path.abspath(__file__))
    service_account_file = os.path.join(main_directory, 'gspread', 'service_account_camping_apps.json')

    # Load service account credentials from the JSON key file
    with open(service_account_file) as f:
        credentials = load(f)
    return credentials