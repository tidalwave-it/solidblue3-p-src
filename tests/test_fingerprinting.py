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

from solidblue3.utilities import extract, format_bytes, html_red, html_bold, html_italic
from solidblue3.fingerprinting import FingerprintingControl


# ============================================================
# extract()
# ============================================================

class TestExtract:
    STRING = 'foo bar 2134 bar foo 694 foo bar 594'

    def test_no_match_returns_none_triple(self):
        assert extract('barfoo', self.STRING) == (None, None, None)

    def test_one_group(self):
        assert extract(r'^[a-z\s]+([0-9]+)[a-z\s]+[0-9]+[a-z\s]+[0-9]+$', self.STRING) == ('2134', None, None)

    def test_two_groups(self):
        assert extract(r'^[a-z\s]+([0-9]+)[a-z\s]+([0-9]+)[a-z\s]+[0-9]+$', self.STRING) == ('2134', '694', None)

    def test_three_groups(self):
        assert extract(r'^[a-z\s]+([0-9]+)[a-z\s]+([0-9]+)[a-z\s]+([0-9]+)$', self.STRING) == ('2134', '694', '594')


# ============================================================
# html helpers
# ============================================================

class TestHtmlHelpers:
    def test_html_red(self):
        assert html_red('foo bar') == '<span style="color: red">foo bar</span>'

    def test_html_bold(self):
        assert html_bold('foo bar') == '<b>foo bar</b>'

    def test_html_italic(self):
        assert html_italic('foo bar') == '<em>foo bar</em>'


# ============================================================
# format_bytes()
# ============================================================

class TestFormatBytes:
    @pytest.mark.parametrize('size, expected', [
        (1,              '1 bytes'),
        (12,             '12 bytes'),
        (123,            '123 bytes'),
        (1234,           '1.0 kB'),
        (12345,          '12.0 kB'),
        (123456,         '123.0 kB'),
        (1234567,        '1.2 MB'),
        (12345678,       '12.3 MB'),
        (123456789,      '123.5 MB'),
        (1234567890,     '1.23 GB'),
        (12345678901,    '12.35 GB'),
        (123456789012,   '123.46 GB'),
        (1234567890123,  '1.235 TB'),
        (12345678901234, '12.346 TB'),
        (123456789012345,'123.457 TB'),
    ])
    def test_format_bytes(self, size, expected):
        assert format_bytes(size) == expected


# ============================================================
# FingerprintingControl.backup_name_hint()
# ============================================================

class TestBackupNameHint:
    def test_single_folder(self):
        assert FingerprintingControl.backup_name_hint(['/my/path/FG-2020-0003']) == 'FG-2020-0003'

    def test_two_consecutive_folders(self):
        assert FingerprintingControl.backup_name_hint(['/my/path/FG-2020-0003', '/my/path/FG-2020-0004']) == 'FG-2020-0003,0004'

    def test_range_of_folders(self):
        assert FingerprintingControl.backup_name_hint([
            '/my/path/FG-2020-0009',
            '/my/path/FG-2020-0007',
            '/my/path/FG-2020-0008',
        ]) == 'FG-2020-0007 => 0009'

    def test_non_consecutive_returns_none(self):
        assert FingerprintingControl.backup_name_hint([
            '/my/path/FG-2020-0006',
            '/my/path/FG-2020-0004',
            '/my/path/FG-2020-0007',
        ]) is None