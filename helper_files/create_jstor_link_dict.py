import re
import json
import sys
import os
from helper_files.create_jstor_url_dict import create_jstor_url_dict
from helper_files.create_publisher_url_dict import get_url_dict
from helper_files.convert_roman_numbers import from_roman
from helper_files.config import JSTOR_JSON, PUBLISHER_JSON, JSTOR_MAPPING


# Funktion, um die Inhalte zweier Issue-Dictionaries zu matchen.
def match_issue_dicts(jstor_mapping_dict, publisher_issue_dict, jstor_issue_dict, total_nr, total_matches):
    # print(total_matches)
    publisher_issue_dict = {re.sub(r'[^\divxlIVXL-]', '', pagination): publisher_issue_dict[pagination] for pagination in publisher_issue_dict}
    for pagination in publisher_issue_dict:
        if pagination == "ll":
            total_nr += 1
            continue
        pagination = re.sub(r'[^\divxlIVXL-]', '', pagination)
        if pagination in jstor_issue_dict:
            # prüfen, ob nur ein Artikel mit dieser Seitennummerierung erschienen ist
            if len(jstor_issue_dict[pagination]) == 1:
                for author in jstor_issue_dict[pagination]:
                    total_nr += len(jstor_issue_dict[pagination][author])
                    publisher_author = \
                        list(publisher_issue_dict[pagination].keys())[0]
                    if len(jstor_issue_dict[pagination][author]) == 1:
                        jstor_mapping_dict[publisher_issue_dict[pagination][publisher_author][0]] = \
                        jstor_issue_dict[pagination][author][0]
                        total_matches += 1
                    else:
                        author_publication_list_jstor = sorted(jstor_issue_dict[pagination][author])
                        author_publication_list_publisher = sorted(
                            publisher_issue_dict[pagination][publisher_author])
                        for p in range(len(author_publication_list_publisher)):
                            if p < len(author_publication_list_jstor):
                                jstor_mapping_dict[author_publication_list_publisher[p]] = \
                                author_publication_list_jstor[p]
                                total_matches += 1
            # mehrere auf der selben Seite erschienene Artikel anhand der Autoren zuordnen
            else:
                for jstor_author in jstor_issue_dict[pagination]:
                    total_nr += len(jstor_issue_dict[pagination][jstor_author])
                    author_publication_list_jstor = sorted(
                        list(set(jstor_issue_dict[pagination][jstor_author])))
                    for publisher_author in publisher_issue_dict[pagination]:
                        author_publication_list_publisher = sorted(
                            list(set(publisher_issue_dict[pagination][publisher_author])))
                        publisher_names_list = [name.lower() for name in re.findall(r'\w+', publisher_author)]
                        names_list = [name.lower() for name in re.findall(r'\w+', jstor_author)]
                        # prüfen, ob die Anzahl der Artikel mit der selben Seitenzahl übereinstimmt
                        if len([name for name in names_list if name in publisher_names_list]) >= 2:
                            if len(author_publication_list_jstor) != len(author_publication_list_publisher):
                                '''print('_______________________________')
                                print('different list length')
                                print(author_publication_list_publisher, author_publication_list_jstor)
                                print('_______________________________')'''
                                # Probleme bei:
                                # Review by: John Habgood
                                # http://www.jstor.org/stable/23959547
                                # Review by: John S. Habgood
                                # https://www.jstor.org/stable/23959548
                                # solche Autoren evtl. zusammenlegen.
                            else:
                                for p in range(len(author_publication_list_publisher)):
                                    if p < len(author_publication_list_jstor):
                                        jstor_mapping_dict[author_publication_list_publisher[p]] = \
                                            author_publication_list_jstor[p]
                                        total_matches += 1
        else:
            total_nr += 1
            pagination_found = False
            # unerwünschte Zeichen in der Seitennummerierung entfernen
            old_dict = jstor_issue_dict
            jstor_issue_dict = {re.sub(r'[^\divxlIVXL-]', '', p): jstor_issue_dict[p] for p in jstor_issue_dict}
            pop_keys = {}
            for p in jstor_issue_dict:
                if re.findall(r'(?i)(?=[MDCLXVI])M*(?:C[MD]|D?C*)(?:X[CL]|L?X*)(?:I[XV]|V?I*)-\d+', p):
                    new_pagination = []
                    int_page = re.findall(r'-(\d+)', p)[0]
                    for pag in re.findall(r'(?i)(?=[MDCLXVI])M*(?:C[MD]|D?C*)(?:X[CL]|L?X*)(?:I[XV]|V?I*)', p):
                        new_pagination.append(str(from_roman(pag)))
                    new_pagination.append(int_page)
                    new_pagination = '-'.join(new_pagination)
                    print('converted', new_pagination, 'from roman number', p)
                    pop_keys[p] = new_pagination
                elif re.findall(r'(?i)(?=[MDCLXVI])M*(?:C[MD]|D?C*)(?:X[CL]|L?X*)(?:I[XV]|V?I*)', p):
                    new_pagination = []
                    for pag in re.findall(r'(?i)(?=[MDCLXVI])M*(?:C[MD]|D?C*)(?:X[CL]|L?X*)(?:I[XV]|V?I*)', p):
                        new_pagination.append(str(from_roman(pag)))
                    new_pagination = '-'.join(new_pagination)
                    print('converted', new_pagination, 'from roman number', p)
                    pop_keys[p] = new_pagination
            for pop_key in pop_keys:
                jstor_issue_dict[pop_keys[pop_key]] = jstor_issue_dict[pop_key]
                jstor_issue_dict.pop(pop_key)
            for p in jstor_issue_dict:
                try:
                    # Berechnung der Differenz der letzten angegebenen Seitenzahlen
                    if '-' in p and '-' in pagination:
                        difference = abs(int(p.split('-')[1]) - int(pagination.split('-')[1]))
                    elif '-' in pagination:
                        difference = abs(int(p) - int(pagination.split('-')[1]))
                    elif '-' in p:
                            difference = abs(int(p.split('-')[1]) - int(pagination))
                    else:
                        difference = abs(int(p) - int(pagination))
                    if difference <= 5:
                        p = p.replace('*', '')
                        if len(jstor_issue_dict[p]) == 1:
                            for author in jstor_issue_dict[p]:
                                total_nr += len(
                                    jstor_issue_dict[p][author])
                                publisher_author = \
                                    list(
                                        publisher_issue_dict[pagination].keys())[
                                        0]
                                if len(jstor_issue_dict[p][
                                           author]) == 1:
                                    jstor_mapping_dict[
                                        publisher_issue_dict[pagination][
                                            publisher_author][0]] = \
                                        jstor_issue_dict[p][author][0]
                                    total_matches += 1
                                    pagination_found = True
                                else:
                                    author_publication_list_jstor = sorted(
                                        jstor_issue_dict[p][author])
                                    author_publication_list_publisher = sorted(
                                        publisher_issue_dict[pagination][
                                            publisher_author])
                                    for ap in range(len(author_publication_list_publisher)):
                                        if ap < len(author_publication_list_jstor):
                                            jstor_mapping_dict[
                                                author_publication_list_publisher[ap]] = \
                                                author_publication_list_jstor[ap]
                                            pagination_found = True
                                            total_matches += 1
                        else:
                            for jstor_author in jstor_issue_dict[p]:
                                total_nr += len(
                                    jstor_issue_dict[p][jstor_author])
                                author_publication_list_jstor = sorted(list(set(
                                    jstor_issue_dict[p][jstor_author])))
                                for publisher_author in publisher_issue_dict[
                                    pagination]:
                                    author_publication_list_publisher = sorted(
                                        list(set(
                                            publisher_issue_dict[pagination][
                                                publisher_author])))
                                    publisher_names_list = [name.lower() for name in
                                                            re.findall(r'\w+',
                                                                       publisher_author)]
                                    names_list = [name.lower() for name in
                                                  re.findall(r'\w+', jstor_author)]
                                    if len([name for name in names_list if
                                            name in publisher_names_list]) >= 2:
                                        if len(author_publication_list_jstor) != len(
                                                author_publication_list_publisher):
                                            '''print('_______________________________')
                                            print('different list length')
                                            print(author_publication_list_publisher, author_publication_list_jstor)
                                            print('_______________________________')'''
                                            # Probleme bei:
                                            # Review by: John Habgood
                                            # http://www.jstor.org/stable/23959547
                                            # Review by: John S. Habgood
                                            # https://www.jstor.org/stable/23959548
                                            # solche Autoren evtl. zusammenlegen.
                                        for ap in range(len(author_publication_list_publisher)):
                                            if ap < len(author_publication_list_jstor):
                                                jstor_mapping_dict[
                                                    author_publication_list_publisher[ap]] = \
                                                    author_publication_list_jstor[ap]
                                                total_matches += 1
                                                pagination_found = True
                except Exception as e:
                    print('Error', e, p, pagination)
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]

                    print(exc_type, fname, exc_tb.tb_lineno)
            if not pagination_found:
                '''print('_______________________________')
                print('pagination not found')
                print(pagination, publisher_issue_dict[pagination])
                print(jstor_issue_dict)
                print('_______________________________')'''
                pass
    # print(total_matches)
    return total_nr, total_matches


