#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#  SolidBlue III - Open source data manager.
#
#  __author__ = "Fabrizio Giudici"
#  __copyright__ = "Copyright © 2020 by Fabrizio Giudici"
#  __credits__ = ["Fabrizio Giudici"]
#  __license__ = "Apache v2"
#  __version__ = "1.0-ALPHA-3-SNAPSHOT"
#  __maintainer__ = "Fabrizio Giudici"
#  __email__ = "fabrizio.giudici@tidalwave.it"
#  __status__ = "Prototype"

import os
from collections import namedtuple
from pathlib import Path

import yaml


class Config:
    script_path = Path(os.path.realpath(__file__)).parent

    @staticmethod
    def home_folder() -> str:
        return os.getenv("HOME")

    @staticmethod
    def app_folder_path() -> str:
        return f'{Config.home_folder()}/Library/Application Support/SolidBlue'

    @staticmethod
    def resource(resource: str) -> str:
        return f'{Config.script_path}/resources/{resource}'

    @staticmethod
    def config() -> dict:
        with open(f'{Config.app_folder_path()}/config.yaml', 'r') as stream:
            return yaml.safe_load(stream)

    @staticmethod
    def working_folder() -> str:
        return '/tmp/SolidBlue'  # FIXME

    @staticmethod
    def database_folder() -> str:
        return f'{Config.app_folder_path()}/db'

    Scan = namedtuple('Scan', 'label, icon, path, filter')

    @staticmethod
    def scan_config() -> [Scan]:
        result = {}

        for scan in Config.config()['scan']:
            key = list(scan.keys())[0]
            dict = scan[key]
            path = dict['path']
            dict['path'] = path if path.startswith('/') else f'{Config.home_folder()}/{path}'
            result[key] = Config.Scan(**dict)

        return result

    PushFiles = namedtuple('PushFiles', 'label, icon, server, extra_rsync_flags, items')
    PushFilesItem = namedtuple('PushFilesItem', 'source, target, extra_rsync_flags')

    @staticmethod
    def push_files_config() -> [PushFiles]:
        def to_named_tuple_dict(records: list[dict], tuple_clz) -> dict[str, namedtuple]:
            result = {}

            for record in records:
                key = list(record.keys())[0]
                result[key] = tuple_clz(**fixed_fields(record[key], tuple_clz._fields))

            return result

        def fixed_fields(field_dict: dict, fields, names_of_fields_with_path=['source']) -> dict:
            for field_name in field_dict.keys():
                if field_name in names_of_fields_with_path:
                    path = field_dict[field_name]
                    field_dict[field_name] = path if path.startswith('/') else f'{Config.home_folder()}/{path}'
                elif field_name == 'items':
                    field_dict[field_name] = to_named_tuple_dict(field_dict[field_name], Config.PushFilesItem)

            for field in fields:
                if field not in field_dict:
                    if field == 'extra_rsync_flags':
                        field_dict[field] = []
                    else:
                        field_dict[field] = ''

            return field_dict

        return to_named_tuple_dict(Config.config()['push-files'], Config.PushFiles)

    @staticmethod
    def encrypted_backup_key_file() -> str:
        return Config.config()['backup']['keyfile']

    @staticmethod
    def encrypted_volumes_mount_folder() -> str:
        return f'{Config.app_folder_path()}/var/EncryptedBackups'

    @staticmethod
    def veracrypt_algorithms() -> dict:
        return {
            'AES': 'aes',
            'Serpent': 'serpent',
            'Twofish': 'twofish',
            'AES(Twofish)': 'aes-twofish',
            'AES(Twofish(Serpent))': 'aes-twofish-serpent',
            'Serpent(AES)': 'serpent-aes',
            'Serpent(Twofish(AES))': 'serpent-twofish-aes',
            'Twofish(Serpent)': 'twofish-serpent'
        }

    @staticmethod
    def veracrypt_default_algorithm() -> str:
        return 'AES(Twofish(Serpent))'

    @staticmethod
    def veracrypt_hash_algorithms() -> dict:
        return {
            'SHA 256': 'sha-256',
            'SHA 512': 'sha-512',
            'Whirlpool': 'whirlpool',
            'RIPEMD 160': 'ripemd-160'
        }

    @staticmethod
    def veracrypt_default_hash_algorithm() -> str:
        return 'Whirlpool'


if __name__ == '__main__':
    print(f'Scan config: {Config.scan_config()}')
    print(f'Push media config: {Config.push_files_config()}')
