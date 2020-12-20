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
import re
import subprocess
import uuid

VERACRYPT = '/Applications/VeraCrypt.app/Contents/MacOS/VeraCrypt'


#
# Shows a macOS notification.
#
def notification(text: str):
    subprocess.run(['osascript', '-e', f'display notification "{text}" with title "SolidBlue"'], check=True)


#
# Extracts up to three substrings by using a regular expression.
#
def extract(regex: str, string: str) -> (str, str, str):
    result = [None, None, None]
    match = re.search(regex, string)

    for i in [1, 2, 3]:
        result[i - 1] = match.group(i) if match is not None and match.re.groups >= i else None

    return tuple(result)


#
# Returns an HTML text in red color.
#
def html_red(text: str) -> str:
    return f'<span style="color: red">{text}</span>'


#
# Returns an HTML text in bold.
#
def html_bold(text: str) -> str:
    return f'<b>{text}</b>'


#
# Returns an HTML text in italic.
#
def html_italic(text: str) -> str:
    return f'<em>{text}</em>'


#
# Format byte count in a human readable format.
# See https://stackoverflow.com/questions/12523586/python-format-size-application-converting-b-to-kb-mb-gb-tb
#
def format_bytes(size: int) -> str:
    power = 10 ** 3
    i = 0
    power_labels = {0: 'bytes', 1: 'kB', 2: 'MB', 3: 'GB', 4: 'TB'}
    power_digits = {0: 0, 1: 0, 2: 1, 3: 2, 4: 3}

    while size > power:
        size /= power
        i += 1

    return f'{round(size, power_digits[i])} {power_labels[i]}'


#
# Generates a new unique id.
#
def generate_id() -> str:
    return str(uuid.uuid4())


#
#
#
def file_enumeration_message(files: [str]) -> str:
    total_size = sum(file.size for file in files)
    return f'Found {len(files)} files ({format_bytes(int(round(total_size)))})'


#
#
#
def eject_optical_disc(base_path: str):
    os.system("drutil tray eject")


#
#
#
def veracrypt_mount_image(image_file: str, mount_point: str, key_file: str, logger_function=None):
    mount_point = os.path.realpath(mount_point)
    cmd_line = f'{VERACRYPT} --text --non-interactive --keyfiles "{key_file}" "{image_file}" "{mount_point}"'

    if logger_function:
        logger_function(cmd_line)

    return_code = os.system(cmd_line)

    if return_code:
        raise RuntimeError(f'Veracrypt returned {return_code}')


#
#
#
def veracrypt_unmount_image(mount_point: str, logger_function=None):
    mount_point = os.path.realpath(mount_point)
    cmd_line = f'{VERACRYPT} --text --non-interactive --force --dismount "{mount_point}"'

    if logger_function:
        logger_function(cmd_line)

    return_code = os.system(cmd_line)

    if return_code:
        raise RuntimeError(f'Veracrypt returned {return_code}')


#
#
#
def shortened_path(path: str) -> str:
    return path.replace(os.getenv("HOME"), '~')