def get_jstor_links(zeder_id: str):
    total_nr = 0
    total_matches = 0
    if create_jstor_url_dict(zeder_id):
        get_url_dict(zeder_id)
        with open(JSTOR_JSON + zeder_id + '.json', 'r',
                      encoding="utf-8") as jstor_file:
                jstor_dict = json.load(jstor_file)
        with open(PUBLISHER_JSON + zeder_id + '.json', 'r',
                  encoding="utf-8") as jstor_file:
            publisher_dict = json.load(jstor_file)
        jstor_mapping_dict = {}
        # über Jahreszahlen im Publisher-Dictionary iterieren
        for year in publisher_dict:
            if not year in jstor_dict:
                print('year', year, 'not found in jstor-dict')
            else:
                # über Jahrgänge in den Jahren iterieren
                for volume in publisher_dict[year]:
                    if volume not in jstor_dict[year]:
                        '''print('________________')
                        print('volume', volume, 'not found in', year)
                        print(jstor_dict[year])
                        print('________________')'''
                        pass
                    else:
                        # über Issues in den Jahrgängen iterieren
                        for issue in publisher_dict[year][volume]:
                            # print('publisher_issue:', issue)
                            if issue not in jstor_dict[year][volume]:
                                issues_found_jstor = sorted(list(jstor_dict[year][volume].keys()))
                                issues_found_publisher = sorted(list(publisher_dict[year][volume].keys()))
                                if len(issues_found_jstor) == len(issues_found_publisher):
                                    for i in range(len(issues_found_publisher)):
                                        jstor_dict[year][volume][issues_found_publisher[i]] = jstor_dict[year][volume][issues_found_jstor[i]]
                                else:
                                    if issues_found_publisher == ['null']:
                                        # falls es keine Issue-Nummer gibt, dann werden alle Issues im JSTOR-Dicitonary ebenfalls unter der Issue-Bezeichnung "null" gespeichert.
                                        new_jstor_dict = {'null': {}}
                                        for issue in jstor_dict[year][volume]:
                                            for jstor_pagination in jstor_dict[year][volume][issue]:
                                                new_jstor_dict['null'][jstor_pagination] = jstor_dict[year][volume][issue][jstor_pagination]
                                        jstor_dict[year][volume] = new_jstor_dict
                                        issue = 'null'
                            if issue in jstor_dict[year][volume]:
                                # hier noch das Vorgehen für die Issues ohne Volume-Angabe implementieren
                                # Auch die Funktion oben noch weiter anpassen
                                total_nr, total_matches = match_issue_dicts(jstor_mapping_dict, publisher_dict[year][volume][issue], jstor_dict[year][volume][issue], total_nr,
                                                  total_matches)
        print('total:', total_nr, 'not matched:', total_nr - total_matches)
        with open(JSTOR_MAPPING + zeder_id + '.json', 'w',
                      encoding="utf-8") as jstor_mapping_file:
                json.dump(jstor_mapping_dict, jstor_mapping_file)


if __name__ == '__main__':
    create_jstor_url_dict('1350')