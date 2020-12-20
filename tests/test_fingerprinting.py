#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#  SolidBlue III - Open source data manager.
#
#  __author__ = "Fabrizio Giudici"
#  __copyright__ = "Copyright © 2020 by Fabrizio Giudici"
#  __credits__ = ["Fabrizio Giudici"]
#  __license__ = "Apache v2"
#  __version__ = "1.0-ALPHA-3"
#  __maintainer__ = "Fabrizio Giudici"
#  __email__ = "fabrizio.giudici@tidalwave.it"
#  __status__ = "Prototype"
import os
import unittest
from collections import namedtuple
from datetime import datetime
from pathlib import Path

from mockito import when, unstub

from config import Config
from executor import Executor
from fingerprinting import FingerprintingControl, FingerprintingPresentation, FingerprintingStats, FingerprintingFileSystem


#
#
#
class MockProcess:
    def __init__(self, stream):
        self.stdout = stream

    def poll(self) -> bool:
        return True


#
#
#
class MockStorage:
    def __init__(self, file_system):
        self.paths_dict_by_id = file_system.paths_dict_by_id
        self.done = []

    def find_mappings(self):  # (id, map)
        return self.paths_dict_by_id.items()

    def find_latest_fingerprint_by_id(self, file_id: str) -> (str, str):
        return f'md5({self.paths_dict_by_id[file_id]})', None

    def find_backup_item_id(self, backup_id: str, file_id: str) -> str:
        return 'id-of-backup-of-' + file_id

    def find_backup_by_volume_id(self, volume_id):
        pass

    def find_backup_by_label(self, label: str):
        pass

    def open(self):
        self.done += [('open()',)]

    def close(self):
        self.done += [('close()',)]

    def commit(self):
        self.done += [('commit()',)]

    def add_path(self, file_id: str, path: str, commit=False):
        self.done += [('add_path()', file_id, path, commit)]

    def update_path(self, file_id: str, path: str, commit=False):
        self.done += [('update_path()', file_id, path, commit)]

    def add_fingerprint(self, file_id: str, file_name: str, algorithm: str, fingerprint: str, timestamp, commit=False):
        self.done += [('insert_fingerprint()', file_id, algorithm, fingerprint, timestamp, commit)]

    def add_backup(self, base_path: str, label: str, volume_id: str, creation_date: datetime, registration_date: datetime, encrypted, commit=False) -> str:
        new_id = 'id-of-new-backup'
        self.done += [('add_backup()', new_id, base_path, label, volume_id, creation_date, registration_date, encrypted, commit)]
        return new_id

    def add_backup_item(self, backup_id: str, file_id, backup_file: str, commit=False) -> str:
        self.done += [('add_backup_item()', backup_id, file_id, backup_file, commit)]

    def set_backup_check_latest_timestamp(self, backup_id, timestamp):
        self.done += [('set_backup_check_latest_timestamp', backup_id, timestamp)]

    def things_done(self):
        return self.done


#
#
#
class MockFileSystem:
    def __init__(self):
        self.paths_dict_by_id = {}
        self.files = []
        self.fingerprints_dict_by_id = {}
        self.attributes_dict_by_path_and_name = {}

        self.done = []

        class MockStats(FingerprintingStats):
            def stop(self):
                self.processed_file_count = 4
                self.plain_io_reads = 1234567894
                self.mmap_reads = 359665044
                self.elapsed = 59

        self.stats = MockStats()

    def enumerate_files(self, folders: [str], file_filter: str = '.*') -> [FingerprintingFileSystem.FileInfo]:
        result = []

        for folder in folders:
            result += filter(lambda file: file.path.startswith(folder), self.files)

        return result

    def get_attribute(self, path: str, name: str) -> str:
        key = (path, name)
        return self.attributes_dict_by_path_and_name[key] if key in self.attributes_dict_by_path_and_name else None

    @staticmethod
    def compute_fingerprint(path: str) -> (str, str):
        if 'with_error' in path:
            return 'error', 'I/O error'
        else:
            return 'md5', f'md5({path})'

    def find_volume_uuid(self, mount_point: str) -> str:
        pass

    def creation_date(self, path: str) -> datetime:
        pass

    def size(self, file: str) -> int:
        pass

    def exists(self, file: str):
        pass

    def set_attribute(self, path: str, name: str, value: str):
        self.done += [('set_attribute()', path, name, value)]

    def eject_optical_disc(self, mount_point: str):
        self.done += [('eject_optical_disk()', mount_point)]

    def make_dirs(self, path: str):
        self.done += [('make_dirs()', path)]

    def mount_veracrypt_image(self, image_file: str, mount_point: str, key_file: str):
        self.done += [('mount_veracrypt_image()', image_file, mount_point)]

    def unmount_veracrypt_image(self, mount_point: str):
        self.done += [('unmount_veracrypt_image()', mount_point)]

    def remove_folder(self, folder: str):
        self.done += [('remove_folder()', folder)]

    def copy_with_xattrs(self, source_path: str, target_path: str, executor):
        self.done += [('copy_with_xattrs()', source_path, target_path)]

    def create_veracrypt_image(self, algorithm: str, hash_algorithm: str, key_file: str, size: int, image_file: str, executor, veracrypt_post_processor):
        self.done += [('create_veracrypt_image', algorithm, hash_algorithm, key_file, size, image_file)]

    def create_hybrid_disk_image(self, label: str, image_file: str, source_folder: str, executor):
        self.done += [('create_hybrid_disk_image', label, image_file, source_folder)]

    def burn(self, image_file: str, post_processor, executor):
        self.done += [('burn', image_file)]

    def unmount_optical_disk(self, mount_point: str, executor):
        self.done += [('unmount_optical_disk', mount_point)]

    def mock_file(self, path: str, file_id: str = None, fingerprint: str = None, timestamp: datetime = None, timestamp_str: str = None, size: int = 0):
        file_info = FingerprintingFileSystem.FileInfo(name=Path(path).name, folder=str(Path(path).parent), path=path, size=size)
        self.files += [file_info]

        if file_id:
            self.paths_dict_by_id[file_id] = path
            self.attributes_dict_by_path_and_name[(path, 'it.tidalwave.datamanager.id')] = file_id

        if file_id and fingerprint:
            self.fingerprints_dict_by_id[file_id] = ('md5', fingerprint, timestamp)

        if fingerprint:
            self.attributes_dict_by_path_and_name[(path, 'it.tidalwave.datamanager.fingerprint.md5')] = fingerprint

        if timestamp_str:
            self.attributes_dict_by_path_and_name[(path, 'it.tidalwave.datamanager.fingerprint.md5.timestamp')] = timestamp_str

    def things_done(self) -> [str]:
        return self.done


