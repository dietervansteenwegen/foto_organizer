import logging, logging.handlers
import os
import threading
from time import sleep
from typing import Iterator, List, Tuple
from photo_renamer import PhotoRenamer as pr
from datetime import datetime
from fnmatch import fnmatch as filename_match

INCLUDE_CAMERA_MODEL: bool = True
REPLACE_CHARS_IN_MODEL = (('_', '-'), ('(', ''), (')', ''), (' ', '-'))
KEYWORDS_TO_KEEP = ['HDR', 'PORTRAIT', 'WA', 'BURST', 'COVER', 'TOP']
PROCESS_DOUBLES: bool = False  # if a picture with same datetime exist: True: rename, else: don't process original
DT_AND_DT_ORIG_NEED_TO_MATCH: bool = False
# IMAGE_DIR = 'P:\Automatic Upload\Motorola moto g(8) plus'
SOURCE_PATH = 'P:/temp'
TARGET_PATH = 'P:/Automatic Upload/temp2'

MSG_PROCESSED = ('Processed: {0[processed]}, moved: {0[moved]}, double: {0[double]}, '
                 'no dt: {0[no_dt]}, whatsapp: {0[whatsapp]}, dt_mismatch: {0[dt_mismatch]}')
LOG_FILENAME = 'output.log'
DT_FORMAT = '%d/%m/%Y %H:%M:%S'
LOG_MSG_FORMAT = '%(asctime)s|%(levelname)s|%(message)s'
LOG_NAME = 'PhotoRenamer'
files = {'processed': 0, 'moved': 0, 'double': 0, 'no_dt': 0, 'whatsapp': 0, 'dt_mismatch': 0}


def create_logger():
    rf_handler = logging.handlers.RotatingFileHandler(LOG_FILENAME,
                                                      maxBytes=1000000,
                                                      backupCount=5)
    formatter = logging.Formatter(LOG_MSG_FORMAT, DT_FORMAT)
    rf_handler.setFormatter(formatter)
    logger = logging.getLogger(LOG_NAME)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(rf_handler)
    logger.info('---Init logger---')
    logger.debug('Base directory: "{}"'.format(abs_src_path))
    return logger


def find_files(source_dir: str,
               pattern: Tuple[str, ...],
               logger: logging.Logger,
               e: threading.Event = None) -> Iterator[str]:
    """Generate a list of picture files and yield one by one.

    Args:
        source_dir (str): Source dir to scan for pictures
        pattern (Tuple[str, ...]): Filename pattern to search for (i.e. '*.jpg')
        logger (logging.Logger): Where to log to.
        e (threading.Event, optional): To signal that list has been created. Defaults to None.

    Yields:
        str: file in (subdir of) source_dir matching the pattern.
    """
    try:
        logger.debug('Creating file list, this might take a while.')

        all_files_full = [
            file for file in os.listdir(source_dir)
            if os.path.isfile(os.path.join(source_dir, file))
        ]  # all files (full path) in (subdirs of) source_dir
        files_full = [file for file in all_files_full if check_multiple_patterns(file, pattern)]

        msg = f'Done creating file list, total of {len(files_full)} files in {source_dir}'
        print(msg)
        logger.debug(msg)

        if e:
            e.set()

        yield from files_full

    except FileNotFoundError:
        import sys
        msg = 'FileNotFoundError: No files found, does directory exist? Exiting...'
        print(msg)
        logger.error(msg)
        sys.exit()


def check_multiple_patterns(file_full: str, patterns: Tuple[str, ...]) -> bool:
    """Check if the filename matches one of the patterns in patterns

    Args:
        file_full (str): Full path of the file to check
        patterns (List[str]): List of patterns to check for

    Returns:
        bool: True if filename matches one of the patterns
    """
    return any(filename_match(file_full, pattern) for pattern in patterns)


def print_results() -> None:
    """Print actions and time taken."""
    total_time = datetime.now() - start_time
    total_time_str = '{} minutes, {} seconds'.format(total_time.seconds // 60,
                                                     total_time.seconds % 60)

    print('Finished.')
    logger.info('Finished.')

    print(MSG_PROCESSED.format(files))
    logger.info(MSG_PROCESSED.format(files))

    msg_time = 'Total time: ' + total_time_str
    print(msg_time)
    logger.info(msg_time)


def print_info(e: threading.Event = None) -> None:
    """Print info to stdout

    Print either that files are being listed of the current status.

    Args:
        e (threading.Event, optional): signal that file list has been made. Defaults to None.
    """
    while True:
        cur_time = datetime.now().strftime(DT_FORMAT)
        if e and not e.is_set():
            print(cur_time + ' Listing files, this might take a while...')
        else:
            print(cur_time + ' ' + MSG_PROCESSED.format(files))
        sleep(5)


def main_operation(abs_src_path: str, 
                   abs_target_path:str, 
                   logger: logging.Logger, 
                   e: threading.Event = None):
    """List all files to be checked, then go over them and move if necessary.

    Args:
        abs_src_path (str): Absolute source directory (where files currently are)
        abs_target_path (str): Absolute target directory (where files should go)
        logger (logging.Logger): where to log to
        e (threading.Event, optional): [description]. Defaults to None.
    """
    global files

    for file in find_files(abs_src_path, ('*.jpeg', '*.jpg'), logger=logger, e=e):
        jpg = pr(src_path=abs_src_path, file=file, logger=logger)
        files['processed'] += 1
        logger.debug('Processing "{}"'.format(file))

        if not jpg.get_exif_data():
            files['no_dt'] += 1
            if jpg.check_whatsapp():
                files['whatsapp'] += 1
            else:
                logger.warning(
                    'no dt(_orig) for file "{}" and not a WhatsApp picture. Skipping this file.'.
                    format(file))
                continue
        if DT_AND_DT_ORIG_NEED_TO_MATCH and not jpg.dt_matches_dt_orig():
            # both are in exif data, but don't match. Might add option to keep the oldest date
            logger.warning(
                'dt ({}) does not match dt_orig ({}) for "{}". Skipping this file...'.format(
                    jpg.dt, jpg.dt_orig, file))
            files['dt_mismatch'] += 1
            continue

        new_path, new_filename = jpg.new_filename(target_path = abs_target_path, 
                                                  include_cam_model= INCLUDE_CAMERA_MODEL, 
                                                  keywords_to_keep= KEYWORDS_TO_KEEP,
                                                  replace_chars_in_model= REPLACE_CHARS_IN_MODEL)
        rtn = jpg.move_file(os.path.join(abs_src_path, file), new_path, new_filename,
                            PROCESS_DOUBLES)
        if rtn[0]:
            logger.debug('moved file {} to {}'.format(file, rtn[0]))
            files['moved'] += 1
        else:
            logger.info(
                'file {} is a double and has not been processed (PROCESS_DOUBLES SET TO {}'.format(
                    file, PROCESS_DOUBLES))
        if rtn[1]:
            files['double'] += 1


if __name__ == '__main__':

    abs_src_path = os.path.abspath(SOURCE_PATH)
    abs_target_path = os.path.abspath(TARGET_PATH)
    logger = create_logger()

    start_time = datetime.now()

    e = threading.Event()

    main_thread = threading.Thread(name='main_operation',
                                    target = main_operation,
                                    args=(abs_src_path, abs_target_path, logger, e))
    print_thread = threading.Thread(name='print_info',
                                        target=print_info,
                                        args=(e,),
                                        daemon = True)
    main_thread.start()
    print_thread.start()
    main_thread.join()

    print_results()