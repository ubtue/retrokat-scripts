import os
from shutil import copy2
from time import strftime
import json
import xml.etree.ElementTree as ElementTree
from termcolor import colored
from helper_files.config import NAME_BENU, FINAL_FILES, UPLOAD_PRODUCTIVE, PRODUCTIVE_FILES_RENAMED_JSON


BENU_username = NAME_BENU
move_to_scp_server = ''
commands = ''
timestamp = strftime('%y%m%d')
total_record_number = 0
file_nr = 0
file_nr_for_filename = 4
with open(PRODUCTIVE_FILES_RENAMED_JSON, 'r') as renamed_files_file:
    renamed_files = json.load(renamed_files_file)
    file_nr_for_filename += len(
        [renamed_files[filename] for filename in renamed_files if timestamp + '_' in renamed_files[filename]])
    for file in os.listdir(FINAL_FILES):
        if '.xml' not in file:
            print(file)
            continue
        if (file not in renamed_files) or (timestamp in renamed_files[file]):
            ElementTree.register_namespace('', "http://www.loc.gov/MARC21/slim")
            result_tree = ElementTree.parse(FINAL_FILES + file)
            result_root = result_tree.getroot()
            records = result_root.findall('.//{http://www.loc.gov/MARC21/slim}record')
            total_record_number += len(records)
            if total_record_number > 20000:
                print(colored('total record number exceeds maximum capazity of ftp-server.', 'red'))
                continue
            file_nr_for_filename += 1
            file_nr += 1
            if file in renamed_files:
                if timestamp in renamed_files[file]:
                    new_filename_for_ftp = renamed_files[file]
            else:
                new_filename_for_ftp = 'ixtheo_zotero_' + timestamp + '_' + str(file_nr_for_filename).zfill(3) + '.xml'
            copy2(FINAL_FILES + file, UPLOAD_PRODUCTIVE + new_filename_for_ftp)
            renamed_files[file] = new_filename_for_ftp
            move_to_scp_server += '\npython3 upload_to_bsz_ftp_server.py ' + new_filename_for_ftp + ' /pub/UBTuebingen_Default/'

with open(PRODUCTIVE_FILES_RENAMED_JSON, 'w') as renamed_files_file:
    json.dump(renamed_files, renamed_files_file)

print(str(file_nr), 'files renamed and moved to folder')
print(total_record_number, 'records moved to folder')

commands = 'Dateien auf BENU verschieben & von BENU auf den FTP-Server legen:' \
           '\nW:\ncd \"' + UPLOAD_PRODUCTIVE + '\"' \
           '\nscp ixtheo_zotero_' + timestamp + '_*.xml {0}@benu.ub.uni-tuebingen.de:/home/{0}/bsz' \
           '\n\nssh {0}@benu.ub.uni-tuebingen.de\ncd /home/{0}/bsz' + move_to_scp_server
print(commands.format(BENU_username))
