"""
This is the main file of the project.
TODO: Add description
@Author: Harlock Official https://github.com/HarlockOfficial
"""
import datetime
import enum
import requests
from typing import List, Dict
from bs4 import BeautifulSoup
from lxml.html.clean import Cleaner


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


def sanitize(dirty_html):
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


def parse_menu(html) -> Dict[str, Dict[str, List[str]]]:
    """
    Parses the html of the daily menu and returns a dictionary with the menu
    """
    # TODO clean the code
    html_content = sanitize(html)
    soup = BeautifulSoup(html_content, 'html.parser')
    # time_table = soup.select("table#menu")[0]
    
    menu_table = soup.select('table#menu')[1]
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

    selector = 'tr:nth-child(n+ ' + str(int(first_turn['rowspan'])+1) + '):nth-child(-n+' + str(int(first_turn['rowspan']) + int(second_turn['rowspan'])+1) + ')'
    turn_rows = menu_table.select(selector)[1:]
    for row in turn_rows:
        out['Pranzo']['Secondo'].append(row.select('td:not([rowspan])')[0].text)

    for row in lunch_turn_rows:
        lst = list(filter(lambda x: x.text in ['Contorno'], row.select('td[rowspan]')))
        if len(lst)>0:
            third_turn = lst[0]

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

    selector = 'tr:nth-child(n+ ' + str(int(lunch_turn['rowspan']) + int(first_turn['rowspan']) + 2) + \
        '):nth-child(-n+ ' + str( int(lunch_turn['rowspan']) + int(first_turn['rowspan']) + int(second_turn['rowspan']) + 1) + ')'
    turn_rows = menu_table.select(selector)[1:]
    for row in turn_rows:
        out['Cena']['Secondo'].append(row.select('td:not([rowspan])')[0].text)

    for row in dinner_turn_rows:
        lst = list(filter(lambda x: x.text in ['Contorno'], row.select('td[rowspan]')))
        if len(lst)>0:
            third_turn = lst[0]

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
    

def main():
    """
    Main function of the project
    """
    for canteen in Canteen:
        url = build_daily_url(datetime.date.today(), canteen)
        headers = {'Accept-Encoding': 'identity'}
        request = requests.get(url, headers=headers, timeout=60)
        if request.status_code == 200:
            menu = parse_menu(request.content.decode('utf-8'))
            save_to_db(menu, canteen)
        else:
            print("Error: " + str(request.status_code) + " for " + canteen)

         
if __name__ == '__main__':
    main()
