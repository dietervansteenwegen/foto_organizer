from datetime import datetime
import os
import shutil
from typing import Tuple, Union
from exif import Image

DOUBLES_FILENAME = 'doubles.list'


class PhotoRenamer:
    def __init__(self, src_path, file, logger):
        self.logger = logger
        self.path = src_path
        self.src_file = file

    def rename_if_jpeg(self) -> None:
        """If file exention is .jpeg, rename to .jpg and update self.src_file"""
        if self.src_file[-5:].lower() != '.jpeg':
            return
        jpg_filename = self.src_file[:-5] + '.jpg'
        if self.logger:
            self.logger.info('Renaming "{}" to "{}"'.format(self.src_file, jpg_filename))
        os.rename(os.path.join(self.path, self.src_file), os.path.join(self.path, jpg_filename))
        self.src_file = jpg_filename

    def get_exif_data(self) -> bool:
        """Populate properties from exif data.

        Populate self.dt, self.dt_orig, self.model

        Returns:
            bool: True is self.dt or self.dt_orig has succesfully been parsed.
        """
        with open(os.path.join(self.path, self.src_file), 'rb') as src_file:
            exif_src = Image(src_file)

            # get datetime
            try:
                dt = getattr(exif_src, 'datetime')
                self.dt = datetime.strptime(dt, '%Y:%m:%d %H:%M:%S')
            except (KeyError, ValueError, AttributeError):
                self.dt = None

            # get datetime_original
            try:
                dt_orig = getattr(exif_src, 'datetime_original')
                self.dt_orig = datetime.strptime(dt_orig, '%Y:%m:%d %H:%M:%S')
            except (KeyError, ValueError, AttributeError):
                self.dt_orig = None

            # get model
            try:
                self.model = getattr(exif_src, 'model')
            except (KeyError, AttributeError):
                self.model = None

        properties = (self.dt, self.dt_orig, self.model)
        if not all(properties):
            issues = []
            if not self.dt:
                issues.append('dt')
            if not self.dt_orig:
                issues.append('dt_orig')
            if not self.model:
                issues.append('model')
            msg = 'Could not get the following exif data for file {}: '.format(self.src_file)
            msg += ','.join(issues)
            self.logger.info(msg)

        return bool(self.dt or self.dt_orig)

    def check_whatsapp(self) -> Union[bool, None]:
        """ Check if filename matches whatsapp pattern and extract date and set number.
        example filename: IMG-20181108-WA0025
        Returns True succesful
        Returns False if not
        TODO: maybe files can have a WA filename with correct original date,
                but have exif data that doesn't match.
        TODO: If that is possible, check first if whatsapp image, then overwrite exif dt_orig.
        """
        if self.src_file[:4] == 'IMG-':
            try:
                without_ext = os.path.splitext(self.src_file)[0]
                self.dt = datetime.strptime(without_ext[4:12], '%Y%m%d')
                number = int(without_ext[-4:])
                self.dt = self.dt.replace(minute=number // 60, second=number % 60)

            except Exception:
                return False

            else:
                return True
        else:
            return None

    def dt_matches_dt_orig(self) -> bool:
        """ check if both datetimes are filled in and match.
        Return True if only one is filled in, or if both match. Else return False.
        """
        if not (self.dt and self.dt_orig):
            return True
        return self.dt == self.dt_orig

    def new_filename(self,
                     target_path: str,
                     include_cam_model: bool = True,
                     keywords_to_keep: Union[str, None] = None,
                     replace_chars_in_model: Union[None, list[str]] = None) -> Tuple[str, str]:
        """Generate new filename based on target path and picture properties

        Args:
            target_path (str): Base path for target
            include_cam_model (bool, optional): Add camera model (if available)to filename. 
                                                Defaults to True.
            keywords_to_keep (Union[str, None], optional): Certain keywords that should be kept if
                                                           they are in orig filename (BURST,...)
                                                           Defaults to None.
            replace_chars_in_model (Union[None, list[str]], optional): List of lists containing . Defaults to None.

        Returns:
            Tuple[str, str]: target path, filename
        """
        new_filename = ''
        date_source = self.dt_orig or self.dt
        new_filename += date_source.strftime('%Y%m%d_%H%M%S')

        if keywords_to_keep:
            for keyword in keywords_to_keep:
                if keyword in self.src_file:
                    new_filename += '_' + keyword

        if include_cam_model and self.model and replace_chars_in_model:
            for i, j in replace_chars_in_model:
                self.model = self.model.replace(i, j)
            new_filename += '(_{})'.format(self.model)

        new_filename += '.jpg'
        year = str(date_source.year)
        month = ('{:02d}'.format(date_source.month))
        target_dir = os.path.join(target_path, year, month)
        return target_dir, new_filename.upper()

    def move_file(self,
                  src_file: str,
                  new_path: str,
                  new_filename: str,
                  process_doubles: bool = True) -> Tuple[Union[str, None], bool]:
        """Move source file to new path and filename.

        Args:
            src_file (str): Original path+filename
            new_path (str): Target path
            new_filename (str): target filename
            process_doubles (bool, optional): If target already exists, generate new filename. 
                                              Defaults to True.

        Returns:
            Tuple[Union[str,None], bool]: filename if new file was moved (None if not),
                                          is a double
        """

        ideal_target_file = os.path.join(new_path, new_filename)
        target_file = self.generate_unique_filename(ideal_target_file, process_doubles)
        is_double = (target_file != ideal_target_file)
        if target_file:
            if not os.path.isdir(new_path):
                os.makedirs(new_path)
            return (shutil.move(src_file, target_file), is_double)
        else:
            return (None, is_double)
        """Generate unique filename (if required)
        checks if base_filename already exists.
        if not, return base_filename.
        If it exists, return a newly generated filename if process_doubles is enabled
        """

    def generate_unique_filename(self, base_filename: str,
                                 process_doubles: bool) -> Union[str, None]:
        """Generate a unique target file name

        If target file name already exists, add underscore and counter until target filename is
        a unique filename.

        Args:
            base_filename (str): original target filename
            process_doubles (bool): proceed with generating alternative filenames if 
                                    target already exists

        Returns:
            Union[str, None]: None if target exists but process_doubles is True
                              str if a new, unique filename has been generated
        """
        if not os.path.isfile(base_filename):
            return base_filename

        with open(DOUBLES_FILENAME, 'a+') as file:
            file.write(base_filename + '\n')
        if not process_doubles:
            return None
        counter = 1
        filename, ext = base_filename.rsplit('.', 1)
        new_filename = filename + '_COPY[{}]' + '.' + ext
        while os.path.exists(new_filename.format(counter)):
            counter += 1
        self.logger.info('Double filename: {}'.format(new_filename.format(counter)))
        return new_filename.format(counter)
