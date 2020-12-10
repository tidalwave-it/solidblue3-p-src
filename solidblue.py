#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#  SolidBlue III - Open source data manager.
#
#  __author__ = "Fabrizio Giudici"
#  __copyright__ = "Copyright © 2020 by Fabrizio Giudici"
#  __credits__ = ["Fabrizio Giudici"]
#  __license__ = "Apache v2"
#  __version__ = "1.0-ALPHA-3-SNAPSHOT"
#  __maintainer__ = "Fabrizio Giudici"
#  __email__ = "fabrizio.giudici@tidalwave.it"
#  __status__ = "Prototype"

import datetime
import sys
import threading
import traceback
from collections import namedtuple
from pathlib import Path
from urllib.parse import urlparse

from PySide2.QtCore import *
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import *

import utilities
from config import Config
from executor import Worker, Executor
from fingerprinting import FingerprintingControl, FingerprintingPresentation
from rsync import RSync, RSyncPresentation
from utilities import *


#
# Base class for all dialogs.
#
class DialogSupport(QDialog):
    def __init__(self, main_window: QMainWindow):
        super(DialogSupport, self).__init__(main_window)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)


#
# The dialog box with the options for starting a file scan.
#
class OnlyNewFilesDialog(DialogSupport):
    Options = namedtuple('Options', 'only_new_files')

    def __init__(self, main_window: QMainWindow):
        super().__init__(main_window)
        self.cb_only_new_files = QCheckBox(self)
        self.cb_only_new_files.setText('Only scan new files')
        self.cb_only_new_files.setChecked(True)
        layout = QVBoxLayout()
        layout.addWidget(self.cb_only_new_files)
        layout.addWidget(self.button_box)
        self.setLayout(layout)

    def user_options(self):
        return OnlyNewFilesDialog.Options(only_new_files=self.cb_only_new_files.isChecked())


#
# The dialog box with the options for creating a new encrypted backup.
#
class CreateBackupDialog(DialogSupport):
    Options = namedtuple('Options', 'label folders algorithm hash_algorithm burn')
    signal_populate = Signal()

    def __init__(self, main_window: QMainWindow):
        super().__init__(main_window)
        self.le_label = QLineEdit()
        self.cb_do_not_burn = QCheckBox()
        self.cb_algorithm = QComboBox()
        self.cb_algorithm.setModel(QStringListModel())
        self.cb_hash_algorithm = QComboBox()
        self.cb_hash_algorithm.setModel(QStringListModel())
        self.cb_do_not_burn.setText('Only test, do not burn')
        le_label = self.le_label

        class DropModel(QStringListModel):
            def supportedDragActions(self):
                return Qt.DropAction.CopyAction

            # def supportedDropActions(self):
            #    return Qt.DropAction.CopyAction

            def flags(self, index: QModelIndex):
                return Qt.ItemIsDropEnabled | super().flags(index)

            def canDropMimeData(self, data: QMimeData, action, row, column, parent):
                # print(f'asked can drop {data.formats()} {action}', flush=True)
                return data.formats() == ['text/uri-list']  # and action == Qt.DropAction.CopyAction

            def dropMimeData(self, data: QMimeData, action, row, column, parent):
                if not self.canDropMimeData(data, action, row, column, parent):
                    return False

                urls = filter(lambda url: url != '', data.text().split('\n'))
                paths = [urlparse(url).path for url in urls]
                folders = list(filter(lambda path: Path(path).is_dir(), paths))
                self.setStringList(sorted(self.stringList() + folders))
                backup_name_hint = FingerprintingControl.backup_name_hint(self.stringList())

                if backup_name_hint:
                    le_label.setText(backup_name_hint)

                return True

        self.lv_folders = QListView()
        self.lv_folders.setModel(DropModel())
        self.lv_folders.setAcceptDrops(True)
        self.lv_folders.viewport().setAcceptDrops(True)
        self.lv_folders.setDropIndicatorShown(True)
        layout = QVBoxLayout()
        layout.addWidget(self.le_label)
        layout.addWidget(self.lv_folders)
        layout.addWidget(self.cb_algorithm)
        layout.addWidget(self.cb_hash_algorithm)
        layout.addWidget(self.cb_do_not_burn)
        layout.addWidget(self.button_box)
        self.setLayout(layout)

        self.cb_algorithm.model().setStringList(sorted(Config.veracrypt_algorithms().keys()))
        self.cb_algorithm.setCurrentText(Config.veracrypt_default_algorithm())
        self.cb_hash_algorithm.model().setStringList(sorted(Config.veracrypt_hash_algorithms().keys()))
        self.cb_hash_algorithm.setCurrentText(Config.veracrypt_default_hash_algorithm())
        self.resize(640, 480)
        self.signal_populate.connect(self.__slot_populate)

    def user_options(self) -> Options:
        algorithm = Config.veracrypt_algorithms()[self.cb_algorithm.currentText()]
        hash_algorithm = Config.veracrypt_hash_algorithms()[self.cb_hash_algorithm.currentText()]

        return CreateBackupDialog.Options(
            label=self.le_label.text(),
            folders=sorted(self.lv_folders.model().stringList()),
            algorithm=algorithm,
            hash_algorithm=hash_algorithm,
            burn=not self.cb_do_not_burn.isChecked())

    def __slot_populate(self):
        self.le_label.setText('')
        self.lv_folders.model().setStringList([])


