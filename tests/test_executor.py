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
import os
import unittest
from pathlib import Path

from executor import Executor


class TestExecutor(unittest.TestCase):
    #
    #
    #
    def test_special_readline(self):
        actual = []

        with open(self.__test_resource('drutil/drutil.log'), 'rb') as file:
            while True:
                string = Executor.special_read_line(file, 'utf-8')

                if string == '':
                    break

                actual += [string]

        expected = ['Burning Image to Disc: /tmp/SolidBlue/FG-2019-0001,0002 #2.dmg\n', '\n',
                    'Please insert blank or appendable media in (null) CDDVDW SE-208DB.\n', 'Preparing... done.\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', 'Writing track 1 ... [                                                   ] 1% \r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '*                                                  ] 1% \r', ' \r', '\r', ' \r', '\r', ' \r',
                    '2% \r', ' \r', '\r', ' \r', '\r', ' \r', '3% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '*                                                 ] 3% \r',
                    ' \r', '\r', ' \r', '\r', ' \r', '4% \r', ' \r', '\r', ' \r', '\r', ' \r', '5% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '*                                                ] 5% \r', ' \r', '\r', ' \r', '\r', ' \r', '6% \r', ' \r', '\r', ' \r', '\r', ' \r',
                    '7% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '*                                               ] 7% \r', ' \r', '\r', ' \r', '\r', ' \r', '8% \r', ' \r', '\r', ' \r', '\r', ' \r',
                    '9% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '*                                              ] 9% \r', ' \r', '\r', ' \r', '\r', ' \r', '10% \r', ' \r', '\r', ' \r', '\r', ' \r',
                    '1% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '*                                             ] 11% \r', ' \r', '\r', ' \r', '\r', ' \r', '2% \r', ' \r', '\r', ' \r', '\r', ' \r',
                    '3% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '*                                            ] 13% \r', ' \r', '\r', ' \r', '\r', ' \r', '4% \r', ' \r', '\r', ' \r', '\r', ' \r', '5% \r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '*                                           ] 15% \r', ' \r', '\r', ' \r', '\r', ' \r', '6% \r', ' \r', '\r', ' \r', '\r', ' \r', '7% \r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '*                                          ] 17% \r',
                    ' \r', '\r', ' \r', '\r', ' \r', '8% \r', ' \r', '\r', ' \r', '\r', ' \r', '9% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '*                                         ] 19% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '20% \r', ' \r',
                    '\r', ' \r', '\r', ' \r', '1% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '*                                        ] 21% \r', ' \r', '\r', ' \r', '\r', ' \r', '2% \r', ' \r', '\r', ' \r', '\r', ' \r', '3% \r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '*                                       ] 23% \r', ' \r', '\r', ' \r', '\r', ' \r', '4% \r',
                    ' \r', '\r', ' \r', '\r', ' \r', '5% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '*                                      ] 25% \r', ' \r', '\r',
                    ' \r', '\r', ' \r', '6% \r', ' \r', '\r', ' \r', '\r', ' \r', '7% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '*                                     ] 27% \r',
                    ' \r', '\r', ' \r', '\r', ' \r', '8% \r', ' \r', '\r', ' \r', '\r', ' \r', '9% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '*                                    ] 29% \r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '30% \r', ' \r', '\r', ' \r', '\r', ' \r', '1% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '*                                   ] 31% \r',
                    ' \r', '\r', ' \r', '\r', ' \r', '2% \r', ' \r', '\r', ' \r', '\r', ' \r', '3% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '*                                  ] 33% \r', ' \r', '\r', ' \r', '\r',
                    ' \r', '4% \r', ' \r', '\r', ' \r', '\r', ' \r', '5% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '*                                 ] 35% \r', ' \r', '\r', ' \r', '\r', ' \r', '6% \r', ' \r', '\r', ' \r', '\r',
                    ' \r', '7% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '*                                ] 37% \r', ' \r', '\r', ' \r', '\r', ' \r', '8% \r', ' \r', '\r', ' \r', '\r', ' \r', '9% \r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '*                               ] 39% \r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '40% \r', ' \r', '\r', ' \r', '\r', ' \r', '1% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '*                              ] 41% \r', ' \r', '\r', ' \r', '\r', ' \r', '2% \r', ' \r', '\r', ' \r', '\r', ' \r', '3% \r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '*                             ] 43% \r', ' \r', '\r', ' \r', '\r', ' \r', '4% \r', ' \r',
                    '\r', ' \r', '\r', ' \r', '5% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '*                            ] 45% \r', ' \r', '\r', ' \r', '\r',
                    ' \r', '6% \r', ' \r', '\r', ' \r', '\r', ' \r', '7% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '*                           ] 47% \r', ' \r', '\r',
                    ' \r', '\r', ' \r', '8% \r', ' \r', '\r', ' \r', '\r', ' \r', '9% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '*                          ] 49% \r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '50% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '*                         ] 50% \r', ' \r', '\r', ' \r', '\r', ' \r', '1% \r', ' \r', '\r', ' \r',
                    '\r', ' \r', '2% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '*                        ] 52% \r', ' \r', '\r', ' \r', '\r', ' \r', '3% \r', ' \r', '\r', ' \r', '\r', ' \r', '4% \r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '*                       ] 54% \r', ' \r',
                    '\r', ' \r', '\r', ' \r', '5% \r', ' \r', '\r', ' \r', '\r', ' \r', '6% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '*                      ] 56% \r', ' \r', '\r', ' \r', '\r', ' \r', '7% \r', ' \r', '\r', ' \r',
                    '\r', ' \r', '8% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '*                     ] 58% \r',
                    ' \r', '\r', ' \r', '\r', ' \r', '9% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '60% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '*                    ] 60% \r', ' \r', '\r', ' \r', '\r', ' \r', '1% \r', ' \r', '\r', ' \r', '\r', ' \r',
                    '2% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '*                   ] 62% \r', ' \r', '\r', ' \r', '\r', ' \r', '3% \r',
                    ' \r', '\r', ' \r', '\r', ' \r', '4% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '*                  ] 64% \r', ' \r', '\r', ' \r',
                    '\r', ' \r', '5% \r', ' \r', '\r', ' \r', '\r', ' \r', '6% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '*                 ] 66% \r', ' \r', '\r',
                    ' \r', '\r', ' \r', '7% \r', ' \r', '\r', ' \r', '\r', ' \r', '8% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '*                ] 68% \r', ' \r', '\r', ' \r',
                    '\r', ' \r', '9% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '70% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '*               ] 70% \r', ' \r', '\r', ' \r', '\r',
                    ' \r', '1% \r', ' \r', '\r', ' \r', '\r', ' \r', '2% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '*              ] 72% \r', ' \r', '\r', ' \r', '\r', ' \r', '3% \r', ' \r', '\r', ' \r',
                    '\r', ' \r', '4% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '*             ] 74% \r', ' \r', '\r', ' \r', '\r', ' \r', '5% \r', ' \r', '\r', ' \r', '\r', ' \r', '6% \r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '*            ] 76% \r', ' \r', '\r', ' \r', '\r', ' \r',
                    '7% \r', ' \r', '\r', ' \r', '\r', ' \r', '8% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '*           ] 78% \r', ' \r', '\r', ' \r', '\r', ' \r', '9% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '80% \r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '*          ] 80% \r', ' \r', '\r', ' \r', '\r', ' \r', '1% \r',
                    ' \r', '\r', ' \r', '\r', ' \r', '2% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '*         ] 82% \r', ' \r', '\r',
                    ' \r', '\r', ' \r', '3% \r', ' \r', '\r', ' \r', '\r', ' \r', '4% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '*        ] 84% \r', ' \r', '\r', ' \r', '\r', ' \r', '5% \r', ' \r', '\r', ' \r', '\r', ' \r', '6% \r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '*       ] 86% \r', ' \r', '\r', ' \r', '\r', ' \r', '7% \r', ' \r', '\r', ' \r', '\r', ' \r', '8% \r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '*      ] 88% \r', ' \r', '\r', ' \r', '\r', ' \r', '9% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '90% \r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '*     ] 90% \r', ' \r', '\r', ' \r', '\r', ' \r', '1% \r', ' \r', '\r', ' \r', '\r', ' \r', '2% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '*    ] 92% \r', ' \r', '\r', ' \r', '\r',
                    ' \r', '3% \r', ' \r', '\r', ' \r', '\r', ' \r', '4% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '*   ] 94% \r', ' \r', '\r', ' \r', '\r', ' \r', '5% \r', ' \r', '\r', ' \r', '\r', ' \r',
                    '6% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '*  ] 96% \r',
                    ' \r', '\r', ' \r', '\r', ' \r', '7% \r', ' \r', '\r', ' \r', '\r', ' \r', '8% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '* ] 98% \r', ' \r', '\r', ' \r', '\r', ' \r', '9% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '*] 100% \r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    'done.\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', 'Closing... (this might take a while) [********************************* ] 99% \r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r',
                    ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r', '\r', ' \r',
                    ' done.\r', '                                          \r', 'Burn completed.\n', '\n']

        print(actual)
        self.assertEqual(actual, expected)

    @staticmethod
    def __test_resource(name: str) -> str:
        script_path = Path(os.path.realpath(__file__)).parent.parent
        return f'{script_path}/test-resources/{name}'


if __name__ == '__main__':
    unittest.main()
