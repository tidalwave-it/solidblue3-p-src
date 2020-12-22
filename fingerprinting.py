#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#  SolidBlue III - Open source data manager.
#
#  __author__ = "Fabrizio Giudici"
#  __copyright__ = "Copyright © 2020 by Fabrizio Giudici"
#  __credits__ = ["Fabrizio Giudici"]
#  __license__ = "Apache v2"
#  __version__ = "1.0-ALPHA-4-SNAPSHOT"
#  __maintainer__ = "Fabrizio Giudici"
#  __email__ = "fabrizio.giudici@tidalwave.it"
#  __status__ = "Prototype"

import hashlib
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time
from collections import namedtuple
from datetime import datetime
from pathlib import Path

import mmap
import xattr

import utilities
from config import Config
from executor import Executor
from utilities import format_bytes, generate_id, extract, veracrypt_mount_image, veracrypt_unmount_image

XATTR_ID = 'it.tidalwave.datamanager.id'
XATTR_FINGERPRINT = 'it.tidalwave.datamanager.fingerprint.md5'
XATTR_FINGERPRINT_TIMESTAMP = 'it.tidalwave.datamanager.fingerprint.md5.timestamp'
CHARSET = 'utf-8'
MMAP_THRESHOLD = 128 * 1024 * 1024