#
# The dialog box with the options for selecting an unregistered backup volume.
#
class UnregisteredBackupDialog(DialogSupport):
    Options = namedtuple('Options', 'base_path, label, eject_after_scan')
    signal_populate = Signal(object)

    def __init__(self, main_window: QMainWindow):
        super().__init__(main_window)
        self.cb_volume_mount_point = QComboBox()
        self.cb_volume_mount_point.setEditable(False)
        self.cb_volume_mount_point.setModel(QStringListModel())
        self.le_backup_name = QLineEdit()
        self.cb_eject_after_scan = QCheckBox()
        self.cb_eject_after_scan.setText('Eject after scan')
        layout = QVBoxLayout()
        layout.addWidget(self.cb_volume_mount_point)
        layout.addWidget(self.le_backup_name)
        layout.addWidget(self.cb_eject_after_scan)
        layout.addWidget(self.button_box)
        self.setLayout(layout)
        self.signal_populate.connect(self.__slot_populate)

        def __on_mount_point_selected(text):
            nonlocal self
            self.mount_point, label, _ = utilities.extract(r'(.*) \((.*)\)', text)
            self.le_backup_name.setText(label)

        self.cb_volume_mount_point.textActivated.connect(__on_mount_point_selected)

    def user_options(self) -> Options:
        return UnregisteredBackupDialog.Options(base_path=self.mount_point,
                                                label=self.le_backup_name.text(),
                                                eject_after_scan=self.cb_eject_after_scan.isChecked())

    def __slot_populate(self, items):
        self.mount_point = ''
        self.le_backup_name.setText('')
        self.cb_volume_mount_point.model().setStringList([f'{item[0]} ({item[1]})' for item in items])


#
# The dialog box with the options for selecting a registered backup volume.
#
class RegisteredBackupDialog(DialogSupport):
    Options = namedtuple('Options', 'base_path, label, eject_after_scan')
    signal_populate = Signal(object)

    def __init__(self, main_window: QMainWindow):
        super().__init__(main_window)
        self.cb_volume_mount_point = QComboBox()
        self.cb_volume_mount_point.setEditable(False)
        self.cb_volume_mount_point.setModel(QStringListModel())
        self.cb_eject_after_scan = QCheckBox()
        self.cb_eject_after_scan.setText('Eject after scan')
        layout = QVBoxLayout()
        layout.addWidget(self.cb_volume_mount_point)
        layout.addWidget(self.cb_eject_after_scan)
        layout.addWidget(self.button_box)
        self.setLayout(layout)
        self.signal_populate.connect(self.__slot_populate)

    def user_options(self) -> Options:
        string = self.cb_volume_mount_point.currentText()
        volume_mount_point, label, _ = utilities.extract(r'^(.*) \(.*\)$', string)
        return RegisteredBackupDialog.Options(base_path=volume_mount_point,
                                              label=label,
                                              eject_after_scan=self.cb_eject_after_scan.isChecked())

    def __slot_populate(self, items):
        self.cb_volume_mount_point.model().setStringList([f'{item[0]} ({item[1]})' for item in items])


