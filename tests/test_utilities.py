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

# -*- coding: utf-8 -*-

import unittest

import utilities


class TestUtilities(unittest.TestCase):
    def test_extract(self):
        string = 'foo bar 2134 bar foo 694 foo bar 594'
        self.assertEqual(utilities.extract(u'barfoo', string), (None, None, None))
        self.assertEqual(utilities.extract(u'^[a-z\s]+([0-9]+)[a-z\s]+[0-9]+[a-z\s]+[0-9]+$', string), ('2134', None, None))
        self.assertEqual(utilities.extract(u'^[a-z\s]+([0-9]+)[a-z\s]+([0-9]+)[a-z\s]+[0-9]+$', string), ('2134', '694', None))
        self.assertEqual(utilities.extract(u'^[a-z\s]+([0-9]+)[a-z\s]+([0-9]+)[a-z\s]+([0-9]+)$', string), ('2134', '694', '594'))

    def test_html_red(self):
        self.assertEqual(utilities.html_red('foo bar'), '<span style="color: red">foo bar</span>')

    def test_html_bold(self):
        self.assertEqual(utilities.html_bold('foo bar'), '<b>foo bar</b>')

    def test_format_bytes(self):
        self.assertEqual(utilities.format_bytes(1), '1 bytes')
        self.assertEqual(utilities.format_bytes(12), '12 bytes')
        self.assertEqual(utilities.format_bytes(123), '123 bytes')
        self.assertEqual(utilities.format_bytes(1234), '1.0 kB')
        self.assertEqual(utilities.format_bytes(12345), '12.0 kB')
        self.assertEqual(utilities.format_bytes(123456), '123.0 kB')
        self.assertEqual(utilities.format_bytes(1234567), '1.2 MB')
        self.assertEqual(utilities.format_bytes(12345678), '12.3 MB')
        self.assertEqual(utilities.format_bytes(123456789), '123.5 MB')
        self.assertEqual(utilities.format_bytes(1234567890), '1.23 GB')
        self.assertEqual(utilities.format_bytes(12345678901), '12.35 GB')
        self.assertEqual(utilities.format_bytes(123456789012), '123.46 GB')
        self.assertEqual(utilities.format_bytes(1234567890123), '1.235 TB')
        self.assertEqual(utilities.format_bytes(12345678901234), '12.346 TB')
        self.assertEqual(utilities.format_bytes(123456789012345), '123.457 TB')


if __name__ == '__main__':
    unittest.main()
