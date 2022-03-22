# based on https://github.com/matthewcn56/bruin-fitness-pal/blob/main/server/menu_scraper.py
import requests
from bs4 import BeautifulSoup
import json
import re


DINING_HALL = 'DeNeve'


# https://www.fda.gov/food/new-nutrition-facts-label/daily-value-new-nutrition-and-supplement-facts-labels
daily_values = {
    'calcium': 1300,  # mg
    'vitamin-a': 900, # µg Retinol Activity Equivalent
    'vitamin-c': 90,  # mg  
    'iron': 18,       # mg
}

nutrient_key_names = {
    'total fat':          'fat',
        'saturated fat':  'saturated-fat',
        'trans fat':      'trans-fat',
    'cholesterol':        'cholesterol',
    'sodium':             'sodium',
    'total carbohydrate': 'carbohydrates',
        'sugars':         'sugars',
        'dietary fiber':  'fiber',
    'protein':            'proteins',
    'calcium':            'calcium',
    'vitamin a':          'vitamin-a',
    'vitamin c':          'vitamin-c',
    'iron':               'iron',

}


def get_recipe_info(recipe_link):
    html = requests.get(recipe_link)
    soup = BeautifulSoup(html.content, 'html.parser')
    results = soup.find(id="main-content")
    container = results.find("div", class_="recipecontainer")
    if (not container):
        return {}

    nutrients = {}
    info = {
        'nutrition': nutrients
    }

    container = container.find("div", class_="nfbox")
    # Calories
    calories = container.find("p", class_="nfcal")
    nutrients['calories'] = float(re.search(
        r'\d+(?:\.\d+)?', calories.text).group(0))

    serving_info = container.find('p', class_='nfserv').text
    match = re.search(
        r'Serving Size ([\.\d]+(?:/[\.\d]+)?)\s+([a-zA-Z][a-zA-Z\s]*)',
        serving_info)
    portion = match.group(1)
    if '/' in portion:
        portion = portion.split('/')
        portion = int(portion[0].strip())/int(portion[1].strip())
    else:
        portion = float(portion)
    info['portion'] = portion
    info['unit'] = match.group(2)

    for nfnutrient in container.find_all('p', class_='nfnutrient'):
        # nfnutrient.text example: Saturated Fat 3.4g 17%
        match = re.search(r'([a-zA-Z\s]+)(\d+(?:\.\d+)?)([^\d\s]?g)',
                          nfnutrient.text)
        key_name = nutrient_key_names[match.group(1).strip().lower()]
        nutrients[key_name] = match.group(2).strip()

    for nfvit in (container.find_all('span', class_='nfvitleft')
                  + container.find_all('span', class_='nfvitright')):
        vit_name = nfvit.find('span', class_='nfvitname').text
        vit_dv = nfvit.find('span', class_='nfvitpct').text.strip('% ')
        key_name = nutrient_key_names[vit_name.strip().lower()]
        nutrients[key_name] = float(vit_dv)/100*daily_values[key_name]

    return(info)


#print(get_recipe_info('https://menu.dining.ucla.edu/Recipes/141138/1!10'))






def get_dining_hall_menu(dining_hall, date):
    html = requests.get('https://menu.dining.ucla.edu/Menus/' + dining_hall + '/' + date)
    soup = BeautifulSoup(html.content, 'html.parser')
    results = soup.find(id='main-content')
    meal_time_blocks = results.find_all('div', class_='menu-block')

    menu_items = []
    for meal_time_block in meal_time_blocks:
        meal_time = meal_time_block.find('h3', class_='col-header').text

        menu_bar_list = meal_time_block.find('ul', class_='sect-list')
        # menu bars: the kitchen, capri, harvest, flex bar, etc.
        for menu_bar in menu_bar_list.find_all('li', class_='sect-item'):
            bar_name = menu_bar.text.strip().splitlines()[0].strip()
            item_list = menu_bar.find('ul', class_='item-list')
            for item in item_list.find_all('li', class_='menu-item'):
                recipe_link = item.find('a', class_='recipelink')
                recipe_url = recipe_link['href']
                recipe_name = recipe_link.text
                recipe_id = re.search('/Recipes/(\d+)/', recipe_url).group(1)
                menu_item = {
                    'name': recipe_name,
                    'brand': dining_hall + ' ' + bar_name + ' ' + meal_time,
                    'uniqueId': recipe_id,
                }
                menu_item.update(get_recipe_info(recipe_url))
                menu_items.append(menu_item)
                                        
    return menu_items

with open('ucla_menu_' + DINING_HALL + '.json', 'w', encoding='utf-8') as f:
    info = {
        'version': 1,
        'foodList': get_dining_hall_menu(DINING_HALL, ''),
    }
    f.write(json.dumps(info, indent=4, sort_keys=True))
