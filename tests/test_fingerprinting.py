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

import unittest
from datetime import datetime
from pathlib import Path

from fingerprinting import FingerprintingControl, FingerprintingPresentation, FingerprintingStorageStats


#
#
#
class MockStorage:
    def __init__(self):
        self.files_map = {}
        self.files = []
        self.fingerprints_map = {}
        self.attributes_map = {}
        self.attributes_done = []
        self.paths_done = []
        self.fingerprints_done = []

        class MockStorageStats(FingerprintingStorageStats):
            def stop(self):
                self.processed_file_count = 4
                self.plain_io_reads = 1234567894
                self.mmap_reads = 359665044
                self.elapsed = 59

        self.stats = MockStorageStats()

        def register_file(path: str, file_id: str = None, fingerprint: str = None, timestamp: datetime = None, timestamp_str: str = None):
            self.files += [path]

            if file_id:
                self.files_map[file_id] = path
                self.fingerprints_map[file_id] = ('md5', fingerprint, timestamp)
                self.attributes_map[(path, 'it.tidalwave.datamanager.id')] = file_id
                self.attributes_map[(path, 'it.tidalwave.datamanager.fingerprint.md5')] = fingerprint
                self.attributes_map[(path, 'it.tidalwave.datamanager.fingerprint.md5.timestamp')] = timestamp_str

        old_timestamp = datetime(2020, 10, 1, 0, 0, 0)
        old_timestamp_str = '2020-10-01 00:00:00'

        register_file('folder/file_with_unchanged_md5',
                      '00000000-0000-0000-0000-000000000001',
                      'md5(folder/file_with_unchanged_md5)',
                      old_timestamp,
                      old_timestamp_str)
        register_file('folder/file_with_changed_md5',
                      '00000000-0000-0000-0000-000000000002',
                      'oldmd5(folder/file_with_changed_md5)',
                      old_timestamp,
                      old_timestamp_str)
        register_file('folder/file_with_error',
                      '00000000-0000-0000-0000-000000000003',
                      'md5(folder/file_with_error)',
                      old_timestamp,
                      old_timestamp_str)
        register_file('folder/file_moved',
                      '00000000-0000-0000-0000-000000000004',
                      'md5(folder/file_moved)',
                      old_timestamp,
                      old_timestamp_str)
        register_file('folder/new_file')
        register_file('folder/new_file_with_error')

        self.files_map['00000000-0000-0000-0000-000000000004'] = 'oldfolder/file_moved'

    def open(self):
        pass

    def close(self):
        pass

    def find_mappings(self):
        return self.files_map.items()

    def get_attribute(self, path: str, name: str) -> str:
        key = (path, name)
        return self.attributes_map[key] if key in self.attributes_map else None

    def set_attribute(self, path: str, name: str, value: str):
        self.attributes_done += [('set_attribute()', path, name, value)]

    def add_path(self, file_id: str, path: str, commit=False):
        self.paths_done += [('add_path()', file_id, path, commit)]

    def update_path(self, file_id: str, path: str, commit=False):
        self.paths_done += [('update_path()', file_id, path, commit)]

    def add_fingerprint(self, file_id: str, file_name: str, algorithm: str, fingerprint: str, timestamp, commit=False):
        self.fingerprints_done += [('insert_fingerprint()', file_id, algorithm, fingerprint, timestamp, commit)]

    def walk(self, folder: str, filter: str, function):
        result = None

        for file in self.files:
            result = function(str(Path(file).parent), str(Path(file).name))

        return result

    def things_done(self):
        return self.paths_done + self.fingerprints_done + self.attributes_done

    @staticmethod
    def compute_fingerprint(path: str) -> (str, str):
        if 'with_error' in path:
            return 'error', 'I/O error'
        else:
            return 'md5', f'md5({path})'


