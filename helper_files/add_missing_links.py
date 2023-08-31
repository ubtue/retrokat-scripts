import urllib.request
from bs4 import BeautifulSoup
import json
from helper_files.config import MISSING_LINKS


def get_records_with_missing_links(eppn, zid):
    records_with_missing_links = []
    empty_page = False
    start_nr = 1
    while not empty_page:
        filedata = urllib.request.urlopen('http://sru.k10plus.de/'
                                          'opac-de-627?version=1.1&operation=searchRetrieve&query=pica.1049%3D' + eppn +
                                          '+and+pica.1045%3Drel-nt+and+pica.1001%3Db&maximumRecords=100&startRecord=' + str(start_nr) + '&recordSchema=picaxml')
        data = filedata.read()
        xml_soup = BeautifulSoup(data, "lxml")
        if not xml_soup.find('zs:records'):
            empty_page = True
            continue
        start_nr += 100
        for record in xml_soup.find('zs:records').find_all('zs:record'):
            record_state = record.find('datafield', tag='002@').find('subfield', code='0').text
            if record_state[1] != 's':
                continue
            if record.find('datafield', tag='017C'):
                pass
            else:
                if record.find('datafield', tag='004V'):
                    doi = record.find('datafield', tag='004V').find('subfield', code='0').text
                else:
                    doi = None
                title = record.find('datafield', tag='021A').find('subfield', code='a').text
                if record.find('datafield', tag='028A'):
                    if record.find('datafield', tag='028A').find('subfield', code='A') and record.find('datafield', tag='028A').find('subfield', code='D'):
                        author = record.find('datafield', tag='028A').find('subfield', code='A').text + ', ' + record.find('datafield', tag='028A').find('subfield', code='D').text
                source_information = record.find('datafield', tag='031A')
                try:
                    if source_information.find('subfield', code='j'):
                        year = source_information.find('subfield', code='j').text
                    else:
                        year = None
                    if source_information.find('subfield', code='d'):
                        volume = source_information.find('subfield', code='d').text
                    else:
                        volume = None
                    if source_information.find('subfield', code='e'):
                        issue = source_information.find('subfield', code='e').text
                    else:
                        issue = None
                    if source_information.find('subfield', code='h'):
                        pages = source_information.find('subfield', code='h').text
                    else:
                        pages = None
                    record_id = record.find('datafield', tag='003@').find('subfield', code='0').text
                    records_with_missing_links.append({'title': title, 'year': year,
                                                             'volume': volume, 'issue': issue, 'pages': pages,
                                                             'doi': doi, 'id': record_id})
                except Exception as e:
                    print(e)
                    print(record)

    with open(MISSING_LINKS + zid + '.json', 'w') as json_file:
        json.dump(records_with_missing_links, json_file)


if __name__ == '__main__':
    get_records_with_missing_links('505950618', '2022')