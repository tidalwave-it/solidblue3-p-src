#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#  SolidBlue III - Open source data manager.
#
#  __author__ = "Fabrizio Giudici"
#  __copyright__ = "Copyright © 2026 by Fabrizio Giudici"
#  __credits__ = ["Fabrizio Giudici"]
#  __license__ = "Apache v2"
#  __version__ = "1.0-ALPHA-1"
#  __maintainer__ = "Fabrizio Giudici"
#  __email__ = "fabrizio.giudici@tidalwave.it"
#  __status__ = "Prototype"

#  SolidBlue III - Open source data manager.
#
import subprocess
import sys
import time
import traceback

from PySide6.QtCore import QRunnable, Signal, QObject, Slot, QThreadPool


class WorkerSignals(QObject):
    finished = Signal()
    error = Signal(tuple)


#
#
#
class Worker(QRunnable):
    #
    # Constructor.
    #
    def __init__(self, task, log_exception, *args, **kwargs):
        super(Worker, self).__init__()
        self.task = task
        self.log_exception = log_exception
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    #
    #
    #
    @Slot()
    def run(self):
        try:
            result = self.task(*self.args, **self.kwargs)
        except BaseException as e:
            self.log_exception('In worker', e)
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit(exctype, value, traceback.format_exc())
        finally:
            self.signals.finished.emit()


#
#
#
class Executor:
    #
    # Constructor
    #
    def __init__(self, log, log_exception):
        self.thread_pool = QThreadPool()
        self.log = log
        self.log_exception = log_exception

    #
    #
    #
    def submit(self, worker):
        self.thread_pool.start(worker)

    #
    # Execs a process and returns the exit code. Output is written to log file and to the console.
    #
    def execute(self, args, output_processor, fail_on_result_code: bool = False, retry_on_failure: bool = False, max_retries: int = 2, charset: str = 'utf-8'):
        retries = 0
        while retries <= max_retries:
            process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0)
            self.process_output(process, output_processor, charset)
            self.log(f'>>>> subprocess terminated ({process.returncode})')

            if process.returncode == 0:
                return process.returncode

            if fail_on_result_code:
                raise RuntimeError(f'Error: process return code is {process.returncode}')

            if not retry_on_failure:
                return process.returncode

            retries += 1
            if retries > max_retries:
                self.log(f'MAX RETRIES ({max_retries}) REACHED, GIVING UP')
                return process.returncode

            self.log(f'RESTARTING PROCESS BECAUSE OF FAILURE  ({process.returncode})') # TODO also do self.presentation.notify_message(...)
            time.sleep(1)
        return None # never reached

    #
    #
    #
    def process_output(self, process, output_processor, charset: str = 'utf-8'):
        while True:
            line = self.special_read_line(process.stdout, charset)

            if line == '' and process.poll() is not None:
                break

            output_processor(line[0:-1])

    #
    #
    #
    @staticmethod
    def special_read_line(readable, charset: str) -> str:
        line_buffer = bytearray()

        while True:
            buffer = readable.read(1)

            if buffer:
                byte = buffer[0]
                line_buffer.append(byte if byte != 8 else 13)

            if not buffer or line_buffer[-1] == 13 or line_buffer[-1] == 10:
                try:
                    return line_buffer.decode(charset)
                except BaseException as e:
                    return f'Warning: {str(e)} - {line_buffer.hex()}'
