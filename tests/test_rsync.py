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

import pytest

from solidblue3.rsync import RSync, RSyncPresentation


# ============================================================
# Test double
# ============================================================

class RecordingPresentation(RSyncPresentation):
    def __init__(self):
        self.calls = []

    def notify_status(self, status: str):
        self.calls.append(('notify_status', status))

    def notify_message(self, message: str):
        self.calls.append(('notify_message', message))

    def notify_progress(self, partial: int, total: int):
        self.calls.append(('notify_progress', partial, total))

    def notify_progress_indeterminate(self):
        self.calls.append(('notify_progress_indeterminate',))

    def notify_secondary_progress(self, progress: float):
        self.calls.append(('notify_secondary_progress', progress))

    def notify_reset_progress(self):
        self.calls.append(('notify_reset_progress',))

    def notify_error(self, message: str):
        self.calls.append(('notify_error', message))


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def presentation():
    return RecordingPresentation()


@pytest.fixture
def rsync(presentation):
    return RSync(presentation=presentation, log=lambda _: None)


def feed(rsync_instance, text, is_ccc=True):
    """Feed multi-line text line by line into the post-processor."""
    for line in text.splitlines():
        rsync_instance._post_processor(line, is_ccc=is_ccc)


# ============================================================
# Final stats parsing
#
# In CCC rsync output the "total: matches=..." trigger line comes first,
# setting final_stats=True. All subsequent lines are processed by
# __process_final_stats, which reformats byte counts, speedup, etc.
# ============================================================

class TestFinalStats:
    FINAL_STATS_INPUT = """\
total: matches=295822  hash_hits=32390938  false_alarms=732 data=794606220
Number of files: 64456
Number of extended attributes: 0
Size of transferred xattrs: 0 bytes
Number of files transferred: 14257
Total file size: 23145325944 bytes
Total transferred file size: 5515226582 bytes
Literal data: 794606220 bytes
Matched data: 4720620362 bytes
File list size: 2387145
File list generation time: 2.870 seconds
File list transfer time: 0.000 seconds
Total bytes sent: 540789287
Total bytes received: 2733421
sent 540789287 bytes  received 2733421 bytes  1559606.05 bytes/sec
total size is 23145325944  speedup is 42.58
DEBUG: exit_cleanup[sender]: cleanup_child_pid: 68637. Error code: 0 at main.c:1444
"""

    def test_byte_counts_formatted(self, rsync, presentation):
        feed(rsync, self.FINAL_STATS_INPUT)

        assert ('notify_message', 'Total file size: 23.15 GB') in presentation.calls
        assert ('notify_message', 'Total transferred file size: 5.52 GB') in presentation.calls
        assert ('notify_message', 'Literal data: 794.6 MB') in presentation.calls
        assert ('notify_message', 'Matched data: 4.72 GB') in presentation.calls
        assert ('notify_message', 'File list size: 2.4 MB') in presentation.calls

    def test_transfer_summary_formatted(self, rsync, presentation):
        feed(rsync, self.FINAL_STATS_INPUT)

        assert ('notify_message', 'sent 540.8 MB, received 2.7 MB (1.6 MB/sec)') in presentation.calls

    def test_speedup_formatted(self, rsync, presentation):
        feed(rsync, self.FINAL_STATS_INPUT)

        assert ('notify_message', 'Speedup is 42x') in presentation.calls

    def test_exact_sequence(self, rsync, presentation):
        feed(rsync, self.FINAL_STATS_INPUT)

        expected = [
            ('notify_message', 'Number of files: 64456'),
            ('notify_message', 'Number of extended attributes: 0'),
            ('notify_message', 'Size of transferred xattrs: 0 bytes'),
            ('notify_message', 'Number of files transferred: 14257'),
            ('notify_message', 'Total file size: 23.15 GB'),
            ('notify_message', 'Total transferred file size: 5.52 GB'),
            ('notify_message', 'Literal data: 794.6 MB'),
            ('notify_message', 'Matched data: 4.72 GB'),
            ('notify_message', 'File list size: 2.4 MB'),
            ('notify_message', 'File list generation time: 2.870 seconds'),
            ('notify_message', 'File list transfer time: 0.000 seconds'),
            ('notify_message', 'sent 540.8 MB, received 2.7 MB (1.6 MB/sec)'),
            ('notify_message', 'Speedup is 42x'),
            ('notify_message', 'DEBUG: exit_cleanup[sender]: cleanup_child_pid: 68637. Error code: 0 at main.c:1444'),
        ]
        assert presentation.calls == expected


# ============================================================
# Building file list
# ============================================================

class TestBuildingFileList:
    def test_triggers_indeterminate_progress(self, rsync, presentation):
        feed(rsync, 'building file list ...')
        assert ('notify_progress_indeterminate',) in presentation.calls

    def test_triggers_status(self, rsync, presentation):
        feed(rsync, 'building file list ...')
        assert ('notify_status', 'Building file list...') in presentation.calls


# ============================================================
# File progress
# ============================================================

class TestFileProgress:
    def test_partial_progress_updates_secondary(self, rsync, presentation):
        feed(rsync, '     1234567  45%  1.23MB/s    0:00:01')
        assert ('notify_secondary_progress', 0.45) in presentation.calls


# ============================================================
# Reset on new connection
# ============================================================

class TestReset:
    def test_opening_connection_resets_final_stats(self, rsync, presentation):
        feed(rsync, 'total: matches=1  hash_hits=1  false_alarms=0 data=1')
        assert rsync.final_stats

        feed(rsync, 'opening connection using ...')
        assert not rsync.final_stats

    def test_filesystem_check_resets_final_stats(self, rsync, presentation):
        feed(rsync, 'total: matches=1  hash_hits=1  false_alarms=0 data=1')
        assert rsync.final_stats

        feed(rsync, 'do_filesystem_compatibility_checks: filesystem_capabilities(/Volumes/MyDisk)')
        assert not rsync.final_stats

    def test_filesystem_check_sets_base_folder(self, rsync, presentation):
        feed(rsync, 'do_filesystem_compatibility_checks: filesystem_capabilities(/Volumes/MyDisk)')
        assert rsync.base_folder == '/Volumes/MyDisk'


# ============================================================
# Error lines
# ============================================================

class TestErrors:
    @pytest.mark.parametrize('error_line', [
        'rsync error: some error (code 23) at main.c:1442',
        'rsync warning: some problem',
        'IO error encountered -- skipping file deletion',
        'some/file has vanished: "some/path"',
        'connection unexpectedly closed (1234 bytes received so far)',
    ])
    def test_error_line_triggers_notify_error(self, rsync, presentation, error_line):
        feed(rsync, error_line)
        error_calls = [c for c in presentation.calls if c[0] == 'notify_error']
        assert len(error_calls) == 1