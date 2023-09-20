import os
from shutil import copy2
from time import strftime
from helper_files.config import NAME_BENU, UPLOAD_ADDITIONAL

BENU_username = NAME_BENU
move_to_scp_server = ''
commands = ''
timestamp = strftime('%Y%m%d')
total_record_number = 0
file_nr = 0
file_nr_for_filename = 4

for file in os.listdir('review_information'):
    if timestamp in file:
        copy2('review_information/' + file, UPLOAD_ADDITIONAL + file)
        move_to_scp_server += '\npython3 upload_to_bsz_ftp_server.py ' + file + ' /pub/UBTuebingen_Sonstiges/'

commands = 'Dateien auf BENU verschieben & von BENU auf den FTP-Server legen:' \
           '\nW:\ncd "'+ UPLOAD_ADDITIONAL + \
           '"\nscp ' + timestamp + '_*.csv {0}@benu.ub.uni-tuebingen.de:/home/{0}/bsz' \
           '\n\nssh {0}@benu.ub.uni-tuebingen.de\ncd /home/{0}/bsz' + move_to_scp_server
print(commands.format(BENU_username))
