import os
import re

def extract_unique_links(file_path):
    links = set()
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            links.add(line.strip())
    return links

def find_result_json_files(root_folder):
    result_files = []
    for foldername, subfolders, filenames in os.walk(root_folder):
        for filename in filenames:
            if filename == 'result.json':
                result_files.append(os.path.join(foldername, filename))
    return result_files

ROOT_FOLDER = r'D:\Downloads\Telegram Desktop'

OUTPUT_FILE = "telegram_output_testflight_list.txt"
EXISTING_LINKS_FILE = "Testflight_List.txt"

PATTERN = r'https?://testflight\.apple\.com/join/[a-zA-Z0-9]{8}+'

if not os.path.exists(EXISTING_LINKS_FILE):
    with open(EXISTING_LINKS_FILE, 'w'):
        pass

result_json_files = find_result_json_files(ROOT_FOLDER)

unique_links = set()

for file in result_json_files:
    json_path = file.replace('\\', '\\\\')
    with open(json_path, 'r', encoding='utf-8') as file:
        file_content = file.read()

        testflight_links = re.findall(PATTERN, file_content)

        unique_links.update(testflight_links)

with open(OUTPUT_FILE, 'a+') as output:
    for link in unique_links:
        output.write('\n' + link)

new_links = extract_unique_links(OUTPUT_FILE)
unique_lines = set()
with open(OUTPUT_FILE, 'r', encoding='utf-8') as infile, open(EXISTING_LINKS_FILE, 'w', encoding='utf-8') as outfile:
    for line in infile:
        unique_lines.add(line.strip())

    for line in unique_lines:
        outfile.write('\n' + line)
