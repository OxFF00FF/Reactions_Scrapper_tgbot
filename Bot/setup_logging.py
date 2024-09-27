import logging
import logging.handlers
import os
import platform
import subprocess
from datetime import datetime
from logging.handlers import RotatingFileHandler

import pkg_resources

from Bot.colors import *


def system_info():
    # Информация о системе с помощью модуля platform
    print("=== System Information ===")
    print(f"System: {platform.system()}")
    print(f"Machine: {platform.machine()}")
    print(f"Platform: {platform.platform()}")
    print(f"Python Version: {platform.python_version()}")
    print(f"Python Implementation: {platform.python_implementation()}")
    print(f"Python Compiler: {platform.python_compiler()}")
    print(f"Python Build: {platform.python_build()}")
    print(f"Current User: {os.getlogin()}")
    print(f"Current Working Directory: {os.getcwd()}")

    # Информация об установленных пакетах Python с помощью pkg_resources
    print("\n=== Installed Python Packages (pkg_resources) ===")
    installed_packages = pkg_resources.working_set
    for package in installed_packages:
        print(f"{package.key} ({package.version})")

    print("\n=== Installed Python Packages (pip list) ===")
    result = subprocess.run(['pip', 'list'], capture_output=True, text=True)
    print(result.stdout)


def set_logger(log_name: str = 'app', log_file: str = 'logs.log'):
    class ColorFormatter(logging.Formatter):
        LEVEL_COLORS = {
            logging.DEBUG: LIGHT_BLUE,
            logging.INFO: GREEN,
            logging.WARNING: YELLOW,
            logging.ERROR: LIGHT_RED,
            logging.CRITICAL: RED
        }

        def format(self, record):
            asctime = DARK_GRAY
            name = DARK_GRAY
            filename = DARK_GRAY
            funcname = DARK_GRAY
            lineno = DARK_GRAY

            level = self.LEVEL_COLORS.get(record.levelno, DEFAULT)
            record.asctime = self.formatTime(record)
            log_message = f"{asctime}{record.asctime}{WHITE} - " \
                          f"{name}{record.name}{WHITE} - " \
                          f"{level}{BOLD}{record.levelname}{RESET}{WHITE} |  " \
                          f"{record.getMessage()}  |{WHITE} " \
                          f"{filename}{record.filename} · " \
                          f"{funcname}{record.funcName}() · " \
                          f"{lineno}{record.lineno} line{RESET}"
            return log_message

        def formatTime(self, record, datefmt=None):
            log_time = datetime.fromtimestamp(record.created)
            if datefmt:
                return log_time.strftime(datefmt)
            return log_time.strftime('%Y-%m-%d %H:%M:%S')

    class FileFormatter(logging.Formatter):
        def format(self, record):
            log_message = f"{record.asctime} - " \
                          f"{record.name} - " \
                          f"{record.levelname.ljust(8)} |  " \
                          f"{record.getMessage()}  | " \
                          f"{record.filename} · " \
                          f"{record.funcName}() · " \
                          f"{record.lineno} line"
            return log_message

        def formatTime(self, record, datefmt=None):
            log_time = datetime.fromtimestamp(record.created)
            if datefmt:
                return log_time.strftime(datefmt)
            return log_time.strftime('%Y-%m-%d %H:%M:%S')

    log_directory = os.path.join(os.path.dirname(__file__), f'../logs/{log_name}')
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)
    log_file_path = os.path.join(log_directory, log_file)

    app_logger = logging.getLogger(log_name)
    app_logger.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    color_formatter = ColorFormatter()
    file_formatter = FileFormatter()
    console_handler.setFormatter(color_formatter)
    app_logger.addHandler(console_handler)

    # File handler (RotatingFileHandler)
    file_handler = RotatingFileHandler(log_file_path, maxBytes=10 * 1024 * 1024, backupCount=5, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    app_logger.addHandler(file_handler)

    return logging.getLogger(log_name)


logger = set_logger()
