#
# A simple web crawler to
# 1. retrieve IIDX game score data registered on IIDX Score Table (IST) at https://score.iidx.app/
# 2. prepare the retrieved data as CSV file
#
# Before running, update the definitions in TODO section below
#

import requests
from bs4 import BeautifulSoup
import re
import csv


# TODO: define game card ID and output CSV filename
card_id = "xxxx-xxxx"
filename = "ist_score_history.csv"


# START variable initializations
seed_url = "https://score.iidx.app/users/" + card_id + "/score_activities?q%5Bcreated_at_gteq%5D=9999-12-31"

# mapping of game version names and numbers
dict_version = {
    "1st&substream": "1",
    "2nd style": "2",
    "3rd style": "3",
    "4th style": "4",
    "5th style": "5",
    "6th style": "6",
    "7th style": "7",
    "8th style": "8",
    "9th style": "9",
    "10th style": "10",
    "IIDX RED": "11",
    "HAPPY SKY": "12",
    "DistorteD": "13",
    "GOLD": "14",
    "DJ TROOPERS": "15",
    "EMPRESS": "16",
    "SIRIUS": "17",
    "Resort Anthem": "18",
    "Lincle": "19",
    "tricoro": "20",
    "SPADA": "21",
    "PENDUAL": "22",
    "copula": "23",
    "SINOBUZ": "24",
    "CANNON BALLERS": "25",
    "Rootage": "26",
    "HEROIC VERSE": "27",
    "BISTROVER":"28",
    "CastHour":"29",
    "RESIDENT":"30",
    "?":"?"
}

# mapping of chart difficulties and colour representations on IST
dict_difficulty = {
    "#FF33CC": "L",
    "#FCF3CF": "H",
    "#FADBD8": "A",
    "#D6EAF8": "N"
}

# mapping of gauge types and colour representations on IST
dict_clear_type = {
    "#9595ff": "ASSIST",
    "#98fb98": "EASY",
    "#afeeee": "CLEAR",
    "#ff6347": "HARD",
    "#ffd900": "EXH",
    "#ff8c00": "FC",
    "#c0c0c0": "FAILED",
    "#ffffff": "NO PLAY"
}

# set http headers for requests
http_headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '3600',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36'
    }
# END variable initializations

# START get_next_URL
def get_next_URL(url):
    next_url = ""
    next_date = ""
    
    req = requests.get(url)
    soup = BeautifulSoup(req.content, 'html.parser')
    
    nav_pagination = soup.select_one("body > section.section > div.container > nav.pagination > ul.pagination-list")
    
    # if pagination exists
    if nav_pagination:
        a_next_nav = nav_pagination.find_all("a", rel="next")
        # if next page exists in pagination
        if a_next_nav:
            next_url = "https://score.iidx.app" + a_next_nav[0]['href']
            next_date = re.findall("\d+-\d+-\d+$", next_url)[0]
    
    # proceed to next play date if pagination does not exist
    if next_url == "":
        nav_breadcrumb = soup.select_one("body > section.section > div.container > nav.breadcrumb")
        next_url = "https://score.iidx.app" + nav_breadcrumb.find_all(href=re.compile("score_activities"))[0]['href']
        next_date = re.findall("\d+-\d+-\d+$", next_url)[0]
        current_date = re.findall("\d+-\d+-\d+$", url)[0]
        # stops if reaches first play date
        if next_date > current_date: next_url = ""
    
    return next_url
# END get_next_URL

# START write_score_record_to_csv_from_URL
def write_score_record_to_csv_from_URL(url):
    req = requests.get(url, http_headers)
    soup = BeautifulSoup(req.content, 'html.parser')
    
    op_play_date = soup.select_one("body > section.section > div.container > nav.breadcrumb > ul > li.is-active").string
    
    table = soup.select_one("body > section.section > div.container > table.is-striped.is-hoverable.is-fullwidth")
    rows = table.select("tbody > tr")
    
    # for each row containing a score record
    for r in rows:
        cols = r.select("td")
        # retrieve fields to be written to csv
        op_name = cols[0].select_one("a").string
        op_difficulty = dict_difficulty[cols[0]["bgcolor"]]
        op_clear_type = dict_clear_type[cols[2]["bgcolor"]]
        op_version = dict_version[cols[3].string]
        op_level = cols[4].string
        op_rank = re.search("[A-Z]+$|$", cols[5].string).group()
        op_score = re.search("^\d+|$", cols[7].string).group()
        op_miss_count = re.search("^\d+|$", cols[8].string).group()
        
        if op_score == "0": continue
        
        # append score record to csv
        op_song_fields = [op_version, op_name, "", "",
                          op_difficulty, op_level, "",
                          "", op_play_date, op_clear_type, op_rank, op_score, op_miss_count,
                          url]
        write_to_csv(filename, "append", op_song_fields)
        
        # for debug use
        #print(op_version, op_name,
        #      op_difficulty, op_level,
        #      op_play_date, op_clear_type, op_rank, op_score, op_miss_count, sep='|')
# END write_score_record_to_csv_from_URL

# START write_to_csv
def write_to_csv(filename, write_mode, list_of_fields):
    permission_flag = {"new_file": "w", "append": "a+"}
    with open(filename, permission_flag[write_mode], newline='', encoding='utf-8') as write_obj:
        write_obj.write('\ufeff')
        writer = csv.writer(write_obj)
        writer.writerow(list_of_fields)
# END write_to_csv

# START main
def main():
    print("--- JOB START ---")
    
    csv_header = ["VERSION", "NAME", "GENRE", "ARTIST",
                  "DIFFICULTY", "LEVEL", "NOTES",
                  "PLAY VERSION", "PLAY DATE", "CLEAR TYPE", "RANK", "EX SCORE", "MISS COUNT",
                  "IST URL"]
    write_to_csv(filename, "new_file", csv_header)
    
    current_url = seed_url
    while current_url:
        # display progress on screen
        print(current_url)
        write_score_record_to_csv_from_URL(current_url)
        current_url = get_next_URL(current_url)
    
    print("--- JOB END ---")
# END main
    
if __name__ == '__main__':
    main()
