import json
import os
import xml.etree.ElementTree as ElementTree
import re
from helper_files.search_reviewed_publication import search_publication, search_publication_with_isbn
from helper_files.convert_roman_numbers import from_roman
from hebrew_numbers import gematria_to_int
from bs4 import BeautifulSoup
import urllib.request
from helper_files.language_detection import detect_title
from datetime import datetime
from helper_files.get_k10plus_credentials import get_credentials
from helper_files.regex_helper import regexISBN
from helper_files.config import RESULT_FILES, EXCLUDE_JSON, MISSING_LINKS, PRESENT_RECORDS_JSON, JSTOR_MAPPING

TMP_DATA_FILES = "volume_files/"

username, password = get_credentials()
month_dict = {'January': '1', 'February': '2', 'March': '3', 'April': '4', 'May': '5',
              'June': '6', 'July': '7', 'August': '8', 'September': '9', 'October': '10',
              'November': '11', 'December': '12',
              'Januar': '1', 'Februar': '2', 'März': '3', 'Mai': '5',
              'Juni': '6', 'Juli': '7', 'Juli/August': '7/8', 'Oktober': '10',
              'Dezember': '12',
              '3e livraison': '3', '4e livraison': '4', '2e livraison': '2', '1re livraison': '1',
              '[4]': '4', '[1]': '1', '(2)': '2'}


def create_marc_field(record, field_dict: dict):
    new_datafield = ElementTree.SubElement(record, "{http://www.loc.gov/MARC21/slim}datafield",
                                           {'tag': field_dict['tag'], 'ind1': field_dict['ind1'],
                                            'ind2': field_dict['ind2']})
    for subfield_code in field_dict['subfields']:
        for subfield_text in field_dict['subfields'][subfield_code]:
            new_datafield.tail = "\n"
            new_subfield = ElementTree.SubElement(new_datafield, "{http://www.loc.gov/MARC21/slim}subfield",
                                                  {'code': subfield_code})
            new_subfield.text = subfield_text


def get_subfield(record, tag, subfield_code):
    searchstring = '{http://www.loc.gov/MARC21/slim}datafield[@tag="' \
                   + tag + '"]/{http://www.loc.gov/MARC21/slim}subfield[@code="' + subfield_code + '"]'
    if record.find(searchstring) is None:
        return None
    return record.find(searchstring).text


def get_fields(record, tag):
    searchstring = '{http://www.loc.gov/MARC21/slim}datafield[@tag="' \
                   + tag + '"]'
    return record.findall(searchstring)


def check_abstract(record):
    abstract_tag = record.find \
        ('{http://www.loc.gov/MARC21/slim}datafield[@tag="520"]/{http://www.loc.gov/MARC21/slim}subfield[@code="a"]')
    if abstract_tag is not None:
        if re.search(r'^.{0,125}Article .+ was published on .+ in the journal .+ (.+).', abstract_tag.text, re.IGNORECASE):
            abstract_tags = get_fields(record, '520')
            for abstract_tag in abstract_tags:
                record.remove(abstract_tag)
        elif re.search \
                (r'^.{0,125},\s+Volume\s+(os-)?(\d+|[CcLlXxVvIi]+),\s+Issue\s+[\d–\-/CcLlXxVvIi]+,\s+.+,\s+Pages(\s+[\dCcLlXxVvIi]+[\d–a-zA-Z]*,)?', abstract_tag.text, re.IGNORECASE):
            abstract_tags = get_fields(record, '520')
            for abstract_tag in abstract_tags:
                record.remove(abstract_tag)
        if re.search(r'^No\s+Abstract', abstract_tag.text, re.IGNORECASE):
            abstract_tags = get_fields(record, '520')
            for abstract_tag in abstract_tags:
                record.remove(abstract_tag)
        elif 60 < len(abstract_tag.text) < 150:
            pass
            # print("Short abstract:", abstract_tag.text)
        elif len(abstract_tag.text) < 60:
            abstract_tags = get_fields(record, '520')
            for abstract_tag in abstract_tags:
                record.remove(abstract_tag)
        elif 'http' in abstract_tag.text:
            pass
            # print("Link in abstract:", abstract_tag.text)
    return None


def create_review_link(record):
    tags = record.findall \
        ('{http://www.loc.gov/MARC21/slim}datafield[@tag="650"]/{http://www.loc.gov/MARC21/slim}subfield[@code="a"]')
    keywords = get_fields(record, '650')
    records_found = {}
    tag_nr = 0
    review_title = ''
    for tag in tags:
        if re.search(r'^#reviewed_pub#', tag.text, re.IGNORECASE):
            pub_title = re.findall(r'#title::([^#]+)#', tag.text, re.IGNORECASE)[0] if re.findall(r'#title::([^#]+)#', tag.text, re.IGNORECASE) else ''
            pub_author = re.findall(r'#name::([^#]+)#', tag.text, re.IGNORECASE)[0] if re.findall(r'#name::([^#]+)#', tag.text, re.IGNORECASE) else ''
            pub_year = re.findall(r'#year::([^#]+)#', tag.text, re.IGNORECASE)[0] if re.findall(r'#year::([^#]+)#', tag.text, re.IGNORECASE) else ''
            pub_place = re.findall(r'#place::([^#]+)#', tag.text, re.IGNORECASE)[0] if re.findall(r'#place::([^#]+)#', tag.text, re.IGNORECASE) else ''
            pub_isbn = re.findall(r'#isbn::([^#]+)#', tag.text, re.IGNORECASE)[0] if re.findall(r'#isbn::([^#]+)#', tag.text, re.IGNORECASE) else ''
            review_year = int(get_subfield(record, '264', 'c'))
            if not pub_isbn:
                records_found = search_publication(pub_title, pub_author, pub_year, pub_place, review_year)
                if tag_nr == 0:
                    review_title = '[Rezension von: ' + pub_author.split('::')[0] + ', ' + pub_title
                if tag_nr == 1:
                    review_title += '...'
            else:
                records_found = search_publication_with_isbn(pub_isbn)
            for keyword in keywords:
                if keyword.find('{http://www.loc.gov/MARC21/slim}subfield[@code="a"]').text == tag.text:
                    if keyword in record:
                        record.remove(keyword)
        tag_nr += 1
    if review_title:
        review_title += ']'
    return records_found, review_title


