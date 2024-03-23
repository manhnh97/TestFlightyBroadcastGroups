import re
import os

LISTAPPSEARCH = "ListAppSearch_Ma"+".txt"
EXISTING_LINKS_FILE = "Testflight_List.txt"
PATTERN = r'https?://testflight\.apple\.com/join/[a-zA-Z0-9]{8}'

main_directory = os.path.dirname(os.path.abspath(__file__))
listappsearch_folder = os.path.join(main_directory, 'Result_Keywords_Search')

# Read existing links into a set
with open(EXISTING_LINKS_FILE, 'r', encoding='utf-8') as infile:
    existing_links = {line.strip() for line in infile}
    
list_newtestflight_apps = set()

# Iterate over files in the directory
for (dirpath, dirnames, filenames) in os.walk(listappsearch_folder):
    for filename in filenames:
        with open(os.path.join(dirpath, filename), 'r', encoding='utf-8') as outfile:
            for line in outfile:
                testflight_link_search = re.search(PATTERN, line, re.IGNORECASE)
                if testflight_link_search:
                    link = testflight_link_search.group(0)
                    if link not in existing_links:
                        list_newtestflight_apps.add(link)

# Write the unique links to the output file
with open(LISTAPPSEARCH, 'w', encoding='utf-8') as output_unique:
    for link in list_newtestflight_apps:
        output_unique.write(link + '\n')
