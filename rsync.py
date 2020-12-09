#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#  SolidBlue III - Open source data manager.
#
#  __author__ = "Fabrizio Giudici"
#  __copyright__ = "Copyright © 2020 by Fabrizio Giudici"
#  __credits__ = ["Fabrizio Giudici"]
#  __license__ = "Apache v2"
#  __version__ = "1.0-ALPHA-2"
#  __maintainer__ = "Fabrizio Giudici"
#  __email__ = "fabrizio.giudici@tidalwave.it"
#  __status__ = "Prototype"

from utilities import extract, format_bytes, html_red


class RSyncPresentation:
    def notify_status(self, status: str):
        pass

    def notify_message(self, message: str):
        pass

    def notify_progress(self, partial: int, total: int):
        pass

    def notify_progress_indeterminate(self):
        pass

    def notify_secondary_progress(self, progress: float):
        pass

    def notify_reset_progress(self):
        pass

    def notify_error(self, message: str):
        pass


class RSync:
    #
    # Constructor.
    #
    def __init__(self, presentation: RSyncPresentation, log):
        self.presentation = presentation
        self.log = log
        self.progress = 0
        self.progress_total = 0
        self.file_size_map_by_file = {}
        self.base_folder = ''
        self.final_stats = False

    #
    # A post-processor for plain rsync.
    #
    def post_processor(self, string: str):
        self._post_processor(string, False)

    #
    # A post-processor for CCC rsync3.
    #
    def ccc_post_processor(self, string: str):
        self._post_processor(string, True)

    #
    # A post-processor for rsync.
    #
    def _post_processor(self, string: str, is_ccc: bool):
        filesystem_check, _, _ = extract(r'^do_filesystem_compatibility_checks: filesystem_capabilities\((.*)\)$', string)
        opening, _, _ = extract(r'^(opening connection).*$', string)

        if filesystem_check or opening:  # Used to reset, must be the first check
            self.final_stats = False

        if filesystem_check:  # Used to reset, must be the first check
            self.base_folder = filesystem_check

        if self.final_stats:
            self.__process_final_stats(string)
            # don't break, because some errors are logged after stats and need to be processed.
        else:
            self.final_stats, _, _ = extract(r'^(total: matches=[0-9]+  hash_hits=[0-9]+  false_alarms=[0-9]+ data=[0-9]+)$', string)

            if self.final_stats:
                self.log(string)

        ignorable, _, _ = extract(r'^('
                                  r'DEBUG: .*|'
                                  r'S;;;.*|'
                                  r'make_file.*|'
                                  r'.*expand file_list .* did move|'
                                  r'itemize\(generator\):.*|'
                                  r'recv_generator(\([0-9]+\))?: F_FFLAGS.*|'
                                  r'recv_generator\(generator\): F_HLINK_NOT_FIRST.*|'
                                  r'recv_generator\(generator\): itemizing.*|'
                                  r'recv_generator\(generator\): Truncating file.*|'
                                  r'recv_generator: Calling set_file_attrs: ITEM_REPORT_XATTR.*|'
                                  r'receive_data: Receiving data for.*|'
                                  r'recv_files: Location identified for incoming file.*|'
                                  r' Comparing to existing file of size: [0-9]+.*|'
                                  # r'recv_files: Finished receive_data.*|'
                                  r'recv_files: Calling set_file_attrs: ITEM_REPORT_XATTR.*|'
                                  r' *|'
                                  r'set_file_attrs: .*)$', string)

        error, _, _ = extract('(^.* failed: Operation not permitted.*$|'
                              '^rsync: send_files failed.*$|'
                              '^rsync error: .*$|'
                              '^rsync warning: .*$|'
                              '^rsync: set_file_attrs: failed to set times.*$|'
                              '^IO error encountered.*$|'
                              '^.*Broken pipe.*$|'
                              '^.*file has vanished:.*$|'
                              '^.*connection unexpectedly closed.*$|'
                              '^.*Device error.*$|'
                              '^skipping non-regular file.*$|'
                              '^.*failed: Permission denied.*$|'
                              '^File size and modification date match, but checksums were different:.*$)', string)

        deleting, _, _________ = extract(r'^S;;;DELETE;;;PROG;;;0;;;CF;;;(.*)$', string)
        read_bytes, _, _______ = extract(r'^Read ([0-9]+) bytes$', string)
        transferred_size, _, _ = extract(r'^DEBUG: \[generator\] RECVGEN: stats.total_unchanged_size \|"[^"]+"\|\+[0-9]+\|([0-9]+)', string)
        partial_progress, _, _ = extract('^recv_files: Finished receive_data, file size at .* is ([0-9]+).*', string)
        file_name, file_size, send_scan_progress = \
            extract(r'^DEBUG: \[sender\] MKFILE: stats.total_size \|"([^"]+)"\|\+([0-9]+)\|([0-9]+)\|', string)

        if deleting is not None:
            self.log(string)
            self.presentation.notify_message(f'Deleting {deleting}')

        if read_bytes is not None:
            return

        if send_scan_progress is not None:
            self.file_size_map_by_file[file_name] = int(file_size)
            self.presentation.notify_status(f'Computing file size: {format_bytes(int(send_scan_progress))} ...')
            return

        if transferred_size is not None:
            self.progress = int(transferred_size)
            self.presentation.notify_progress(self.progress, self.progress_total)
            return

        if partial_progress is not None:
            self.__increment_progress(int(partial_progress))
            return

        building_file_list, _, _ = extract(r'^(building file list).*$', string)
        partial_file_count, _, _ = extract(r'^ *([0-9]+) files\.\.\.$', string)
        file_up_to_date, _, _ = extract(r'^(.*) is uptodate$', string)
        file_partial_size, file_progress, _ = extract(r'^\s*([0-9]+)\s+([0-9]+)%.*$', string)
        file_count, _, _________ = extract(r'^ *([0-9]+) files to consider.*$', string)
        total_size = None

        if file_count is None:
            file_count, total_size, _ = extract(r'^S;;;FTC;;;NOF;;;([0-9]+);;;BT;;;[.0-9]+;;;TS;;;([0-9]+)$', string)

            if file_count is not None:
                self.log(string)

        if building_file_list is not None:
            self.presentation.notify_status('Building file list...')
            self.presentation.notify_progress_indeterminate()
            self.presentation.notify_message(string)
            return

        if file_progress is not None:
            self.presentation.notify_secondary_progress(int(file_progress) / 100.0)

            if is_ccc and file_progress == '100':
                self.__increment_progress(int(file_partial_size))

            # We count progress as soon as the file name is emitted without the 'uptodate' trailing, because smaller
            # files don't receive the partial progress notification.
            #
            # if not is_ccc and file_progress == '100':
            #    self.increment_progress()

            return

        if partial_file_count is not None:
            # self.log(f'Partial file count: {partial_file_count}')
            return

        if file_count is not None:
            self.progress_total = int(file_count)
            message = f'{file_count} files to consider'

            if total_size is not None:  # more precise
                self.progress_total = int(total_size)
                message += f' ({format_bytes(int(total_size))})'

            self.progress = 0
            self.presentation.notify_reset_progress()
            self.presentation.notify_status(message)
            self.presentation.notify_message(message)
            return

        if file_up_to_date is not None:
            self.log(string)  # keep the info in the log
            self.presentation.notify_status(string)

            if not is_ccc:
                self.__increment_progress(1)
            else:
                file_name = self.base_folder + file_up_to_date

                if file_name in self.file_size_map_by_file:
                    self.__increment_progress(self.file_size_map_by_file[file_name])

            return

        if ignorable is not None:
            # self.log(string)
            return

        if error is not None:
            string = html_red(string)
            self.presentation.notify_message(string)
            self.presentation.notify_error(string)

        # Todo: exclude [sender,receiver], deleting, delta-transmission enabled and the final stats
        # See comment above
        if not is_ccc:
            self.__increment_progress(1)

        if not self.final_stats:
            self.presentation.notify_status(string)
            self.presentation.notify_message(string)

    #
    # Processes the final stats.
    #
    def __process_final_stats(self, string):
        # S;;;SUM_STATS;;;TS;;;23058364756;;;TTS;;;0;;;FC;;;0;;;DIRS;;;11921;;;REG;;;46766;;;SYM;;;1;;;DEV;;;0;;;SPEC;;;0;;;HLNK;;;0;;;XATTR;;;0;;;XS;;;0;;;LF;;;2906345184
        # Number of files: 58688
        # Number of files transferred: 17453
        # Total file size: 23058366849 bytes
        # Total transferred file size: 5734458584 bytes
        # Literal data: 1043579678 bytes
        # Matched data: 4690878906 bytes
        # File list size: 2156684
        # File list generation time: 0.556 seconds
        # File list transfer time: 0.000 seconds
        # Total bytes sent: 756640254
        # Total bytes received: 2829189

        self.log(string)
        total_bytes, _, _ = extract(r'^(Total bytes) .*$', string)
        n1, n2, n3 = extract(r'^sent ([0-9]+) bytes  received ([0-9]+) bytes  ([0-9]+)[.0-9]* bytes\/sec$', string)
        t1, t2, t3 = extract(r'^(.* )([0-9]+)( bytes)$', string)
        file_list_size, _, _ = extract(r'^File list size: ([0-9]+)$', string)
        speed_up, _, _ = extract(r'^total size is [0-9]+  speedup is ([0-9]+)[.0-9]*$', string)

        if total_bytes:
            return

        if file_list_size:
            string = f'File list size: {format_bytes(int(file_list_size))}'

        if n1 and n2 and n3:
            string = f'sent {format_bytes(int(n1))}, received {format_bytes(int(n2))} ({format_bytes(int(n3))}/sec)'

        if t1 and t2 and t3:
            string = f'{t1}{format_bytes(int(t2))}'

        if speed_up:
            string = f'Speedup is {speed_up}x'

        self.presentation.notify_message(string)
        return

    #
    #
    #
    def __increment_progress(self, amount: int):
        self.progress += amount
        self.presentation.notify_progress(self.progress, self.progress_total)