def check_and_split_in_issues(zeder_id, conf_available):
    issue_tree = ElementTree.parse('helper_files/marcxml_empty.xml')
    issue_root = issue_tree.getroot()
    all_title_beginnings = {}
    missing_authors = []
    record_nr = 0
    for file in os.listdir(TMP_DATA_FILES):
        os.unlink(TMP_DATA_FILES + file)
    for file in os.listdir(RESULT_FILES):
        if file == zeder_id + '.xml':
            all_issues = []
            ElementTree.register_namespace('', "http://www.loc.gov/MARC21/slim")
            result_tree = ElementTree.parse(RESULT_FILES + file)
            result_root = result_tree.getroot()
            records = result_root.findall('.//{http://www.loc.gov/MARC21/slim}record')
            paginations = ['-']
            reviews = 0
            current_issue = 'first'
            records = [record for record in records]
            with open(EXCLUDE_JSON, 'r') as exclusion_file:
                exclude_everywhere = json.load(exclusion_file)
            for record in records:
                record_nr += 1
                if get_subfield(record, '936', 'e'):
                    new_issue = str(get_subfield(record, '936', 'd').zfill(3)).replace('/', '-') + \
                                str(get_subfield(record, '936', 'e').zfill(2)).replace('/', '-')
                elif get_subfield(record, '936', 'd'):
                    new_issue = str(get_subfield(record, '936', 'd').zfill(3)).replace('/', '-') + '000'
                else:
                    if zeder_id not in ['0001']:
                        print('discarded:', get_subfield(record, '245', 'a'), 'because it is no journal article')
                        continue
                    else:
                        new_issue = '000000'
                if new_issue not in all_issues:
                    with open(TMP_DATA_FILES + current_issue + '.xml', 'w') as xml_file:
                        xml_file.close()
                    issue_tree.write(TMP_DATA_FILES + current_issue + '.xml', xml_declaration=True)
                    all_issues.append(new_issue)
                    issue_tree = ElementTree.parse('helper_files/marcxml_empty.xml')
                    issue_root = issue_tree.getroot()
                    paginations = []
                    reviews = 0
                    current_issue = new_issue
                title = get_subfield(record, '245', 'a')
                found = False
                for exclude_regex in exclude_everywhere:
                    if re.search(exclude_regex, title, re.IGNORECASE):
                        found = True
                if not record.find('{http://www.loc.gov/MARC21/slim}datafield[@tag="100"]'):
                    if title not in missing_authors:
                        if not found:
                            missing_authors.append(title)
                title_beginning = ' '.join(title.split()[:3])
                if not found:
                    if title_beginning not in all_title_beginnings:
                        all_title_beginnings[title_beginning] = 1
                    else:
                        all_title_beginnings[title_beginning] += 1
                if get_subfield(record, '655', 'a'):
                    reviews += 1
                pagination = get_subfield(record, '936', 'h')
                if pagination:
                    paginations.append(pagination)
                issue_root.append(record)
                if records.index(record) == (len(records) - 1):
                    issue_tree.write(TMP_DATA_FILES + current_issue + '.xml', xml_declaration=True)
    if conf_available:
        if input("Show titles with multiple occurence and missing authors? (y/n) ") == 'y':
            conf_available = False
    if not conf_available:
        treshold = record_nr/1000 if record_nr >= 3000 else 2
        print([beginning for beginning in all_title_beginnings if all_title_beginnings[beginning] > treshold])
        print(missing_authors)
    return record_nr


