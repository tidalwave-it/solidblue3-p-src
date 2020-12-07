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

import subprocess
import sys
import traceback

from PySide2.QtCore import QRunnable, Signal, QObject, Slot, QThreadPool

from utilities import html_red


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
    # Execs a process and returns the exit code. Output is written to log file and to the console.
    #
    def execute(self, args, output_processor, fail_on_result_code: bool = False):
        process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='latin-1')

        while True:
            try:
                line = process.stdout.readline()

                if line == '' and process.poll() is not None:
                    break

                output_processor(line[0:-1])
            except UnicodeDecodeError as e:
                self.log_exception('>>>> Error in decoding subprocess output', e)
                line = html_red('ERROR in decoding subprocess output')
                # FIXME: self.widgets.log_to_console(line)
            except BaseException as e:
                self.log_exception('>>>> Error in processing subprocess output', e)
                line = html_red('ERROR in processing subprocess output')
                # FIXME: self.widgets.log_to_console(line)

        self.log('>>>> subprocess terminated')

        if fail_on_result_code and process.returncode != 0:
            raise RuntimeError(f'Error: process return code is {process.returncode}')

        return process.returncode

    #
    #
    #
    def submit(self, worker):
        self.thread_pool.start(worker)
