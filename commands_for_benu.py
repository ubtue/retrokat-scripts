import os
import re
from shutil import copy2
from time import strftime
import json
import xml.etree.ElementTree as ElementTree
from termcolor import colored
from helper_files.config import NAME_BENU, RESULT_FILES, SHARED_FOLDER


BENU_username = NAME_BENU
commands = ''

if __name__ == '__main__':
    zeder_id = input('Bitte geben Sie die ZEDER-ID ein: ')

    change_to_shared_folder = ''
    if re.findall('^[A-Z]:', SHARED_FOLDER):
        change_to_shared_folder = SHARED_FOLDER[:2] + '\n' +\
            'cd '+ SHARED_FOLDER[2:]
    else:
        change_to_shared_folder = 'cd ' + SHARED_FOLDER

    commands = 'ZEDER-Daten auf benu importieren: \n'\
        '\nssh {0}@benu.ub.uni-tuebingen.de\ncd /tmp\n' \
        'cp /usr/local/zotero-enhancement-maps/{0}_retrokat/zotero-enhancement-maps/zotero_harvester.conf '\
        '/tmp/zotero_harvester_{0}.conf\n'\
        'zeder_to_zotero_importer /tmp/zotero_harvester_{0}.conf IMPORT IxTheo ' \
        + zeder_id + ' \"NAME,ONLINE_PPN,ONLINE_ISSN,PRINT_PPN,PRINT_ISSN,UPLOAD_OPERATION,' \
        'LICENSE,PERSONALIZED_AUTHORS,EXPECTED_LANGUAGES,ENTRY_POINT_URL,UPDATE_WINDOW,SELECTIVE_EVALUATION,' \
        'SSGN,ADDITIONAL_SELECTORS\"'\
        '\n\nNun muss die Datei /tmp/zotero_test_{0}.conf angepasst werden (siehe Anleitungen).\n' \
        'Dabei Änderung des Titels zu ZEDER-ID\n' \
        'vim /tmp/zotero_harvester_{0}.conf\n'\
        '\nHarvesten der Daten:'\
        '\n/usr/local/bin/zotero_harvester \"--min-log-level=DEBUG\" \"--force-downloads\" '\
        '\"--output-directory=/tmp/XML_' + zeder_id + '\" \"--output-filename=3635.xml\" '\
        '\"/tmp/zotero_harvester_{0}.conf\" \"JOURNAL\" \"' + zeder_id + '\"'\
        '\nexit\n' + change_to_shared_folder +\
        '\nscp {0}@benu.ub.uni-tuebingen.de:/tmp/XML_' + zeder_id + '/ixtheo/' + zeder_id +\
               '.xml \"' + RESULT_FILES + zeder_id + '.xml\"'


    print(commands.format(BENU_username))
