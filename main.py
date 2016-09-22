import requests
import json
import os
import re
import math

config = None
with open('config.json') as config_file:
    config = json.load(config_file)

def get_champion_data():
    champion_data = None

    # If there is cached data, use cached data
    # TODO - Test if this file is older than a threshold, so we aren't using super stale data
    #           Maybe pull once a day, since champions don't come out more frequently than this
    if os.path.isfile(config['Cache_Champions']):
        with open(config['Cache_Champions']) as data_file:
            print("Loading champion data from cache...")
            champion_data = json.load(data_file)
            print("Loaded " + str(len(champion_data['data'])) + " champions")
    else:
        print("No champion data cached. Pulling from Riot Dev API...")
        r = requests.get(config['ChampionsAPI'] + "?api_key=" + os.environ['RIOT_DEV_API_KEY'])
        if r.status_code == 200:
            try:
                champion_data = r.json()
            except:
                print("Couldn't parse result into json object")
        else:
            print("Couldn't load champion data from champion API. Status Code: " + str(r.status_code))
    return champion_data

def get_champion_background_page_ids(champions):
    force_refresh_background = True
    for champId in champions:
        champion = champions[champId]
        if force_refresh_background or 'background' not in champion or champion['background'] == '':
            print("No background for " + champion['name'] + ". Looking it up...")
            r = requests.get(config['ChampionBackgroundAPI'] + champion['name'])
            if r.status_code == 200:
                result = r.json()['query']['export']['*']

                # do some manual lore parsing, yucky
                lore = ""
                #{{Champion bio*}}
                regex = re.search('(?s)({{Champion bio.*?\n\n)', result)
                if regex != None:
                    regex_match = (regex.group(0))
                    champion['meta'] = regex.group(0)

                    lore_index_start = result.find(regex_match)
                    if lore_index_start:
                        lore = result[lore_index_start + len(regex_match) + 1:]

                    lore_section_start = max(lore.find('== Lore =='), 0)
                    lore_end_index = lore.find('==', lore_section_start + len('== Lore =='))

                    lore_end_index_alt = lore.find('{{Section')
                    if lore_end_index_alt < lore_end_index or lore_end_index == 0:
                        lore_end_index = lore_end_index_alt

                    if lore_end_index:
                        lore = lore[0:lore_end_index]
                    else:
                        print "END INDEX NOT FOUND -- " + champion['name']
                        break

                    champion['background'] = lore
            else:
                print("Couldn't load champion data from champion API. Status Code: " + str(r.status_code))

def run():
    if 'RIOT_DEV_API_KEY' in os.environ:
        champion_data = get_champion_data()
        get_champion_background_page_ids(champion_data['data'])

        if champion_data != None:
            #create output dir if it doesn't exist
            if not os.path.exists(config['Cache']):
                os.makedirs(config['Cache'])
            with open(config['Cache_Champions'], 'w+') as champions_output_file:
                json.dump(champion_data, champions_output_file)
    else:
        print("Please make sure RIOT_DEV_API_KEY is specified within your environment variables.")

if __name__ == "__main__":
    run()