def transform(zeder_id: str, exclude: list[str], Volumes_to_catalogue: list[int], record_nr, default_lang: str, conf_langs: list[str], is_jstor_data: str, embargo: int, check_for_duplicates: str):
    responsibles_corrected = {}
    personal_titles = {}
    total_jstor_fails = 0
    total_jstor_links = 0
    review_links_created = 0
    Volumes_discarded = []
    post_process_nr = 0
    discarded_nr = 0
    discarded_by_volume_nr = 0
    proper_nr = 0
    deduplicate_nr = 0
    time = datetime.now()
    current_year = int(time.strftime("%Y"))
    volume_list = []
    different_volume_counting = []
    for i in range(0, len(Volumes_to_catalogue), 2):
        volume_list += [str(year) for year in range(Volumes_to_catalogue[i], Volumes_to_catalogue[i+1] + 1)]
    embargo_list = [year for year in volume_list if year in [str(current_year - i) for i in range(0, embargo)]]
    print('embargo_list:', embargo_list)
    source_ppn = ""
    found_volume_list = []
    ppns_linked = []
    links_to_add = {}
    links_to_add_nr = 0
    urls = []
    dois = []
    excluded_titles = []
    review_links = []
    jstor_dict = {}
    languages_dict = {}
    review_dict = {}
    all_sources = {}
    all_languages = []
    with open(MISSING_LINKS + zeder_id + '.json', 'r') as missing_link_file:
        records_with_missing_links = json.load(missing_link_file)
        missing_link_lookup_years = [missing_link_record['year'] for missing_link_record in records_with_missing_links]
    with open(PRESENT_RECORDS_JSON, 'r', encoding='utf-8') as present_record_file:
        all_present_records = json.load(present_record_file)
        recognized_present_record_list = []
        if zeder_id in all_present_records:
            present_record_lookup_years = [present_record['year'] for present_record in all_present_records[zeder_id]]
            present_record_list = all_present_records[zeder_id]
            for entry in present_record_list:
                for special_char in ["'", '"', "(", ")", "?"]:
                    entry['title'] = entry['title'].replace(special_char, '.')
                entry['title'] = re.sub(r'[^\x00-\x7F]', '.', entry['title'])
        else:
            present_record_lookup_years = []
            present_record_list = []
    if zeder_id + '_review_urls.json' in os.listdir('review_links'):
        with open('review_links/' + zeder_id + '_review_urls.json', 'r') as review_link_file:
            review_links = json.load(review_link_file)
    if zeder_id + '.json' in os.listdir(JSTOR_MAPPING):
        with open(JSTOR_MAPPING + zeder_id + '.json', 'r',
                  encoding="utf-8") as jstor_file:
            jstor_dict = json.load(jstor_file)
    if zeder_id + '_languages.json' in os.listdir(JSTOR_MAPPING):
        with open(JSTOR_MAPPING + zeder_id + '_languages.json', 'r',
                  encoding="utf-8") as jstor_file:
            languages_dict = json.load(jstor_file)
    if is_jstor_data == 'false' and zeder_id + '_reviews.json' in os.listdir(JSTOR_MAPPING):
        with open(JSTOR_MAPPING + zeder_id + '_reviews.json', 'r',
                      encoding="utf-8") as review_data_file:
            review_dict = json.load(review_data_file)
    post_process_tree = ElementTree.parse('helper_files/marcxml_empty.xml')
    post_process_root = post_process_tree.getroot()
    proper_tree = ElementTree.parse('helper_files/marcxml_empty.xml')
    proper_root = proper_tree.getroot()
    for file in os.listdir(TMP_DATA_FILES):
        ElementTree.register_namespace('', "http://www.loc.gov/MARC21/slim")
        result_tree = ElementTree.parse(TMP_DATA_FILES + file)
        result_root = result_tree.getroot()
        records = result_root.findall('.//{http://www.loc.gov/MARC21/slim}record')
        for record in records:
            discard = False
            append_to_postprocess = False
            found_urls = get_fields(record, '856')
            url = get_subfield(record, '856', 'u')
            doi = get_subfield(record, '024', 'a')
            if check_for_duplicates:
                url = "https://sru.bsz-bw.de/cbsx?version=1.1&operation=searchRetrieve&query=pica.{0}%3D{1}" \
                      "&maximumRecords=10&recordSchema=picaxml&x-username={2}&x-password={3}"\
                    .format(check_for_duplicates, doi.replace('/', '*'), username, password)
                xml_data = urllib.request.urlopen(url)
                xml_soup = BeautifulSoup(xml_data, features='lxml')
                if xml_soup.find('zs:numberofrecords').text != '0':
                    discarded_nr += 1
                    continue
                else:
                    print(doi)
            year = get_subfield(record, '264', 'c')
            if year not in found_volume_list:
                found_volume_list.append(year)
            volume = get_subfield(record, '936', 'd')
            if doi:
                if doi in dois:
                    discarded_nr += 1
                    deduplicate_nr += 1
                    continue
            for found_url in found_urls:
                found_url = found_url.find('{http://www.loc.gov/MARC21/slim}subfield[@code="u"]').text
                if found_url != "https://www.no_url.com" and found_url:
                    if found_url in urls:
                        discard = True
                        deduplicate_nr += 1
                        print("deduplicated:", found_url)
                        continue
            if url == 'https://www.no_url.com':
                record.remove(record.find('{http://www.loc.gov/MARC21/slim}datafield[@tag="856"]'))
                record.remove(record.find('{http://www.loc.gov/MARC21/slim}datafield[@tag="URL"]'))
            urls.append(url)
            # Special treatment for Harrassowitz-journals published on JSTOR
            if zeder_id in ['1548']:
                if doi is None:
                    create_marc_field(record, {'tag': '024', 'ind1': '7', 'ind2': ' ',
                                           'subfields': {'a': [url.replace('https://www.jstor.org/stable/', '')],
                                                         '2': 'doi'}})
            dois.append(doi)
            title = get_subfield(record, '245', 'a')
            for exclude_regex in exclude:
                if re.search(exclude_regex, title, re.IGNORECASE):
                    if title not in excluded_titles:
                        excluded_titles.append(title)
                    discard = True
            if discard:
                discarded_nr += 1
                continue
            differences_from_source = False
            post_process_volume = False
            if volume:
                if '-' in volume:
                    volume = re.sub(r'(\d+).+?(\d+)', r'\1/\2', volume)
                    volume_tag = \
                        record.find('{http://www.loc.gov/MARC21/slim}datafield[@tag="936"]'
                                    '/{http://www.loc.gov/MARC21/slim}subfield[@code="d"]')
                    volume_tag.text = volume
                if re.search(r'[^\d/]', volume):
                    new_volume = re.findall(r'[^\d](\d{1,3}(?:-\d+)?)(?:[^\d]|$)', volume)
                    if new_volume:
                        if re.findall(r'^\d+,\d+', volume):
                            new_volume = re.findall(r'^(\d+),\d+', volume)[0]
                            band = re.findall(r'^\d+,(\d+)', volume)[0]
                            post_process_volume = True
                            differences_from_source = True
                        volume = new_volume[0]
                        volume_tag = \
                            record.find('{http://www.loc.gov/MARC21/slim}datafield[@tag="936"]'
                                        '/{http://www.loc.gov/MARC21/slim}subfield[@code="d"]')
                        volume_tag.text = volume
                        differences_from_source = True
                    else:
                        if re.findall(r'^(?=[MDCLXVI])M*(?:C[MD]|D?C*)(?:X[CL]|L?X*)(?:I[XV]|V?I*)$', volume):
                            new_volume = from_roman \
                                (re.findall(r'^(?=[MDCLXVI])M*(?:C[MD]|D?C*)(?:X[CL]|L?X*)(?:I[XV]|V?I*)$', volume)[0])
                        elif re.findall(r'(?=[MDCLXVI])M*(?:C[MD]|D?C*)(?:X[CL]|L?X*)(?:I[XV]|V?I*)$', volume):
                            new_volume = from_roman \
                                (re.findall(r'(?=[MDCLXVI])M*(?:C[MD]|D?C*)(?:X[CL]|L?X*)(?:I[XV]|V?I*)$', volume)[0])
                        if new_volume:
                            volume_tag = \
                                    record.find('{http://www.loc.gov/MARC21/slim}datafield[@tag="936"]'
                                                '/{http://www.loc.gov/MARC21/slim}subfield[@code="d"]')
                            volume_tag.text = str(new_volume)
                            volume = new_volume
                            differences_from_source = True
                        else:
                            print(volume, 'is not convertible to ararbic number')
                            print(new_volume)
            issue = get_subfield(record, '936', 'e')
            if issue:
                if re.search(r'[^\d/]', issue):
                    if re.findall(r'(\d+).+?(\d+)', issue):
                        issue = re.sub(r'(\d+).+?(\d+)', r'\1/\2', issue)
                        issue_tag = \
                            record.find('{http://www.loc.gov/MARC21/slim}datafield[@tag="936"]'
                                        '/{http://www.loc.gov/MARC21/slim}subfield[@code="e"]')
                        issue_tag.text = issue
                    else:
                        new_issue = ''
                        if re.findall(r'^(?=[MDCLXVI])M*(?:C[MD]|D?C*)(?:X[CL]|L?X*)(?:I[XV]|V?I*)$', issue):
                            new_issue = from_roman(
                                re.findall(r'^(?=[MDCLXVI])M*(?:C[MD]|D?C*)(?:X[CL]|L?X*)(?:I[XV]|V?I*)$', issue)[0])
                        elif re.findall(r'^(?=[mdclxvi])m*(?:c[md]|d?c*)(?:x[cl]|l?x*)(?:i[xv]|v?i*)$', issue):
                            new_issue = from_roman(
                                re.findall(r'^(?=[mdclxvi])m*(?:c[md]|d?c*)(?:x[cl]|l?x*)(?:i[xv]|v?i*)$', issue)[0])
                        if new_issue:
                            issue_tag = \
                                record.find('{http://www.loc.gov/MARC21/slim}datafield[@tag="936"]'
                                            '/{http://www.loc.gov/MARC21/slim}subfield[@code="e"]')
                            issue_tag.text = str(new_issue)
                            issue = new_issue
                            differences_from_source = True
                        else:
                            if issue in month_dict:
                                new_issue = month_dict[issue]
                                issue_tag = \
                                    record.find('{http://www.loc.gov/MARC21/slim}datafield[@tag="936"]'
                                                '/{http://www.loc.gov/MARC21/slim}subfield[@code="e"]')
                                issue_tag.text = str(new_issue)
                                issue = new_issue
                                differences_from_source = True
                            else:
                                print(issue, 'not found in dict')
                                append_to_postprocess = True

            pagination = get_subfield(record, '936', 'h')
            if pagination:
                if zeder_id == "1153" and re.findall(r'(\d+)\s+f', pagination):
                    first_page = re.findall(r'(\d+)\s+f', pagination)[0]
                    pagination_tag = \
                        record.find('{http://www.loc.gov/MARC21/slim}datafield[@tag="936"]'
                                    '/{http://www.loc.gov/MARC21/slim}subfield[@code="h"]')
                    pagination_tag.text = first_page + '-' + str(int(first_page) +1)
                    pagination = pagination_tag.text
                    differences_from_source = True
                if '–' in pagination:
                    pagination = pagination.replace('–', '-')
                    pagination_tag = \
                        record.find('{http://www.loc.gov/MARC21/slim}datafield[@tag="936"]'
                                    '/{http://www.loc.gov/MARC21/slim}subfield[@code="h"]')
                    pagination_tag.text = pagination
                if '-' in pagination:
                    pagination = re.sub(r'(\d+).+?(\d+)', r'\1-\2', pagination)
                    if re.findall(r'(\d+)-(\d+)', pagination):
                        fpage, lpage = re.findall(r'(\d+)-(\d+)', pagination)[0]
                        if fpage == lpage:
                            pagination_tag = \
                                record.find('{http://www.loc.gov/MARC21/slim}datafield[@tag="936"]'
                                            '/{http://www.loc.gov/MARC21/slim}subfield[@code="h"]')
                            pagination_tag.text = fpage
                    elif re.findall(r'(?=[MDCLXVI])M*(?:C[MD]|D?C*)(?:X[CL]|L?X*)(?:I[XV]|V?I*)-\d+', pagination):
                        new_pagination = []
                        int_page = re.findall(r'-(\d+)', pagination)[0]
                        for pag in re.findall(r'(?=[MDCLXVI])M*(?:C[MD]|D?C*)(?:X[CL]|L?X*)(?:I[XV]|V?I*)', pagination):
                            new_pagination.append(str(from_roman(pag)))
                        new_pagination.append(int_page)
                        print('converted', new_pagination, 'from roman number', pagination)
                        pagination = '-'.join(new_pagination)
                        pagination_tag = \
                            record.find('{http://www.loc.gov/MARC21/slim}datafield[@tag="936"]'
                                        '/{http://www.loc.gov/MARC21/slim}subfield[@code="h"]')
                        pagination_tag.text = pagination
                        differences_from_source = True

                    elif re.findall(r'(?=[MDCLXVI])M*(?:C[MD]|D?C*)(?:X[CL]|L?X*)(?:I[XV]|V?I*)', pagination):
                        new_pagination = []
                        for pag in re.findall(r'(?=[MDCLXVI])M*(?:C[MD]|D?C*)(?:X[CL]|L?X*)(?:I[XV]|V?I*)', pagination):
                            new_pagination.append(str(from_roman(pag)))
                        print('converted', new_pagination, 'from roman number', pagination)
                        pagination = '-'.join(new_pagination)
                        pagination_tag = \
                            record.find('{http://www.loc.gov/MARC21/slim}datafield[@tag="936"]'
                                        '/{http://www.loc.gov/MARC21/slim}subfield[@code="h"]')
                        pagination_tag.text = pagination
                        differences_from_source = True

                    elif re.findall(r'(?=[mdclxvi])m*(?:c[md]|d?c*)(?:x[cl]|l?x*)(?:i[xv]|v?i*)', pagination):
                        new_pagination = []
                        for pag in re.findall(r'(?=[mdclxvi])m*(?:c[md]|d?c*)(?:x[cl]|l?x*)(?:i[xv]|v?i*)', pagination):
                            new_pagination.append(str(from_roman(pag)))
                        print('converted', new_pagination, 'from roman number', pagination)
                        pagination = '-'.join(new_pagination)
                        pagination_tag = \
                            record.find('{http://www.loc.gov/MARC21/slim}datafield[@tag="936"]'
                                        '/{http://www.loc.gov/MARC21/slim}subfield[@code="h"]')
                        pagination_tag.text = pagination
                        differences_from_source = True
                    else:
                        arabic_page_numbers = []
                        paginations = pagination.split('-')
                        for page_number in paginations:
                            try:
                                arabic_page_number = gematria_to_int(page_number)
                                arabic_page_numbers.append(arabic_page_number)
                            except:
                                append_to_postprocess = True
                        if len(arabic_page_numbers) > 0:
                            pagination_tag = \
                                record.find('{http://www.loc.gov/MARC21/slim}datafield[@tag="936"]'
                                            '/{http://www.loc.gov/MARC21/slim}subfield[@code="h"]')
                            pagination_tag.text = str(arabic_page_numbers[0]) + '-' + str(arabic_page_numbers[1])
                            create_marc_field(record, {'tag': '041', 'ind1': ' ', 'ind2': ' ',
                                                       'subfields': {'a': ['heb']}})
                            differences_from_source = True
                elif re.findall(r'(?i)(?=[MDCLXVI])M*(?:C[MD]|D?C*)(?:X[CL]|L?X*)(?:I[XV]|V?I*)', pagination):
                    new_pagination = []
                    for pag in re.findall(r'(?i)(?=[MDCLXVI])M*(?:C[MD]|D?C*)(?:X[CL]|L?X*)(?:I[XV]|V?I*)', pagination.upper()):
                        new_pagination.append(str(from_roman(pag)))
                    print('converted', new_pagination, 'from roman number', pagination)
                    pagination = '-'.join(new_pagination)
                    pagination_tag = \
                        record.find('{http://www.loc.gov/MARC21/slim}datafield[@tag="936"]'
                                    '/{http://www.loc.gov/MARC21/slim}subfield[@code="h"]')
                    pagination_tag.text = pagination
                    differences_from_source = True
                elif not re.findall(r'\d+', pagination):
                    append_to_postprocess = True
            else:
                pass
                # print('no pagination:', url)
                #append_to_postprocess = True
            if differences_from_source:
                if post_process_volume:
                    if len(different_volume_counting)>0:
                        volume_tag = \
                        record.find('{http://www.loc.gov/MARC21/slim}datafield[@tag="773"]'
                                    '/{http://www.loc.gov/MARC21/slim}subfield[@code="g"]')
                        volume_tag.text = new_volume + '. ' + different_volume_counting[0] + ' (' + year + '), ' +\
                            band + '. ' + different_volume_counting[1] + ', ' + issue +\
                            '. ' + different_volume_counting[2] + ', Seite ' + pagination
                    else:
                        print('Untergliederte Bandzählung erkannt. Eingabe der Vorlageform nötig.')
                        different_volume_counting.append(input('Wie lautet die erste Gliederungsebene z.B. Jahrgang: '))
                        different_volume_counting.append(input('Wie lautet die zweite Gliederungsebene z.B. Band: '))
                        different_volume_counting.append(input('Wie lautet die Heft-Gliederungsebene z.B. Heft: '))
                source_tag = record.find('{http://www.loc.gov/MARC21/slim}datafield[@tag="936"]')
                original_source_tag = ElementTree.SubElement(source_tag, "{http://www.loc.gov/MARC21/slim}subfield",
                                       {'code': 'y'})
                if get_subfield(record, '773', 'g'):
                    original_source_tag.text = get_subfield(record, '773', 'g')
                else:
                    print('no subfield 773 $g')
            author = get_subfield(record, '100', 'a')
            source = get_subfield(record, '773', 'g')
            if get_subfield(record, '773', 'w') is not None:
                source_ppn = get_subfield(record, '773', 'w').replace('(DE-627)', '')
            # Dubletten im Ergebnis herausfiltern:
            if source in all_sources and zeder_id in ['1157b', '1259++']:
                previous_title = all_sources[source]['title']
                previous_author = all_sources[source]['author']
                if (previous_title == title) and (previous_author == author):
                    print('same title and author:', source, url)
                    discarded_nr += 1
                    continue
            all_sources[source] = {'title': title, 'author': author}
            if [year in missing_link_lookup_years]:
                for entry in [entry for entry in records_with_missing_links if entry['year'] == year]:
                    if ('volume' in entry) and ('issue' in entry) and ('pages' in entry):
                        if (entry['volume'] == volume) and (entry['issue'] == issue) and (
                                entry['pages'] == pagination):
                            if not entry['doi'] and doi is not None:
                                links_to_add[entry['id']] = {'to_remove': [], 'to_add': ['2051 ' + doi, '4950 ' + url + '$xR$3Volltext$4ZZ$534']}
                                links_to_add_nr += 1
                            if url is not None:
                                if 'doi.org' in url:
                                    links_to_add[entry['id']] = {'to_remove': [], 'to_add': ['4950 ' + url + '$xR$3Volltext$4ZZ$534']}
                                    links_to_add_nr += 1
                                else:
                                    links_to_add[entry['id']] = {'to_remove': [], 'to_add': ['4950 ' + url + '$xH$3Volltext$4ZZ$534']}
                                    links_to_add_nr += 1
            if year not in volume_list:
                discarded_by_volume_nr += 1
                if year not in Volumes_discarded:
                    Volumes_discarded.append(year)
                continue
            for datafield in record.findall('{http://www.loc.gov/MARC21/slim}datafield[@tag="935"]'):
                if datafield.find('{http://www.loc.gov/MARC21/slim}subfield[@code="a"]') is not None:
                    if datafield.find('{http://www.loc.gov/MARC21/slim}subfield[@code="a"]').text \
                                    not in ['mteo', 'zota', 'nbrk', 'erco', 'ixzs', 'ixrk', 'NABZ', 'rplv', 'sels']:
                                print('deleted retrieve sign', datafield.find('{http://www.loc.gov/MARC21/slim}subfield[@code="a"]').text)
                    if datafield.find('{http://www.loc.gov/MARC21/slim}subfield[@code="a"]').text not in ['NABZ', 'mteo', 'rplv', 'sels']:
                        record.remove(datafield)
                    if datafield.find('{http://www.loc.gov/MARC21/slim}subfield[@code="a"]').text == 'rplv':
                        record.find('{http://www.loc.gov/MARC21/slim}leader').text = record.find('{http://www.loc.gov/MARC21/slim}leader').text.replace('00000nab', '00000nam')
            for retrieve_sign in ['ixzs', 'ixrk', 'zota']:
                create_marc_field(record, {'tag': '935', 'ind1': ' ', 'ind2': ' ', 
                                           'subfields': {'a': [retrieve_sign], '2': ['LOK']}})

            if '$$' in title:
                # print(title)
                create_marc_field(record, {'tag': '935', 'ind1': ' ', 'ind2': ' ',
                                           'subfields': {'a': ['nbrk'], '2': ['LOK']}})
            if present_record_list:

                delete_entries = []
                if year in present_record_lookup_years:

                    for entry in [entry for entry in present_record_list if entry['year'] == year]:
                        if ('volume' in entry) and ('issue' in entry):
                            if (entry['volume'] == volume) and (entry['issue'] == issue):
                                if entry['title'] == '*all*':
                                    print('Alle Titel in', issue, volume, year, 'werden gelöscht.')
                                    discard = True
                                else:
                                    if 'doi' in entry:
                                        if entry['doi'] == doi:
                                            delete_entries.append(entry)
                                            discard = True
                                    if 'url' in entry:
                                        all_urls = get_fields(record, '856')
                                        for url in all_urls:
                                            url_text = url.find('{http://www.loc.gov/MARC21/slim}subfield[@code="u"]').text
                                            if entry['url'] == url_text:
                                                delete_entries.append(entry)
                                                discard = True
                                    found = re.search(entry['title'], title, re.IGNORECASE)
                                    if found is not None:
                                        delete_entries.append(entry)
                                        discard = True
                        elif 'volume' in entry:
                            if entry['volume'] == volume:
                                if entry['title'] == '*all*':
                                    print('Alle Titel in', volume, year, 'werden gelöscht.')
                                    discard = True
                                else:
                                    if 'doi' in entry:
                                        if entry['doi'] == doi:
                                            delete_entries.append(entry)
                                            discard = True
                                    if 'url' in entry:
                                        all_urls = get_fields(record, '856')
                                        for url in all_urls:
                                            url_text = url.find('{http://www.loc.gov/MARC21/slim}subfield[@code="u"]').text
                                            if entry['url'] == url_text:
                                                delete_entries.append(entry)
                                                discard = True
                                    found = re.search(entry['title'], title, re.IGNORECASE)
                                    if found is not None:
                                        delete_entries.append(entry)
                                        discard = True
                    for entry in delete_entries:
                        recognized_present_record_list.append(entry)
                        present_record_list.remove(entry)
                """
                for entry in present_record_list:
                    if 'doi' in entry:
                        if entry['doi'] == doi:
                            delete_entries.append(entry)
                            discard = True
                    if 'url' in entry:
                        all_urls = get_fields(record, '856')
                        for url in all_urls:
                            url_text = url.find('{http://www.loc.gov/MARC21/slim}subfield[@code="u"]').text
                            if entry['url'] == url_text:
                                delete_entries.append(entry)
                                discard = True
                for entry in delete_entries:
                    recognized_present_record_list.append(entry)
                    present_record_list.remove(entry)
                """
                # print(discard, '\n____________')
            if discard:
                discarded_nr += 1
                continue
            if any([re.search(regex, title, re.IGNORECASE) for regex in [r'^errat*', r'^corrigend*', r'^correct*', r'^berichtigung*', r'^omission*',
                                                                         r'\berrat((um)|(a))\b', r'\bcorrigend((um)|(a))\b', r'\bcorrections?\b', r'\bberichtigung\b']]):
                create_marc_field(record, {'tag': '935', 'ind1': ' ', 'ind2': ' ',
                                           'subfields': {'a': ['erco'], '2': ['LOK']}})
                # Abrufzeichen für die Nachbearbeitung von Errata/Corrigenda!
            if year in embargo_list:
                print('embargo:', title)
                embargo_url = record.find('{http://www.loc.gov/MARC21/slim}datafield[@tag="856"]'
                                        '/{http://www.loc.gov/MARC21/slim}subfield[@code="u"]').text
                if record.find('{http://www.loc.gov/MARC21/slim}datafield[@tag="856"]') is not None:
                    record.remove(record.find('{http://www.loc.gov/MARC21/slim}datafield[@tag="856"]'))
                record.remove(record.find('{http://www.loc.gov/MARC21/slim}datafield[@tag="URL"]'))
                create_marc_field(record, {'tag': '866', 'ind1': ' ', 'ind2': ' ',
                                           'subfields': {'x': ['EMBARGO#01.01.' + str(int(year) + embargo) + '#' + embargo_url], '2': ['LOK']}})
                print('EMBARGO#01.01.' + str(int(year) + embargo) + '#' + embargo_url)
            responsibles = get_fields(record, '100') + get_fields(record, '700')
            for responsible in responsibles:
                responsible_name = responsible.find('{http://www.loc.gov/MARC21/slim}subfield[@code="a"]').text
                if responsible_name in ["[s.n.]", ", [s.n.]", ", [s.n]"]:
                    record.remove(responsible)
                    continue
                if responsible.find('{http://www.loc.gov/MARC21/slim}subfield[@code="c"]') is not None:
                    personal_title = responsible.find('{http://www.loc.gov/MARC21/slim}subfield[@code="c"]').text
                    personal_titles[personal_title] = 0
                    if re.match(r', [^\s+]+?', responsible_name):
                        responsible.find('{http://www.loc.gov/MARC21/slim}subfield[@code="a"]').text = responsible_name.replace(', ', '') + ', ' + personal_title
                        responsible_name = responsible_name.replace(', ', '') + ', ' + personal_title
                        responsible.remove(responsible.find('{http://www.loc.gov/MARC21/slim}subfield[@code="c"]'))
                        personal_titles[personal_title] += 1
                if responsible.find('{http://www.loc.gov/MARC21/slim}subfield[@code="b"]') is not None:
                    personal_title = responsible.find('{http://www.loc.gov/MARC21/slim}subfield[@code="b"]').text
                    personal_titles[personal_title] = 0
                    if re.match(r', [^\s+]+?', responsible_name):
                        responsible.find('{http://www.loc.gov/MARC21/slim}subfield[@code="a"]').text = responsible_name.replace(', ', '') + ', ' + personal_title
                        responsible_name = responsible_name.replace(', ', '') + ', ' + personal_title
                        responsible.remove(responsible.find('{http://www.loc.gov/MARC21/slim}subfield[@code="b"]'))
                        personal_titles[personal_title] += 1
                if len(responsibles) == 1:
                    if re.match(r', [^\s+]+?', responsible_name):
                        responsible.find('{http://www.loc.gov/MARC21/slim}subfield[@code="a"]').text = responsible_name.replace(', ', '')
                        responsible.attrib['ind1'] = '0'
                        if responsible_name not in responsibles_corrected:
                            responsibles_corrected[responsible_name] = url
                if re.match(r'^,', responsible.find('{http://www.loc.gov/MARC21/slim}subfield[@code="a"]').text):
                    append_to_postprocess = True
                if re.match(r'^\w\.*, (?:\w\.?\s?)+$', responsible.find('{http://www.loc.gov/MARC21/slim}subfield[@code="a"]').text):
                    gnd_link = responsible.find('{http://www.loc.gov/MARC21/slim}subfield[@code="0"]')
                    if gnd_link is not None:
                        responsible.remove(gnd_link)
                    responsible.attrib['ind1'] = '0'
                    responsible.find('{http://www.loc.gov/MARC21/slim}subfield[@code="a"]').text = re.sub(
                        r'^(\w\.*), ((?:\w\.?\s?)+)$', r'\2 \1',
                        responsible.find('{http://www.loc.gov/MARC21/slim}subfield[@code="a"]').text)
                if re.search(r'\s+\.\s+', responsible.find('{http://www.loc.gov/MARC21/slim}subfield[@code="a"]').text):
                    responsible.find('{http://www.loc.gov/MARC21/slim}subfield[@code="a"]').text = re.sub(r'\s+\.\s+', ' ',
                                                                                                          responsible.find('{http://www.loc.gov/MARC21/slim}subfield[@code="a"]').text)
            if url in jstor_dict:
                if jstor_dict[url] in review_dict:
                    for tag in review_dict[jstor_dict[url]]:
                        create_marc_field(record, {'tag': '650', 'ind1': ' ', 'ind2': '4',
                                                   'subfields': {'a': [tag]}})
                elif jstor_dict[url].replace('http:', 'https:') in review_dict:
                    for tag in review_dict[jstor_dict[url].replace('http:', 'https:')]:
                        create_marc_field(record, {'tag': '650', 'ind1': ' ', 'ind2': '4',
                                                   'subfields': {'a': [tag]}})
            if url in review_links:
                create_marc_field(record, {'tag': '655', 'ind1': ' ', 'ind2': '7',
                                               'subfields': {'a': ['Rezension'],
                                                             '0': ['(DE-588)4049712-4', '(DE-627)106186019'],
                                                             '2': ['gnd-content']}})
                review_links.remove(url)
            form_tag = record.find('{http://www.loc.gov/MARC21/slim}datafield[@tag="655"][@ind2="7"]'
                                   '/{http://www.loc.gov/MARC21/slim}subfield[@code="a"]')
            is_review = False
            if form_tag is None:
                review_regex = r'([£$€](?:\s+)?\d+)|(\d+(?:\s+)?(?:([Pp]p)|(S\.)))|(\s+(?:([Pp]p)|(S))[.\s]\s*[\dXIVLCxivlc]+\b)|(\s+[Pp]\.\s*[\dXIVLCxivlc]+\b)|(\d+(?:\s+)?€)|(\s+((pagg?)|(Pagg?))\.\s+[\dXIVLCxivlc]+\b)'
                if re.search(regexISBN, title):
                    create_marc_field(record, {'tag': '655', 'ind1': ' ', 'ind2': '7',
                                               'subfields': {'a': ['Rezension'], '0': ['(DE-588)4049712-4', '(DE-627)106186019'], '2': ['gnd-content']}})
                    is_review = True
                    print('created tag Rezension for url', url)
                elif re.search(review_regex, title):
                    if not (re.search(r'S\.\s*I\.', title)):
                        print(re.search(review_regex, title))
                        print(title)
                        print('tagged nbrk Rezension', url)
                        create_marc_field(record, {'tag': '935', 'ind1': ' ', 'ind2': ' ',
                                                   'subfields': {'a': ['nbrk'], '2': ['LOK']}})
                        create_marc_field(record, {'tag': '655', 'ind1': ' ', 'ind2': '7',
                                                   'subfields': {'a': ['Rezension'],
                                                                 '0': ['(DE-588)4049712-4', '(DE-627)106186019'],
                                                                 '2': ['gnd-content']}})
                        is_review = True

            elif form_tag.text == "Rezension":
                is_review = True
            records_found, review_title = create_review_link(record)
            if review_title and not is_review:
                is_review = True
                create_marc_field(record, {'tag': '655', 'ind1': ' ', 'ind2': '7',
                                           'subfields': {'a': ['Rezension'],
                                                         '0': ['(DE-588)4049712-4', '(DE-627)106186019'],
                                                         '2': ['gnd-content']}})
            if is_review:
                if review_title:
                    if len(title) < 60:
                        create_marc_field(record, {'tag': '246', 'ind1': '1', 'ind2': ' ',
                                                   'subfields': {'a': [review_title], 'i': ['Fingierter Rezensionstitel: ']}})
                if not records_found:
                    abstract_tag = record.find \
                        ('{http://www.loc.gov/MARC21/slim}datafield[@tag="520"]/{http://www.loc.gov/MARC21/slim}subfield[@code="a"]')
                    if abstract_tag is not None:
                        abstract = abstract_tag.text
                    else:
                        abstract = ""
                    isbn_list = list(set(re.findall(regexISBN, title) + re.findall(regexISBN, abstract))) #ursprünglich (fehlerhaft): [^\d]((?:\d{3}[\- ])?(?:\d[\-]?[\s]?){8,9}[\dXx])
                    for isbn in isbn_list:
                        isbn = re.sub(r'[\- ]', '', isbn)
                        records_found = records_found | search_publication_with_isbn(isbn) #vorher ohne records_found |
                all_ppns = [record for record in records_found]
                ppn_nr = 0
                comment = 'Rezensionsverknüpfungen ['
                for ppn in all_ppns:
                    ppns_linked.append(ppn)
                    create_marc_field(record, {'tag': '787', 'ind1': '0', 'ind2': '8',
                                               'subfields': {'i': ['Rezension von'], 'w': ['(DE-627)' + ppn]}})
                    review_links_created += 1
                    if ppn_nr == 0:
                        # create_marc_field(record, {'tag': '935', 'ind1': ' ', 'ind2': ' ', 'subfields': {'a': ['aurl'], '2': ['LOK']}})
                        comment += 'PPN ' + ppn
                    else:
                        comment += ' | PPN ' + ppn
                    ppn_nr += 1
                comment += '] maschinell zugeordnet'
                if all_ppns:
                    create_marc_field(record, {'tag': '887', 'ind1': ' ', 'ind2': ' ',
                                               'subfields': {'a': [comment], '2': ['ixzom']}})
            language_tag = record.find('{http://www.loc.gov/MARC21/slim}datafield[@tag="041"]')
            if language_tag is None:
                detected_lang = detect_title(title)
                if detected_lang in conf_langs:
                    if "[Rezension von: " not in title and "(Book Review)" not in title:
                        pass
                        # print('language', detected_lang, 'will be set for title', title)
                    create_marc_field(record, {'tag': '041', 'ind1': ' ', 'ind2': ' ',
                                               'subfields': {'a': [detected_lang]}})
                else:
                    if "[Rezension von: " not in title and "(Book Review)" not in title:
                        pass
                        # print("no language:", title)
                    if default_lang != "":
                        create_marc_field(record, {'tag': '041', 'ind1': ' ', 'ind2': ' ',
                                                   'subfields': {'a': [default_lang]}})
                    else:
                        create_marc_field(record, {'tag': '935', 'ind1': ' ', 'ind2': ' ',
                                                   'subfields': {'a': ['nbrk'], '2': ['LOK']}})
            else:
                if language_tag.find('{http://www.loc.gov/MARC21/slim}subfield[@code="a"]').text not in all_languages:
                    all_languages.append(language_tag.find('{http://www.loc.gov/MARC21/slim}subfield[@code="a"]').text)
                if language_tag.find('{http://www.loc.gov/MARC21/slim}subfield[@code="a"]').text not in conf_langs:
                    detected_lang = detect_title(title)
                    if detected_lang in conf_langs and "[Rezension von: " not in title:
                        language_tag.find('{http://www.loc.gov/MARC21/slim}subfield[@code="a"]').text = detected_lang
                    else:

                        if default_lang != "":
                            language_tag.find('{http://www.loc.gov/MARC21/slim}subfield[@code="a"]').text = default_lang
                        else:
                            print("no language:", title)
                            record.remove(record.find('{http://www.loc.gov/MARC21/slim}datafield[@tag="041"]'))
                            create_marc_field(record, {'tag': '935', 'ind1': ' ', 'ind2': ' ',
                                                       'subfields': {'a': ['nbrk'], '2': ['LOK']}})
                elif "[Rezension von: " in title:
                    language_tag.find('{http://www.loc.gov/MARC21/slim}subfield[@code="a"]').text = default_lang
            if is_review:
                record.remove(record.find('{http://www.loc.gov/MARC21/slim}datafield[@tag="041"]'))
                create_marc_field(record, {'tag': '041', 'ind1': ' ', 'ind2': ' ',
                                           'subfields': {'a': [default_lang]}})
            if url in jstor_dict:
                if jstor_dict[url] in languages_dict:
                    if len(languages_dict[jstor_dict[url]]) == 3:
                        record.remove(record.find('{http://www.loc.gov/MARC21/slim}datafield[@tag="041"]'))
                        create_marc_field(record, {'tag': '041', 'ind1': ' ', 'ind2': ' ',
                                                   'subfields': {'a': [languages_dict[jstor_dict[url]]]}})
                    else:
                        create_marc_field(record, {'tag': '041', 'ind1': ' ', 'ind2': ' ',
                                                       'subfields': {'a': languages_dict[jstor_dict[url]].split('; ')}})
                        # print('added jstor languages:', url, languages_dict[jstor_dict[url]])
            check_abstract(record)
            journal_link_tag = record.find('{http://www.loc.gov/MARC21/slim}datafield[@tag="773"]'
                                            '/{http://www.loc.gov/MARC21/slim}subfield[@code="t"]')
            if journal_link_tag is not None:
                journal_link_tag.text = journal_link_tag.text.strip('+')
                journal_link_tag.text = re.sub(r'(^.+)_\d+$', r'\1', journal_link_tag.text)
                journal_name_tag = record.find('{http://www.loc.gov/MARC21/slim}datafield[@tag="JOU"]'
                                               '/{http://www.loc.gov/MARC21/slim}subfield[@code="a"]')
                journal_name_tag.text = journal_link_tag.text
            if jstor_dict and is_jstor_data == 'false':
                if url in jstor_dict:
                    total_jstor_links += 1
                    create_marc_field(record, {'tag': '866', 'ind1': ' ', 'ind2': ' ',
                                               'subfields': {'x': ['JSTOR#' + jstor_dict[url]], '2': ['LOK']}})
                else:
                    total_jstor_fails += 1
            if append_to_postprocess:
                post_process_root.append(record)
                post_process_nr += 1
            else:
                proper_root.append(record)
                proper_nr += 1
            if len(record.findall('{http://www.loc.gov/MARC21/slim}datafield[@tag="655"][@ind2="7"]'
                                   '/{http://www.loc.gov/MARC21/slim}subfield[@code="a"]')) > 1:
                for form_tag in record.findall('{http://www.loc.gov/MARC21/slim}datafield[@tag="655"][@ind2="7"]'
                                       '/{http://www.loc.gov/MARC21/slim}subfield[@code="a"]'):
                    print(url)
                    record.remove(form_tag)

    if links_to_add_nr > 0:
        with open(MISSING_LINKS + zeder_id + '_links_to_add.json', 'w', newline='') as links_to_add_file:
            json.dump(links_to_add, links_to_add_file)
    os.remove(MISSING_LINKS + zeder_id + '.json')
    if ppns_linked:
        with open(zeder_id + '_ppns_linked.json', 'w') as ppns_linked_file:
            json.dump(ppns_linked, ppns_linked_file)
    proper_tree.write(zeder_id + '_proper.xml', encoding='utf-8', xml_declaration=True)
    if post_process_nr > 0:
        post_process_tree.write(zeder_id + '_post_process.xml', encoding='utf-8', xml_declaration=True)
    with open('statistics_' + zeder_id + '.txt', 'w', encoding='utf-8') as statistics_file:
        if present_record_list:
            if len(present_record_list) > 10:
                print(str(present_record_list))
                input('Zur Kenntnisnahme: Die oben genannten Dubletten wurden nicht erkannt')
                print('Die folgenden Dubletten wurden erkannt: ' + str(recognized_present_record_list))
            elif len(present_record_list) > 0:
                input('Die folgenden Dubletten wurden nicht erkannt: ' + str(present_record_list))
                print('Die folgenden Dubletten wurden erkannt: ' + str(recognized_present_record_list))
            statistics_file.write('missing doublets:' + str(present_record_list) + '\n')
        missing_Volumes = sorted(list(set([volume for volume in volume_list if volume not in found_volume_list])))
        if Volumes_to_catalogue != [1000, 3000] and missing_Volumes:
            input('Zur Kenntnisnahme: Die Bände ' + str(missing_Volumes) + ' fehlen')
            statistics_file.write('Zur Kenntnisnahme: Die Bände ' + str(missing_Volumes) + ' fehlen' + '\n')
        url = 'https://sru.bsz-bw.de/cbsx?version=1.1&operation=searchRetrieve&query=pica.ppn%3D{0}&maximumRecords=10&recordSchema=picaxml&x-username={1}&x-password={2}'.format(source_ppn, username, password)
        print(url)
        xml_data = urllib.request.urlopen(url)
        xml_soup = BeautifulSoup(xml_data, features='lxml')
        for record in xml_soup.find_all('record'):
            journal_title = record.find('datafield', tag='021A').find('subfield', code='a').text
            if record.find('datafield', tag='002@').find('subfield', code='0').text == 'Obv':
                input('Der Titel lautet: ' + journal_title + ', es handelt sich um eine Online-Aufnahme')
                statistics_file.write('Der Titel lautet: ' + journal_title + ', es handelt sich um eine Online-Aufnahme' + '\n')
            else:
                input('Der Titel lautet: ' + journal_title + ', es handelt sich NICHT um eine Online-Aufnahme')
                statistics_file.write(
                    'Der Titel lautet: ' + journal_title + ', es handelt sich NICHT um eine Online-Aufnahme' + '\n')
        statistics_file.write('total number of records harvested:' + str(record_nr) + '\n')
        statistics_file.write('proper:' + str(proper_nr) + '\n')
        statistics_file.write('post_process:' + str(post_process_nr) + '\n')
        statistics_file.write('discarded:' + str(discarded_nr + discarded_by_volume_nr) + '\n')
        statistics_file.write('discarded by volume:' + str(discarded_by_volume_nr) + '\n')
        statistics_file.write('duplicate records in result:' + str(deduplicate_nr) + '\n')
        statistics_file.write('Volumes discarded:' + str(sorted(Volumes_discarded)) + '\n')
        statistics_file.write('total jstor fails:' + str(total_jstor_fails) + '\n')
        statistics_file.write('total jstor links:' + str(total_jstor_links) + '\n')
        statistics_file.write('review links created:' + str(review_links_created) + '\n')
        statistics_file.write('found missing links to add:' + str(links_to_add_nr) + '\n')
        statistics_file.write('excluded titles:' + str(excluded_titles) + '\n')
        statistics_file.write('responsibles corrected:' + str(responsibles_corrected) + '\n')
        statistics_file.write('personal titles corrected:' + str(personal_titles) + '\n')
        statistics_file.write('review links:' + str(review_links) + '\n')
        statistics_file.write('languages:' + str(review_links) + '\n')
        print('total number of records harvested:', record_nr)
        print('proper:', proper_nr)
        print('post_process:', post_process_nr)
        print('discarded:', discarded_nr + discarded_by_volume_nr)
        print('discarded by volume:', discarded_by_volume_nr)
        print('duplicate records in result:', deduplicate_nr)
        print('Volumes discarded:', sorted(Volumes_discarded))
        print('total jstor fails:', total_jstor_fails)
        print('total jstor links:', total_jstor_links)
        print('review links created:', review_links_created)
        print('found missing links to add:', links_to_add_nr)
        print('excluded titles:', excluded_titles)
        print('responsibles corrected:', responsibles_corrected)
        print('personal titles corrected:', personal_titles)
        print('review links;', review_links)
        print('languages:', all_languages)


# announcement, books and media received