#
#
#
class MockPresentation(FingerprintingPresentation):
    def __init__(self):
        self.things_done = []

    def notify_message(self, message: str):
        self.things_done += [('notify_message()', message)]

    def notify_counting(self):
        self.things_done += [('notify_counting()',)]

    def notify_file_count(self, file_count: int):
        self.things_done += [('notify_file_count()', file_count)]

    def notify_progress(self, partial: int, total: int):
        self.things_done += [('notify_progress()', partial, total)]

    def notify_secondary_progress(self, progress: float):
        self.things_done += [('notify_secondary_progress()', progress)]

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
    def setUp(self):
        self.maxDiff = None

    #
    #
    #
    def tearDown(self):
        unstub()

    #
    #
    #
    def __mock_backup_files(self, base_path_of_backup: str):
        self.file_system.mock_file(path=f'{base_path_of_backup}/Folder1/File1', file_id='id-of-File1', size=234235545)
        self.file_system.mock_file(path=f'{base_path_of_backup}/Folder1/File2', file_id='id-of-File2', size=44234254)
        self.file_system.mock_file(path=f'{base_path_of_backup}/Folder2/File3', file_id='id-of-File3', size=80358495)
        self.file_system.mock_file(path=f'{base_path_of_backup}/Folder2/File4', file_id='id-of-File4', size=5839558)
        self.file_system.mock_file(path=f'{base_path_of_backup}/Folder3/File5', file_id='id-of-File5', size=14593583)
        self.file_system.mock_file(path=f'{base_path_of_backup}/Folder3/File6', file_id='id-of-File6', size=55024583)

    #
    #
    #
    def __mock_veracrypt_files(self, backup_label: str):
        self.file_system.mock_file(path=f'/Volumes/{backup_label}/{backup_label}.veracrypt', file_id=None, size=234235545)

    #
    #
    #
    def __mock_files(self):
        old_timestamp = datetime(2020, 10, 1, 0, 0, 0)
        old_timestamp_str = '2020-10-01 00:00:00'

        self.file_system.mock_file(path='folder/file_with_unchanged_md5',
                                   file_id='00000000-0000-0000-0000-000000000001',
                                   fingerprint='md5(folder/file_with_unchanged_md5)',
                                   timestamp=old_timestamp,
                                   timestamp_str=old_timestamp_str,
                                   size=56948594)
        self.file_system.mock_file(path='folder/file_with_changed_md5',
                                   file_id='00000000-0000-0000-0000-000000000002',
                                   fingerprint='oldmd5(folder/file_with_changed_md5)',
                                   timestamp=old_timestamp,
                                   timestamp_str=old_timestamp_str,
                                   size=75876784)
        self.file_system.mock_file(path='folder/file_with_error',
                                   file_id='00000000-0000-0000-0000-000000000003',
                                   fingerprint='md5(folder/file_with_error)',
                                   timestamp=old_timestamp,
                                   timestamp_str=old_timestamp_str,
                                   size=2342342)
        self.file_system.mock_file(path='folder/file_moved',
                                   file_id='00000000-0000-0000-0000-000000000004',
                                   fingerprint='md5(folder/file_moved)',
                                   timestamp=old_timestamp,
                                   timestamp_str=old_timestamp_str,
                                   size=1696838)
        self.file_system.mock_file(path='folder/new_file',
                                   size=6426694)
        self.file_system.mock_file(path='folder/new_file_with_error',
                                   size=13346039)

        self.file_system.paths_dict_by_id['00000000-0000-0000-0000-000000000004'] = 'oldfolder/file_moved'

    #
    #
    #
    def test_full_scan(self):
        # GIVEN
        self.__setup_fixture()
        self.__mock_files()
        # WHEN
        self.under_test.scan(folder='folder', file_filter='.*')
        # THEN
        actual = self.storage.things_done() + self.file_system.things_done() + self.presentation.things_done
        now = self.__mock_time_provider()
        now_str = '2020-11-01 00:00:00'
        expected = [
            # STORAGE
            ('open()',),
            ('update_path()', '00000000-0000-0000-0000-000000000004', 'folder/file_moved', True),
            ('insert_fingerprint()', '00000000-0000-0000-0000-000000000004', 'md5', 'md5(folder/file_moved)', now, True),
            ('insert_fingerprint()', '00000000-0000-0000-0000-000000000002', 'md5', 'md5(folder/file_with_changed_md5)', now, True),
            ('insert_fingerprint()', '00000000-0000-0000-0000-000000000003', 'error', 'I/O error', now, True),
            ('insert_fingerprint()', '00000000-0000-0000-0000-000000000001', 'md5', 'md5(folder/file_with_unchanged_md5)', now, True),
            ('add_path()', '00000000-0000-0000-0000-000000001001', 'folder/new_file', True),
            ('insert_fingerprint()', '00000000-0000-0000-0000-000000001001', 'md5', 'md5(folder/new_file)', now, True),
            ('add_path()', '00000000-0000-0000-0000-000000001002', 'folder/new_file_with_error', True),
            ('insert_fingerprint()', '00000000-0000-0000-0000-000000001002', 'error', 'I/O error', now, True),
            ('close()',),
            # FILE SYSTEM
            ('set_attribute()', 'folder/file_moved', 'it.tidalwave.datamanager.fingerprint.md5', 'md5(folder/file_moved)'),
            ('set_attribute()', 'folder/file_moved', 'it.tidalwave.datamanager.fingerprint.md5.timestamp', now_str),
            ('set_attribute()', 'folder/file_with_changed_md5', 'it.tidalwave.datamanager.fingerprint.md5', 'md5(folder/file_with_changed_md5)'),
            ('set_attribute()', 'folder/file_with_changed_md5', 'it.tidalwave.datamanager.fingerprint.md5.timestamp', now_str),
            ('set_attribute()', 'folder/file_with_unchanged_md5', 'it.tidalwave.datamanager.fingerprint.md5', 'md5(folder/file_with_unchanged_md5)'),
            ('set_attribute()', 'folder/file_with_unchanged_md5', 'it.tidalwave.datamanager.fingerprint.md5.timestamp', now_str),
            ('set_attribute()', 'folder/new_file', 'it.tidalwave.datamanager.id', '00000000-0000-0000-0000-000000001001'),
            ('set_attribute()', 'folder/new_file', 'it.tidalwave.datamanager.fingerprint.md5', 'md5(folder/new_file)'),
            ('set_attribute()', 'folder/new_file', 'it.tidalwave.datamanager.fingerprint.md5.timestamp', now_str),
            ('set_attribute()', 'folder/new_file_with_error', 'it.tidalwave.datamanager.id', '00000000-0000-0000-0000-000000001002'),
            # PRESENTATION
            ('notify_counting()',),
            ('notify_message()', "Counting files in ['folder']..."),
            ('notify_file_count()', 6),
            ('notify_message()', 'Found 6 files (156.6 MB)'),
            ('notify_file_moved()', 'oldfolder/file_moved', 'folder/file_moved'),
            ('notify_file()', 'folder/file_moved', False),
            ('notify_progress()', 1696838, 156637291),
            ('notify_file()', 'folder/file_with_changed_md5', False),
            ('notify_error()', 'Mismatch for folder/file_with_changed_md5: found md5(folder/file_with_changed_md5) '
                               'expected oldmd5(folder/file_with_changed_md5)'),
            ('notify_progress()', 77573622, 156637291),
            ('notify_error()', 'Error for folder/file_with_error: I/O error'),
            ('notify_progress()', 79915964, 156637291),
            ('notify_file()', 'folder/file_with_unchanged_md5', False),
            ('notify_progress()', 136864558, 156637291),
            ('notify_file()', 'folder/new_file', True),
            ('notify_progress()', 143291252, 156637291),
            ('notify_error()', 'Error for folder/new_file_with_error: I/O error'),
            ('notify_progress()', 156637291, 156637291),
            ('notify_message()', '4 files (1.59 GB) processed in 59 seconds (27.0 MB/sec)'),
            ('notify_message()', '1.23 GB in plain I/O, 359.7 MB in memory mapped I/O')
        ]

        self.assertEqual(actual, expected)

    #
    #
    #
    def test_scan_only_new_files(self):
        # GIVEN
        self.__setup_fixture()
        self.__mock_files()
        # WHEN
        self.under_test.scan(folder='folder', file_filter='.*', only_new_files=True)
        # THEN
        actual = self.storage.things_done() + self.file_system.things_done() + self.presentation.things_done
        now = self.__mock_time_provider()
        expected = [
            # STORAGE
            ('open()',),
            ('add_path()', '00000000-0000-0000-0000-000000001001', 'folder/new_file', True),
            ('insert_fingerprint()', '00000000-0000-0000-0000-000000001001', 'md5', 'md5(folder/new_file)', now, True),
            ('add_path()', '00000000-0000-0000-0000-000000001002', 'folder/new_file_with_error', True),
            ('insert_fingerprint()', '00000000-0000-0000-0000-000000001002', 'error', 'I/O error', now, True),
            ('close()',),
            # FILE SYSTEM
            ('set_attribute()', 'folder/new_file', 'it.tidalwave.datamanager.id', '00000000-0000-0000-0000-000000001001'),
            ('set_attribute()', 'folder/new_file', 'it.tidalwave.datamanager.fingerprint.md5', 'md5(folder/new_file)'),
            ('set_attribute()', 'folder/new_file', 'it.tidalwave.datamanager.fingerprint.md5.timestamp', '2020-11-01 00:00:00'),
            ('set_attribute()', 'folder/new_file_with_error', 'it.tidalwave.datamanager.id', '00000000-0000-0000-0000-000000001002'),
            # PRESENTATION
            ('notify_counting()',),
            ('notify_message()', "Counting files in ['folder']..."),
            ('notify_file_count()', 6),
            ('notify_message()', 'Found 6 files (156.6 MB)'),
            ('notify_message()', 'Scanning only new files'),
            ('notify_file()', 'folder/file_moved', False),
            ('notify_progress()', 1696838, 156637291),
            ('notify_file()', 'folder/file_with_changed_md5', False),
            ('notify_progress()', 77573622, 156637291),
            ('notify_file()', 'folder/file_with_error', False),
            ('notify_progress()', 79915964, 156637291),
            ('notify_file()', 'folder/file_with_unchanged_md5', False),
            ('notify_progress()', 136864558, 156637291),
            ('notify_file()', 'folder/new_file', True),
            ('notify_progress()', 143291252, 156637291),
            ('notify_error()', 'Error for folder/new_file_with_error: I/O error'),
            ('notify_progress()', 156637291, 156637291),
            ('notify_message()', '4 files (1.59 GB) processed in 59 seconds (27.0 MB/sec)'),
            ('notify_message()', '1.23 GB in plain I/O, 359.7 MB in memory mapped I/O')
        ]

        self.assertEqual(actual, expected)

    #
    #
    #
    def test_register_backup_and_eject(self):
        # GIVEN
        now = self.__mock_time_provider()
        volume_creation_date = datetime(2020, 10, 1, 0, 0, 0)
        backup_label = 'Backup Label'
        volume_uuid = 'uuid-of-volume'
        # WHEN
        actual = self.__test_register_backup(volume_uuid=volume_uuid, backup_label=backup_label, encrypted=False, eject_after=True)
        # THEN
        base_path_of_backup = f'/Volumes/{backup_label}'
        new_backup_id = 'id-of-new-backup'
        expected = [
            # STORAGE
            ('open()',),
            ('add_backup()', new_backup_id, base_path_of_backup, backup_label, volume_uuid, volume_creation_date, now, False, False),
            ('add_backup_item()', new_backup_id, 'id-of-File1', 'Folder1/File1', False),
            ('add_backup_item()', new_backup_id, 'id-of-File2', 'Folder1/File2', False),
            ('add_backup_item()', new_backup_id, 'id-of-File3', 'Folder2/File3', False),
            ('add_backup_item()', new_backup_id, 'id-of-File4', 'Folder2/File4', False),
            ('add_backup_item()', new_backup_id, 'id-of-File5', 'Folder3/File5', False),
            ('add_backup_item()', new_backup_id, 'id-of-File6', 'Folder3/File6', False),
            ('commit()',),
            ('close()',),
            # FILE SYSTEM
            ('eject_optical_disk()', f'/Volumes/{backup_label}'),
            # PRESENTATION
            ('notify_message()', f'Volume UUID {volume_uuid} created on 2020-10-01 00:00:00'),
            ('notify_counting()',),
            ('notify_message()', f"Counting files in ['{base_path_of_backup}']..."),
            ('notify_file_count()', 6),
            ('notify_message()', 'Found 6 files (434.3 MB)'),
            ('notify_file()', 'Folder1/File1', True),
            ('notify_progress()', 1, 6),
            ('notify_file()', 'Folder1/File2', True),
            ('notify_progress()', 2, 6),
            ('notify_file()', 'Folder2/File3', True),
            ('notify_progress()', 3, 6),
            ('notify_file()', 'Folder2/File4', True),
            ('notify_progress()', 4, 6),
            ('notify_file()', 'Folder3/File5', True),
            ('notify_progress()', 5, 6),
            ('notify_file()', 'Folder3/File6', True),
            ('notify_progress()', 6, 6)]

        self.assertEqual(actual, expected)

    #
    #
    #
    def test_register_veracrypt_backup_and_eject(self):
        # WHEN
        backup_label = 'Backup Label'
        volume_uuid = 'uuid-of-volume'
        actual = self.__test_register_backup(volume_uuid=volume_uuid, backup_label=backup_label, encrypted=True, eject_after=True)
        # THEN
        now = self.__mock_time_provider()
        volume_creation_date = datetime(2020, 10, 1, 0, 0, 0)
        veracrypt_mount_point = Config.encrypted_volumes_mount_folder()
        base_path_of_backup = f'{veracrypt_mount_point}/{backup_label}'
        new_backup_id = 'id-of-new-backup'
        expected = [
            # STORAGE
            ('open()',),
            ('add_backup()', new_backup_id, base_path_of_backup, backup_label, volume_uuid, volume_creation_date, now, True, False),
            ('add_backup_item()', new_backup_id, 'id-of-File1', 'Folder1/File1', False),
            ('add_backup_item()', new_backup_id, 'id-of-File2', 'Folder1/File2', False),
            ('add_backup_item()', new_backup_id, 'id-of-File3', 'Folder2/File3', False),
            ('add_backup_item()', new_backup_id, 'id-of-File4', 'Folder2/File4', False),
            ('add_backup_item()', new_backup_id, 'id-of-File5', 'Folder3/File5', False),
            ('add_backup_item()', new_backup_id, 'id-of-File6', 'Folder3/File6', False),
            ('commit()',),
            ('close()',),
            # FILE SYSTEM
            ('make_dirs()', veracrypt_mount_point),
            ('mount_veracrypt_image()', f'/Volumes/{backup_label}/{backup_label}.veracrypt', f'{veracrypt_mount_point}/{backup_label}'),
            ('eject_optical_disk()', f'/Volumes/{backup_label}'),
            ('unmount_veracrypt_image()', f'{veracrypt_mount_point}/{backup_label}'),
            # PRESENTATION
            ('notify_message()', f'Detected a VeraCrypt backup, mounting image at "{veracrypt_mount_point}/{backup_label}" ...'),
            ('notify_message()', f'Volume UUID {volume_uuid} created on 2020-10-01 00:00:00'),
            ('notify_counting()',),
            ('notify_message()', f"Counting files in ['{base_path_of_backup}']..."),
            ('notify_file_count()', 6),
            ('notify_message()', 'Found 6 files (434.3 MB)'),
            ('notify_file()', 'Folder1/File1', True),
            ('notify_progress()', 1, 6),
            ('notify_file()', 'Folder1/File2', True),
            ('notify_progress()', 2, 6),
            ('notify_file()', 'Folder2/File3', True),
            ('notify_progress()', 3, 6),
            ('notify_file()', 'Folder2/File4', True),
            ('notify_progress()', 4, 6),
            ('notify_file()', 'Folder3/File5', True),
            ('notify_progress()', 5, 6),
            ('notify_file()', 'Folder3/File6', True),
            ('notify_progress()', 6, 6),
            ('notify_message()', f'Unmounting VeraCrypt image at "{veracrypt_mount_point}/{backup_label}" ...')]

        self.assertEqual(actual, expected)

    #
    #
    #
    def __test_register_backup(self, volume_uuid: str, backup_label: str, encrypted: bool, eject_after: bool) -> [str]:
        # GIVEN
        volume_creation_date = datetime(2020, 10, 1, 0, 0, 0)
        veracrypt_mount_point = Config.encrypted_volumes_mount_folder()
        volume_mount_point = f'/Volumes/{backup_label}'
        base_path_of_backup = volume_mount_point if not encrypted else f'{veracrypt_mount_point}/{backup_label}'
        when(MockStorage).find_backup_by_volume_id(volume_uuid).thenReturn(None)
        when(MockStorage).find_backup_by_label(backup_label).thenReturn(None)
        when(MockFileSystem).find_volume_uuid(volume_mount_point).thenReturn(volume_uuid)
        when(MockFileSystem).creation_date(base_path_of_backup).thenReturn(volume_creation_date)
        self.__setup_fixture()
        self.__mock_backup_files(base_path_of_backup)

        if encrypted:
            self.__mock_veracrypt_files(backup_label)
        # WHEN
        self.under_test.register_backup(backup_label, volume_mount_point, eject_after=eject_after)

        return self.storage.things_done() + self.file_system.things_done() + self.presentation.things_done

    #
    #
    #
    def test_register_backup_with_existing_volume_id(self):
        # GIVEN
        volume_uuid = 'uuid-of-volume'
        backup_label = 'Backup Label'
        volume_creation_date = datetime(2020, 10, 1, 0, 0, 0)
        volume_mount_point = f'/Volumes/{backup_label}'
        when(MockStorage).find_backup_by_volume_id(volume_uuid).thenReturn('not null')
        when(MockFileSystem).find_volume_uuid(volume_mount_point).thenReturn(volume_uuid)
        when(MockFileSystem).creation_date(volume_mount_point).thenReturn(volume_creation_date)
        self.__setup_fixture(mock_storage_clz=MockStorage, mock_file_system_clz=MockFileSystem)
        # WHEN
        self.under_test.register_backup(backup_label, volume_mount_point, eject_after=True)
        # THEN
        actual = self.storage.things_done() + self.file_system.things_done() + self.presentation.things_done
        expected = [
            # STORAGE
            ('open()',),
            ('close()',),
            # PRESENTATION
            ('notify_message()', 'Volume UUID uuid-of-volume created on 2020-10-01 00:00:00'),
            ('notify_error()', 'Backup with the same volume id already registered')]
        self.assertEqual(actual, expected)

    #
    #
    #
    def test_register_backup_with_existing_volume_label(self):
        # GIVEN
        volume_uuid = 'uuid-of-volume'
        backup_label = 'Backup Label'
        volume_creation_date = datetime(2020, 10, 1, 0, 0, 0)
        volume_mount_point = f'/Volumes/{backup_label}'
        when(MockStorage).find_backup_by_label(backup_label).thenReturn('not null')
        when(MockFileSystem).find_volume_uuid(volume_mount_point).thenReturn(volume_uuid)
        when(MockFileSystem).creation_date(volume_mount_point).thenReturn(volume_creation_date)
        self.__setup_fixture(mock_storage_clz=MockStorage, mock_file_system_clz=MockFileSystem)
        # WHEN
        self.under_test.register_backup(backup_label, volume_mount_point, eject_after=True)
        # THEN
        actual = self.storage.things_done() + self.file_system.things_done() + self.presentation.things_done
        expected = [
            # STORAGE
            ('open()',),
            ('close()',),
            # PRESENTATION
            ('notify_message()', 'Volume UUID uuid-of-volume created on 2020-10-01 00:00:00'),
            ('notify_error()', 'Backup with the same label already registered')]
        self.assertEqual(actual, expected)

    #
    #
    #
    def test_check_backup(self):
        # GIVEN
        now = self.__mock_time_provider()
        backup_label = 'Backup Label'
        backup_id = 'backup-id'
        # WHEN
        actual = self.__test_check_backup(backup_id=backup_id, encrypted=False, eject_after=True)
        # THEN
        expected = [
            # STORAGE
            ('open()',),
            ('insert_fingerprint()', 'id-of-backup-of-id-of-File1', 'md5', f'md5(/Volumes/{backup_label}/Folder1/File1)', now, False),
            ('insert_fingerprint()', 'id-of-backup-of-id-of-File2', 'md5', f'md5(/Volumes/{backup_label}/Folder1/File2)', now, False),
            ('insert_fingerprint()', 'id-of-backup-of-id-of-File3', 'md5', f'md5(/Volumes/{backup_label}/Folder2/File3)', now, False),
            ('insert_fingerprint()', 'id-of-backup-of-id-of-File4', 'md5', f'md5(/Volumes/{backup_label}/Folder2/File4)', now, False),
            ('insert_fingerprint()', 'id-of-backup-of-id-of-File5', 'md5', f'md5(/Volumes/{backup_label}/Folder3/File5)', now, False),
            ('insert_fingerprint()', 'id-of-backup-of-id-of-File6', 'md5', f'md5(/Volumes/{backup_label}/Folder3/File6)', now, False),
            ('set_backup_check_latest_timestamp', backup_id, now),
            ('commit()',),
            ('close()',),
            # FILE SYSTEM
            ('eject_optical_disk()', f'/Volumes/{backup_label}'),
            # PRESENTATION
            ('notify_counting()',),
            ('notify_message()', f"Counting files in ['/Volumes/{backup_label}']..."),
            ('notify_file_count()', 6),
            ('notify_message()', 'Found 6 files (434.3 MB)'),
            ('notify_file()', 'Folder1/File1', False),
            ('notify_progress()', 234235545, 434286018),
            ('notify_file()', 'Folder1/File2', False),
            ('notify_progress()', 278469799, 434286018),
            ('notify_file()', 'Folder2/File3', False),
            ('notify_progress()', 358828294, 434286018),
            ('notify_file()', 'Folder2/File4', False),
            ('notify_progress()', 364667852, 434286018),
            ('notify_file()', 'Folder3/File5', False),
            ('notify_progress()', 379261435, 434286018),
            ('notify_file()', 'Folder3/File6', False),
            ('notify_progress()', 434286018, 434286018)]

        self.assertEqual(actual, expected)

    #
    #
    #
    def test_check_encrypted_backup(self):
        # GIVEN
        now = self.__mock_time_provider()
        backup_label = 'Backup Label'
        backup_id = 'backup-id'
        # WHEN
        actual = self.__test_check_backup(backup_id=backup_id, encrypted=True, eject_after=True)
        # THEN
        veracrypt_mount_point = Config.encrypted_volumes_mount_folder()
        expected = [
            ('open()',),
            ('insert_fingerprint()', 'id-of-backup-of-id-of-File1', 'md5', f'md5({veracrypt_mount_point}/{backup_label}/Folder1/File1)', now, False),
            ('insert_fingerprint()', 'id-of-backup-of-id-of-File2', 'md5', f'md5({veracrypt_mount_point}/{backup_label}/Folder1/File2)', now, False),
            ('insert_fingerprint()', 'id-of-backup-of-id-of-File3', 'md5', f'md5({veracrypt_mount_point}/{backup_label}/Folder2/File3)', now, False),
            ('insert_fingerprint()', 'id-of-backup-of-id-of-File4', 'md5', f'md5({veracrypt_mount_point}/{backup_label}/Folder2/File4)', now, False),
            ('insert_fingerprint()', 'id-of-backup-of-id-of-File5', 'md5', f'md5({veracrypt_mount_point}/{backup_label}/Folder3/File5)', now, False),
            ('insert_fingerprint()', 'id-of-backup-of-id-of-File6', 'md5', f'md5({veracrypt_mount_point}/{backup_label}/Folder3/File6)', now, False),
            ('set_backup_check_latest_timestamp', backup_id, now),
            ('commit()',),
            ('close()',),
            # FILE SYSTEM
            ('make_dirs()', veracrypt_mount_point),
            ('mount_veracrypt_image()', f'/Volumes/{backup_label}/{backup_label}.veracrypt', f'{veracrypt_mount_point}/{backup_label}'),
            ('eject_optical_disk()', f'/Volumes/{backup_label}'),
            ('unmount_veracrypt_image()', f'{veracrypt_mount_point}/{backup_label}'),
            # PRESENTATION
            ('notify_message()', f'Detected a VeraCrypt backup, mounting image at "{veracrypt_mount_point}/{backup_label}" ...'),
            ('notify_counting()',),
            ('notify_message()', f"Counting files in ['{veracrypt_mount_point}/{backup_label}']..."),
            ('notify_file_count()', 6),
            ('notify_message()', 'Found 6 files (434.3 MB)'),
            ('notify_file()', 'Folder1/File1', False),
            ('notify_progress()', 234235545, 434286018),
            ('notify_file()', 'Folder1/File2', False),
            ('notify_progress()', 278469799, 434286018),
            ('notify_file()', 'Folder2/File3', False),
            ('notify_progress()', 358828294, 434286018),
            ('notify_file()', 'Folder2/File4', False),
            ('notify_progress()', 364667852, 434286018),
            ('notify_file()', 'Folder3/File5', False),
            ('notify_progress()', 379261435, 434286018),
            ('notify_file()', 'Folder3/File6', False),
            ('notify_progress()', 434286018, 434286018),
            ('notify_message()', f'Unmounting VeraCrypt image at "{veracrypt_mount_point}/{backup_label}" ...')]

        self.assertEqual(actual, expected)

    #
    #
    #
    Backup = namedtuple('Backup', 'id, base_path, label, volume_id, encrypted, creation_date, registration_date, latest_check_date')

    def __test_check_backup(self, backup_id: str, encrypted: bool, eject_after: bool) -> [str]:
        # GIVEN
        volume_uuid = 'uuid-of-volume'
        backup_label = 'Backup Label'
        veracrypt_mount_point = Config.encrypted_volumes_mount_folder()
        base_path_of_backup = f'/Volumes/{backup_label}' if not encrypted else f'{veracrypt_mount_point}/{backup_label}'

        bbb = TestFingerprintControl.Backup(id=backup_id,
                                            base_path='/Volumes/basepath',  # FIXME
                                            label={backup_label},
                                            volume_id=volume_uuid,
                                            encrypted=encrypted,
                                            creation_date=None,
                                            registration_date=None,
                                            latest_check_date=None)
        when(MockStorage).find_backup_by_volume_id(volume_uuid).thenReturn(bbb)
        when(MockFileSystem).find_volume_uuid(f'/Volumes/{backup_label}').thenReturn(volume_uuid)
        self.__setup_fixture()
        self.__mock_backup_files(base_path_of_backup)

        if encrypted:
            self.__mock_veracrypt_files(backup_label)

        # WHEN
        self.under_test.check_backup(f'/Volumes/{backup_label}', eject_after=eject_after)
        # THEN
        return self.storage.things_done() + self.file_system.things_done() + self.presentation.things_done

    #
    #
    #
    def test_create_encrypted_backup(self):
        # GIVEN
        now = self.__mock_time_provider()
        volume_uuid = 'uuid'
        backup_label = 'Backup Label'
        work_area = Config.working_folder()
        when(MockFileSystem).find_volume_uuid(f'/Volumes/{backup_label}').thenReturn(volume_uuid)
        when(MockFileSystem).size(f'{work_area}/{backup_label}_contents/{backup_label}.veracrypt').thenReturn(5953059400)
        when(MockFileSystem).size(f'{work_area}/{backup_label}.dmg').thenReturn(5953234324)
        when(MockFileSystem).exists(f'/Volumes/{backup_label}').thenReturn(True)

        # Same fields of the add_backup() expected outcome below
        ev_mount_folder = Config.encrypted_volumes_mount_folder()
        new_backup_id = 'id-of-new-backup'
        bbb = TestFingerprintControl.Backup(id=new_backup_id,
                                            base_path=f'{ev_mount_folder}/{backup_label}',
                                            label=backup_label,
                                            volume_id=volume_uuid,
                                            encrypted=True,
                                            creation_date=now,
                                            registration_date=now,
                                            latest_check_date=now)
        when(MockStorage).find_backup_by_volume_id(volume_uuid) \
            .thenReturn(None) \
            .thenReturn(bbb)  # FIXME: this should be done only after creation
        self.__setup_fixture()
        self.__mock_backup_files('/foo')
        self.__mock_veracrypt_files(backup_label)
        # FIXME: this should be done only after creation
        self.__mock_backup_files(f'{ev_mount_folder}/{backup_label}')  # the copied ones
        # WHEN
        self.under_test.create_encrypted_backup(backup_label, 'aes', 'sha-256', folders=['/foo/Folder1', '/foo/Folder2', '/foo/Folder3'], burn=True)
        # THEN
        actual = self.storage.things_done() + self.file_system.things_done() + self.presentation.things_done
        expected = [
            # STORAGE
            ('open()',),
            ('add_backup()', new_backup_id, f'{ev_mount_folder}/{backup_label}', backup_label, volume_uuid, None, now, True, False),
            ('add_backup_item()', new_backup_id, 'id-of-File1', 'Folder1/File1', False),
            ('add_backup_item()', new_backup_id, 'id-of-File2', 'Folder1/File2', False),
            ('add_backup_item()', new_backup_id, 'id-of-File3', 'Folder2/File3', False),
            ('add_backup_item()', new_backup_id, 'id-of-File4', 'Folder2/File4', False),
            ('add_backup_item()', new_backup_id, 'id-of-File5', 'Folder3/File5', False),
            ('add_backup_item()', new_backup_id, 'id-of-File6', 'Folder3/File6', False),
            ('commit()',),
            ('close()',),
            ('open()',),
            ('insert_fingerprint()', 'id-of-backup-of-id-of-File1', 'md5', f'md5({ev_mount_folder}/{backup_label}/Folder1/File1)', now, False),
            ('insert_fingerprint()', 'id-of-backup-of-id-of-File2', 'md5', f'md5({ev_mount_folder}/{backup_label}/Folder1/File2)', now, False),
            ('insert_fingerprint()', 'id-of-backup-of-id-of-File3', 'md5', f'md5({ev_mount_folder}/{backup_label}/Folder2/File3)', now, False),
            ('insert_fingerprint()', 'id-of-backup-of-id-of-File4', 'md5', f'md5({ev_mount_folder}/{backup_label}/Folder2/File4)', now, False),
            ('insert_fingerprint()', 'id-of-backup-of-id-of-File5', 'md5', f'md5({ev_mount_folder}/{backup_label}/Folder3/File5)', now, False),
            ('insert_fingerprint()', 'id-of-backup-of-id-of-File6', 'md5', f'md5({ev_mount_folder}/{backup_label}/Folder3/File6)', now, False),
            ('set_backup_check_latest_timestamp', new_backup_id, now),
            ('commit()',),
            ('close()',),
            # FILE SYSTEM
            ('remove_folder()', work_area),
            ('make_dirs()', f'{work_area}/{backup_label}_contents'),
            ('create_veracrypt_image', 'aes', 'sha-256', Config.encrypted_backup_key_file(), 443034407,
             f'{work_area}/{backup_label}_contents/{backup_label}.veracrypt'),
            ('mount_veracrypt_image()', f'{work_area}/{backup_label}_contents/{backup_label}.veracrypt', f'/Volumes/{backup_label}'),
            ('make_dirs()', f'/Volumes/{backup_label}/Folder1'),
            ('copy_with_xattrs()', '/foo/Folder1/File1', f'/Volumes/{backup_label}/Folder1/File1'),
            ('make_dirs()', f'/Volumes/{backup_label}/Folder1'),
            ('copy_with_xattrs()', '/foo/Folder1/File2', f'/Volumes/{backup_label}/Folder1/File2'),
            ('make_dirs()', f'/Volumes/{backup_label}/Folder2'),
            ('copy_with_xattrs()', '/foo/Folder2/File3', f'/Volumes/{backup_label}/Folder2/File3'),
            ('make_dirs()', f'/Volumes/{backup_label}/Folder2'),
            ('copy_with_xattrs()', '/foo/Folder2/File4', f'/Volumes/{backup_label}/Folder2/File4'),
            ('make_dirs()', f'/Volumes/{backup_label}/Folder3'),
            ('copy_with_xattrs()', '/foo/Folder3/File5', f'/Volumes/{backup_label}/Folder3/File5'),
            ('make_dirs()', f'/Volumes/{backup_label}/Folder3'),
            ('copy_with_xattrs()', '/foo/Folder3/File6', f'/Volumes/{backup_label}/Folder3/File6'),
            ('unmount_veracrypt_image()', f'/Volumes/{backup_label}'),
            ('create_hybrid_disk_image', backup_label, f'{work_area}/{backup_label}', f'{work_area}/{backup_label}_contents'),
            ('burn', f'{work_area}/{backup_label}.dmg'),
            ('make_dirs()', ev_mount_folder),
            ('mount_veracrypt_image()', f'/Volumes/{backup_label}/{backup_label}.veracrypt', f'{ev_mount_folder}/{backup_label}'),
            ('unmount_veracrypt_image()', f'{ev_mount_folder}/{backup_label}'),
            ('make_dirs()', ev_mount_folder),
            ('mount_veracrypt_image()', f'/Volumes/{backup_label}/{backup_label}.veracrypt', f'{ev_mount_folder}/{backup_label}'),
            ('unmount_veracrypt_image()', f'{ev_mount_folder}/{backup_label}'),
            ('unmount_optical_disk', f'/Volumes/{backup_label}'),
            ('eject_optical_disk()', f'/Volumes/{backup_label}'),
            ('remove_folder()', work_area),
            # PRESENTATION
            ('notify_counting()',),
            ('notify_message()', "Counting files in ['/foo/Folder1', '/foo/Folder2', '/foo/Folder3']..."),
            ('notify_file_count()', 6),
            ('notify_message()', 'Found 6 files (434.3 MB)'),
            ('notify_message()', f'Cleaning up working area ({work_area})...'),
            ('notify_message()', 'Veracrypt image size is 5.95 GB'),
            ('notify_message()', 'Mounting encrypted image...'),
            ('notify_message()', 'Copying files...'),
            ('notify_secondary_progress()', 0),
            ('notify_file()', 'File1', False),
            ('notify_secondary_progress()', 0.539357785633338),
            ('notify_file()', 'File2', False),
            ('notify_secondary_progress()', 0.6412129045333438),
            ('notify_file()', 'File3', False),
            ('notify_secondary_progress()', 0.8262487833536469),
            ('notify_file()', 'File4', False),
            ('notify_secondary_progress()', 0.839695124607949),
            ('notify_file()', 'File5', False),
            ('notify_secondary_progress()', 0.873298746173311),
            ('notify_file()', 'File6', False),
            ('notify_secondary_progress()', 1.0),
            ('notify_message()', 'Unmounting encrypted image...'),
            ('notify_message()', 'Burn image size is 5.95 GB'),
            ('notify_message()', f'Detected a VeraCrypt backup, mounting image at "{ev_mount_folder}/{backup_label}" ...'),
            ('notify_message()', f'Volume UUID {volume_uuid} created on None'),
            ('notify_counting()',),
            ('notify_message()', f"Counting files in ['{ev_mount_folder}/{backup_label}']..."),
            ('notify_file_count()', 6),
            ('notify_message()', 'Found 6 files (434.3 MB)'),
            ('notify_file()', 'Folder1/File1', True),
            ('notify_progress()', 1, 6),
            ('notify_file()', 'Folder1/File2', True),
            ('notify_progress()', 2, 6),
            ('notify_file()', 'Folder2/File3', True),
            ('notify_progress()', 3, 6),
            ('notify_file()', 'Folder2/File4', True),
            ('notify_progress()', 4, 6),
            ('notify_file()', 'Folder3/File5', True),
            ('notify_progress()', 5, 6),
            ('notify_file()', 'Folder3/File6', True),
            ('notify_progress()', 6, 6),
            ('notify_message()', f'Unmounting VeraCrypt image at "{ev_mount_folder}/{backup_label}" ...'),
            ('notify_message()', f'Detected a VeraCrypt backup, mounting image at "{ev_mount_folder}/{backup_label}" ...'),
            ('notify_counting()',),
            ('notify_message()', f"Counting files in ['{ev_mount_folder}/{backup_label}']..."),
            ('notify_file_count()', 6),
            ('notify_message()', 'Found 6 files (434.3 MB)'),
            ('notify_file()', 'Folder1/File1', False),
            ('notify_progress()', 234235545, 434286018),
            ('notify_file()', 'Folder1/File2', False),
            ('notify_progress()', 278469799, 434286018),
            ('notify_file()', 'Folder2/File3', False),
            ('notify_progress()', 358828294, 434286018),
            ('notify_file()', 'Folder2/File4', False),
            ('notify_progress()', 364667852, 434286018),
            ('notify_file()', 'Folder3/File5', False),
            ('notify_progress()', 379261435, 434286018),
            ('notify_file()', 'Folder3/File6', False),
            ('notify_progress()', 434286018, 434286018),
            ('notify_message()', f'Unmounting VeraCrypt image at "{ev_mount_folder}/{backup_label}" ...'),
            ('notify_message()', f'Cleaning up working area ({work_area})...')]
        self.assertEqual(actual, expected)

    #
    #
    #
    def test_veracrypt_post_processor(self):
        # GIVEN
        self.__setup_fixture()
        # WHEN
        with open(self.__test_resource('veracrypt/veracrypt.log'), 'rb') as file:
            process = MockProcess(file)
            self.executor.process_output(process, self.under_test.veracrypt_post_processor)
        # THEN
        expected = [
            ('notify_secondary_progress()', 0.126),
            ('notify_file()', 'Done:   0.126%  Speed: 3.7 MiB/s  Left: 36 minutes', False),
            ('notify_secondary_progress()', 0.504),
            ('notify_file()', 'Done:   0.504%  Speed:  14 MiB/s  Left: 9 minutes', False),
            ('notify_secondary_progress()', 0.882),
            ('notify_file()', 'Done:   0.882%  Speed:  24 MiB/s  Left: 5 minutes', False),
            ('notify_secondary_progress()', 1.272),
            ('notify_file()', 'Done:   1.272%  Speed:  33 MiB/s  Left: 3 minutes', False),
            ('notify_secondary_progress()', 1.64),
            ('notify_file()', 'Done:   1.640%  Speed:  41 MiB/s  Left: 3 minutes', False),
            ('notify_secondary_progress()', 2.009),
            ('notify_file()', 'Done:   2.009%  Speed:  49 MiB/s  Left: 2 minutes', False),
            ('notify_secondary_progress()', 2.38),
            ('notify_file()', 'Done:   2.380%  Speed:  57 MiB/s  Left: 2 minutes', False),
            ('notify_secondary_progress()', 2.755),
            ('notify_file()', 'Done:   2.755%  Speed:  64 MiB/s  Left: 2 minutes', False),
            ('notify_secondary_progress()', 3.075),
            ('notify_file()', 'Done:   3.075%  Speed:  69 MiB/s  Left: 113 s', False),
            ('notify_secondary_progress()', 3.363),
            ('notify_file()', 'Done:   3.363%  Speed:  74 MiB/s  Left: 106 s', False),
            ('notify_secondary_progress()', 3.615),
            ('notify_file()', 'Done:   3.615%  Speed:  77 MiB/s  Left: 101 s', False),
            ('notify_secondary_progress()', 3.95),
            ('notify_file()', 'Done:   3.950%  Speed:  82 MiB/s  Left: 94 s', False),
            ('notify_secondary_progress()', 4.291),
            ('notify_file()', 'Done:   4.291%  Speed:  87 MiB/s  Left: 89 s', False),
            ('notify_secondary_progress()', 4.632),
            ('notify_file()', 'Done:   4.632%  Speed:  91 MiB/s  Left: 84 s', False),
            ('notify_secondary_progress()', 4.991), ('notify_file()', 'Done:   4.991%  Speed:  96 MiB/s  Left: 80 s', False),
            ('notify_secondary_progress()', 5.329),
            ('notify_file()', 'Done:   5.329%  Speed: 100 MiB/s  Left: 76 s', False),
            ('notify_secondary_progress()', 5.688),
            ('notify_file()', 'Done:   5.688%  Speed: 105 MiB/s  Left: 73 s', False),
            ('notify_secondary_progress()', 6.032),
            ('notify_file()', 'Done:   6.032%  Speed: 108 MiB/s  Left: 70 s', False),
            ('notify_secondary_progress()', 6.358),
            ('notify_file()', 'Done:   6.358%  Speed: 112 MiB/s  Left: 67 s', False),
            ('notify_secondary_progress()', 6.708),
            ('notify_file()', 'Done:   6.708%  Speed: 115 MiB/s  Left: 65 s', False),
            ('notify_secondary_progress()', 7.074),
            ('notify_file()', 'Done:   7.074%  Speed: 119 MiB/s  Left: 63 s', False),
            ('notify_secondary_progress()', 7.408),
            ('notify_file()', 'Done:   7.408%  Speed: 122 MiB/s  Left: 61 s', False),
            ('notify_secondary_progress()', 7.762),
            ('notify_file()', 'Done:   7.762%  Speed: 125 MiB/s  Left: 59 s', False),
            ('notify_secondary_progress()', 8.102),
            ('notify_file()', 'Done:   8.102%  Speed: 128 MiB/s  Left: 58 s', False),
            ('notify_secondary_progress()', 8.287),
            ('notify_file()', 'Done:   8.287%  Speed: 129 MiB/s  Left: 57 s', False),
            ('notify_secondary_progress()', 8.606),
            ('notify_file()', 'Done:   8.606%  Speed: 131 MiB/s  Left: 56 s', False),
            ('notify_secondary_progress()', 8.944),
            ('notify_file()', 'Done:   8.944%  Speed: 134 MiB/s  Left: 55 s', False),
            ('notify_secondary_progress()', 9.236),
            ('notify_file()', 'Done:   9.236%  Speed: 135 MiB/s  Left: 54 s', False),
            ('notify_secondary_progress()', 9.564),
            ('notify_file()', 'Done:   9.564%  Speed: 138 MiB/s  Left: 53 s', False),
            ('notify_secondary_progress()', 9.902),
            ('notify_file()', 'Done:   9.902%  Speed: 140 MiB/s  Left: 52 s', False),
            ('notify_secondary_progress()', 10.213),
            ('notify_file()', 'Done:  10.213%  Speed: 142 MiB/s  Left: 51 s', False),
            ('notify_secondary_progress()', 10.514),
            ('notify_file()', 'Done:  10.514%  Speed: 144 MiB/s  Left: 50 s', False),
            ('notify_secondary_progress()', 10.851),
            ('notify_file()', 'Done:  10.851%  Speed: 146 MiB/s  Left: 49 s', False),
            ('notify_secondary_progress()', 11.202),
            ('notify_file()', 'Done:  11.202%  Speed: 148 MiB/s  Left: 48 s', False),
            ('notify_secondary_progress()', 11.561),
            ('notify_file()', 'Done:  11.561%  Speed: 150 MiB/s  Left: 47 s', False),
            ('notify_secondary_progress()', 11.899),
            ('notify_file()', 'Done:  11.899%  Speed: 152 MiB/s  Left: 46 s', False),
            ('notify_secondary_progress()', 12.24),
            ('notify_file()', 'Done:  12.240%  Speed: 154 MiB/s  Left: 46 s', False),
            ('notify_secondary_progress()', 12.578),
            ('notify_file()', 'Done:  12.578%  Speed: 156 MiB/s  Left: 45 s', False),
            ('notify_secondary_progress()', 12.872),
            ('notify_file()', 'Done:  12.872%  Speed: 157 MiB/s  Left: 44 s', False),
            ('notify_secondary_progress()', 13.244),
            ('notify_file()', 'Done:  13.244%  Speed: 159 MiB/s  Left: 44 s', False),
            ('notify_secondary_progress()', 13.579),
            ('notify_file()', 'Done:  13.579%  Speed: 161 MiB/s  Left: 43 s', False),
            ('notify_secondary_progress()', 13.944),
            ('notify_file()', 'Done:  13.944%  Speed: 163 MiB/s  Left: 42 s', False),
            ('notify_secondary_progress()', 14.288),
            ('notify_file()', 'Done:  14.288%  Speed: 165 MiB/s  Left: 42 s', False),
            ('notify_secondary_progress()', 14.642),
            ('notify_file()', 'Done:  14.642%  Speed: 166 MiB/s  Left: 41 s', False),
            ('notify_secondary_progress()', 15.004),
            ('notify_file()', 'Done:  15.004%  Speed: 168 MiB/s  Left: 41 s', False),
            ('notify_secondary_progress()', 15.345),
            ('notify_file()', 'Done:  15.345%  Speed: 169 MiB/s  Left: 40 s', False),
            ('notify_secondary_progress()', 15.698),
            ('notify_file()', 'Done:  15.698%  Speed: 171 MiB/s  Left: 39 s', False),
            ('notify_secondary_progress()', 16.018),
            ('notify_file()', 'Done:  16.018%  Speed: 172 MiB/s  Left: 39 s', False),
            ('notify_secondary_progress()', 16.374),
            ('notify_file()', 'Done:  16.374%  Speed: 174 MiB/s  Left: 39 s', False),
            ('notify_secondary_progress()', 16.706),
            ('notify_file()', 'Done:  16.706%  Speed: 175 MiB/s  Left: 38 s', False),
            ('notify_secondary_progress()', 17.068),
            ('notify_file()', 'Done:  17.068%  Speed: 176 MiB/s  Left: 38 s', False),
            ('notify_secondary_progress()', 17.406),
            ('notify_file()', 'Done:  17.406%  Speed: 178 MiB/s  Left: 37 s', False),
            ('notify_secondary_progress()', 17.765),
            ('notify_file()', 'Done:  17.765%  Speed: 179 MiB/s  Left: 37 s', False),
            ('notify_secondary_progress()', 18.109),
            ('notify_file()', 'Done:  18.109%  Speed: 180 MiB/s  Left: 36 s', False),
            ('notify_secondary_progress()', 18.469),
            ('notify_file()', 'Done:  18.469%  Speed: 182 MiB/s  Left: 36 s', False),
            ('notify_secondary_progress()', 18.819),
            ('notify_file()', 'Done:  18.819%  Speed: 183 MiB/s  Left: 36 s', False),
            ('notify_secondary_progress()', 19.163),
            ('notify_file()', 'Done:  19.163%  Speed: 184 MiB/s  Left: 35 s', False),
            ('notify_secondary_progress()', 19.494),
            ('notify_file()', 'Done:  19.494%  Speed: 185 MiB/s  Left: 35 s', False),
            ('notify_secondary_progress()', 19.851),
            ('notify_file()', 'Done:  19.851%  Speed: 186 MiB/s  Left: 34 s', False),
            ('notify_secondary_progress()', 19.974),
            ('notify_file()', 'Done:  19.974%  Speed: 185 MiB/s  Left: 35 s', False),
            ('notify_secondary_progress()', 20.259),
            ('notify_file()', 'Done:  20.259%  Speed: 186 MiB/s  Left: 34 s', False),
            ('notify_secondary_progress()', 20.637),
            ('notify_file()', 'Done:  20.637%  Speed: 187 MiB/s  Left: 34 s', False),
            ('notify_secondary_progress()', 20.984),
            ('notify_file()', 'Done:  20.984%  Speed: 188 MiB/s  Left: 34 s', False),
            ('notify_secondary_progress()', 21.331),
            ('notify_file()', 'Done:  21.331%  Speed: 189 MiB/s  Left: 33 s', False),
            ('notify_secondary_progress()', 21.687),
            ('notify_file()', 'Done:  21.687%  Speed: 190 MiB/s  Left: 33 s', False),
            ('notify_secondary_progress()', 22.013),
            ('notify_file()', 'Done:  22.013%  Speed: 191 MiB/s  Left: 33 s', False),
            ('notify_secondary_progress()', 22.317),
            ('notify_file()', 'Done:  22.317%  Speed: 191 MiB/s  Left: 32 s', False),
            ('notify_secondary_progress()', 22.501),
            ('notify_file()', 'Done:  22.501%  Speed: 191 MiB/s  Left: 32 s', False),
            ('notify_secondary_progress()', 22.772),
            ('notify_file()', 'Done:  22.772%  Speed: 191 MiB/s  Left: 32 s', False),
            ('notify_secondary_progress()', 23.11),
            ('notify_file()', 'Done:  23.110%  Speed: 192 MiB/s  Left: 32 s', False),
            ('notify_secondary_progress()', 23.438),
            ('notify_file()', 'Done:  23.438%  Speed: 193 MiB/s  Left: 32 s', False),
            ('notify_secondary_progress()', 23.782),
            ('notify_file()', 'Done:  23.782%  Speed: 194 MiB/s  Left: 31 s', False),
            ('notify_secondary_progress()', 24.12),
            ('notify_file()', 'Done:  24.120%  Speed: 194 MiB/s  Left: 31 s', False),
            ('notify_secondary_progress()', 24.464),
            ('notify_file()', 'Done:  24.464%  Speed: 195 MiB/s  Left: 31 s', False),
            ('notify_secondary_progress()', 24.762),
            ('notify_file()', 'Done:  24.762%  Speed: 196 MiB/s  Left: 31 s', False),
            ('notify_secondary_progress()', 25.06),
            ('notify_file()', 'Done:  25.060%  Speed: 196 MiB/s  Left: 31 s', False),
            ('notify_secondary_progress()', 25.244),
            ('notify_file()', 'Done:  25.244%  Speed: 196 MiB/s  Left: 31 s', False),
            ('notify_secondary_progress()', 25.422),
            ('notify_file()', 'Done:  25.422%  Speed: 195 MiB/s  Left: 31 s', False),
            ('notify_secondary_progress()', 25.671),
            ('notify_file()', 'Done:  25.671%  Speed: 195 MiB/s  Left: 30 s', False),
            ('notify_secondary_progress()', 25.929),
            ('notify_file()', 'Done:  25.929%  Speed: 195 MiB/s  Left: 30 s', False),
            ('notify_secondary_progress()', 26.267),
            ('notify_file()', 'Done:  26.267%  Speed: 196 MiB/s  Left: 30 s', False),
            ('notify_secondary_progress()', 26.553),
            ('notify_file()', 'Done:  26.553%  Speed: 196 MiB/s  Left: 30 s', False),
            ('notify_secondary_progress()', 26.731),
            ('notify_file()', 'Done:  26.731%  Speed: 196 MiB/s  Left: 30 s', False),
            ('notify_secondary_progress()', 27.047),
            ('notify_file()', 'Done:  27.047%  Speed: 196 MiB/s  Left: 30 s', False),
            ('notify_secondary_progress()', 27.41),
            ('notify_file()', 'Done:  27.410%  Speed: 197 MiB/s  Left: 29 s', False),
            ('notify_secondary_progress()', 27.766),
            ('notify_file()', 'Done:  27.766%  Speed: 198 MiB/s  Left: 29 s', False),
            ('notify_secondary_progress()', 28.11),
            ('notify_file()', 'Done:  28.110%  Speed: 199 MiB/s  Left: 29 s', False),
            ('notify_secondary_progress()', 28.448),
            ('notify_file()', 'Done:  28.448%  Speed: 199 MiB/s  Left: 29 s', False),
            ('notify_secondary_progress()', 28.795),
            ('notify_file()', 'Done:  28.795%  Speed: 200 MiB/s  Left: 28 s', False),
            ('notify_secondary_progress()', 29.139),
            ('notify_file()', 'Done:  29.139%  Speed: 200 MiB/s  Left: 28 s', False),
            ('notify_secondary_progress()', 29.474),
            ('notify_file()', 'Done:  29.474%  Speed: 201 MiB/s  Left: 28 s', False),
            ('notify_secondary_progress()', 29.799),
            ('notify_file()', 'Done:  29.799%  Speed: 202 MiB/s  Left: 28 s', False),
            ('notify_secondary_progress()', 30.106),
            ('notify_file()', 'Done:  30.106%  Speed: 202 MiB/s  Left: 28 s', False),
            ('notify_secondary_progress()', 30.466),
            ('notify_file()', 'Done:  30.466%  Speed: 203 MiB/s  Left: 27 s', False),
            ('notify_secondary_progress()', 30.816),
            ('notify_file()', 'Done:  30.816%  Speed: 203 MiB/s  Left: 27 s', False),
            ('notify_secondary_progress()', 31.154),
            ('notify_file()', 'Done:  31.154%  Speed: 204 MiB/s  Left: 27 s', False),
            ('notify_secondary_progress()', 31.449),
            ('notify_file()', 'Done:  31.449%  Speed: 204 MiB/s  Left: 27 s', False),
            ('notify_secondary_progress()', 31.759),
            ('notify_file()', 'Done:  31.759%  Speed: 205 MiB/s  Left: 27 s', False),
            ('notify_secondary_progress()', 31.937),
            ('notify_file()', 'Done:  31.937%  Speed: 204 MiB/s  Left: 27 s', False),
            ('notify_secondary_progress()', 32.235),
            ('notify_file()', 'Done:  32.235%  Speed: 204 MiB/s  Left: 26 s', False),
            ('notify_secondary_progress()', 32.582),
            ('notify_file()', 'Done:  32.582%  Speed: 205 MiB/s  Left: 26 s', False),
            ('notify_secondary_progress()', 32.917),
            ('notify_file()', 'Done:  32.917%  Speed: 205 MiB/s  Left: 26 s', False),
            ('notify_secondary_progress()', 33.255),
            ('notify_file()', 'Done:  33.255%  Speed: 206 MiB/s  Left: 26 s', False),
            ('notify_secondary_progress()', 33.608),
            ('notify_file()', 'Done:  33.608%  Speed: 207 MiB/s  Left: 26 s', False),
            ('notify_secondary_progress()', 33.946),
            ('notify_file()', 'Done:  33.946%  Speed: 207 MiB/s  Left: 25 s', False),
            ('notify_secondary_progress()', 34.296),
            ('notify_file()', 'Done:  34.296%  Speed: 208 MiB/s  Left: 25 s', False),
            ('notify_secondary_progress()', 34.631),
            ('notify_file()', 'Done:  34.631%  Speed: 208 MiB/s  Left: 25 s', False),
            ('notify_secondary_progress()', 34.975),
            ('notify_file()', 'Done:  34.975%  Speed: 209 MiB/s  Left: 25 s', False),
            ('notify_secondary_progress()', 35.316),
            ('notify_file()', 'Done:  35.316%  Speed: 209 MiB/s  Left: 25 s', False),
            ('notify_secondary_progress()', 35.666),
            ('notify_file()', 'Done:  35.666%  Speed: 210 MiB/s  Left: 24 s', False),
            ('notify_secondary_progress()', 35.982),
            ('notify_file()', 'Done:  35.982%  Speed: 210 MiB/s  Left: 24 s', False),
            ('notify_secondary_progress()', 36.323),
            ('notify_file()', 'Done:  36.323%  Speed: 210 MiB/s  Left: 24 s', False),
            ('notify_secondary_progress()', 36.658),
            ('notify_file()', 'Done:  36.658%  Speed: 211 MiB/s  Left: 24 s', False),
            ('notify_secondary_progress()', 37.005),
            ('notify_file()', 'Done:  37.005%  Speed: 211 MiB/s  Left: 24 s', False),
            ('notify_secondary_progress()', 37.346),
            ('notify_file()', 'Done:  37.346%  Speed: 212 MiB/s  Left: 24 s', False),
            ('notify_secondary_progress()', 37.677),
            ('notify_file()', 'Done:  37.677%  Speed: 212 MiB/s  Left: 23 s', False),
            ('notify_secondary_progress()', 38.009),
            ('notify_file()', 'Done:  38.009%  Speed: 213 MiB/s  Left: 23 s', False),
            ('notify_secondary_progress()', 38.338),
            ('notify_file()', 'Done:  38.338%  Speed: 213 MiB/s  Left: 23 s', False),
            ('notify_secondary_progress()', 38.688),
            ('notify_file()', 'Done:  38.688%  Speed: 213 MiB/s  Left: 23 s', False),
            ('notify_secondary_progress()', 39.017),
            ('notify_file()', 'Done:  39.017%  Speed: 214 MiB/s  Left: 23 s', False),
            ('notify_secondary_progress()', 39.336),
            ('notify_file()', 'Done:  39.336%  Speed: 214 MiB/s  Left: 23 s', False),
            ('notify_secondary_progress()', 39.674),
            ('notify_file()', 'Done:  39.674%  Speed: 215 MiB/s  Left: 22 s', False),
            ('notify_secondary_progress()', 39.999),
            ('notify_file()', 'Done:  39.999%  Speed: 215 MiB/s  Left: 22 s', False),
            ('notify_secondary_progress()', 40.337),
            ('notify_file()', 'Done:  40.337%  Speed: 215 MiB/s  Left: 22 s', False),
            ('notify_secondary_progress()', 40.678),
            ('notify_file()', 'Done:  40.678%  Speed: 216 MiB/s  Left: 22 s', False),
            ('notify_secondary_progress()', 41.004),
            ('notify_file()', 'Done:  41.004%  Speed: 216 MiB/s  Left: 22 s', False),
            ('notify_secondary_progress()', 41.329),
            ('notify_file()', 'Done:  41.329%  Speed: 216 MiB/s  Left: 22 s', False),
            ('notify_secondary_progress()', 41.67),
            ('notify_file()', 'Done:  41.670%  Speed: 217 MiB/s  Left: 21 s', False),
            ('notify_secondary_progress()', 42.005),
            ('notify_file()', 'Done:  42.005%  Speed: 217 MiB/s  Left: 21 s', False),
            ('notify_secondary_progress()', 42.349),
            ('notify_file()', 'Done:  42.349%  Speed: 217 MiB/s  Left: 21 s', False),
            ('notify_secondary_progress()', 42.672),
            ('notify_file()', 'Done:  42.672%  Speed: 218 MiB/s  Left: 21 s', False),
            ('notify_secondary_progress()', 43.022),
            ('notify_file()', 'Done:  43.022%  Speed: 218 MiB/s  Left: 21 s', False),
            ('notify_secondary_progress()', 43.35),
            ('notify_file()', 'Done:  43.350%  Speed: 218 MiB/s  Left: 21 s', False),
            ('notify_secondary_progress()', 43.587),
            ('notify_file()', 'Done:  43.587%  Speed: 218 MiB/s  Left: 21 s', False),
            ('notify_secondary_progress()', 43.787),
            ('notify_file()', 'Done:  43.787%  Speed: 218 MiB/s  Left: 20 s', False),
            ('notify_secondary_progress()', 44.115),
            ('notify_file()', 'Done:  44.115%  Speed: 218 MiB/s  Left: 20 s', False),
            ('notify_secondary_progress()', 44.429),
            ('notify_file()', 'Done:  44.429%  Speed: 218 MiB/s  Left: 20 s', False),
            ('notify_secondary_progress()', 44.766),
            ('notify_file()', 'Done:  44.766%  Speed: 219 MiB/s  Left: 20 s', False),
            ('notify_secondary_progress()', 45.098),
            ('notify_file()', 'Done:  45.098%  Speed: 219 MiB/s  Left: 20 s', False),
            ('notify_secondary_progress()', 45.405),
            ('notify_file()', 'Done:  45.405%  Speed: 219 MiB/s  Left: 20 s', False),
            ('notify_secondary_progress()', 45.725),
            ('notify_file()', 'Done:  45.725%  Speed: 219 MiB/s  Left: 20 s', False),
            ('notify_secondary_progress()', 46.081),
            ('notify_file()', 'Done:  46.081%  Speed: 219 MiB/s  Left: 19 s', False),
            ('notify_secondary_progress()', 46.403),
            ('notify_file()', 'Done:  46.403%  Speed: 220 MiB/s  Left: 19 s', False),
            ('notify_secondary_progress()', 46.625),
            ('notify_file()', 'Done:  46.625%  Speed: 219 MiB/s  Left: 19 s', False),
            ('notify_secondary_progress()', 46.852),
            ('notify_file()', 'Done:  46.852%  Speed: 219 MiB/s  Left: 19 s', False),
            ('notify_secondary_progress()', 47.174),
            ('notify_file()', 'Done:  47.174%  Speed: 220 MiB/s  Left: 19 s', False),
            ('notify_secondary_progress()', 47.531),
            ('notify_file()', 'Done:  47.531%  Speed: 220 MiB/s  Left: 19 s', False),
            ('notify_secondary_progress()', 47.862),
            ('notify_file()', 'Done:  47.862%  Speed: 220 MiB/s  Left: 19 s', False),
            ('notify_secondary_progress()', 48.004),
            ('notify_file()', 'Done:  48.004%  Speed: 220 MiB/s  Left: 19 s', False),
            ('notify_secondary_progress()', 48.289),
            ('notify_file()', 'Done:  48.289%  Speed: 220 MiB/s  Left: 19 s', False),
            ('notify_secondary_progress()', 48.649),
            ('notify_file()', 'Done:  48.649%  Speed: 220 MiB/s  Left: 18 s', False),
            ('notify_secondary_progress()', 48.901),
            ('notify_file()', 'Done:  48.901%  Speed: 220 MiB/s  Left: 18 s', False),
            ('notify_secondary_progress()', 49.073),
            ('notify_file()', 'Done:  49.073%  Speed: 219 MiB/s  Left: 18 s', False),
            ('notify_secondary_progress()', 49.413),
            ('notify_file()', 'Done:  49.413%  Speed: 220 MiB/s  Left: 18 s', False),
            ('notify_secondary_progress()', 49.748),
            ('notify_file()', 'Done:  49.748%  Speed: 220 MiB/s  Left: 18 s', False),
            ('notify_secondary_progress()', 50.108),
            ('notify_file()', 'Done:  50.108%  Speed: 220 MiB/s  Left: 18 s', False),
            ('notify_secondary_progress()', 50.396),
            ('notify_file()', 'Done:  50.396%  Speed: 220 MiB/s  Left: 18 s', False),
            ('notify_secondary_progress()', 50.728),
            ('notify_file()', 'Done:  50.728%  Speed: 221 MiB/s  Left: 18 s', False),
            ('notify_secondary_progress()', 51.072),
            ('notify_file()', 'Done:  51.072%  Speed: 221 MiB/s  Left: 17 s', False),
            ('notify_secondary_progress()', 51.302),
            ('notify_file()', 'Done:  51.302%  Speed: 221 MiB/s  Left: 17 s', False),
            ('notify_secondary_progress()', 51.505),
            ('notify_file()', 'Done:  51.505%  Speed: 221 MiB/s  Left: 17 s', False),
            ('notify_secondary_progress()', 51.84),
            ('notify_file()', 'Done:  51.840%  Speed: 221 MiB/s  Left: 17 s', False),
            ('notify_secondary_progress()', 52.187),
            ('notify_file()', 'Done:  52.187%  Speed: 221 MiB/s  Left: 17 s', False),
            ('notify_secondary_progress()', 52.516),
            ('notify_file()', 'Done:  52.516%  Speed: 221 MiB/s  Left: 17 s', False),
            ('notify_secondary_progress()', 52.86),
            ('notify_file()', 'Done:  52.860%  Speed: 222 MiB/s  Left: 17 s', False),
            ('notify_secondary_progress()', 53.185),
            ('notify_file()', 'Done:  53.185%  Speed: 222 MiB/s  Left: 17 s', False),
            ('notify_secondary_progress()', 53.366),
            ('notify_file()', 'Done:  53.366%  Speed: 221 MiB/s  Left: 17 s', False),
            ('notify_secondary_progress()', 53.615),
            ('notify_file()', 'Done:  53.615%  Speed: 221 MiB/s  Left: 17 s', False),
            ('notify_secondary_progress()', 53.965),
            ('notify_file()', 'Done:  53.965%  Speed: 222 MiB/s  Left: 16 s', False),
            ('notify_secondary_progress()', 54.245),
            ('notify_file()', 'Done:  54.245%  Speed: 222 MiB/s  Left: 16 s', False),
            ('notify_secondary_progress()', 54.558),
            ('notify_file()', 'Done:  54.558%  Speed: 222 MiB/s  Left: 16 s', False),
            ('notify_secondary_progress()', 54.878),
            ('notify_file()', 'Done:  54.878%  Speed: 222 MiB/s  Left: 16 s', False),
            ('notify_secondary_progress()', 55.234),
            ('notify_file()', 'Done:  55.234%  Speed: 222 MiB/s  Left: 16 s', False),
            ('notify_secondary_progress()', 55.553),
            ('notify_file()', 'Done:  55.553%  Speed: 222 MiB/s  Left: 16 s', False),
            ('notify_secondary_progress()', 55.867),
            ('notify_file()', 'Done:  55.867%  Speed: 223 MiB/s  Left: 16 s', False),
            ('notify_secondary_progress()', 56.198),
            ('notify_file()', 'Done:  56.198%  Speed: 223 MiB/s  Left: 15 s', False),
            ('notify_secondary_progress()', 56.512),
            ('notify_file()', 'Done:  56.512%  Speed: 223 MiB/s  Left: 15 s', False),
            ('notify_secondary_progress()', 56.843),
            ('notify_file()', 'Done:  56.843%  Speed: 223 MiB/s  Left: 15 s', False),
            ('notify_secondary_progress()', 57.166),
            ('notify_file()', 'Done:  57.166%  Speed: 223 MiB/s  Left: 15 s', False),
            ('notify_secondary_progress()', 57.501),
            ('notify_file()', 'Done:  57.501%  Speed: 224 MiB/s  Left: 15 s', False),
            ('notify_secondary_progress()', 57.838),
            ('notify_file()', 'Done:  57.838%  Speed: 224 MiB/s  Left: 15 s', False),
            ('notify_secondary_progress()', 58.179),
            ('notify_file()', 'Done:  58.179%  Speed: 224 MiB/s  Left: 15 s', False),
            ('notify_secondary_progress()', 58.514),
            ('notify_file()', 'Done:  58.514%  Speed: 224 MiB/s  Left: 15 s', False),
            ('notify_secondary_progress()', 58.87),
            ('notify_file()', 'Done:  58.870%  Speed: 225 MiB/s  Left: 14 s', False),
            ('notify_secondary_progress()', 59.178),
            ('notify_file()', 'Done:  59.178%  Speed: 225 MiB/s  Left: 14 s', False),
            ('notify_secondary_progress()', 59.343),
            ('notify_file()', 'Done:  59.343%  Speed: 224 MiB/s  Left: 14 s', False),
            ('notify_secondary_progress()', 59.58),
            ('notify_file()', 'Done:  59.580%  Speed: 224 MiB/s  Left: 14 s', False),
            ('notify_secondary_progress()', 59.939),
            ('notify_file()', 'Done:  59.939%  Speed: 224 MiB/s  Left: 14 s', False),
            ('notify_secondary_progress()', 60.286),
            ('notify_file()', 'Done:  60.286%  Speed: 225 MiB/s  Left: 14 s', False),
            ('notify_secondary_progress()', 60.64),
            ('notify_file()', 'Done:  60.640%  Speed: 225 MiB/s  Left: 14 s', False),
            ('notify_secondary_progress()', 60.977),
            ('notify_file()', 'Done:  60.977%  Speed: 225 MiB/s  Left: 14 s', False),
            ('notify_secondary_progress()', 61.328),
            ('notify_file()', 'Done:  61.328%  Speed: 225 MiB/s  Left: 13 s', False),
            ('notify_secondary_progress()', 61.665),
            ('notify_file()', 'Done:  61.665%  Speed: 226 MiB/s  Left: 13 s', False),
            ('notify_secondary_progress()', 62.016),
            ('notify_file()', 'Done:  62.016%  Speed: 226 MiB/s  Left: 13 s', False),
            ('notify_secondary_progress()', 62.36),
            ('notify_file()', 'Done:  62.360%  Speed: 226 MiB/s  Left: 13 s', False),
            ('notify_secondary_progress()', 62.691),
            ('notify_file()', 'Done:  62.691%  Speed: 226 MiB/s  Left: 13 s', False),
            ('notify_secondary_progress()', 63.005),
            ('notify_file()', 'Done:  63.005%  Speed: 226 MiB/s  Left: 13 s', False),
            ('notify_secondary_progress()', 63.339),
            ('notify_file()', 'Done:  63.339%  Speed: 227 MiB/s  Left: 13 s', False),
            ('notify_secondary_progress()', 63.677),
            ('notify_file()', 'Done:  63.677%  Speed: 227 MiB/s  Left: 13 s', False),
            ('notify_secondary_progress()', 63.981),
            ('notify_file()', 'Done:  63.981%  Speed: 227 MiB/s  Left: 12 s', False),
            ('notify_secondary_progress()', 64.319),
            ('notify_file()', 'Done:  64.319%  Speed: 227 MiB/s  Left: 12 s', False),
            ('notify_secondary_progress()', 64.497),
            ('notify_file()', 'Done:  64.497%  Speed: 227 MiB/s  Left: 12 s', False),
            ('notify_secondary_progress()', 64.768),
            ('notify_file()', 'Done:  64.768%  Speed: 227 MiB/s  Left: 12 s', False),
            ('notify_secondary_progress()', 65.109),
            ('notify_file()', 'Done:  65.109%  Speed: 227 MiB/s  Left: 12 s', False),
            ('notify_secondary_progress()', 65.446),
            ('notify_file()', 'Done:  65.446%  Speed: 227 MiB/s  Left: 12 s', False),
            ('notify_secondary_progress()', 65.763),
            ('notify_file()', 'Done:  65.763%  Speed: 227 MiB/s  Left: 12 s', False),
            ('notify_secondary_progress()', 66.101),
            ('notify_file()', 'Done:  66.101%  Speed: 227 MiB/s  Left: 12 s', False),
            ('notify_secondary_progress()', 66.439),
            ('notify_file()', 'Done:  66.439%  Speed: 228 MiB/s  Left: 11 s', False),
            ('notify_secondary_progress()', 66.758),
            ('notify_file()', 'Done:  66.758%  Speed: 228 MiB/s  Left: 11 s', False),
            ('notify_secondary_progress()', 67.099),
            ('notify_file()', 'Done:  67.099%  Speed: 228 MiB/s  Left: 11 s', False),
            ('notify_secondary_progress()', 67.421),
            ('notify_file()', 'Done:  67.421%  Speed: 228 MiB/s  Left: 11 s', False),
            ('notify_secondary_progress()', 67.756),
            ('notify_file()', 'Done:  67.756%  Speed: 228 MiB/s  Left: 11 s', False),
            ('notify_secondary_progress()', 68.091),
            ('notify_file()', 'Done:  68.091%  Speed: 228 MiB/s  Left: 11 s', False),
            ('notify_secondary_progress()', 68.404),
            ('notify_file()', 'Done:  68.404%  Speed: 228 MiB/s  Left: 11 s', False),
            ('notify_secondary_progress()', 68.727),
            ('notify_file()', 'Done:  68.727%  Speed: 229 MiB/s  Left: 11 s', False),
            ('notify_secondary_progress()', 68.896),
            ('notify_file()', 'Done:  68.896%  Speed: 228 MiB/s  Left: 11 s', False),
            ('notify_secondary_progress()', 68.994),
            ('notify_file()', 'Done:  68.994%  Speed: 228 MiB/s  Left: 11 s', False),
            ('notify_secondary_progress()', 69.191),
            ('notify_file()', 'Done:  69.191%  Speed: 227 MiB/s  Left: 11 s', False),
            ('notify_secondary_progress()', 69.313),
            ('notify_file()', 'Done:  69.313%  Speed: 227 MiB/s  Left: 10 s', False),
            ('notify_secondary_progress()', 69.485),
            ('notify_file()', 'Done:  69.485%  Speed: 226 MiB/s  Left: 10 s', False),
            ('notify_secondary_progress()', 69.584),
            ('notify_file()', 'Done:  69.584%  Speed: 226 MiB/s  Left: 10 s', False),
            ('notify_secondary_progress()', 69.75),
            ('notify_file()', 'Done:  69.750%  Speed: 225 MiB/s  Left: 10 s', False),
            ('notify_secondary_progress()', 69.879),
            ('notify_file()', 'Done:  69.879%  Speed: 225 MiB/s  Left: 10 s', False),
            ('notify_secondary_progress()', 69.998),
            ('notify_file()', 'Done:  69.998%  Speed: 224 MiB/s  Left: 10 s', False),
            ('notify_secondary_progress()', 70.173),
            ('notify_file()', 'Done:  70.173%  Speed: 224 MiB/s  Left: 10 s', False),
            ('notify_secondary_progress()', 70.272),
            ('notify_file()', 'Done:  70.272%  Speed: 224 MiB/s  Left: 10 s', False),
            ('notify_secondary_progress()', 70.468),
            ('notify_file()', 'Done:  70.468%  Speed: 223 MiB/s  Left: 10 s', False),
            ('notify_secondary_progress()', 70.567),
            ('notify_file()', 'Done:  70.567%  Speed: 223 MiB/s  Left: 10 s', False),
            ('notify_secondary_progress()', 70.739),
            ('notify_file()', 'Done:  70.739%  Speed: 222 MiB/s  Left: 10 s', False),
            ('notify_secondary_progress()', 70.861),
            ('notify_file()', 'Done:  70.861%  Speed: 222 MiB/s  Left: 10 s', False),
            ('notify_secondary_progress()', 70.993),
            ('notify_file()', 'Done:  70.993%  Speed: 221 MiB/s  Left: 10 s', False),
            ('notify_secondary_progress()', 71.156),
            ('notify_file()', 'Done:  71.156%  Speed: 221 MiB/s  Left: 10 s', False),
            ('notify_secondary_progress()', 71.279),
            ('notify_file()', 'Done:  71.279%  Speed: 221 MiB/s  Left: 10 s', False),
            ('notify_secondary_progress()', 71.451),
            ('notify_file()', 'Done:  71.451%  Speed: 220 MiB/s  Left: 10 s', False),
            ('notify_secondary_progress()', 71.645),
            ('notify_file()', 'Done:  71.645%  Speed: 220 MiB/s  Left: 10 s', False),
            ('notify_secondary_progress()', 71.746),
            ('notify_file()', 'Done:  71.746%  Speed: 219 MiB/s  Left: 10 s', False),
            ('notify_secondary_progress()', 71.943),
            ('notify_file()', 'Done:  71.943%  Speed: 219 MiB/s  Left: 10 s', False),
            ('notify_secondary_progress()', 72.047),
            ('notify_file()', 'Done:  72.047%  Speed: 219 MiB/s  Left: 10 s', False),
            ('notify_secondary_progress()', 72.237),
            ('notify_file()', 'Done:  72.237%  Speed: 218 MiB/s  Left: 10 s', False),
            ('notify_secondary_progress()', 72.36),
            ('notify_file()', 'Done:  72.360%  Speed: 218 MiB/s  Left: 10 s', False),
            ('notify_secondary_progress()', 72.532),
            ('notify_file()', 'Done:  72.532%  Speed: 218 MiB/s  Left: 10 s', False),
            ('notify_secondary_progress()', 72.735),
            ('notify_file()', 'Done:  72.735%  Speed: 218 MiB/s  Left: 10 s', False),
            ('notify_secondary_progress()', 72.944),
            ('notify_file()', 'Done:  72.944%  Speed: 217 MiB/s  Left: 10 s', False),
            ('notify_secondary_progress()', 73.183),
            ('notify_file()', 'Done:  73.183%  Speed: 217 MiB/s  Left: 10 s', False),
            ('notify_secondary_progress()', 73.411),
            ('notify_file()', 'Done:  73.411%  Speed: 217 MiB/s  Left: 9 s', False),
            ('notify_secondary_progress()', 73.613),
            ('notify_file()', 'Done:  73.613%  Speed: 217 MiB/s  Left: 9 s', False),
            ('notify_secondary_progress()', 73.81),
            ('notify_file()', 'Done:  73.810%  Speed: 217 MiB/s  Left: 9 s', False),
            ('notify_secondary_progress()', 74.007),
            ('notify_file()', 'Done:  74.007%  Speed: 216 MiB/s  Left: 9 s', False),
            ('notify_secondary_progress()', 74.203),
            ('notify_file()', 'Done:  74.203%  Speed: 216 MiB/s  Left: 9 s', False),
            ('notify_secondary_progress()', 74.403),
            ('notify_file()', 'Done:  74.403%  Speed: 216 MiB/s  Left: 9 s', False),
            ('notify_secondary_progress()', 74.602),
            ('notify_file()', 'Done:  74.602%  Speed: 216 MiB/s  Left: 9 s', False),
            ('notify_secondary_progress()', 74.796),
            ('notify_file()', 'Done:  74.796%  Speed: 216 MiB/s  Left: 9 s', False),
            ('notify_secondary_progress()', 74.996),
            ('notify_file()', 'Done:  74.996%  Speed: 215 MiB/s  Left: 9 s', False),
            ('notify_secondary_progress()', 75.207),
            ('notify_file()', 'Done:  75.207%  Speed: 215 MiB/s  Left: 9 s', False),
            ('notify_secondary_progress()', 75.429),
            ('notify_file()', 'Done:  75.429%  Speed: 215 MiB/s  Left: 9 s', False),
            ('notify_secondary_progress()', 75.653),
            ('notify_file()', 'Done:  75.653%  Speed: 215 MiB/s  Left: 9 s', False),
            ('notify_secondary_progress()', 75.874),
            ('notify_file()', 'Done:  75.874%  Speed: 215 MiB/s  Left: 9 s', False),
            ('notify_secondary_progress()', 76.071),
            ('notify_file()', 'Done:  76.071%  Speed: 215 MiB/s  Left: 9 s', False),
            ('notify_secondary_progress()', 76.267),
            ('notify_file()', 'Done:  76.267%  Speed: 214 MiB/s  Left: 8 s', False),
            ('notify_secondary_progress()', 76.451),
            ('notify_file()', 'Done:  76.451%  Speed: 214 MiB/s  Left: 8 s', False),
            ('notify_secondary_progress()', 76.562),
            ('notify_file()', 'Done:  76.562%  Speed: 214 MiB/s  Left: 8 s', False),
            ('notify_secondary_progress()', 76.749),
            ('notify_file()', 'Done:  76.749%  Speed: 213 MiB/s  Left: 8 s', False),
            ('notify_secondary_progress()', 76.857),
            ('notify_file()', 'Done:  76.857%  Speed: 213 MiB/s  Left: 8 s', False),
            ('notify_secondary_progress()', 77.05),
            ('notify_file()', 'Done:  77.050%  Speed: 213 MiB/s  Left: 8 s', False),
            ('notify_secondary_progress()', 77.152),
            ('notify_file()', 'Done:  77.152%  Speed: 212 MiB/s  Left: 8 s', False),
            ('notify_secondary_progress()', 77.308),
            ('notify_file()', 'Done:  77.308%  Speed: 212 MiB/s  Left: 8 s', False),
            ('notify_secondary_progress()', 77.447),
            ('notify_file()', 'Done:  77.447%  Speed: 212 MiB/s  Left: 8 s', False),
            ('notify_secondary_progress()', 77.566),
            ('notify_file()', 'Done:  77.566%  Speed: 211 MiB/s  Left: 8 s', False),
            ('notify_secondary_progress()', 77.741),
            ('notify_file()', 'Done:  77.741%  Speed: 211 MiB/s  Left: 8 s', False),
            ('notify_secondary_progress()', 77.843),
            ('notify_file()', 'Done:  77.843%  Speed: 211 MiB/s  Left: 8 s', False),
            ('notify_secondary_progress()', 78.036),
            ('notify_file()', 'Done:  78.036%  Speed: 210 MiB/s  Left: 8 s', False),
            ('notify_secondary_progress()', 78.135),
            ('notify_file()', 'Done:  78.135%  Speed: 210 MiB/s  Left: 8 s', False),
            ('notify_secondary_progress()', 78.233),
            ('notify_file()', 'Done:  78.233%  Speed: 210 MiB/s  Left: 8 s', False),
            ('notify_secondary_progress()', 78.402),
            ('notify_file()', 'Done:  78.402%  Speed: 209 MiB/s  Left: 8 s', False),
            ('notify_secondary_progress()', 78.528),
            ('notify_file()', 'Done:  78.528%  Speed: 209 MiB/s  Left: 8 s', False),
            ('notify_secondary_progress()', 78.626),
            ('notify_file()', 'Done:  78.626%  Speed: 208 MiB/s  Left: 8 s', False),
            ('notify_secondary_progress()', 78.81),
            ('notify_file()', 'Done:  78.810%  Speed: 208 MiB/s  Left: 8 s', False),
            ('notify_secondary_progress()', 78.909),
            ('notify_file()', 'Done:  78.909%  Speed: 208 MiB/s  Left: 8 s', False),
            ('notify_secondary_progress()', 79.121),
            ('notify_file()', 'Done:  79.121%  Speed: 208 MiB/s  Left: 8 s', False),
            ('notify_secondary_progress()', 79.32),
            ('notify_file()', 'Done:  79.320%  Speed: 208 MiB/s  Left: 8 s', False),
            ('notify_secondary_progress()', 79.523),
            ('notify_file()', 'Done:  79.523%  Speed: 207 MiB/s  Left: 8 s', False),
            ('notify_secondary_progress()', 79.741),
            ('notify_file()', 'Done:  79.741%  Speed: 207 MiB/s  Left: 7 s', False),
            ('notify_secondary_progress()', 79.959),
            ('notify_file()', 'Done:  79.959%  Speed: 207 MiB/s  Left: 7 s', False),
            ('notify_secondary_progress()', 80.186),
            ('notify_file()', 'Done:  80.186%  Speed: 207 MiB/s  Left: 7 s', False),
            ('notify_secondary_progress()', 80.383),
            ('notify_file()', 'Done:  80.383%  Speed: 207 MiB/s  Left: 7 s', False),
            ('notify_secondary_progress()', 80.579),
            ('notify_file()', 'Done:  80.579%  Speed: 207 MiB/s  Left: 7 s', False),
            ('notify_secondary_progress()', 80.776),
            ('notify_file()', 'Done:  80.776%  Speed: 207 MiB/s  Left: 7 s', False),
            ('notify_secondary_progress()', 80.911),
            ('notify_file()', 'Done:  80.911%  Speed: 206 MiB/s  Left: 7 s', False),
            ('notify_secondary_progress()', 81.071),
            ('notify_file()', 'Done:  81.071%  Speed: 206 MiB/s  Left: 7 s', False),
            ('notify_secondary_progress()', 81.203),
            ('notify_file()', 'Done:  81.203%  Speed: 206 MiB/s  Left: 7 s', False),
            ('notify_secondary_progress()', 81.366),
            ('notify_file()', 'Done:  81.366%  Speed: 205 MiB/s  Left: 7 s', False),
            ('notify_secondary_progress()', 81.498),
            ('notify_file()', 'Done:  81.498%  Speed: 205 MiB/s  Left: 7 s', False),
            ('notify_secondary_progress()', 81.661),
            ('notify_file()', 'Done:  81.661%  Speed: 205 MiB/s  Left: 7 s', False),
            ('notify_secondary_progress()', 81.777),
            ('notify_file()', 'Done:  81.777%  Speed: 204 MiB/s  Left: 7 s', False),
            ('notify_secondary_progress()', 81.955),
            ('notify_file()', 'Done:  81.955%  Speed: 204 MiB/s  Left: 7 s', False),
            ('notify_secondary_progress()', 82.06),
            ('notify_file()', 'Done:  82.060%  Speed: 204 MiB/s  Left: 7 s', False),
            ('notify_secondary_progress()', 82.25),
            ('notify_file()', 'Done:  82.250%  Speed: 204 MiB/s  Left: 7 s', False),
            ('notify_secondary_progress()', 82.349),
            ('notify_file()', 'Done:  82.349%  Speed: 203 MiB/s  Left: 7 s', False),
            ('notify_secondary_progress()', 82.545),
            ('notify_file()', 'Done:  82.545%  Speed: 203 MiB/s  Left: 6 s', False),
            ('notify_secondary_progress()', 82.643),
            ('notify_file()', 'Done:  82.643%  Speed: 203 MiB/s  Left: 6 s', False),
            ('notify_secondary_progress()', 82.84),
            ('notify_file()', 'Done:  82.840%  Speed: 203 MiB/s  Left: 6 s', False),
            ('notify_secondary_progress()', 82.938),
            ('notify_file()', 'Done:  82.938%  Speed: 202 MiB/s  Left: 6 s', False),
            ('notify_secondary_progress()', 83.116),
            ('notify_file()', 'Done:  83.116%  Speed: 202 MiB/s  Left: 6 s', False),
            ('notify_secondary_progress()', 83.233),
            ('notify_file()', 'Done:  83.233%  Speed: 202 MiB/s  Left: 6 s', False),
            ('notify_secondary_progress()', 83.39),
            ('notify_file()', 'Done:  83.390%  Speed: 201 MiB/s  Left: 6 s', False),
            ('notify_secondary_progress()', 83.528),
            ('notify_file()', 'Done:  83.528%  Speed: 201 MiB/s  Left: 6 s', False),
            ('notify_secondary_progress()', 83.642),
            ('notify_file()', 'Done:  83.642%  Speed: 201 MiB/s  Left: 6 s', False),
            ('notify_secondary_progress()', 83.823),
            ('notify_file()', 'Done:  83.823%  Speed: 201 MiB/s  Left: 6 s', False),
            ('notify_secondary_progress()', 83.921),
            ('notify_file()', 'Done:  83.921%  Speed: 200 MiB/s  Left: 6 s', False),
            ('notify_secondary_progress()', 84.069),
            ('notify_file()', 'Done:  84.069%  Speed: 200 MiB/s  Left: 6 s', False),
            ('notify_secondary_progress()', 84.216),
            ('notify_file()', 'Done:  84.216%  Speed: 200 MiB/s  Left: 6 s', False),
            ('notify_secondary_progress()', 84.317),
            ('notify_file()', 'Done:  84.317%  Speed: 199 MiB/s  Left: 6 s', False),
            ('notify_secondary_progress()', 84.511),
            ('notify_file()', 'Done:  84.511%  Speed: 199 MiB/s  Left: 6 s', False),
            ('notify_secondary_progress()', 84.609),
            ('notify_file()', 'Done:  84.609%  Speed: 199 MiB/s  Left: 6 s', False),
            ('notify_secondary_progress()', 84.735),
            ('notify_file()', 'Done:  84.735%  Speed: 199 MiB/s  Left: 6 s', False),
            ('notify_secondary_progress()', 84.904),
            ('notify_file()', 'Done:  84.904%  Speed: 198 MiB/s  Left: 6 s', False),
            ('notify_secondary_progress()', 85.002),
            ('notify_file()', 'Done:  85.002%  Speed: 198 MiB/s  Left: 6 s', False),
            ('notify_secondary_progress()', 85.199),
            ('notify_file()', 'Done:  85.199%  Speed: 198 MiB/s  Left: 6 s', False),
            ('notify_secondary_progress()', 85.365),
            ('notify_file()', 'Done:  85.365%  Speed: 198 MiB/s  Left: 6 s', False),
            ('notify_secondary_progress()', 85.546),
            ('notify_file()', 'Done:  85.546%  Speed: 198 MiB/s  Left: 5 s', False),
            ('notify_secondary_progress()', 85.718),
            ('notify_file()', 'Done:  85.718%  Speed: 197 MiB/s  Left: 5 s', False),
            ('notify_secondary_progress()', 85.887),
            ('notify_file()', 'Done:  85.887%  Speed: 197 MiB/s  Left: 5 s', False),
            ('notify_secondary_progress()', 86.083),
            ('notify_file()', 'Done:  86.083%  Speed: 197 MiB/s  Left: 5 s', False),
            ('notify_secondary_progress()', 86.28),
            ('notify_file()', 'Done:  86.280%  Speed: 197 MiB/s  Left: 5 s', False),
            ('notify_secondary_progress()', 86.477),
            ('notify_file()', 'Done:  86.477%  Speed: 197 MiB/s  Left: 5 s', False),
            ('notify_secondary_progress()', 86.649),
            ('notify_file()', 'Done:  86.649%  Speed: 197 MiB/s  Left: 5 s', False),
            ('notify_secondary_progress()', 86.821),
            ('notify_file()', 'Done:  86.821%  Speed: 197 MiB/s  Left: 5 s', False),
            ('notify_secondary_progress()', 86.986),
            ('notify_file()', 'Done:  86.986%  Speed: 196 MiB/s  Left: 5 s', False),
            ('notify_secondary_progress()', 87.171),
            ('notify_file()', 'Done:  87.171%  Speed: 196 MiB/s  Left: 5 s', False),
            ('notify_secondary_progress()', 87.361),
            ('notify_file()', 'Done:  87.361%  Speed: 196 MiB/s  Left: 5 s', False),
            ('notify_secondary_progress()', 87.478),
            ('notify_file()', 'Done:  87.478%  Speed: 196 MiB/s  Left: 5 s', False),
            ('notify_secondary_progress()', 87.656),
            ('notify_file()', 'Done:  87.656%  Speed: 196 MiB/s  Left: 5 s', False),
            ('notify_secondary_progress()', 87.754),
            ('notify_file()', 'Done:  87.754%  Speed: 195 MiB/s  Left: 5 s', False),
            ('notify_secondary_progress()', 87.853),
            ('notify_file()', 'Done:  87.853%  Speed: 195 MiB/s  Left: 5 s', False),
            ('notify_secondary_progress()', 88.009),
            ('notify_file()', 'Done:  88.009%  Speed: 195 MiB/s  Left: 4 s', False),
            ('notify_secondary_progress()', 88.148),
            ('notify_file()', 'Done:  88.148%  Speed: 195 MiB/s  Left: 4 s', False),
            ('notify_secondary_progress()', 88.246),
            ('notify_file()', 'Done:  88.246%  Speed: 194 MiB/s  Left: 4 s', False),
            ('notify_secondary_progress()', 88.439),
            ('notify_file()', 'Done:  88.439%  Speed: 194 MiB/s  Left: 4 s', False),
            ('notify_secondary_progress()', 88.541),
            ('notify_file()', 'Done:  88.541%  Speed: 194 MiB/s  Left: 4 s', False),
            ('notify_secondary_progress()', 88.639),
            ('notify_file()', 'Done:  88.639%  Speed: 193 MiB/s  Left: 4 s', False),
            ('notify_secondary_progress()', 88.836),
            ('notify_file()', 'Done:  88.836%  Speed: 193 MiB/s  Left: 4 s', False),
            ('notify_secondary_progress()', 88.934),
            ('notify_file()', 'Done:  88.934%  Speed: 193 MiB/s  Left: 4 s', False),
            ('notify_secondary_progress()', 89.054),
            ('notify_file()', 'Done:  89.054%  Speed: 193 MiB/s  Left: 4 s', False),
            ('notify_secondary_progress()', 89.229),
            ('notify_file()', 'Done:  89.229%  Speed: 193 MiB/s  Left: 4 s', False),
            ('notify_secondary_progress()', 89.33),
            ('notify_file()', 'Done:  89.330%  Speed: 192 MiB/s  Left: 4 s', False),
            ('notify_secondary_progress()', 89.524),
            ('notify_file()', 'Done:  89.524%  Speed: 192 MiB/s  Left: 4 s', False),
            ('notify_secondary_progress()', 89.631),
            ('notify_file()', 'Done:  89.631%  Speed: 192 MiB/s  Left: 4 s', False),
            ('notify_secondary_progress()', 89.818),
            ('notify_file()', 'Done:  89.818%  Speed: 192 MiB/s  Left: 4 s', False),
            ('notify_secondary_progress()', 89.917),
            ('notify_file()', 'Done:  89.917%  Speed: 191 MiB/s  Left: 4 s', False),
            ('notify_secondary_progress()', 90.113),
            ('notify_file()', 'Done:  90.113%  Speed: 191 MiB/s  Left: 4 s', False),
            ('notify_secondary_progress()', 90.212),
            ('notify_file()', 'Done:  90.212%  Speed: 191 MiB/s  Left: 4 s', False),
            ('notify_secondary_progress()', 90.408),
            ('notify_file()', 'Done:  90.408%  Speed: 191 MiB/s  Left: 4 s', False),
            ('notify_secondary_progress()', 90.506),
            ('notify_file()', 'Done:  90.506%  Speed: 191 MiB/s  Left: 4 s', False),
            ('notify_secondary_progress()', 90.691),
            ('notify_file()', 'Done:  90.691%  Speed: 191 MiB/s  Left: 3 s', False),
            ('notify_secondary_progress()', 90.801),
            ('notify_file()', 'Done:  90.801%  Speed: 190 MiB/s  Left: 3 s', False),
            ('notify_secondary_progress()', 90.989),
            ('notify_file()', 'Done:  90.989%  Speed: 190 MiB/s  Left: 3 s', False),
            ('notify_secondary_progress()', 91.096),
            ('notify_file()', 'Done:  91.096%  Speed: 190 MiB/s  Left: 3 s', False),
            ('notify_secondary_progress()', 91.296),
            ('notify_file()', 'Done:  91.296%  Speed: 190 MiB/s  Left: 3 s', False),
            ('notify_secondary_progress()', 91.502),
            ('notify_file()', 'Done:  91.502%  Speed: 190 MiB/s  Left: 3 s', False),
            ('notify_secondary_progress()', 91.707),
            ('notify_file()', 'Done:  91.707%  Speed: 190 MiB/s  Left: 3 s', False),
            ('notify_secondary_progress()', 91.938),
            ('notify_file()', 'Done:  91.938%  Speed: 190 MiB/s  Left: 3 s', False),
            ('notify_secondary_progress()', 92.168),
            ('notify_file()', 'Done:  92.168%  Speed: 190 MiB/s  Left: 3 s', False),
            ('notify_secondary_progress()', 92.374),
            ('notify_file()', 'Done:  92.374%  Speed: 190 MiB/s  Left: 3 s', False),
            ('notify_secondary_progress()', 92.57),
            ('notify_file()', 'Done:  92.570%  Speed: 189 MiB/s  Left: 3 s', False),
            ('notify_secondary_progress()', 92.767),
            ('notify_file()', 'Done:  92.767%  Speed: 189 MiB/s  Left: 3 s', False),
            ('notify_secondary_progress()', 92.964),
            ('notify_file()', 'Done:  92.964%  Speed: 189 MiB/s  Left: 3 s', False),
            ('notify_secondary_progress()', 93.16),
            ('notify_file()', 'Done:  93.160%  Speed: 189 MiB/s  Left: 2 s', False),
            ('notify_secondary_progress()', 93.36),
            ('notify_file()', 'Done:  93.360%  Speed: 189 MiB/s  Left: 2 s', False),
            ('notify_secondary_progress()', 93.562),
            ('notify_file()', 'Done:  93.562%  Speed: 189 MiB/s  Left: 2 s', False),
            ('notify_secondary_progress()', 93.777),
            ('notify_file()', 'Done:  93.777%  Speed: 189 MiB/s  Left: 2 s', False),
            ('notify_secondary_progress()', 93.992),
            ('notify_file()', 'Done:  93.992%  Speed: 189 MiB/s  Left: 2 s', False),
            ('notify_secondary_progress()', 94.207),
            ('notify_file()', 'Done:  94.207%  Speed: 189 MiB/s  Left: 2 s', False),
            ('notify_secondary_progress()', 94.419),
            ('notify_file()', 'Done:  94.419%  Speed: 189 MiB/s  Left: 2 s', False),
            ('notify_secondary_progress()', 94.634),
            ('notify_file()', 'Done:  94.634%  Speed: 189 MiB/s  Left: 2 s', False),
            ('notify_secondary_progress()', 94.788),
            ('notify_file()', 'Done:  94.788%  Speed: 189 MiB/s  Left: 2 s', False),
            ('notify_secondary_progress()', 94.929),
            ('notify_file()', 'Done:  94.929%  Speed: 188 MiB/s  Left: 2 s', False),
            ('notify_secondary_progress()', 95.052),
            ('notify_file()', 'Done:  95.052%  Speed: 188 MiB/s  Left: 2 s', False),
            ('notify_secondary_progress()', 95.224),
            ('notify_file()', 'Done:  95.224%  Speed: 188 MiB/s  Left: 2 s', False),
            ('notify_secondary_progress()', 95.338),
            ('notify_file()', 'Done:  95.338%  Speed: 188 MiB/s  Left: 2 s', False),
            ('notify_secondary_progress()', 95.519),
            ('notify_file()', 'Done:  95.519%  Speed: 188 MiB/s  Left: 1 s', False),
            ('notify_secondary_progress()', 95.62),
            ('notify_file()', 'Done:  95.620%  Speed: 187 MiB/s  Left: 1 s', False),
            ('notify_secondary_progress()', 95.814),
            ('notify_file()', 'Done:  95.814%  Speed: 187 MiB/s  Left: 1 s', False),
            ('notify_secondary_progress()', 95.912),
            ('notify_file()', 'Done:  95.912%  Speed: 187 MiB/s  Left: 1 s', False),
            ('notify_secondary_progress()', 96.109),
            ('notify_file()', 'Done:  96.109%  Speed: 187 MiB/s  Left: 1 s', False),
            ('notify_secondary_progress()', 96.207),
            ('notify_file()', 'Done:  96.207%  Speed: 187 MiB/s  Left: 1 s', False),
            ('notify_secondary_progress()', 96.404),
            ('notify_file()', 'Done:  96.404%  Speed: 187 MiB/s  Left: 1 s', False),
            ('notify_secondary_progress()', 96.502),
            ('notify_file()', 'Done:  96.502%  Speed: 186 MiB/s  Left: 1 s', False),
            ('notify_secondary_progress()', 96.683),
            ('notify_file()', 'Done:  96.683%  Speed: 186 MiB/s  Left: 1 s', False),
            ('notify_secondary_progress()', 96.797),
            ('notify_file()', 'Done:  96.797%  Speed: 186 MiB/s  Left: 1 s', False),
            ('notify_secondary_progress()', 96.895),
            ('notify_file()', 'Done:  96.895%  Speed: 186 MiB/s  Left: 1 s', False),
            ('notify_secondary_progress()', 97.039),
            ('notify_file()', 'Done:  97.039%  Speed: 186 MiB/s  Left: 1 s', False),
            ('notify_secondary_progress()', 97.19),
            ('notify_file()', 'Done:  97.190%  Speed: 185 MiB/s  Left: 1 s', False),
            ('notify_secondary_progress()', 97.313),
            ('notify_file()', 'Done:  97.313%  Speed: 185 MiB/s  Left: 1 s', False),
            ('notify_secondary_progress()', 97.485),
            ('notify_file()', 'Done:  97.485%  Speed: 185 MiB/s  Left: 1 s', False),
            ('notify_secondary_progress()', 97.681),
            ('notify_file()', 'Done:  97.681%  Speed: 185 MiB/s  Left: 1 s', False),
            ('notify_secondary_progress()', 97.878),
            ('notify_file()', 'Done:  97.878%  Speed: 185 MiB/s  Left: 0 s', False),
            ('notify_secondary_progress()', 98.074),
            ('notify_file()', 'Done:  98.074%  Speed: 185 MiB/s  Left: 0 s', False),
            ('notify_secondary_progress()', 98.271),
            ('notify_file()', 'Done:  98.271%  Speed: 185 MiB/s  Left: 0 s', False),
            ('notify_secondary_progress()', 98.474),
            ('notify_file()', 'Done:  98.474%  Speed: 185 MiB/s  Left: 0 s', False),
            ('notify_secondary_progress()', 98.68),
            ('notify_file()', 'Done:  98.680%  Speed: 185 MiB/s  Left: 0 s', False),
            ('notify_secondary_progress()', 98.885),
            ('notify_file()', 'Done:  98.885%  Speed: 185 MiB/s  Left: 0 s', False),
            ('notify_secondary_progress()', 99.094),
            ('notify_file()', 'Done:  99.094%  Speed: 185 MiB/s  Left: 0 s', False),
            ('notify_secondary_progress()', 99.303),
            ('notify_file()', 'Done:  99.303%  Speed: 185 MiB/s  Left: 0 s', False),
            ('notify_secondary_progress()', 99.521),
            ('notify_file()', 'Done:  99.521%  Speed: 185 MiB/s  Left: 0 s', False),
            ('notify_secondary_progress()', 99.739),
            ('notify_file()', 'Done:  99.739%  Speed: 185 MiB/s  Left: 0 s', False),
            ('notify_secondary_progress()', 99.939),
            ('notify_file()', 'Done:  99.939%  Speed: 184 MiB/s  Left: 0 s', False),
            ('notify_secondary_progress()', 100.0),
            ('notify_file()', 'Done: 100.000%  Speed: 184 MiB/s  Left: 0 s', False),
            ('notify_secondary_progress()', 100.0),
            ('notify_file()', 'Done: 100.000%  Speed: 184 MiB/s  Left: 0 s', False),
            ('notify_secondary_progress()', 100.0),
            ('notify_file()', 'Done: 100.000%  Speed: 183 MiB/s  Left: 0 s', False),
            ('notify_secondary_progress()', 100.0),
            ('notify_file()', 'Done: 100.000%  Speed: 183 MiB/s  Left: 0 s', False),
            ('notify_secondary_progress()', 100.0),
            ('notify_file()', 'Done: 100.000%  Speed: 182 MiB/s  Left: 0 s', False),
            ('notify_secondary_progress()', 100.0),
            ('notify_file()', 'Done: 100.000%  Speed: 182 MiB/s  Left: 0 s', False),
            ('notify_secondary_progress()', 100.0),
            ('notify_file()', 'Done: 100.000%  Speed: 182 MiB/s  Left: 0 s', False),
            ('notify_secondary_progress()', 100.0),
            ('notify_file()', 'Done: 100.000%  Speed: 181 MiB/s  Left: 0 s', False),
            ('notify_secondary_progress()', 100.0),
            ('notify_file()', 'Done: 100.000%  Speed: 181 MiB/s  Left: 0 s', False),
            ('notify_secondary_progress()', 100.0),
            ('notify_file()', 'Done: 100.000%  Speed: 180 MiB/s  Left: 0 s', False),
            ('notify_secondary_progress()', 100.0),
            ('notify_file()', 'Done: 100.000%  Speed: 180 MiB/s  Left: 0 s', False),
            ('notify_secondary_progress()', 100.0),
            ('notify_file()', 'Done: 100.000%  Speed: 180 MiB/s  Left: 0 s', False),
            ('notify_secondary_progress()', 100.0),
            ('notify_file()', 'Done: 100.000%  Speed: 179 MiB/s  Left: 0 s', False),
            ('notify_secondary_progress()', 100.0),
            ('notify_file()', 'Done: 100.000%  Speed: 179 MiB/s  Left: 0 s', False),
            ('notify_secondary_progress()', 100.0),
            ('notify_file()', 'Done: 100.000%  Speed: 178 MiB/s  Left: 0 s', False),
            ('notify_secondary_progress()', 100.0),
            ('notify_file()', 'Done: 100.000%  Speed: 178 MiB/s  Left: 0 s', False),
            ('notify_secondary_progress()', 100.0),
            ('notify_file()', 'Done: 100.000%  Speed: 177 MiB/s  Left: 0 s', False),
            ('notify_secondary_progress()', 100.0),
            ('notify_file()', 'Done: 100.000%  Speed: 177 MiB/s  Left: 0 s', False),
            ('notify_secondary_progress()', 100.0),
            ('notify_file()', 'Done: 100.000%  Speed: 177 MiB/s  Left: 0 s', False),
            ('notify_secondary_progress()', 100.0),
            ('notify_file()', 'Done: 100.000%  Speed: 176 MiB/s  Left: 0 s', False),
            ('notify_secondary_progress()', 100.0),
            ('notify_file()', 'Done: 100.000%  Speed: 176 MiB/s  Left: 0 s', False),
            ('notify_secondary_progress()', 100.0),
            ('notify_file()', 'Done: 100.000%  Speed: 176 MiB/s  Left: 0 s', False),
            ('notify_secondary_progress()', 100.0),
            ('notify_file()', 'Done: 100.000%  Speed: 175 MiB/s  Left: 0 s', False),
            ('notify_secondary_progress()', 100.0),
            ('notify_file()', 'Done: 100.000%  Speed: 175 MiB/s  Left: 0 s', False),
            ('notify_secondary_progress()', 100.0),
            ('notify_file()', 'Done: 100.000%  Speed: 174 MiB/s  Left: 0 s', False),
            ('notify_secondary_progress()', 100.0),
            ('notify_file()', 'Done: 100.000%  Speed: 174 MiB/s  Left: 0 s', False),
            ('notify_secondary_progress()', 100.0),
            ('notify_file()', 'Done: 100.000%  Speed: 174 MiB/s  Left: 0 s', False),
            ('notify_message()', 'The VeraCrypt volume has been successfully created.'),
            ('notify_file()', 'The VeraCrypt volume has been successfully created.', False)]

        actual = self.presentation.things_done
        self.assertEqual(actual, expected)

    #
    #
    #
    def test_drutil_post_processor(self):
        # GIVEN
        self.__setup_fixture()
        # WHEN
        with open(self.__test_resource('drutil/drutil.log'), 'rb') as file:
            process = MockProcess(file)
            self.executor.process_output(process, self.under_test.drutil_post_processor)
        # THEN
        expected = [
            ('notify_message()', 'Burning Image to Disc: /tmp/SolidBlue/FG-2019-0001,0002 #2.dmg'),
            ('notify_message()', 'Please insert blank or appendable media in (null) CDDVDW SE-208DB.'),
            ('notify_message()', 'Preparing... done.'),
            ('notify_secondary_progress()', 1.0),
            ('notify_secondary_progress()', 1.0),
            ('notify_secondary_progress()', 3.0),
            ('notify_secondary_progress()', 5.0),
            ('notify_secondary_progress()', 7.0),
            ('notify_secondary_progress()', 9.0),
            ('notify_secondary_progress()', 11.0),
            ('notify_secondary_progress()', 13.0),
            ('notify_secondary_progress()', 15.0),
            ('notify_secondary_progress()', 17.0),
            ('notify_secondary_progress()', 19.0),
            ('notify_secondary_progress()', 21.0),
            ('notify_secondary_progress()', 23.0),
            ('notify_secondary_progress()', 25.0),
            ('notify_secondary_progress()', 27.0),
            ('notify_secondary_progress()', 29.0),
            ('notify_secondary_progress()', 31.0),
            ('notify_secondary_progress()', 33.0),
            ('notify_secondary_progress()', 35.0),
            ('notify_secondary_progress()', 37.0),
            ('notify_secondary_progress()', 39.0),
            ('notify_secondary_progress()', 41.0),
            ('notify_secondary_progress()', 43.0),
            ('notify_secondary_progress()', 45.0),
            ('notify_secondary_progress()', 47.0),
            ('notify_secondary_progress()', 49.0),
            ('notify_secondary_progress()', 50.0),
            ('notify_secondary_progress()', 52.0),
            ('notify_secondary_progress()', 54.0),
            ('notify_secondary_progress()', 56.0),
            ('notify_secondary_progress()', 58.0),
            ('notify_secondary_progress()', 60.0),
            ('notify_secondary_progress()', 62.0),
            ('notify_secondary_progress()', 64.0),
            ('notify_secondary_progress()', 66.0),
            ('notify_secondary_progress()', 68.0),
            ('notify_secondary_progress()', 70.0),
            ('notify_secondary_progress()', 72.0),
            ('notify_secondary_progress()', 74.0),
            ('notify_secondary_progress()', 76.0),
            ('notify_secondary_progress()', 78.0),
            ('notify_secondary_progress()', 80.0),
            ('notify_secondary_progress()', 82.0),
            ('notify_secondary_progress()', 84.0),
            ('notify_secondary_progress()', 86.0),
            ('notify_secondary_progress()', 88.0),
            ('notify_secondary_progress()', 90.0),
            ('notify_secondary_progress()', 92.0),
            ('notify_secondary_progress()', 94.0),
            ('notify_secondary_progress()', 96.0),
            ('notify_secondary_progress()', 98.0),
            ('notify_secondary_progress()', 100.0),
            ('notify_message()', 'done.'),
            ('notify_secondary_progress()', 99.0),
            ('notify_message()', 'done.'),
            ('notify_message()', 'Burn completed.')]

        actual = self.presentation.things_done
        self.assertEqual(actual, expected)

    #
    # Set up the test fixture.
    #
    def __setup_fixture(self, mock_file_system_clz=MockFileSystem, mock_storage_clz=MockStorage):
        self.next_id = 1000
        self.executor = Executor(log=self.__log, log_exception=self.__log_exception)
        self.presentation = MockPresentation()
        self.file_system = mock_file_system_clz()
        self.storage = mock_storage_clz(self.file_system)
        self.under_test = FingerprintingControl(database_folder='db-folder',
                                                executor=self.executor,
                                                presentation=self.presentation,
                                                storage=self.storage,
                                                file_system=self.file_system,
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

    @staticmethod
    def __log(string):
        print(string, flush=True)

    @staticmethod
    def __log_exception(string, exception):
        print(string, flush=True)
        print(str(exception), flush=True)

    @staticmethod
    def __debug(message: str):
        print(message, flush=True)

    @staticmethod
    def __test_resource(name: str) -> str:
        script_path = Path(os.path.realpath(__file__)).parent.parent
        return f'{script_path}/test-resources/{name}'


if __name__ == '__main__':
    unittest.main()
