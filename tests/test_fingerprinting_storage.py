#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#  SolidBlue III - Open source data manager.
#
#  __author__ = "Fabrizio Giudici"
#  __copyright__ = "Copyright © 2020 by Fabrizio Giudici"
#  __credits__ = ["Fabrizio Giudici"]
#  __license__ = "Apache v2"
#  __version__ = "1.0-ALPHA-1"
#  __maintainer__ = "Fabrizio Giudici"
#  __email__ = "fabrizio.giudici@tidalwave.it"
#  __status__ = "Prototype"

import subprocess
import tempfile
import unittest
from datetime import datetime
from os import mkdir

from fingerprinting import FingerprintingStorage


class TestFingerprintStorage(unittest.TestCase):
    under_test = None
    next_id = None
    database_folder = None

    #
    #
    #
    def test_database_creation(self):
        self.__setup_fixture()

        self.under_test.open()
        self.under_test.close()

        expected = """PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE files (
                            id TEXT PRIMARY KEY,
                            path TEXT NOT NULL
                            );
CREATE TABLE fingerprints (
                            id TEXT PRIMARY KEY,
                            name TEXT NOT NULL,
                            file_id TEXT NOT NULL,
                            algorithm TEXT NOT NULL,
                            fingerprint TEXT NOT NULL,
                            timestamp INTEGER NOT NULL
                            );
CREATE TABLE backups(
                            id TEXT PRIMARY KEY,
                            base_path TEXT NOT NULL,
                            label TEXT NOT NULL UNIQUE,
                            volume_id TEXT NOT NULL UNIQUE,
                            encrypted INTEGER NOT NULL,
                            creation_date INTEGER NOT NULL,
                            registration_date INTEGER NOT NULL,
                            latest_check_date
                            );
CREATE TABLE backup_files(
                            id TEXT PRIMARY KEY,
                            backup_id TEXT NOT NULL,
                            file_id TEXT NOT NULL,
                            path TEXT NOT NULL
                            );
CREATE INDEX files__path ON files (path);
CREATE INDEX fingerprints__name ON fingerprints (name);
CREATE INDEX fingerprints__file_id ON fingerprints (file_id);
CREATE INDEX fingerprints__timestamp ON fingerprints (timestamp);
CREATE INDEX backups__volume_id ON backups (volume_id);
COMMIT;
"""
        actual = self.__database_dump('.dump')
        self.assertEqual(expected, actual)

    #
    #
    #
    def test_add_path(self):
        self.__setup_fixture()

        self.under_test.open()
        self.under_test.add_path(self.__mock_generate_id(), '/the/path', commit=True)
        self.under_test.close()

        expected = """INSERT INTO "table" VALUES('00000000-0000-0000-0000-000000001001','/the/path');
"""
        actual = self.__database_dump('select * from files;')
        self.assertEqual(expected, actual)

    #
    #
    #
    def test_add_backup(self):
        self.__setup_fixture()

        self.under_test.open()
        creation_date = datetime(2020, 10, 1, 2, 3, 4)
        registration_date = datetime(2021, 11, 5, 6, 7, 8)
        self.under_test.add_backup('/the/path', 'label', 'volume id', creation_date, registration_date, True, commit=True)
        self.under_test.close()

        expected = """INSERT INTO "table" VALUES('00000000-0000-0000-0000-000000001001','/the/path','label','volume id',1,'2020-10-01 02:03:04','2021-11-05 06:07:08',NULL);
"""
        actual = self.__database_dump('select * from backups;')
        self.assertEqual(expected, actual)

    #
    #
    #
    def test_add_fingerprint(self):
        self.__setup_fixture()

        self.under_test.open()
        file_id = '00000000-0000-0000-0000-000000000001'
        timestamp = datetime(2020, 10, 1, 2, 3, 4)
        self.under_test.add_fingerprint(file_id, 'file_name', 'md5', '114dfaaa497f81c463dcc690db527a0d', timestamp, commit=True)
        self.under_test.close()

        expected = """INSERT INTO "table" VALUES('00000000-0000-0000-0000-000000001001','file_name','00000000-0000-0000-0000-000000000001','md5','114dfaaa497f81c463dcc690db527a0d','2020-10-01 02:03:04');
"""
        actual = self.__database_dump('select * from fingerprints;')
        self.assertEqual(expected, actual)

    #
    #
    #
    def __database_dump(self, dump) -> str:
        args = ['sqlite3', f'{self.database_folder}/fingerprints.db']
        process = subprocess.Popen(args, stdin=subprocess.PIPE, text=True, encoding='latin-1')
        process.communicate(f'.output {self.database_folder}/dump.sql\n'
                            f'.mode insert\n'
                            f'{dump}\n'
                            f'.exit')

        with open(f'{self.database_folder}/dump.sql', 'rt') as f:
            actual = f.read()

        return actual

    #
    # Set up the test fixture.
    #
    def __setup_fixture(self):
        self.next_id = 1000
        self.database_folder = tempfile.TemporaryDirectory().name
        mkdir(self.database_folder)
        self.__debug(f'test database folder: {self.database_folder}')
        self.under_test = FingerprintingStorage(database_folder=self.database_folder,
                                                id_generator=self.__mock_generate_id,
                                                debug_function=self.__debug)

    #
    # Various mock methods.
    #
    def __mock_generate_id(self) -> str:
        self.next_id += 1
        return f'00000000-0000-0000-0000-00000000{self.next_id}'

    #
    #
    #
    def __debug(self, message: str):
        print(f'>>>> {message}', flush=True)
        pass


if __name__ == '__main__':
    unittest.main()
