"""
This is the main file of the project.
TODO: Add description
@Author: Harlock Official https://github.com/HarlockOfficial
"""
import datetime
import enum
import os
from typing import List, Dict

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from lxml.html.clean import Cleaner

import data_base as db


load_dotenv()


class Canteen(enum.Enum):
    """
    This enum contains all the canteens of the university
    """
    MATTEOTTI = "Matteotti"
    PETRARCA = "Petrarca"
    STRABONE = "Strabone"
    TENNA = "Tenna"
    PARADISO = "Paradiso"
    DAVACK = "Davack"
    GMA = "Gma"
    ACCORETTI = "Accoretti"
    BERTELLI = "Bertelli"
    DUCA = "Duca"
    TRIDENTE = "Tridente"

    def __str__(self):
        return self.value


def build_daily_url(date: datetime.date, canteen: Canteen):
    """
    Builds the url of the daily menu of the specified canteen for the specified day

    @param date: The date of which you want to get the menu
    @param canteen: The canteen of which you want to get the menu

    @return: The url of the daily menu of the specified canteen for the specified day
    """
    month = str(date.month) if date.month > 9 else "0" + str(date.month)
    day = str(date.day) if date.day > 9 else "0" + str(date.day)
    canteen = str(canteen)
    return "https://www.erdis.it/menu/Mensa_" + canteen + \
        "/Menu_Del_Giorno_" + str(date.year) + "_" + month + "_" + day + "_" + canteen + ".html"


def sanitise(dirty_html):
    """
    Sanitises the html of the daily menu
    """
    cleaner = Cleaner(page_structure=True,
                  meta=True,
                  embedded=True,
                  links=True,
                  style=True,
                  processing_instructions=True,
                  inline_style=True,
                  scripts=True,
                  javascript=True,
                  comments=True,
                  frames=True,
                  forms=True,
                  annoying_tags=True,
                  remove_unknown_tags=True,
                  safe_attrs_only=True,
                  safe_attrs=frozenset(['src','color', 'href', 'title', 'class', 'name', 'id', 'rowspan']),
                  remove_tags=()
                )

    return cleaner.clean_html(dirty_html)


def get_daily_menu(menu_table) -> Dict[str, Dict[str, List[str]]]:
    """
    Gets the daily menu from the html of the daily menu
    """
    full_turn_list = menu_table.select('tr>td')
    full_turn_list = list(filter(lambda x: x.text in ['Pranzo', 'Cena'], full_turn_list))

    out = {
        'Pranzo': {
            'Primo': [],
            'Secondo': [],
            'Contorno': [],
            'Frutta': []
        },
        'Cena': {
            'Primo': [],
            'Secondo': [],
            'Contorno': [],
            'Frutta': []
        }
    }

    lunch_turn = list(filter(lambda x: x.text in ['Pranzo'], full_turn_list))[0]
    selector = 'tr:nth-child(-n+ ' + lunch_turn['rowspan'] + ')'
    lunch_turn_rows = menu_table.select(selector)[1:]

    for row in lunch_turn_rows:
        lst = list(filter(lambda x: x.text in ['Primo'], row.select('td[rowspan]')))
        if len(lst)>0:
            first_turn = lst[0]
            break

    selector = 'tr:nth-child(-n+ ' + str(int(first_turn['rowspan'])+1) + ')'
    turn_rows = menu_table.select(selector)[1:]
    for row in turn_rows:
        out['Pranzo']['Primo'].append(row.select('td:not([rowspan])')[0].text)

    for row in lunch_turn_rows:
        lst = list(filter(lambda x: x.text in ['Secondo'], row.select('td[rowspan]')))
        if len(lst)>0:
            second_turn = lst[0]
            break

    selector = 'tr:nth-child(n+ ' + str(int(first_turn['rowspan'])+1) + '):nth-child(-n+' + str(int(first_turn['rowspan']) + int(second_turn['rowspan'])+1) + ')'
    turn_rows = menu_table.select(selector)[1:]
    for row in turn_rows:
        out['Pranzo']['Secondo'].append(row.select('td:not([rowspan])')[0].text)

    for row in lunch_turn_rows:
        lst = list(filter(lambda x: x.text in ['Contorno'], row.select('td[rowspan]')))
        if len(lst)>0:
            third_turn = lst[0]
            break

    selector = 'tr:nth-child(n+ ' + str(int(first_turn['rowspan']) + int(second_turn['rowspan']) + 1) + \
        '):nth-child(-n+' + str(int(first_turn['rowspan']) + int(second_turn['rowspan']) + int(third_turn['rowspan'])+1) + ')'
    turn_rows = menu_table.select(selector)[1:]
    for row in turn_rows:
        out['Pranzo']['Contorno'].append(row.select('td:not([rowspan])')[0].text)

    selector = 'tr:nth-child(n+ ' + str(int(first_turn['rowspan']) + int(second_turn['rowspan']) + int(third_turn['rowspan']) + 1) + \
        '):nth-child(-n+' + str(int(lunch_turn['rowspan'])+1) + ')'
    turn_rows = menu_table.select(selector)[1:]
    for row in turn_rows:
        out['Pranzo']['Frutta'].append(list(filter(lambda x: x.text != "Frutta", row.select('td:not([rowspan])')))[0].text)


    dinner_turn = list(filter(lambda x: x.text in ['Cena'], full_turn_list))[0]
    selector = 'tr:nth-child(n+ ' + str(int(lunch_turn['rowspan']) + 2) + '):nth-child(-n+' + str(int(lunch_turn['rowspan']) + int(dinner_turn['rowspan']) + 1) + ')'
    dinner_turn_rows = menu_table.select(selector)
    for row in dinner_turn_rows:
        lst = list(filter(lambda x: x.text in ['Primo'], row.select('td[rowspan]')))
        if len(lst)>0:
            first_turn = lst[0]
            break

    selector = 'tr:nth-child(n+ ' + str(int(lunch_turn['rowspan']) + 2) + \
        '):nth-child(-n+ ' + str(int(lunch_turn['rowspan']) + int(first_turn['rowspan'])+1) + ')'
    turn_rows = menu_table.select(selector)[1:]
    for row in turn_rows:
        out['Cena']['Primo'].append(row.select('td:not([rowspan])')[0].text)

    for row in dinner_turn_rows:
        lst = list(filter(lambda x: x.text in ['Secondo'], row.select('td[rowspan]')))
        if len(lst)>0:
            second_turn = lst[0]
            break

    selector = 'tr:nth-child(n+ ' + str(int(lunch_turn['rowspan']) + int(first_turn['rowspan']) + 2) + \
        '):nth-child(-n+ ' + str( int(lunch_turn['rowspan']) + int(first_turn['rowspan']) + int(second_turn['rowspan']) + 1) + ')'
    turn_rows = menu_table.select(selector)[1:]
    for row in turn_rows:
        out['Cena']['Secondo'].append(row.select('td:not([rowspan])')[0].text)

    for row in dinner_turn_rows:
        lst = list(filter(lambda x: x.text in ['Contorno'], row.select('td[rowspan]')))
        if len(lst)>0:
            third_turn = lst[0]
            break

    selector = 'tr:nth-child(n+ ' + str(int(lunch_turn['rowspan'])+int(first_turn['rowspan']) + int(second_turn['rowspan']) + 2) + \
        '):nth-child(-n+ ' + str(int(lunch_turn['rowspan']) + int(first_turn['rowspan']) + int(second_turn['rowspan'])+ int(third_turn['rowspan']) + 1) + ')'
    turn_rows = menu_table.select(selector)[1:]
    for row in turn_rows:
        out['Cena']['Contorno'].append(row.select('td:not([rowspan])')[0].text)

    selector = 'tr:nth-child(n+ ' + str(int(lunch_turn['rowspan']) + int(first_turn['rowspan']) + int(second_turn['rowspan']) + int(third_turn['rowspan']) + 2) + \
        '):nth-child(-n+' + str(int(lunch_turn['rowspan']) + int(dinner_turn['rowspan'])+1) + ')'
    turn_rows = menu_table.select(selector)

    for row in turn_rows:
        out['Cena']['Frutta'].append(list(filter(lambda x: x.text != "Frutta", row.select('td:not([rowspan])')))[0].text)

    return out