#
# Storage support for fingerprinting.
#
class FingerprintingStorage:
    def __init__(self, database_folder: str, id_generator=None, debug_function=None):
        self.generate_id = id_generator if id_generator is not None else generate_id
        self.debug = debug_function
        self.database_file = f'{database_folder}/fingerprints.db'
        self.conn = None

    #
    # Destructor.
    #
    def __del__(self):
        self.close()

    #
    # SQLlite can be used only from the thread that opened the connection; so we must open and close a connection every time.
    #
    def open(self):
        self.debug(f'Opening db connection: {self.database_file} ...')
        self.conn = sqlite3.connect(self.database_file)

        cursor = self.conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS files (
                            id TEXT PRIMARY KEY,
                            path TEXT NOT NULL
                            );""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS fingerprints (
                            id TEXT PRIMARY KEY,
                            name TEXT NOT NULL,
                            file_id TEXT NOT NULL,
                            algorithm TEXT NOT NULL,
                            fingerprint TEXT NOT NULL,
                            timestamp INTEGER NOT NULL
                            );""")
        cursor.execute("""CREATE INDEX IF NOT EXISTS files__path ON files (path);""")
        cursor.execute("""CREATE INDEX IF NOT EXISTS fingerprints__name ON fingerprints (name);""")
        cursor.execute("""CREATE INDEX IF NOT EXISTS fingerprints__file_id ON fingerprints (file_id);""")
        cursor.execute("""CREATE INDEX IF NOT EXISTS fingerprints__timestamp ON fingerprints (timestamp);""")

        cursor.execute("""CREATE TABLE IF NOT EXISTS backups(
                            id TEXT PRIMARY KEY,
                            base_path TEXT NOT NULL,
                            label TEXT NOT NULL UNIQUE,
                            volume_id TEXT NOT NULL UNIQUE,
                            encrypted INTEGER NOT NULL,
                            creation_date INTEGER NOT NULL,
                            registration_date INTEGER NOT NULL,
                            latest_check_date
                            );""")
        cursor.execute("""CREATE INDEX IF NOT EXISTS backups__volume_id ON backups (volume_id);""")

        cursor.execute("""CREATE TABLE IF NOT EXISTS backup_files(
                            id TEXT PRIMARY KEY,
                            backup_id TEXT NOT NULL,
                            file_id TEXT NOT NULL,
                            path TEXT NOT NULL
                            );""")
        self.conn.commit()

    #
    # Closes the connection to the database.
    #
    def close(self):
        if self.conn:
            self.debug('Closing db connection...')
            self.conn.close()
            self.conn = None

    #
    # Returns the (id, path) mappings.
    #
    def find_mappings(self) -> [(str, str)]:
        return self.__query('SELECT id, path FROM files ORDER BY path', (), commit=True)

    #
    # Adds a new file.
    #
    def add_path(self, file_id: str, path: str, commit=False):
        self.__update('INSERT INTO files(id, path) VALUES(?, ?)', (file_id, path), commit)

    #
    # Updates a file mapping.
    #
    def update_path(self, file_id: str, path: str, commit=False):
        self.__update('UPDATE files SET path = ? WHERE id = ?', (path, file_id), commit)

    #
    #
    #
    def find_file_id_by_name(self, file_name) -> str:
        rows = self.__query('SELECT id FROM files WHERE path LIKE ?', (f'%/{file_name}',))
        return rows[0][0] if len(rows) == 1 else None
        # FIXME: len(rows) > 1 should raise an exception

    #
    # Adds a fingerprint into the database.
    #
    def add_fingerprint(self, file_id: str, file_name: str, algorithm: str, fingerprint: str, timestamp, commit=False):
        if not file_id:  # should be done by file_id NOT NULL in the schema, but we have to fix old imported data without file_id first
            raise RuntimeError('file_id can\'t be null')

        t = (self.generate_id(), file_id, file_name, algorithm, fingerprint, timestamp)
        self.__update('INSERT INTO fingerprints(id, file_id, name, algorithm, fingerprint, timestamp) values(?, ?, ?, ?, ?, ?)', t, commit)

    #
    # Deletes a fingerprint.
    #
    def delete_fingerprint(self, fingerprint_id: str, commit=False):
        self.__update('DELETE FROM fingerprints WHERE id = ?', (fingerprint_id,), commit)

    #
    # Retrieves (fingerprint, timestamp) tuples for the given file_id.
    #
    def find_fingerprint_by_file_id(self, file_id: str) -> (str, str):
        return self.__query('SELECT fingerprint, datetime(timestamp) FROM fingerprints WHERE file_id = ? ORDER BY timestamp', (file_id,), commit=False)

    #
    # Retrieves the latest (fingerprint, timestamp) tuple for the given file_id.
    #
    def find_latest_fingerprint_by_id(self, file_id: str) -> (str, str):
        fingerprints = self.find_fingerprint_by_file_id(file_id)
        return fingerprints[-1] if len(fingerprints) > 0 else (None, None)

    #
    # Adds a backup. Returns the backup id.
    #
    def add_backup(self, base_path: str, label: str, volume_id: str, creation_date: datetime, registration_date: datetime, encrypted,
                   commit=False) -> str:
        backup_id = self.generate_id()
        t = (backup_id, base_path, label, volume_id, creation_date, registration_date, encrypted)
        self.__update('INSERT INTO backups(id, base_path, label, volume_id, creation_date, registration_date, encrypted) VALUES(?, ?, ?, ?, ?, ? ,?)', t,
                      commit)
        return backup_id

    #
    #
    #
    def find_backup_item_id(self, backup_id: str, file_id: str) -> str:
        t = (backup_id, file_id)
        result = self.__query('SELECT id from backup_files WHERE backup_id = ? AND file_id = ?', t)
        # TODO: error if len > 1
        return result[0][0] if len(result) == 1 else None

    #
    # Returns namedtuples for all registered backups.
    #
    def get_backups(self) -> namedtuple:
        need_conn = not self.conn

        if need_conn:
            self.open()

        try:
            t = ()
            return self.__query_nt('SELECT id, base_path, label, volume_id, encrypted, '
                                   'datetime(creation_date), datetime(registration_date), datetime(latest_check_date) '
                                   'FROM backups ORDER BY label', t, commit=False)
        finally:
            if need_conn:
                self.close()

    #
    # Sets the latest check timestamp.
    #
    def set_backup_check_latest_timestamp(self, backup_id, timestamp):
        self.__update('UPDATE backups SET latest_check_date=? WHERE id=?', (timestamp, backup_id,))

    #
    # Returns a namedtuple for a backup given the base_path.
    #
    def find_backup_by_mount_point(self, mount_point: str) -> namedtuple:
        return self.__single(self.__query_nt('SELECT * FROM backups WHERE base_path=?', (mount_point,)))

    #
    # Returns a namedtuple for a backup given the volume id.
    #
    def find_backup_by_volume_id(self, volume_id):
        return self.__single(self.__query_nt('SELECT * FROM backups WHERE volume_id=?', (volume_id,)))

    #
    # Returns a namedtuple for a backup given the volume label.
    #
    def find_backup_by_label(self, label):
        return self.__single(self.__query_nt('SELECT * FROM backups WHERE label=?', (label,)))

    #
    #
    #
    @staticmethod
    def __single(rows):
        count = len(rows)

        if count == 0:
            return None

        if count == 1:
            return rows[0]

        raise RuntimeError(f'Expected only 0 or 1 results, found {count}')

    #
    # Adds a backup file.
    #
    def add_backup_item(self, backup_id: str, file_id, backup_file: str, commit=False) -> str:
        backup_item_id = self.generate_id()
        t = (backup_item_id, backup_id, file_id, backup_file)
        self.__update('INSERT INTO backup_files(id, backup_id, file_id, path) VALUES(?, ?, ?, ?)', t, commit)
        return backup_item_id

    #
    # Commits the current transaction.
    #
    def commit(self):
        self.debug('Committing...')
        self.conn.commit()

    #
    # Executes a query.
    #
    def __query(self, sql: str, args, commit=False):
        self.debug(f'{sql} - {args}')
        cursor = self.conn.cursor()
        cursor.execute(sql, args)
        rows = cursor.fetchall()
        #  self.debug(f'>>>> {rows}')

        if commit:
            self.commit()

        return rows

    #
    # Executes a query into a namedtuple.
    #
    def __query_nt(self, sql: str, args, commit=False):
        self.debug(f'{sql} - {args}')

        def row_factory(cursor, row):
            fields = []
            date_time_fields = []

            for field in [col[0] for col in cursor.description]:
                if re.match('^datetime(.*)$', field):
                    field = field[9:-1]
                    date_time_fields += [field]

                fields += [field]

            Row = namedtuple("Row", fields)
            row = Row(*row)

            for field in date_time_fields:
                date_time_str = getattr(row, field)
                date_time = datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S') if date_time_str else None
                row = row._replace(**{field: date_time})

            return row

        self.conn.row_factory = row_factory
        cursor = self.conn.cursor()
        cursor.execute(sql, args)
        rows = cursor.fetchall()
        #  self.debug(f'>>>> {rows}')

        if commit:
            self.commit()

        return rows

    #
    # Executes an update.
    #
    def __update(self, sql: str, args, commit=False):
        self.debug(f'{sql} {args}')
        self.conn.cursor().execute(sql, args)

        if commit:
            self.commit()


#
#
#
class FingerprintingStats:
    def __init__(self):
        self.processed_file_count = 0
        self.plain_io_reads = 0
        self.mmap_reads = 0
        self.elapsed = 0
        self.__start_time = 0

    def reset(self):
        self.processed_file_count = 0
        self.plain_io_reads = 0
        self.mmap_reads = 0
        self.elapsed = 0
        self.__start_time = time.time()

    def stop(self):
        self.elapsed = time.time() - self.__start_time


#
#
#
class FingerprintingFileSystem:
    FileInfo = namedtuple("FileInfo", 'name, folder, path, size')

    #
    #
    #
    def __init__(self, stats: FingerprintingStats = None, debug_function=None):
        self.stats = stats if stats else FingerprintingStats()
        self.debug = debug_function

    #
    # Sets a single attribute.
    #
    @staticmethod
    def set_attribute(path: str, name: str, value: str):
        xattr.setxattr(path, name, value.encode(CHARSET))

    #
    # Get a single attribute.
    #
    @staticmethod
    def get_attribute(path: str, name: str) -> str:
        return xattr.getxattr(path, name).decode(CHARSET) if name in xattr.listxattr(path) else None

    #
    # Returns a list of files in the given folder (recursively inspected), matching the given filter.
    #
    @staticmethod
    def enumerate_files(folders: [str], file_filter: str = '.*') -> [FileInfo]:
        result = []

        for folder in folders:
            for sub_folder, _, files in os.walk(folder, followlinks=True):
                for file in files:
                    if re.search(file_filter, file.lower()):
                        path = f'{sub_folder}/{file}'
                        file_info = FingerprintingFileSystem.FileInfo(file, sub_folder, path, os.stat(path).st_size)
                        result += [file_info]

        return result

    #
    # Computes a fingerprint; returns (algorithm, fingerprint) or (error, error_message).
    #
    def compute_fingerprint(self, path: str) -> (str, str):
        try:
            with open(path, 'rb') as file:
                size = os.stat(path).st_size

                if size < MMAP_THRESHOLD:  # Preliminary tests, plain I/O is 3x faster
                    data = file.read()
                    self.stats.plain_io_reads = self.stats.plain_io_reads + size
                else:
                    with mmap.mmap(file.fileno(), length=0, access=mmap.ACCESS_READ) as stream:
                        data = stream.read()
                        self.stats.mmap_reads = self.stats.mmap_reads + size

                self.stats.processed_file_count = self.stats.processed_file_count + 1
                return 'md5', hashlib.md5(data).hexdigest()
        except OSError as e:
            self.debug(f'While processing {path}: {e.strerror}')
            return 'error', e.strerror

    #
    # Returns the volume UUID.
    #
    @staticmethod
    def find_volume_uuid(mount_point: str) -> str:
        process = subprocess.Popen(['diskutil', 'info', mount_point], text=True, stdout=subprocess.PIPE)
        volume_id, _, _ = extract('.*Volume UUID: *([0-9A-F-]+)', str(process.stdout.readlines()))
        return volume_id

    #
    # Ejects an optical disk mounted at the specified point.
    #
    @staticmethod
    def eject_optical_disc(mount_point: str):
        utilities.eject_optical_disc(mount_point)

    #
    # Create a directory and all its parents.
    #
    @staticmethod
    def make_dirs(veracrypt_mount_folder):
        os.makedirs(veracrypt_mount_folder, exist_ok=True)

    #
    #
    #
    @staticmethod
    def remove_folder(folder: str):
        if Path(folder).exists():
            shutil.rmtree(folder)

    #
    # Returns the creation date of the given file.
    #
    @staticmethod
    def creation_date(path: str) -> datetime:
        return datetime.fromtimestamp(os.stat(path).st_ctime)

    #
    #
    #
    @staticmethod
    def copy_with_xattrs(source_path: str, target_path: str, executor):
        # Can't use shutils.copy*() because they don't preserve extended attributes
        executor(['cp', '-p', source_path, target_path], log_cmdline=False, fail_on_result_code=True)

    #
    #
    #
    @staticmethod
    def create_veracrypt_image(algorithm: str, hash_algorithm: str, key_file: str, size: int, image_file: str, executor, veracrypt_post_processor):
        executor([utilities.VERACRYPT,
                  '--text',
                  '--non-interactive',
                  '--create',
                  image_file,
                  '--volume-type=normal',
                  f'--size={size}',
                  f'--encryption={algorithm}',
                  f'--hash={hash_algorithm}',
                  '--filesystem=hfs',
                  '--keyfiles',
                  key_file,
                  '--quick',
                  '--random-source=/dev/urandom'],
                 veracrypt_post_processor,
                 fail_on_result_code=True)

    #
    #
    #
    @staticmethod
    def create_hybrid_disk_image(label: str, image_file: str, source_folder: str, executor):
        # -hfs because we don't know how to retrieve an unique id for -udf or -joliet.
        executor(['hdiutil', 'makehybrid', '-o', image_file, source_folder, '-ov', '-hfs', '-default-volume-name', label],
                 fail_on_result_code=True)

    #
    #
    #
    @staticmethod
    def burn(image_file: str, post_processor, executor):
        # It seems it's impossible to prevent drutil from ejecting the media.
        executor(['drutil', 'burn', '-noverify', '-speed', '6', image_file], output_processor=post_processor, fail_on_result_code=True)

    #
    #
    #
    def mount_veracrypt_image(self, image_file: str, mount_point: str, key_file: str):
        veracrypt_mount_image(image_file, mount_point, key_file, self.debug)

    #
    #
    #
    def unmount_veracrypt_image(self, mount_point: str):
        veracrypt_unmount_image(mount_point, self.debug)

    #
    #
    #
    @staticmethod
    def unmount_optical_disk(mount_point: str, executor):
        executor(['hdiutil', 'detach', mount_point], fail_on_result_code=True)

    #
    #
    #
    @staticmethod
    def size(file: str) -> int:
        return os.stat(file).st_size

    #
    #
    #
    @staticmethod
    def exists(file: str) -> bool:
        return os.path.exists(file)


#
# Presentation.
#
class FingerprintingPresentation:
    def notify_message(self, message: str):
        pass

    def notify_counting(self):
        pass

    def notify_file_count(self, file_count: int):
        pass

    def notify_progress(self, partial: int, total: int):
        pass

    def notify_file(self, path: str, is_new: bool):
        pass

    def notify_file_moved(self, old_path: str, new_path: str):
        pass

    def notify_error(self, message: str):
        pass

    def notify_secondary_progress(self, progress: float):
        pass


#
# Control for fingerprint management.
#
class FingerprintingControl:
    #
    # Constructor.
    #
    def __init__(self,
                 database_folder: str,
                 executor: Executor,
                 presentation: FingerprintingPresentation,
                 storage: FingerprintingStorage = None,
                 file_system: FingerprintingFileSystem = None,
                 time_provider=None,
                 id_generator=None,
                 log=None,
                 debug_function=None):
        self.executor = executor
        self.presentation = presentation
        self.time_provider = time_provider if time_provider is not None else self.__time_provider
        self.generate_id = id_generator if id_generator is not None else generate_id
        self.storage = storage if storage is not None else FingerprintingStorage(database_folder=database_folder,
                                                                                 id_generator=self.generate_id,
                                                                                 debug_function=debug_function)
        self.file_system = file_system if file_system else FingerprintingFileSystem(debug_function=debug_function)
        self.log = log
        self.debug = debug_function

    #
    # Scans files.
    #
    def scan(self, folder: str, file_filter: str, only_new_files=False):
        stats = self.file_system.stats

        try:
            stats.reset()
            self.storage.open()
            files = self.__count_files([folder], file_filter)
            path_map_by_id = self.__load_id_map()

            if only_new_files:
                self.presentation.notify_message('Scanning only new files')

            new_timestamp = self.time_provider()
            new_timestamp_str = new_timestamp.strftime("%Y-%m-%d %H:%M:%S")
            total_progress = sum(file.size for file in files)
            current_progress = 0

            for file in files:
                path = file.path
                file_name = file.name
                file_id, fingerprint, _ = self.__get_attributes(path)

                if file_id is None:
                    file_id = self.generate_id()
                    self.file_system.set_attribute(path, XATTR_ID, file_id)
                    self.storage.add_path(file_id, path, commit=True)
                else:
                    if only_new_files:
                        self.presentation.notify_file(path, is_new=False)
                        current_progress += file.size
                        self.presentation.notify_progress(current_progress, total_progress)
                        continue

                    prev_path = path_map_by_id[file_id]

                    if prev_path != path:
                        self.presentation.notify_file_moved(prev_path, path)
                        self.storage.update_path(file_id, path, commit=True)

                algorithm, new_fingerprint = self.file_system.compute_fingerprint(path)
                self.storage.add_fingerprint(file_id, file_name, algorithm, new_fingerprint, new_timestamp, commit=True)

                if algorithm == 'error':
                    self.presentation.notify_error(f'Error for {path}: {new_fingerprint}')
                else:
                    self.file_system.set_attribute(path, XATTR_FINGERPRINT, new_fingerprint)
                    self.file_system.set_attribute(path, XATTR_FINGERPRINT_TIMESTAMP, new_timestamp_str)
                    self.presentation.notify_file(path, is_new=fingerprint is None)

                    if fingerprint is not None and new_fingerprint != fingerprint:
                        self.presentation.notify_error(f'Mismatch for {path}: found {new_fingerprint} expected {fingerprint}')

                current_progress += file.size
                self.presentation.notify_progress(current_progress, total_progress)
        finally:
            stats.stop()
            total_reads = stats.plain_io_reads + stats.mmap_reads
            elapsed = stats.elapsed
            file_count = stats.processed_file_count
            speed = total_reads / elapsed

            self.presentation.notify_message(
                f'{file_count} files ({format_bytes(total_reads)}) processed in {round(elapsed)} seconds ({format_bytes(speed)}/sec)')
            self.presentation.notify_message(f'{format_bytes(stats.plain_io_reads)} in plain I/O, {format_bytes(stats.mmap_reads)} in memory mapped I/O')
            self.storage.close()

    #
    # Registers a new backup.
    #
    def register_backup(self, label: str, mount_point: str, eject_after: bool = False):
        veracrypt_backup, actual_mount_point = self.__check_veracrypt_backup(mount_point)

        try:
            self.storage.open()
            volume_id = self.file_system.find_volume_uuid(mount_point)  # Beware: of the container volume!
            assert volume_id
            creation_date = self.file_system.creation_date(actual_mount_point)
            self.presentation.notify_message(f'Volume UUID {volume_id} created on {creation_date}')

            if self.storage.find_backup_by_volume_id(volume_id):
                self.presentation.notify_error('Backup with the same volume id already registered')
                return

            if self.storage.find_backup_by_label(label):
                self.presentation.notify_error('Backup with the same label already registered')
                return

            files = self.__count_files([actual_mount_point])
            registration_date = self.time_provider()
            backup_id = self.storage.add_backup(actual_mount_point, label, volume_id, creation_date, registration_date, veracrypt_backup)

            for current_progress, file in enumerate(files, start=1):
                file_id = self.__find_file_id(file.path)

                if file_id:
                    backup_file = file.path.replace(f'{actual_mount_point}/', '')
                    self.storage.add_backup_item(backup_id, file_id, backup_file)
                    self.presentation.notify_file(backup_file, is_new=True)

                self.presentation.notify_progress(current_progress, len(files))

            self.storage.commit()

            if eject_after:
                self.file_system.eject_optical_disc(mount_point)
        finally:
            self.storage.close()
            self.__eventually_unmount_veracrypt_backup(veracrypt_backup, actual_mount_point)

    #
    # Checks an existing backup.
    #
    def check_backup(self, mount_point: str, eject_after: bool = False):
        veracrypt_backup, actual_mount_point = self.__check_veracrypt_backup(mount_point)
        new_timestamp = self.time_provider()

        try:
            self.storage.open()
            current_volume_id = self.file_system.find_volume_uuid(mount_point)  # Beware: of the container volume!
            assert current_volume_id
            backup = self.storage.find_backup_by_volume_id(current_volume_id)

            if not backup:
                self.presentation.notify_error(f'{backup.base_path} is not a registered backup')
                return

            files = self.__count_files([actual_mount_point])
            check_timestamp = self.time_provider()
            total_progress = sum(file.size for file in files)
            current_progress = 0

            for file in files:
                file_relative_path = file.path.replace(f'{actual_mount_point}/', '')
                file_id = self.__find_file_id(file.path)

                if file_id:
                    self.presentation.notify_file(file_relative_path, is_new=False)
                    original_fingerprint, _ = self.storage.find_latest_fingerprint_by_id(file_id)
                    algorithm, fingerprint = self.file_system.compute_fingerprint(file.path)
                    backup_item_id = self.storage.find_backup_item_id(backup.id, file_id)

                    if not backup_item_id:
                        self.presentation.notify_error(f'File was not registered as part of the backup: {file_relative_path} - registering now')
                        backup_item_id = self.storage.add_backup_item(backup.id, file_id, file_relative_path)

                    self.storage.add_fingerprint(backup_item_id, file.name, algorithm, fingerprint, new_timestamp)

                    if algorithm == 'error':
                        self.presentation.notify_error(f'{file_relative_path}: {algorithm}')
                    elif original_fingerprint != fingerprint:
                        self.presentation.notify_error(f'Mismatch for {file_relative_path}: found {original_fingerprint} expected {fingerprint}')

                current_progress += file.size
                self.presentation.notify_progress(current_progress, total_progress)

            self.storage.set_backup_check_latest_timestamp(backup.id, check_timestamp)
            self.storage.commit()

            if eject_after:
                self.file_system.eject_optical_disc(mount_point)
        finally:
            self.storage.close()
            self.__eventually_unmount_veracrypt_backup(veracrypt_backup, actual_mount_point)

    #
    #
    #
    def create_encrypted_backup(self,
                                backup_name: str,
                                algorithm: str,
                                hash_algorithm: str,
                                folders: [str],
                                burn: bool):
        # DVD_RAW_SIZE = 8543666176
        backup_label = backup_name

        working_folder = Config.working_folder()
        veracrypt_image_folder = f'{working_folder}/{backup_name}_contents'
        veracrypt_image_file = f'{veracrypt_image_folder}/{backup_name}.veracrypt'
        veracrypt_mount_point = f'/Volumes/{backup_name}'
        opt_image_file = f'{working_folder}/{backup_name}'
        opt_image_file_with_ext = f'{opt_image_file}.dmg'
        key_file = Config.encrypted_backup_key_file()

        try:
            files_to_backup = self.__count_files(folders)
            total_size = sum(file.size for file in files_to_backup)
            size = int(round((total_size + len(files_to_backup) * 10 * 1024) * 1.02))

            # TODO: check size

            self.presentation.notify_message(f'Cleaning up working area ({working_folder})...')
            self.file_system.remove_folder(working_folder)

            self.file_system.make_dirs(veracrypt_image_folder)
            self.file_system.create_veracrypt_image(algorithm, hash_algorithm, key_file, size, veracrypt_image_file, self.__execute,
                                                    self.veracrypt_post_processor)
            veracrypt_image_size = self.file_system.size(veracrypt_image_file)
            self.presentation.notify_message(f'Veracrypt image size is {format_bytes(veracrypt_image_size)}')

            self.presentation.notify_message('Mounting encrypted image...')
            self.file_system.mount_veracrypt_image(veracrypt_image_file, veracrypt_mount_point, key_file)

            self.presentation.notify_message('Copying files...')
            self.presentation.notify_secondary_progress(0)
            total_progress = sum(file.size for file in files_to_backup)
            current_progress = 0

            for file in files_to_backup:
                parent = None

                for folder in folders:
                    if file.folder.startswith(folder):
                        parent = Path(folder).name
                        break

                assert parent is not None
                target_folder = f'{veracrypt_mount_point}/{parent}'
                self.file_system.make_dirs(target_folder)
                self.presentation.notify_file(file.name, is_new=False)
                self.file_system.copy_with_xattrs(file.path, f'{target_folder}/{file.name}', self.__execute)
                current_progress += file.size
                self.presentation.notify_secondary_progress(current_progress / total_progress)

            self.presentation.notify_message('Unmounting encrypted image...')
            self.file_system.unmount_veracrypt_image(veracrypt_mount_point)
            # self.widgets.signal_status.emit('')
            self.file_system.create_hybrid_disk_image(backup_label, opt_image_file, veracrypt_image_folder, self.__execute)
            opt_image_size = self.file_system.size(opt_image_file_with_ext)
            self.presentation.notify_message(f'Burn image size is {format_bytes(opt_image_size)}')

            if burn:
                optical_mount_point = f'/Volumes/{backup_name}'
                self.file_system.burn(opt_image_file_with_ext, self.drutil_post_processor, self.__execute)

                while not self.file_system.exists(optical_mount_point):
                    self.presentation.notify_message('Optical disk not mounted, please close the tray.')
                    # TODO utilities.inject_optical_disc()
                    time.sleep(5)

                self.register_backup(label=backup_label, mount_point=optical_mount_point)
                self.check_backup(optical_mount_point)
                self.file_system.unmount_optical_disk(optical_mount_point, self.__execute)
                self.file_system.eject_optical_disc(optical_mount_point)
        except BaseException as e:
            self.presentation.notify_error(f'ERROR: Procedure failed: {e}')
        finally:
            if burn:
                self.presentation.notify_message(f'Cleaning up working area ({working_folder})...')
                self.file_system.remove_folder(working_folder)
                # FIXME: what if the verification fails? The backup should be removed.

    #
    # Returns tuples (base_path, label) for all currently mounted backup volumes which have been already registered
    # or not in function of the 'registered' parameter.
    #
    def mounted_backup_volumes(self, registered: bool):
        self.storage.open()
        volume_names = os.listdir('/Volumes')
        result = []

        for volume_name in volume_names:
            mount_point = f'/Volumes/{volume_name}'
            volume_id = self.file_system.find_volume_uuid(mount_point)
            backup = self.storage.find_backup_by_volume_id(volume_id) if volume_id else None

            if backup and registered:
                result += [(mount_point, backup.label)]

            elif not backup and not registered:
                result += [(mount_point, volume_name)]

        self.storage.close()

        return sorted(result)

    #
    # Hints a name for a backup given the folders to use.
    #
    @staticmethod
    def backup_name_hint(folders: [str]) -> str:
        folders = sorted(folders)
        names = [Path(folder).name for folder in folders]
        lengths = [len(name) for name in names]

        if max(lengths) != min(lengths):
            return None

        suffixes = [utilities.extract('^.*-([0-9]+)$', name)[0] for name in names]
        lengths = [len(suffix) for suffix in suffixes]

        if max(lengths) != min(lengths):
            return None

        numbers = [int(suffix) for suffix in suffixes]
        first = min(numbers)
        last = max(numbers)

        if numbers != list(range(first, last + 1)):
            return None

        suffix_length = len(suffixes[0])
        prefix_length = len(names[0]) - suffix_length
        prefix = names[0][0:prefix_length]
        first_str = str(first).zfill(suffix_length)
        last_str = str(last).zfill(suffix_length)

        if last == first:
            return f'{prefix}{first_str}'

        if last == first + 1:
            return f'{prefix}{first_str},{last_str}'

        return f'{prefix}{first_str} => {last_str}'

    #
    # Execs a process and returns the exit code.
    # FIXME: duplicated in solidblue.
    #
    def __execute(self, args, output_processor=None, fail_on_result_code: bool = False, log_cmdline: bool = True):
        def __default_post_processor(string: str):
            self.presentation.notify_message(string)

        if output_processor is None:
            output_processor = __default_post_processor

        if log_cmdline:
            self.presentation.notify_message(utilities.html_italic(' '.join(args)))  # FIXME: should be notify_command()
        else:
            self.log(' '.join(args))

        return self.executor.execute(args, output_processor=output_processor, fail_on_result_code=fail_on_result_code)

    #
    # Post-processor for Veracrypt output.
    #
    def veracrypt_post_processor(self, string: str):
        string = string.strip()
        progress, _, _ = extract('Done: *([0-9.]+)% *Speed: *([0-9].+) *MiB/s *Left: *([0-9]+) *(s|minutes)', string)
        spurious, _, _ = extract('Done: *([0-9.-]+)% *Speed: *Left:$', string)

        if not spurious:
            if progress:
                self.presentation.notify_secondary_progress(float(progress))

            if string != '':
                if 'Error' in string:
                    self.presentation.notify_error(string)
                elif not progress:
                    self.presentation.notify_message(string)

                self.presentation.notify_file(string, is_new=False)  # FIXME: use a specific notify_status()

    #
    # Post-processor for drutil output.
    #
    def drutil_post_processor(self, string: str):
        string = string.strip()

        if string != '':
            progress, _, _ = extract('^.*] ([0-9]+)%.*$', string)
            digits, _, _ = extract('^.*([0-9]+)%.*$', string)
            closing, _, _ = extract('^.*(Closing).*$', string)

            if progress:
                self.presentation.notify_secondary_progress(float(progress))

            elif closing:
                self.presentation.notify_message('Finalising...')

            elif not digits:
                self.presentation.notify_message(string)

    #
    # Check whether this is a Veracrypt backup. If it is, mount the encrypted volume and returns the new mount point.
    #
    def __check_veracrypt_backup(self, mount_point: str) -> (bool, str):
        files_in_volume_root = [file.name for file in self.file_system.enumerate_files([mount_point])]
        veracrypt_backup = len(files_in_volume_root) == 1 and files_in_volume_root[0].endswith('.veracrypt')

        if not veracrypt_backup:
            return False, mount_point

        veracrypt_mount_folder = Config.encrypted_volumes_mount_folder()
        self.file_system.make_dirs(veracrypt_mount_folder)
        label = files_in_volume_root[0].replace('.veracrypt', '')
        veracrypt_mount_point = f'{veracrypt_mount_folder}/{label}'
        key_file = Config.encrypted_backup_key_file()
        self.presentation.notify_message(f'Detected a VeraCrypt backup, mounting image at "{veracrypt_mount_point}" ...')
        self.file_system.mount_veracrypt_image(f'{mount_point}/{files_in_volume_root[0]}', veracrypt_mount_point, key_file)
        return True, veracrypt_mount_point

    #
    #
    #
    def __count_files(self, folders: [str], file_filter: str = '.*') -> [FingerprintingFileSystem.FileInfo]:
        self.presentation.notify_counting()
        self.presentation.notify_message(f'Counting files in {folders}...')
        files = self.file_system.enumerate_files(folders, file_filter)
        files = sorted(files, key=lambda file: file.path)
        self.presentation.notify_file_count(len(files))
        self.presentation.notify_message(utilities.file_enumeration_message(files))
        return files

    #
    #
    #
    def __eventually_unmount_veracrypt_backup(self, veracrypt_backup: bool, mount_point: str):
        if veracrypt_backup:
            self.presentation.notify_message(f'Unmounting VeraCrypt image at "{mount_point}" ...')
            self.file_system.unmount_veracrypt_image(mount_point)

    #
    #
    #
    def __find_file_id(self, path: str) -> str:
        file_id = self.file_system.get_attribute(path, XATTR_ID)

        if not file_id:
            file_name = Path(path).name
            file_id = self.storage.find_file_id_by_name(file_name)

        return file_id

    #
    #
    #
    def __load_id_map(self) -> dict:
        self.debug('Retrieving the id mappings ...')
        path_map_by_id = {}

        for file_id, path in self.storage.find_mappings():
            path_map_by_id[file_id] = path

        return path_map_by_id

    #
    # Gets (file_id, fingerprint, timestamp) attributes for the given path.
    #
    def __get_attributes(self, path: str) -> (str, str, int):
        file_id = self.file_system.get_attribute(path, XATTR_ID)
        fingerprint = self.file_system.get_attribute(path, XATTR_FINGERPRINT)
        timestamp = self.file_system.get_attribute(path, XATTR_FINGERPRINT_TIMESTAMP)
        self.debug(f'__get_attributes({path}): {file_id}, {fingerprint}, {timestamp}')

        return file_id, fingerprint, timestamp

    #
    #
    #
    @staticmethod
    def __time_provider():
        return datetime.now()


#
#
#
def __main():
    debug = '--debug' in sys.argv

    def __debug(message: str):
        if debug:
            print(f'>>>> {message}', flush=True)

    class TerminalPresentation(FingerprintingPresentation):
        progress = ''

        def notify_counting(self):
            print('Counting files...', flush=True)

        def notify_file_count(self, file_count: int):
            print(f'{file_count} files to scan', flush=True)

        def notify_progress(self, partial: int, total: int):
            self.progress = f'{partial}/{total} {round(100.0 * partial / total, 1)}%'

        def notify_file(self, path: str, is_new: bool):
            if is_new:
                print(f'{path}', flush=True)
            else:
                print(f' {self.progress}', end='\r', flush=True)

        def notify_file_moved(self, old_path: str, new_path: str):
            print(f'{old_path}\n    ↳ {new_path}', flush=True)

        def notify_error(self, message: str):
            print(f'ERROR: {message}', flush=True)

    only_new_files = '--only-new-files' in sys.argv

    if '--scan' in sys.argv:
        pass
        # folder = Config.photos_folder()
        # file_filter = Config.photos_file_filter()
    else:
        print(f'{str(Path(sys.argv[0]).name)} [--scan {Config.scan_config().keys()}] [--only-new-files] [--debug]', flush=True)
        sys.exit(1)

    presentation = TerminalPresentation()
    fingerprinting_control = FingerprintingControl(database_folder=Config.database_folder(), presentation=presentation, debug_function=__debug)
    fingerprinting_control.scan(folder=folder, file_filter=file_filter, only_new_files=only_new_files)


if __name__ == '__main__':
    __main()
