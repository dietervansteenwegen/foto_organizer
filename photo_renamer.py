from datetime import datetime
import os
import shutil
from exif import Image

DOUBLES_FILENAME = 'doubles.list'



class PhotoRenamer:
    def __init__(self, path, file, logger = None):
        self.logger = logger
        self.path = path
        self.src_file = file

    def rename_if_jpeg(self):
        if not self.src_file[-5:].lower() == '.jpeg':
            return
        jpg_filename = self.src_file[:-5] + '.jpg'
        if self.logger:
            self.logger.info('Renaming "{}" to "{}"'.format(self.src_file, jpg_filename))
        os.rename(os.path.join(self.path, self.src_file), os.path.join(self.path,jpg_filename))
        self.src_file = jpg_filename

    def get_exif_data(self):
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

        return True if self.dt or self.dt_orig else False

    def check_whatsapp(self):
        """ Check if filename matches whatsapp pattern and extract date and set number.
        example filename: IMG-20181108-WA0025
        Returns True succesful
        Returns False if not
        TODO: maybe files can have a WA filename with correct original date, but have exif data that doesn't match.
        TODO: If that is possible, check first if whatsapp image, then overwrite exif dt_orig.
        """
        if self.src_file[:4] == 'IMG-':
            try:
                without_ext = os.path.splitext(self.src_file)[0]
                self.dt = datetime.strptime(without_ext[4:12], '%Y%m%d')
                number = int(without_ext[-4:])
                self.dt = self.dt.replace(minute = number // 60, second = number %60)

                return True
            except:
                return False


    def dt_matches_dt_orig(self):
        """ check if both datetimes are filled in and match.
        Return True if only one is filled in, or if both match. Else return False.
        """
        if not (self.dt and self.dt_orig):
            return True
        return self.dt == self.dt_orig


    def new_filename(self, include_camera_model = True, keywords_to_keep = None, replace_chars_in_model = None):
        new_filename = ''
        date_source = self.dt_orig if self.dt_orig else self.dt  # prefer dt_orig...
        new_filename += date_source.strftime('%Y%m%d_%H%M%S')

        for keyword in keywords_to_keep:
            if keyword in self.src_file:
                new_filename += '_' + keyword

        if include_camera_model and self.model:
            for i,j in replace_chars_in_model:
                    self.model = self.model.replace(i, j)
            new_filename += '(_{})'.format(self.model)

        new_filename += '.jpg'
        year = str(date_source.year)
        month = ('{:02d}'.format(date_source.month))
        target_dir = os.path.join(self.path, year, month)
        return target_dir, new_filename.upper()

    def move_file(self, src_file, new_path, new_filename, process_doubles = True):
        is_double = False
        ideal_target_file = os.path.join(new_path, new_filename)
        target_file = self.generate_unique_filename(ideal_target_file, process_doubles)
        if not target_file == ideal_target_file:
            is_double = True
        if target_file:
            if not os.path.isdir(new_path):
                os.makedirs(new_path)
            return (shutil.move(src_file, target_file), is_double)
        else:
            return (None, is_double)

    def generate_unique_filename(self, base_filename, process_doubles):
        """ generate unique filename (if required)
        checks if base_filename already exists. 
        if not, return base_filename.
        If it exists, return a newly generated filename if process_doubles is enables
        """
        if not os.path.isfile(base_filename):
            return base_filename

        with open(DOUBLES_FILENAME, 'a+') as file:
            file.write(base_filename + '\n')
        if not process_doubles:
            return None
        counter = 1
        filename, ext = base_filename.rsplit('.', 1)
        new_filename = filename+ '_COPY[{}]' + '.' + ext
        while os.path.exists(new_filename.format(counter)):
            counter +=1
        self.logger.info('Double filename: {}'.format(new_filename.format(counter)))
        return new_filename.format(counter)