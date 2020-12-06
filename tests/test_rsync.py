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

from rsync import RSync


#
#
#
class MockPresentation:
    def __init__(self):
        self.things_done = []

    def notify_status(self, status: str):
        self.things_done += [('notify_status()', status)]

    def notify_message(self, message: str):
        self.things_done += [('notify_message()', message)]

    def notify_progress(self, partial: int, total: int):
        self.things_done += [('notify_progress()', partial, total)]

    def notify_progress_indeterminate(self):
        self.things_done += ['notify_progress_indeterminate()']

    def notify_secondary_progress(self, progress: float):
        self.things_done += [('notify_secondary_progress()', progress)]

    def notify_reset_progress(self):
        self.things_done += ['notify_reset_progress()']

    def notify_error(self, message: str):
        self.things_done += [('notify_error()', message)]


#
#
#
class TestRSync(unittest.TestCase):
    presentation = None
    under_test = None

    def test_process_final_stats(self):
        self.__setup_fixture()

        input = '''
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
            '''

        for string in input.split('\n'):
            self.under_test._post_processor(string, is_ccc=True)

        actual = self.presentation.things_done
        expected = [
            ('notify_message()', 'Number of files: 64456'),
            ('notify_message()', 'Number of extended attributes: 0'),
            ('notify_message()', 'Size of transferred xattrs: 0 bytes'),
            ('notify_message()', 'Number of files transferred: 14257'),
            ('notify_message()', 'Total file size: 23.15 GB'),
            ('notify_message()', 'Total transferred file size: 5.52 GB'),
            ('notify_message()', 'Literal data: 794.6 MB'),
            ('notify_message()', 'Matched data: 4.72 GB'),
            ('notify_message()', 'File list size: 2.4 MB'),
            ('notify_message()', 'File list generation time: 2.870 seconds'),
            ('notify_message()', 'File list transfer time: 0.000 seconds'),
            ('notify_message()', 'sent 540.8 MB, received 2.7 MB (1.6 MB/sec)'),
            ('notify_message()', 'Speedup is 42x'),
            ('notify_message()', 'DEBUG: exit_cleanup[sender]: cleanup_child_pid: 68637. Error code: 0 at main.c:1444'),
            ('notify_message()', '            ')
        ]

        self.assertEqual(expected, actual)

    #
    # Set up the test fixture.
    #
    def __setup_fixture(self):
        self.presentation = MockPresentation()
        self.under_test = RSync(presentation=self.presentation, log=self.__debug)

    def __debug(self, message: str):
        # print(f'>>>> {message}', flush=True)
        pass


if __name__ == '__main__':
    unittest.main()
