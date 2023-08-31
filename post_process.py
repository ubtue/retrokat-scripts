import os
import helper_files.add_missing_links as add_missing_links
from helper_files.transform_MARCXML import transform, check_and_split_in_issues
import json
from helper_files.create_jstor_link_dict import get_jstor_links
from helper_files.get_review_information_from_jstor_data import get_review_information
from helper_files.config import CONFIG_JSON, EXCLUDE_JSON

if __name__ == '__main__':
    zeder_id = input('Bitte geben Sie die ZEDER-ID ein: ')
    conf_dict = {}
    conf_available = False
    if os.path.isfile(CONFIG_JSON):
        with open(CONFIG_JSON, 'r') as conf_file:
            conf_dict = json.load(conf_file)
            if zeder_id in conf_dict:
                conf_available = True
                if 'eppn' not in conf_dict[zeder_id]:
                    conf_dict[zeder_id]['eppn'] = input('Bitte geben Sie die ePPN ein: ')
                if 'lang' not in conf_dict[zeder_id]:
                    conf_dict[zeder_id]['lang'] = input('Bitte geben Sie die Default-Sprache ein: ')
                if 'conf_langs' not in conf_dict[zeder_id]:
                    langs = input('Bitte geben Sie die zulässigen Sprachen ein: ')
                    lang_dict = json.loads(langs)
                    conf_dict[zeder_id]['conf_langs'] = lang_dict
                if 'add_jstor_data_from_file' not in conf_dict[zeder_id]:
                    add_jstor_data = input('Bitte geben Sie an, aus welcher Datei Daten übernommen werden sollen: ')
                    conf_dict[zeder_id]['add_jstor_data_from_file'] = add_jstor_data
                if 'is_jstor' not in conf_dict[zeder_id]:
                    is_jstor_data = input('Bitte geben Sie an, ob es sich um JSTOR-Daten handelt: ')
                    conf_dict[zeder_id]['is_jstor'] = is_jstor_data
                if 'embargo' not in conf_dict[zeder_id]:
                    embargo = int(input('Bitte geben Sie die Dauer des Embargos an: '))
                    conf_dict[zeder_id]['embargo'] = embargo
                with open(CONFIG_JSON, 'w') as conf_file:
                    json.dump(conf_dict, conf_file)
    # if zeder_id + '.json' not in os.listdir(JSTOR_MAPPINGS):
    get_jstor_links(zeder_id)
    record_nr = check_and_split_in_issues(zeder_id, conf_available)
    if not conf_available:
        exclude = input('Bitte geben Sie die Liste auszuschließender Titel ein: ')
        exclude = json.loads(exclude.replace("'", '"'))
        period = []
        period_completed = False
        while not period_completed:
            start_year = int(input('Bitte geben Sie das erste Jahr der Retrokatalogisierung ein: '))
            end_year = int(input('Bitte geben Sie das letzte Jahr der Retrokatalogisierung ein: '))
            period.append(start_year)
            period.append(end_year)
            if input('Wollen Sie weitere Zeiträume hinzufügen? ') == 'n':
                period_completed = True
        eppn = input('Bitte geben Sie die ePPN ein: ')
        default_lang = input('Bitte geben Sie die Default-Sprache ein: ')
        langs = input('Bitte geben Sie die zulässigen Sprachen ein: ')
        conf_langs = json.loads(langs)
        add_jstor_data = input('Bitte geben Sie an, aus welcher Datei Daten übernommen werden sollen: ')
        embargo = int(input('Bitte geben Sie die Dauer des Embargos an: '))
        conf_dict[zeder_id] = {'exclude': exclude, 'period': period, 'eppn': eppn, 'lang': default_lang, 'conf_langs': conf_langs, 'add_jstor_data_from_file': add_jstor_data, 'embargo': embargo}
        if 'is_jstor' not in conf_dict[zeder_id]:
            is_jstor_data = input('Bitte geben Sie an, ob es sich um JSTOR-Daten handelt: ')
            conf_dict[zeder_id]['is_jstor'] = is_jstor_data
        if input('Wollen Sie diese Konfigurationsangaben speichern (j/n)') == 'j':
            with open(CONFIG_JSON, 'w') as conf_file:
                json.dump(conf_dict, conf_file)
    period = conf_dict[zeder_id]['period']
    eppn = conf_dict[zeder_id]['eppn']
    add_missing_links.get_records_with_missing_links(conf_dict[zeder_id]['eppn'], zeder_id)
    with open(EXCLUDE_JSON, 'r') as exclusion_file:
        exclude_everywhere = json.load(exclusion_file)
    exclude = conf_dict[zeder_id]['exclude'] + exclude_everywhere
    default_lang = conf_dict[zeder_id]['lang']
    conf_langs = conf_dict[zeder_id]['conf_langs']
    add_jstor_data = conf_dict[zeder_id]['add_jstor_data_from_file']
    is_jstor_data = conf_dict[zeder_id]['is_jstor']
    embargo = conf_dict[zeder_id]['embargo']
    if add_jstor_data:
        get_review_information(zeder_id, add_jstor_data)
    check_for_duplicates = None
    if 'check_for_duplicates' in conf_dict[zeder_id]:
        check_for_duplicates = conf_dict[zeder_id]['check_for_duplicates']
    transform(zeder_id, exclude, period, record_nr, default_lang, conf_langs, is_jstor_data, embargo, check_for_duplicates)
