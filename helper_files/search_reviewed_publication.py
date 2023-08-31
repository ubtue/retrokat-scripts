import urllib.request
from bs4 import BeautifulSoup
import re
import unidecode


def check_response_for_priority_of_results(xml_soup, review_year):
    records_found = {}
    if xml_soup.find('zs:numberofrecords').text != '0':
        for record in xml_soup.find_all('record'):
            year = None
            if record.find('datafield', tag='011@'):
                if record.find('datafield', tag='011@').find('subfield', code='a'):
                    year = record.find('datafield', tag='011@').find('subfield', code='a').text
                elif record.find('datafield', tag='011@').find('subfield', code='n'):
                    year = record.find('datafield', tag='011@').find('subfield', code='n').text
            try:
                if int(year) > review_year:
                    continue
            except:
                continue
            ppn = record.find('datafield', tag='003@').find('subfield', code='0').text
            ixtheo = False
            # hier den Record auswählen, der eine 1 als SSG Zeichen hat ODER ein anderes Kennzeichen
            ssg_tags = [element.find('subfield', code='a').text for element in record.find_all('datafield', tag='045V')]
            for ssg_tag in ['1', '0', '6,22']:
                if ssg_tag in ssg_tags:
                    ixtheo = True
                    # print('found ssg')
                    break
            if not ixtheo:
                cods = [element.find('subfield', code='a').text for element in record.find_all('datafield', tag='016B')]
                for cod in ['mteo', 'redo', 'DTH5', 'AUGU', 'DAKR', 'MIKA', 'BIIN', 'KALD', 'GIRA']:
                    if cod in cods:
                        ixtheo = True
                        # print('found cod')
                        break
            record_state = record.find('datafield', tag='002@').find('subfield', code='0').text
            if record_state[1] not in ['a', 'c', 'd', 'f', 'F']:
                continue
            if record.find('datafield', tag='006X'):
                if record.find('datafield', tag='006X').find('subfield', code='i'):
                    if re.search(r'^EPF', record.find('datafield', tag='006X').find('subfield', code='i').text):
                        continue
            isbn = None
            if record.find('datafield', tag='004A'):
                if record.find('datafield', tag='004A').find('subfield', code='0'):
                    isbn = record.find('datafield', tag='004A').find('subfield', code='0').text
            is_bsz = False
            if record.find('datafield', tag='007G').find('subfield', code='i').text == 'BSZ':
                is_bsz = True
            records_found[ppn] = {'record_state': record_state, 'is_bsz': is_bsz, 'ixtheo': ixtheo, 'isbn': isbn}
        records_with_identical_isbn = {}
        for ppn_found in records_found:
            if records_found[ppn_found]['isbn'] not in records_with_identical_isbn:
                records_with_identical_isbn[records_found[ppn_found]['isbn']] = [ppn_found]
            else:
                records_with_identical_isbn[records_found[ppn_found]['isbn']].append(ppn_found)
    return records_found


def encode_in_ascii_and_remove_whitespaces_and_points(string: str, is_author, is_place):
    if is_author:
        list_of_letters = re.findall(r'[\w,]+', string)
    elif is_place:
        list_of_letters = [re.findall(r'[\w]+', string)[0]]
    else:
        list_of_letters = [word if word.lower() not in ['all', 'or', 'and', 'any'] else "'" + word for word in re.findall(r'\w+', string)]
    decoded_string = '+'.join(list_of_letters)
    decoded_string = unidecode.unidecode(decoded_string)
    decoded_string = decoded_string.strip('+')
    return decoded_string

# Probleme:
# Plotinus, Self and the Wo rld (Leerzeichen innerhalb führen zu Problemen)


def search_publication(title, author, year, place, review_year):
    if (title.count(" ") < 2) and not year and not place:
        return {}
    pub_dict = {}
    pub_dict["tit"] = encode_in_ascii_and_remove_whitespaces_and_points(title, False, False)
    pub_dict["jah"] = encode_in_ascii_and_remove_whitespaces_and_points(year, False, False)
    if not pub_dict['jah']:
        if place:
            pub_dict["ver"] = encode_in_ascii_and_remove_whitespaces_and_points(place, False, True)
    author = author.replace('::', ' or ')
    author = encode_in_ascii_and_remove_whitespaces_and_points(author, True, False)
    pub_dict["per"] = '"' + author + '"'
    url = 'http://sru.k10plus.de/opac-de-627?version=1.1&operation=searchRetrieve&query='
    for key in pub_dict:
        if pub_dict[key]:
            if pub_dict[key] != 'null':
                url += 'pica.' + key + '%3D' + pub_dict[key].strip('.') + '+and+'
    url = url.strip('+and+').replace("\\", "").replace(" ", "") + '&maximumRecords=10&recordSchema=picaxml'
    xml_data = urllib.request.urlopen(url)
    xml_soup = BeautifulSoup(xml_data, features='lxml')
    if not xml_soup.find('zs:numberofrecords'):
        print(url)
        return {}
    records_found = check_response_for_priority_of_results(xml_soup, review_year)
    return records_found


def search_publication_with_isbn(isbn: str):
    records_found = {}
    isbn = isbn.replace(' ', '')
    isbn = isbn.replace('‑', '')
    isbn = isbn.replace('-', '')
    if not isbn:
        print('no isbn found')
        return {}
    if len(isbn) < 9:
        print('isbn too short', isbn)
        return {}
    url = 'http://sru.k10plus.de/opac-de-627?version=1.1&operation=searchRetrieve&query=pica.isb%3D' + isbn + '&maximumRecords=10&recordSchema=picaxml'
    try:
        xml_data = urllib.request.urlopen(url).read().decode('UTF-8')
        xml_soup = BeautifulSoup(xml_data, features='lxml')
        records_found = check_response_for_priority_of_results(xml_soup, 2021)
        if not records_found:
            if 'x' not in isbn.lower():
                if (9 <= len(isbn) <= 10):
                    isbn = isbn + 'x'
                    url = 'http://sru.k10plus.de/opac-de-627?version=1.1&operation=searchRetrieve&query=pica.isb%3D' + isbn + '&maximumRecords=10&recordSchema=picaxml'
                    xml_data = urllib.request.urlopen(url).read().decode('UTF-8')
                    xml_soup = BeautifulSoup(xml_data, features='lxml')
                    records_found = check_response_for_priority_of_results(xml_soup, 2021)
    except Exception as e:
        print(url)
        print(e)
    return records_found


if __name__ == '__main__':
    # search_publication('The Semantic Field of Cutting Tools in Biblical Hebrew', 'koller, aaron j.', '2012', 'washington')
    search_publication_with_isbn('Book Reviews: Three Thomist Studies. By Frederick E. Crowe, SJ (Supplementary issue of Lonergan Workshop, vol. 16, edited by Michael Vertin and Frederick Lawrence.) Boston: Boston College, 2000. Pp. xxiv+260. ISBN 0-9700862-0-2')

# prüfen, ob SSG-Kennzeichen vorhanden & in Liste schreiben, falls nicht (für Überprüfung an ...).
# mit Dubletten umgehen (immer vorzugsweise die gekennzeichnete, dann andere SWB-Aufnahmen verwenden)
# Abrufzeichen in ...
# in der Datei Abrufzeichen IxTheo.pdf prüfen, alles, was hier zutrifft, übernehmen.
