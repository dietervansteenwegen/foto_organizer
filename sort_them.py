# from plum._plum import UnpackError
import logging, logging.handlers
import os
import threading
from time import sleep
from photo_renamer import PhotoRenamer as pr
from datetime import datetime
from fnmatch import fnmatch as filename_match

IMAGE_DIR = r'G:\temp2\Motorola moto g(8) plus'\\
INCLUDE_CAMERA_MODEL = True
REPLACE_CHARS_IN_MODEL=(('_','-'),('(',''),(')',''),(' ','-'))
KEYWORDS_TO_KEEP = ['HDR', 'PORTRAIT', 'WA', 'BURST', 'COVER', 'TOP']
PROCESS_DOUBLES = True  # if a picture with same datetime exist, if True: rename, if False: don't touch/process original
DT_AND_DT_ORIG_NEED_TO_MATCH = False

MSG_PROCESSED = 'Processed: {0[processed]}, moved: {0[moved]}, double: {0[double]}, no dt: {0[no_dt]}, whatsapp: {0[whatsapp]}, dt_mismatch: {0[dt_mismatch]}'
LOG_FILENAME = 'output.log'
DT_FORMAT = '%d/%m/%Y %H:%M:%S'
LOG_MSG_FORMAT = '%(asctime)s|%(levelname)s|%(message)s'
LOG_NAME = 'PhotoRenamer'
files = {'processed':0, 'moved': 0, 'double':0, 'no_dt':0, 'whatsapp':0, 'dt_mismatch': 0}


def create_logger():
    rf_handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=1000000, backupCount = 5)
    formatter = logging.Formatter(LOG_MSG_FORMAT, DT_FORMAT)
    rf_handler.setFormatter(formatter)
    logger = logging.getLogger(LOG_NAME)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(rf_handler)
    logger.info('---Init logger---')
    logger.debug('Base directory: "{}"'.format(abs_path))
    return logger

def find_files(source_dir, pattern, logger = None, e = None):
    try:
        msg = 'creating file list, this might take a while.'
        if logger: logger.debug(msg)
        files = [file for file in os.listdir(source_dir) if os.path.isfile(os.path.join(source_dir,file)) and check_multiple_patterns(file, pattern)]
        msg = 'done creating file list, total of {} files in {}'.format(len(files), source_dir)
        print(msg)
        if logger: logger.debug(msg)
        if e:
            e.set()
        for file in files:
            yield file
    except FileNotFoundError:
        import sys
        msg = 'FileNotFoundError: No files found, does directory exist? Exiting...'
        print(msg)
        logger.error(msg)
        sys.exit()

def check_multiple_patterns(file, patterns):
    for pattern in patterns:
        if filename_match(file,pattern):
            return True
    return False


def print_results():
    total_time = datetime.now() - start_time
    total_time_str = '{} minutes, {} seconds'.format(total_time.seconds//60, total_time.seconds%60)
    msg_time = 'Total time: ' + total_time_str
    print('Finished.')
    logger.info('Finished.')
    print(MSG_PROCESSED.format(files))
    logger.info(MSG_PROCESSED.format(files))
    print(msg_time)
    logger.info(msg_time)

def print_info(e = None):
    while True:
        cur_time = datetime.now().strftime(DT_FORMAT)
        if e and not e.is_set():
            print(cur_time + ' Listing files, this might take a while...')
        else:
            print(cur_time + ' ' + MSG_PROCESSED.format(files))
        sleep(5)

def main_operation(abs_path, logger, e = None):
    global files

    for file in find_files(abs_path, ('*.jpeg', '*.jpg'), logger = logger, e= e):
        jpg = pr(path=abs_path, file=file, logger=logger)
        files['processed'] += 1
        logger.debug('Processing "{}"'.format(file))

        if not jpg.get_exif_data():
            files['no_dt'] += 1
            if jpg.check_whatsapp():
                files['whatsapp'] +=1
            else:
                logger.warning('no dt(_orig) for file "{}" and not a WhatsApp picture. Skipping this file.'.format(file))
                continue
        if DT_AND_DT_ORIG_NEED_TO_MATCH and not jpg.dt_matches_dt_orig():
            # both are in exif data, but don't match. Might add option to keep the oldest date
            logger.warning('dt ({}) does not match dt_orig ({}) for "{}". Skipping this file...'.format(jpg.dt, jpg.dt_orig, file))
            files['dt_mismatch']  += 1
            continue

        new_path, new_filename = jpg.new_filename(INCLUDE_CAMERA_MODEL, KEYWORDS_TO_KEEP, REPLACE_CHARS_IN_MODEL)
        rtn = jpg.move_file(os.path.join(abs_path, file), new_path, new_filename, PROCESS_DOUBLES)
        if rtn[0]:
            logger.debug('moved file {} to {}'.format(file, rtn[0]))
            files['moved'] += 1
        else:
            logger.info('file {} is a double and has not been processed (PROCESS_DOUBLES SET TO {}'.format(file, PROCESS_DOUBLES))
        if rtn[1]:
                files['double'] += 1


if __name__ == '__main__':
    abs_path = os.path.abspath(IMAGE_DIR)
    logger = create_logger()

    start_time = datetime.now()

    e = threading.Event()

    main_thread = threading.Thread(name='main_operation', \
                                    target = main_operation, \
                                    args=(abs_path, logger, e))
    print_thread = threading.Thread(name='print_info', \
                                        target=print_info, \
                                        args=(e,),
                                        daemon = True)
    main_thread.start()
    print_thread.start()
    main_thread.join()

    print_results()