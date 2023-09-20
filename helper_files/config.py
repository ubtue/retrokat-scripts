import json

base_dir = __file__[:__file__.rfind("/h")]

with open(base_dir+"/personal_config.json", "r") as info_file:
    infos = json.load(info_file)
    SHARED_FOLDER = infos["path_to_shared_folder"]
    NAME_BENU = infos["name_on_benu"]
    structure_json_filename = infos["path_to_structure_file_of_shared_folder"]

with open(structure_json_filename) as structure_json:
    structure = json.load(structure_json)
    MISSING_LINKS = SHARED_FOLDER + structure["folder_for_missing_links"]
    JSTOR_JSON = SHARED_FOLDER + structure["folder_for_jstor_json"]
    PUBLISHER_JSON = SHARED_FOLDER + structure["folder_for_publisher_json"]
    JSTOR_MAPPING = SHARED_FOLDER + structure["folder_for_jstor_mapping"]
    JSTOR_CSV = SHARED_FOLDER + structure["folder_for_jstor_csv"]
    RESULT_FILES = SHARED_FOLDER + structure["folder_for_result_files"]
    FINAL_FILES = SHARED_FOLDER + structure["folder_for_final_files"]
    K10PLUS = SHARED_FOLDER + structure["file_for_k10plus"]
    BASE_FOLDER = SHARED_FOLDER + structure["landing_folder"]
    EXCLUDE_JSON = SHARED_FOLDER + structure["exclude_json"]
    PRESENT_RECORDS_JSON = SHARED_FOLDER + structure["present_records_json"]
    CONFIG_JSON = SHARED_FOLDER + structure["config_json"]
    UPLOAD_PRODUCTIVE = SHARED_FOLDER + structure["folder_for_productive_db"]
    PRODUCTIVE_FILES_RENAMED_JSON = SHARED_FOLDER + structure["productive_db_files_renamed_json"]
    UPLOAD_TEST = SHARED_FOLDER + structure["folder_for_test_db"]
    TEST_FILES_RENAMED_JSON = SHARED_FOLDER + structure["test_db_files_renamed_json"]
    UPLOAD_ADDITIONAL = SHARED_FOLDER + structure["folder_for_additional"]
    PROPER_FILES = SHARED_FOLDER + structure["folder_for_proper_files"]