#
# This class segregates widgets so they are accessed in the proper way.
#
class Widgets(QObject):
    PROGRESS_MAX = 10000

    signal_status = Signal(str)
    signal_log_to_console = Signal(str)
    signal_log_to_error_console = Signal(str)
    signal_progress = Signal(float)
    signal_secondary_progress = Signal(float)
    signal_progress_indeterminate = Signal()
    signal_progress_reset = Signal()
    signal_show_dialog = Signal(QDialog)

    dialog_closed = threading.Event()

    script_path = Path(os.path.realpath(__file__)).parent

    #
    # Constructor.
    #
    def __init__(self, main_window: QMainWindow, executor: Executor, log, log_exception):
        QObject.__init__(self)

        def create_console() -> QTextEdit:
            te_console = QTextEdit()
            te_console.setAlignment(Qt.AlignLeft)
            te_console.setReadOnly(True)
            te_console.setLineWrapMode(QTextEdit.NoWrap)
            return te_console

        def create_progress_bar() -> QProgressBar:
            pb_progress = QProgressBar()
            pb_progress.setRange(0, self.PROGRESS_MAX)
            pb_progress.setMaximum(self.PROGRESS_MAX)
            # pb_progress.setTextVisible(True)
            # pb_progress.setFormat('%v/%m - %__slot_p')
            return pb_progress

        self.main_window = main_window
        self.executor = executor
        self.tb_toolbar = QToolBar()
        self.layout = QVBoxLayout()

        self.log = log
        self.log_exception = log_exception
        self.te_console = create_console()
        self.te_error_console = create_console()
        self.pb_progress = create_progress_bar()
        self.pb_progress_secondary = create_progress_bar()
        self.lb_status = QLabel()
        self.lb_status.setWordWrap(True)

        console_layout = QVBoxLayout()
        console_layout.addWidget(self.te_console, 70)
        console_layout.addWidget(self.te_error_console, 30)

        internal_layout = QVBoxLayout()
        internal_layout.setMargin(16)
        internal_layout.addLayout(console_layout)
        internal_layout.addWidget(self.lb_status)
        internal_layout.addWidget(self.pb_progress)
        internal_layout.addWidget(self.pb_progress_secondary)

        self.layout.setMargin(0)
        self.layout.addWidget(self.tb_toolbar)
        self.layout.addLayout(internal_layout)

        self.signal_status.connect(self.lb_status.setText)
        self.signal_log_to_console.connect(self.__slot_log_to_console)
        self.signal_log_to_error_console.connect(self.__slot_log_to_error_console)
        self.signal_progress.connect(self.__slot_set_progress)
        self.signal_secondary_progress.connect(self.__slot_set_secondary_progress)
        self.signal_progress_indeterminate.connect(self.__slot_progress_indeterminate)
        self.signal_progress_reset.connect(self.__slot_reset_progress)
        self.signal_show_dialog.connect(self.__slot_show_modal_dialog)

        self.d_create_backup_options = CreateBackupDialog(self.main_window)
        self.d_only_new_files = OnlyNewFilesDialog(self.main_window)
        self.d_ask_unregistered_backup = UnregisteredBackupDialog(self.main_window)
        self.d_ask_registered_backup = RegisteredBackupDialog(self.main_window)

    #
    # Add a button in the toolbar.
    #
    def add_button(self, parent: QWidget, icon_name: str, text: str, function, arg=None):
        def arg_helper():
            function(arg)

        action = QAction(QIcon(Config.resource(f'icons/{icon_name}.png')), text, parent)

        if arg:
            self.__connect_action(action, arg_helper)
        else:
            self.__connect_action(action, function)

        button = QToolButton(self.tb_toolbar)
        button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        button.setDefaultAction(action)
        self.tb_toolbar.addWidget(button)

    #
    # Add a separator in the toolbar.
    #
    def add_separator(self):
        self.tb_toolbar.addSeparator()

    #
    # Asks whether only new files should be scanned.
    # This method must be called by a background thread.
    #
    def ask_only_new_files(self) -> OnlyNewFilesDialog.Options:
        return self.show_dialog_and_wait(self.d_only_new_files)

    #
    # Asks options for creating a new backup.
    #
    def ask_backup_options(self) -> CreateBackupDialog.Options:
        self.d_create_backup_options.signal_populate.emit()
        return self.show_dialog_and_wait(self.d_create_backup_options)

    #
    # Picks an unregistered backup volume and related options.
    # This method must be called by a background thread.
    #
    def pick_unregistered_backup(self, values) -> UnregisteredBackupDialog.Options:
        self.d_ask_unregistered_backup.signal_populate.emit(values)
        return self.show_dialog_and_wait(self.d_ask_unregistered_backup)

    #
    # Picks an registered backup volume and related options.
    # This method must be called by a background thread.
    #
    def pick_registered_backup(self, values) -> RegisteredBackupDialog.Options:
        self.d_ask_registered_backup.signal_populate.emit(values)
        return self.show_dialog_and_wait(self.d_ask_registered_backup)

    #
    # Shows a dialog and wait for the user input. If the 'OK' button is pressed, a namedtuple is asked to
    # the dialog method user_options() and returned; otherwise None is returned.
    #
    def show_dialog_and_wait(self, dialog: QDialog) -> namedtuple:
        self.dialog_closed = threading.Event()
        self.signal_show_dialog.emit(dialog)
        self.dialog_closed.wait()
        options = dialog.user_options()
        self.log(f'Options: {options}')
        return options if dialog.result() == QDialog.Accepted else None

    #
    # Logs both to the log file and the console. FIXME: this should be moved elsewhere. Only signals here.
    #
    def log_to_console(self, text: str):
        self.log(text)
        self.signal_log_to_console.emit(text)

    #
    # Logs a bold text both to the log file and the console. FIXME: this should be moved elsewhere. Only signals here.
    #
    def log_bold_to_console(self, text: str):
        self.log(8 * '*' + ' ' + text)
        self.signal_log_to_console.emit(html_bold(text))

    #
    # Logs a red text both to the log file and the console. FIXME: this should be moved elsewhere. Only signals here.
    #
    def log_red_to_console(self, text: str):
        self.log('ERROR ' + text)
        self.signal_log_to_console.emit(html_red(text))

    #
    # Connects an action to a callback.
    #
    def __connect_action(self, action: QAction, function):
        def completed():
            self.tb_toolbar.setEnabled(True)

        def error(exctype, value, traceback):
            self.log(f'ERROR: {exctype}: {value}')

        def start():
            self.tb_toolbar.setEnabled(False)
            worker = Worker(function, log_exception=self.log_exception)
            worker.signals.finished.connect(completed)
            worker.signals.error.connect(error)
            self.__slot_clear_console()
            self.__slot_reset_progress()
            self.executor.submit(worker)

        action.triggered.connect(start)

    @Slot(QDialog)
    def __slot_show_modal_dialog(self, dialog: QDialog):
        # print(f'__slot_show_dialog.thread {QThread.currentThread()}')
        dialog.setModal(True)
        dialog.show()
        dialog.exec_()
        self.dialog_closed.set()

    @Slot(float)
    def __slot_set_progress(self, progress: float):
        self.pb_progress.setMaximum(self.PROGRESS_MAX)  # eventually cancels indeterminate mode
        self.pb_progress.setValue(round(progress * self.PROGRESS_MAX))

    @Slot(float)
    def __slot_set_secondary_progress(self, progress: float):
        self.pb_progress_secondary.setValue(round(progress * self.PROGRESS_MAX))

    @Slot()
    def __slot_progress_indeterminate(self):
        self.pb_progress.setMaximum(0)
        self.pb_progress_secondary.setValue(0)

    @Slot()
    def __slot_reset_progress(self):
        self.pb_progress.reset()
        self.pb_progress_secondary.reset()

    @Slot(str)
    def __slot_log_to_console(self, text: str):
        self.__append_text_and_scroll(self.te_console, text)

    @Slot(str)
    def __slot_log_to_error_console(self, text: str):
        self.__append_text_and_scroll(self.te_error_console, text)

    @Slot()
    def __slot_clear_console(self):
        self.lb_status.setText('')
        self.te_console.setPlainText('')
        self.te_error_console.setPlainText('')

    @staticmethod
    def __append_text_and_scroll(console, text: str):
        console.append(text)
        scroll_bar = console.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())


