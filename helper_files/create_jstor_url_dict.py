import os
import csv
import json
import re
from helper_files.config import JSTOR_MAPPING, JSTOR_CSV, JSTOR_JSON


def create_jstor_url_dict(zeder_id: str):
    if zeder_id + '.csv' not in os.listdir(JSTOR_CSV):
        print('Keine JSTOR-Daten zu', zeder_id, 'gefunden.')
        return False
    else:
        total_nr = 0
        jstor_dict = {}
        languages_dict = {}
        with open (JSTOR_CSV + zeder_id + '.csv', 'r', encoding="utf-8") as jstor_csv_file:
            jstor_csv = csv.reader(jstor_csv_file, quotechar='"', delimiter=',')
            row_nr = 0
            for row in jstor_csv:
                languages_dict[row[0]] = row[15]
                row_nr += 1
                if row_nr < 2:
                    continue
                if 'http://www.' not in row[0]:
                    continue
                year = row[3]
                issue = row[10]
                volume = row[11]
                if volume:
                    volume = volume.split()[0]
                else:
                    volume = 'null'
                firstpage = row[16]
                lastpage = row[17]
                author = row[13]
                if not firstpage:
                    continue
                if firstpage == lastpage:
                    pages = firstpage
                else:
                    pages = firstpage + '-' + lastpage
                issue = re.sub(r'[^\d]', '/', issue)
                volume = re.sub(r'[^\d]', '/', volume)
                year = re.sub(r'[^\d]', '/', year)
                if not year:
                    continue
                if not volume:
                    continue
                if not issue:
                    issue = 'n'
                if year not in jstor_dict:
                    jstor_dict[year] = {}
                if volume not in jstor_dict[year]:
                    jstor_dict[year][volume] = {}
                if issue not in jstor_dict[year][volume]:
                    jstor_dict[year][volume][issue] = {}
                if pages not in jstor_dict[year][volume][issue]:
                    jstor_dict[year][volume][issue][pages] = {}
                if not author:
                    author = 'nn'
                else:
                    if len(author.split('; ')[0].rsplit(' ', 1)) == 2:
                        author_firstname, author_lastname = author.split('; ')[0].rsplit(' ', 1)
                        author = author_lastname + ', ' + author_firstname
                if author not in jstor_dict[year][volume][issue][pages]:
                    jstor_dict[year][volume][issue][pages][author] = [row[0]]
                    total_nr +=1
                else:
                    jstor_dict[year][volume][issue][pages][author] += [row[0]]
                    total_nr += 1
                    # jstor_dict[year][volume][issue][pages][author] = sorted(jstor_dict[year][volume][issue][pages][author])
                    # print(jstor_dict[year][volume][issue][pages][author])
        for year in jstor_dict:
            for volume in jstor_dict[year]:
                for issue in jstor_dict[year][volume]:
                    if issue == 'n':
                        veritable_Volumes = [found_volume for found_volume in jstor_dict[year] if 'n' not in jstor_dict[year][found_volume].keys()]
                        if len(veritable_Volumes) == 1:
                            veritable_volume = veritable_Volumes[0]
                            if volume in jstor_dict[year][veritable_volume]:
                                for pagination in jstor_dict[year][volume][issue]:
                                    if pagination not in jstor_dict[year][veritable_volume][volume]:
                                        jstor_dict[year][veritable_volume][volume][pagination] = jstor_dict[year][volume][issue][pagination]
                        else:
                            matching_Volumes = [vol for vol in veritable_Volumes if volume in jstor_dict[year][vol].keys()]
                            if len(matching_Volumes) == 1:
                                matching_volume = matching_Volumes[0]
                                for pagination in jstor_dict[year][volume][issue]:
                                    if pagination not in jstor_dict[year][matching_volume][volume]:
                                        jstor_dict[year][matching_volume][volume][pagination] = jstor_dict[year][volume][issue][pagination]
                                        print('added', year, matching_volume, volume, pagination)
        with open(JSTOR_JSON + zeder_id + '.json', 'w') as json_file:
            json.dump(jstor_dict, json_file)
        with open(JSTOR_MAPPING + zeder_id + '_languages.json', 'w') as json_languages_file:
            json.dump(languages_dict, json_languages_file)
        return True