def get_daily_time(time_table) -> Dict[str, str]:
    """
    Gets the time of the daily menu
    """
    out = {
        'Pranzo': {
            'IsOpen': False,
            'OpenTime': '12:00',
            'CloseTime': '14:00'
        },
        'Cena': {
            'IsOpen': False,
            'OpenTime': '19:00',
            'CloseTime': '21:00'
        }
    }
    time_table = time_table.select('tr')[1:]
    for index, row in enumerate(time_table):
        data = row.select('td')
        out[data[0].text]['OpenTime'] = data[1].text
        out[data[0].text]['CloseTime'] = data[2].text
        if len(data)>3:
            out[data[0].text]['IsOpen'] = data[3].text == 'NO'
            if hasattr(data[3], 'rowspan') and int(data[3]['rowspan']) == 2 and index<len(time_table)-1:
                tmp_data = time_table[index+1].select('td')
                out[tmp_data[0].text]['IsOpen'] = data[3].text == 'NO'
    return out


def parse_menu(html) -> Dict[str, Dict[str, List[str]]]:
    """
    Parses the html of the daily menu and returns a dictionary with the menu
    """
    html_content = sanitise(html)
    soup = BeautifulSoup(html_content, 'html.parser')
    tables = soup.select('table#menu')
    if len(tables) < 2:
        return None, None
    time_table = tables[0]
    menu_table = tables[1]

    daily_time = get_daily_time(time_table)
    daily_menu = get_daily_menu(menu_table)
    return daily_menu, daily_time


def save_menu_to_db(menu: Dict[str, Dict[str, List[str]]], time: Dict[str, str], canteen: Canteen):
    """
    Saves the menu and timetable to the database
    """
    mongo_client = db.open_connection()
    data_base = db.get_data_base(mongo_client=mongo_client)
    collection = data_base[os.getenv('DB_MENU_COLLECTION')]
    collection.find_one_and_delete({'canteen': canteen.value.lower()})
    collection.insert_one({'canteen': canteen.value.lower(), 'menu': menu, 'time': time, 'date': datetime.date.today().isoformat()})
    db.close_connection(mongo_client)


def init_menu():
    """
    Module main function, does all the work
    """
    for canteen in Canteen:
        url = build_daily_url(datetime.date.today(), canteen)
        headers = {'Accept-Encoding': 'identity'}
        request = requests.get(url, headers=headers, timeout=60)
        if request.status_code == 200:
            menu, time = parse_menu(request.content.decode('utf-8'))
            if menu is not None and time is not None:
                # save_menu_to_db(menu, time, canteen)
                pass
            else:
                time = {
                    'Pranzo':{
                        'IsOpen': False,
                    },
                    'Cena':{
                        'IsOpen': False,
                    }
                }
                # save_menu_to_db(menu, time, canteen)

        else:
            print("Error: " + str(request.status_code) + " for " + canteen)