#
#
#
class AdapterSupport:
    def __init__(self, widgets: Widgets):
        self.widgets = widgets


#
#
#
class RsyncPresentationAdapter(RSyncPresentation, AdapterSupport):
    def __init__(self, widgets: Widgets):
        RSyncPresentation.__init__(self)
        AdapterSupport.__init__(self, widgets)

    def notify_status(self, status: str):
        self.widgets.signal_status.emit(status)

    def notify_progress_indeterminate(self):
        self.widgets.signal_progress_indeterminate.emit()

    def notify_secondary_progress(self, progress: float):
        self.widgets.signal_secondary_progress.emit(progress)

    def notify_reset_progress(self):
        self.widgets.signal_progress_reset.emit()

    # TODO: push up, but if you do it doesn't work
    def notify_progress(self, partial: int, total: int):
        if total > 0:
            self.widgets.signal_progress.emit(float(1.0 * partial / total))

    def notify_message(self, message: str):
        self.widgets.log_to_console(message)

    def notify_error(self, message: str):
        self.widgets.signal_log_to_error_console.emit(message)
    # END TODO


#
#
#
class FingerprintingPresentationAdapter(FingerprintingPresentation, AdapterSupport):
    def __init__(self, widgets: Widgets):
        FingerprintingPresentation.__init__(self)
        AdapterSupport.__init__(self, widgets)

    def notify_counting(self):
        self.widgets.signal_status.emit('Counting files...')
        self.widgets.log_to_console('Counting files...')

    def notify_file_count(self, file_count: int):
        # self.widgets.log_to_console(f'{file_count} files to scan')
        pass

    def notify_file(self, path: str, is_new: bool):
        path = shortened_path(path)
        self.widgets.signal_status.emit(path)

        if is_new:
            self.widgets.log_to_console(path)
        else:
            self.widgets.log(path)

    def notify_file_moved(self, old_path: str, new_path: str):
        old_path = shortened_path(old_path)
        new_path = shortened_path(new_path)
        self.widgets.log_to_console(f'{old_path}\n    ↳ {new_path}')

    def notify_error(self, message: str):
        message = html_red(message)
        self.widgets.log_red_to_console(message)
        self.widgets.signal_log_to_error_console.emit(message)

    # TODO: push up, but if you do it doesn't work
    def notify_progress(self, partial: int, total: int):
        if total > 0:
            self.widgets.signal_progress.emit(float(1.0 * partial / total))

    def notify_secondary_progress(self, progress: float):
        self.widgets.signal_secondary_progress.emit(progress)

    def notify_message(self, message: str):
        self.widgets.log_to_console(message)
    # END TODO