#
#
#
class MockPresentation(FingerprintingPresentation):
    def __init__(self):
        self.things_done = []

    def notify_message(self, message: str):
        self.things_done += [('notify_message()', message)]

    def notify_counting(self):
        self.things_done += ['notify_counting()']

    def notify_file_count(self, file_count: int):
        self.things_done += [('notify_file_count()', file_count)]

    def notify_progress(self, partial: int, total: int):
        self.things_done += [('notify_progress()', partial, total)]

    def notify_file(self, path: str, is_new: bool):
        self.things_done += [('notify_file()', path, is_new)]

    def notify_file_moved(self, old_path: str, new_path: str):
        self.things_done += [('notify_file_moved()', old_path, new_path)]

    def notify_error(self, message: str):
        self.things_done += [('notify_error()', message)]


#
#
#
class TestFingerprintControl(unittest.TestCase):
    under_test = None
    storage = None
    presentation = None
    next_id = None

    #
    #
    #
    def test_full_scan(self):
        self.__setup_fixture()

        self.under_test.scan(folder='folder', file_filter='.*')

        actual = self.storage.things_done() + self.presentation.things_done
        new_timestamp = self.__mock_time_provider()
        new_timestamp_str = '2020-11-01 00:00:00'
        expected = [
            ('update_path()', '00000000-0000-0000-0000-000000000004', 'folder/file_moved', True),
            ('add_path()', '00000000-0000-0000-0000-000000001001', 'folder/new_file', True),
            ('add_path()', '00000000-0000-0000-0000-000000001002', 'folder/new_file_with_error', True),
            ('insert_fingerprint()', '00000000-0000-0000-0000-000000000004', 'md5', 'md5(folder/file_moved)', new_timestamp, True),
            ('insert_fingerprint()', '00000000-0000-0000-0000-000000000002', 'md5', 'md5(folder/file_with_changed_md5)', new_timestamp, True),
            ('insert_fingerprint()', '00000000-0000-0000-0000-000000000003', 'error', 'I/O error', new_timestamp, True),
            ('insert_fingerprint()', '00000000-0000-0000-0000-000000000001', 'md5', 'md5(folder/file_with_unchanged_md5)', new_timestamp, True),
            ('insert_fingerprint()', '00000000-0000-0000-0000-000000001001', 'md5', 'md5(folder/new_file)', new_timestamp, True),
            ('insert_fingerprint()', '00000000-0000-0000-0000-000000001002', 'error', 'I/O error', new_timestamp, True),
            ('set_attribute()', 'folder/file_moved', 'it.tidalwave.datamanager.fingerprint.md5', 'md5(folder/file_moved)'),
            ('set_attribute()', 'folder/file_moved', 'it.tidalwave.datamanager.fingerprint.md5.timestamp', new_timestamp_str),
            ('set_attribute()', 'folder/file_with_changed_md5', 'it.tidalwave.datamanager.fingerprint.md5', 'md5(folder/file_with_changed_md5)'),
            ('set_attribute()', 'folder/file_with_changed_md5', 'it.tidalwave.datamanager.fingerprint.md5.timestamp', new_timestamp_str),
            ('set_attribute()', 'folder/file_with_unchanged_md5', 'it.tidalwave.datamanager.fingerprint.md5', 'md5(folder/file_with_unchanged_md5)'),
            ('set_attribute()', 'folder/file_with_unchanged_md5', 'it.tidalwave.datamanager.fingerprint.md5.timestamp', new_timestamp_str),
            ('set_attribute()', 'folder/new_file', 'it.tidalwave.datamanager.id', '00000000-0000-0000-0000-000000001001'),
            ('set_attribute()', 'folder/new_file', 'it.tidalwave.datamanager.fingerprint.md5', 'md5(folder/new_file)'),
            ('set_attribute()', 'folder/new_file', 'it.tidalwave.datamanager.fingerprint.md5.timestamp', new_timestamp_str),
            ('set_attribute()', 'folder/new_file_with_error', 'it.tidalwave.datamanager.id', '00000000-0000-0000-0000-000000001002'),

            'notify_counting()',
            ('notify_file_count()', 6),
            ('notify_file_moved()', 'oldfolder/file_moved', 'folder/file_moved'),
            ('notify_file()', 'folder/file_moved', False),
            ('notify_progress()', 1, 6),
            ('notify_file()', 'folder/file_with_changed_md5', False),
            ('notify_error()', 'Mismatch for folder/file_with_changed_md5: found md5(folder/file_with_changed_md5) '
                               'expected oldmd5(folder/file_with_changed_md5)'),
            ('notify_progress()', 2, 6),
            ('notify_error()', 'Error for folder/file_with_error: I/O error'),
            ('notify_progress()', 3, 6),
            ('notify_file()', 'folder/file_with_unchanged_md5', False),
            ('notify_progress()', 4, 6),
            ('notify_file()', 'folder/new_file', True),
            ('notify_progress()', 5, 6),
            ('notify_error()', 'Error for folder/new_file_with_error: I/O error'),
            ('notify_progress()', 6, 6),
            ('notify_message()', '4 files (1.59 GB) processed in 59 seconds (27.0 MB/sec)'),
            ('notify_message()', '1.23 GB in plain I/O, 359.7 MB in memory mapped I/O')
        ]

        self.assertEqual(actual, expected)

    #
    #
    #
    def test_scan_only_new_files(self):
        self.__setup_fixture()

        self.under_test.scan(folder='folder', file_filter='.*', only_new_files=True)

        actual = self.storage.things_done() + self.presentation.things_done
        new_timestamp = self.__mock_time_provider()
        expected = [
            ('add_path()', '00000000-0000-0000-0000-000000001001', 'folder/new_file', True),
            ('add_path()', '00000000-0000-0000-0000-000000001002', 'folder/new_file_with_error', True),
            ('insert_fingerprint()', '00000000-0000-0000-0000-000000001001', 'md5', 'md5(folder/new_file)', new_timestamp, True),
            ('insert_fingerprint()', '00000000-0000-0000-0000-000000001002', 'error', 'I/O error', new_timestamp, True),
            ('set_attribute()', 'folder/new_file', 'it.tidalwave.datamanager.id', '00000000-0000-0000-0000-000000001001'),
            ('set_attribute()', 'folder/new_file', 'it.tidalwave.datamanager.fingerprint.md5', 'md5(folder/new_file)'),
            ('set_attribute()', 'folder/new_file', 'it.tidalwave.datamanager.fingerprint.md5.timestamp', '2020-11-01 00:00:00'),
            ('set_attribute()', 'folder/new_file_with_error', 'it.tidalwave.datamanager.id', '00000000-0000-0000-0000-000000001002'),

            'notify_counting()',
            ('notify_file_count()', 6),
            ('notify_message()', 'Scanning only new files'),
            ('notify_file()', 'folder/file_moved', False),
            ('notify_progress()', 1, 6),
            ('notify_file()', 'folder/file_with_changed_md5', False),
            ('notify_progress()', 2, 6),
            ('notify_file()', 'folder/file_with_error', False),
            ('notify_progress()', 3, 6),
            ('notify_file()', 'folder/file_with_unchanged_md5', False),
            ('notify_progress()', 4, 6),
            ('notify_file()', 'folder/new_file', True),
            ('notify_progress()', 5, 6),
            ('notify_error()', 'Error for folder/new_file_with_error: I/O error'),
            ('notify_progress()', 6, 6),
            ('notify_message()', '4 files (1.59 GB) processed in 59 seconds (27.0 MB/sec)'),
            ('notify_message()', '1.23 GB in plain I/O, 359.7 MB in memory mapped I/O')
        ]

        self.assertEqual(actual, expected)

    #
    # Set up the test fixture.
    #
    def __setup_fixture(self):
        self.next_id = 1000
        self.presentation = MockPresentation()
        self.storage = MockStorage()
        self.under_test = FingerprintingControl(database_folder='folder',
                                                presentation=self.presentation,
                                                storage=self.storage,
                                                id_generator=self.__mock_generate_id,
                                                time_provider=self.__mock_time_provider,
                                                debug_function=self.__debug)

    #
    # Various mock methods.
    #
    def __mock_generate_id(self) -> str:
        self.next_id += 1
        return f'00000000-0000-0000-0000-00000000{self.next_id}'

    @staticmethod
    def __mock_time_provider():
        return datetime(2020, 11, 1, 0, 0, 0)

    def __debug(self, message: str):
        # print(message, flush=True)
        pass


if __name__ == '__main__':
    unittest.main()
