import os
import xml.etree.ElementTree as ElementTree


def merge_journal_records():
    ElementTree.register_namespace('', "http://www.loc.gov/MARC21/slim")
    complete_tree = ElementTree.parse('helper_files/marcxml_empty.xml')
    complete_root = complete_tree.getroot()
    zeder_id = input('Bitte geben sie die ZEDER-ID der zusammenzuführenden Records ein: ')
    record_nr = 0
    for file in os.listdir():
        if (zeder_id + '_' in file) and ('.xml' in file):
            print(file)
            tree = ElementTree.parse(file)
            root = tree.getroot()
            records = root.findall('.//{http://www.loc.gov/MARC21/slim}record')
            records = [record for record in records]
            for record in records:
                record_nr += 1
                if record_nr % 500 == 0:
                    print(record_nr)
                complete_root.append(record)
    print(record_nr)
    complete_tree.write(zeder_id + '_proper.xml', encoding='utf-8', xml_declaration=True)
    if zeder_id + '_post_process.xml' in os.listdir():
        os.remove(zeder_id + '_post_process.xml')


if __name__ == '__main__':
    merge_journal_records()