class MainWindow(QWidget):
    #
    # Constructor.
    #
    def __init__(self):
        QWidget.__init__(self)

        self.home = Config.home_folder()
        self.app_folder_path = Config.app_folder_path()
        log_folder = f'{self.app_folder_path}/log'
        log_path = f'{log_folder}/SolidBlue.log'
        os.makedirs(log_folder, exist_ok=True)
        self.log_file = open(log_path, 'wt')
        self.log(f'Home directory: {self.home} - Script directory: {Config.resource("")}')

        self.macos_excludes = Config.resource('macos-excludes.txt')

        self.executor = Executor(self.log, self.log_exception)
        self.widgets = Widgets(self, self.executor, self.log, self.log_exception)

        for scan in Config.scan_config().values():
            self.widgets.add_button(self, scan.icon, f'Scan {scan.label}', self.__scan_files, scan)

        self.widgets.add_separator()
        self.widgets.add_button(self, 'create-backup', 'Create backup', self.__create_encrypted_backup)
        self.widgets.add_button(self, 'register-backup', 'Register backup', self.__register_backup)
        self.widgets.add_button(self, 'check-backup', 'Check backup', self.__check_backup)
        self.widgets.add_button(self, 'show-backups', 'Show backups', self.__show_backups)
        self.widgets.add_separator()

        for pmf in Config.push_files_config().values():
            self.widgets.add_button(self, pmf.icon, pmf.label, self.__push_files, pmf)

        self.widgets.add_separator()
        self.widgets.add_button(self, 'check-all-volumes', 'Check volumes', self.__check_all_volumes)
        self.setLayout(self.widgets.layout)

        self.rsync = RSync(presentation=RsyncPresentationAdapter(self.widgets), log=self.log)
        self.fingerprinting_control = FingerprintingControl(database_folder=Config.database_folder(),
                                                            executor=self.executor,
                                                            presentation=FingerprintingPresentationAdapter(self.widgets),
                                                            log=self.log,
                                                            debug_function=self.debug)

    #
    # Scans files for consistency.
    #
    def __scan_files(self, config: Config.Scan):
        self.log(f'__scan_files({config})')
        options = self.widgets.ask_only_new_files()

        if options:
            self.__start_notification(f'Scanning {config.label}...')
            self.fingerprinting_control.scan(config.path, config.filter, options.only_new_files)
            self.__completion_notification(f'{config.label} scanned.')

    #
    #
    #
    def __create_encrypted_backup(self):
        options = self.widgets.ask_backup_options()

        if options:
            self.__start_notification(f'Creating encrypted backup...')
            self.fingerprinting_control.create_encrypted_backup(folders=options.folders,
                                                                backup_name=options.label,
                                                                algorithm=options.algorithm,
                                                                hash_algorithm=options.hash_algorithm,
                                                                burn=options.burn)
            self.__completion_notification('Encrypted backup created.')

    #
    # Registers a backup in an external volume.
    #
    def __register_backup(self):
        options = self.widgets.pick_unregistered_backup(self.fingerprinting_control.mounted_backup_volumes(registered=False))

        if options:
            self.__start_notification(f'Registering backup {options.base_path} ({options.label})...')
            self.fingerprinting_control.register_backup(options.label, options.base_path, eject_after=options.eject_after_scan)
            self.__completion_notification(f'Backup {options.base_path} registered.')

    #
    # Checks a backup in an external volume.
    #
    def __check_backup(self):
        options = self.widgets.pick_registered_backup(self.fingerprinting_control.mounted_backup_volumes(registered=True))

        if options:
            self.__start_notification(f'Checking backup {options.base_path}...')
            self.fingerprinting_control.check_backup(options.base_path, eject_after=options.eject_after_scan)
            self.__completion_notification(f'Backup {options.base_path} checked.')

    #
    # Prints the backup registry.
    #
    def __show_backups(self):
        def fmt(date):
            return date.strftime("%Y-%m-%d %H:%M") if date else None

        table = '<table border=1>'
        table += f'<tr><td>Volume</td><td>Encrypted</td><td>Created</td><td>Registered</td><td>Checked</td></tr>'

        for backup in self.fingerprinting_control.storage.get_backups():
            encrypted = 'encrypted' if backup.encrypted else ''
            table += f'<tr><td>{backup.label}</td><td>{encrypted}</td><td>{fmt(backup.creation_date)}</td>' \
                     f'<td>{fmt(backup.registration_date)}</td><td>{fmt(backup.latest_check_date)}</td></tr>'

        table += '</table>'
        self.widgets.log_to_console(table)

    #
    # Pushes files to a target.
    #
    def __push_files(self, config: Config.PushFiles):
        self.__start_notification(f'Pushing files to {config.server}...')
        # --ignore-errors is needed to ensure deletions complete also in case of error.
        flags = ['--delete', '--delete-excluded', '--delete-before', '--progress', '--stats', '-rtvv', '--ignore-errors']
        flags += config.extra_rsync_flags
        flags += [f'--exclude-from={self.macos_excludes}']
        rsync = Config.resource('rsync3')

        for item_name, item in config.items.items():
            self.widgets.log_bold_to_console(f'Syncing {item_name}...')

            if not os.path.exists(item.source):
                self.widgets.log_red_to_console(f'Source not mounted: {item.source}')
            else:
                target = f'{config.server}:{item.target}/' if config.server else f'{item.target}/'
                self.__execute([rsync] + flags + item.extra_rsync_flags + [f'{item.source}/', target], self.rsync.ccc_post_processor)

        self.__completion_notification(f'Files pushed to {config.server}.')

    #
    # Checks all mounted volumes.
    #
    def __check_all_volumes(self):
        volumes = sorted(os.listdir('/Volumes'))
        self.__start_notification(f'Checking volumes: {", ".join(volumes)}')

        for step, volume in enumerate(volumes, start=1):
            self.widgets.log_bold_to_console(f'Checking volume: {volume} ...')
            return_code = self.__execute(['sudo', 'diskutil', 'verifyVolume', volume])

            if return_code != 0:
                self.widgets.log_red_to_console(f'WARNING: Exit code: {return_code}')

            self.widgets.signal_progress.emit(1.0 * step / len(volumes))

        self.__completion_notification("All volumes checked")

    #
    # Execs a process and returns the exit code.
    #
    def __execute(self, args, output_processor=None, fail_on_result_code: bool = False, log_cmdline: bool = True):
        if output_processor is None:
            output_processor = self.__default_post_processor

        if log_cmdline:
            self.widgets.log_to_console(html_italic(' '.join(args)))
        else:
            self.log(' '.join(args))

        return self.executor.execute(args, output_processor=output_processor, fail_on_result_code=fail_on_result_code)

    #
    # A string post-processor which just logs to the console.
    #
    def __default_post_processor(self, string: str):
        self.widgets.log_to_console(string)

    #
    # Notifies the start of a task.
    #
    def __start_notification(self, message: str):
        notification(message)
        self.widgets.log_bold_to_console(message)

    #
    # Notifies the completion of a task.
    #
    def __completion_notification(self, message: str):
        self.widgets.log_to_console(message)
        notification(message)

    #
    # Appends a timestamped text.
    #
    def __append_sync_timestamp(self, folder: str, text: str):
        latest_sync_file = f'{folder}/.latest-sync'

        with open(latest_sync_file, 'at') as file:
            file.write(f'{self.__current_timestamp()}: {text}\n')

    #
    # Return a properly formatted timestamp.
    #
    @staticmethod
    def __current_timestamp() -> str:
        return datetime.datetime.now().strftime("%Y-%m-%d (%b %d) %H-%M-%S")

    #
    # Logs a line.
    #
    def log(self, string: str):
        print(string, file=self.log_file)
        self.log_file.flush()

    #
    # Logs an exception
    #
    def log_exception(self, message: str, exception):
        self.log(message)
        traceback.print_exc(file=self.log_file)
        self.log_file.flush()
        self.widgets.log_red_to_console(f'Error: {str(exception)}')

    #
    #
    #
    def debug(self, message: str):
        if True:
            self.log(f'>>>> {message}')


#
# Main function.
#
def __main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.resize(1280, 800)
    main_window.show()
    exit_code = app.exec_()
    main_window.log_file.close()
    sys.exit(exit_code)


#
# Relaunches the script as root.
#
def __relaunch_as_root():
    print('Relaunching as root')
    script = sys.argv[0]
    applescript = f'do shell script "{script}" with administrator privileges'
    os.execvp('osascript', ['osascript', '-e', applescript])


if __name__ == '__main__':
    if os.geteuid() != 0 and '--no-root' not in sys.argv:
        __relaunch_as_root()
    else:
        __main()
