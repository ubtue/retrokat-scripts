import json
from helper_files.config import K10PLUS


def get_credentials():
    with open(K10PLUS, "r") as credential_file:
        credential_dict = json.load(credential_file)
        username = credential_dict["username"]
        password = credential_dict["password"]
    return username, password
