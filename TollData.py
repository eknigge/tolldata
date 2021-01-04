import pandas as pd  # type: ignore
import openpyxl as opxl  # type: ignore
import csv
import pickle
import numpy as np  # type: ignore
import datetime
import random


class PlateCombinatorics:
    """
    Class to handle plate combinatorics. Methods to return variations of plate values
    based on common OCR errors.
    """
    _plate: str = ''
    _result_list: list = []
    _ocr_dict: dict = {'O': 'Q', 'Q': 'O', '8': 'B', 'B': '8', '1': 'I',
                       'I': '1', 'A': '4', '4': 'A', 'D': 'O', 'G': '6',
                       '6': 'G', 'S': '5', '5': 'S'}

    def __init__(self, plate=''):
        self._plate = plate

    def set_plate(self, plate: str):
        """
        Set plate value
        :param plate: plate value
        """
        if not isinstance(plate, str):
            raise TypeError()
        self._plate = plate

    def get_plate(self) -> str:
        """
        :return: plate value
        """
        return self._plate

    def get_plate_combinations(self) -> list:
        """
        :return: return list of plate combinations
        """
        if self._plate == '' or self._plate is None:
            raise ValueError('plate value blank')
        self._result_list.append(self._plate)
        return self.__plate_combinations(self._plate, 0, self._result_list)

    @staticmethod
    def __update_name(old_name: str, new_char: str, index: int) -> str:
        """
        Update input string with new character value at specified index
        :param old_name: str of original name
        :param new_char: replacement character
        :param index: index to replace character
        :return: updated str
        """
        if index == 0:
            return new_char + old_name[1:]
        elif index == len(old_name) - 1:
            return old_name[:index] + new_char
        else:
            new_name = old_name[:index] + new_char + old_name[index + 1:]
            return new_name

    def __plate_combinations(self, plate: str, index: int, result_list: list):
        """
        Recursive method to find all permutations of a plate
        :param plate: str of plate
        :param index: int of index
        :param result_list: list of plate permutations
        :return: list of plate permutations
        """
        if index < len(plate):
            if plate[index] in self._ocr_dict:
                new_plate = self.__update_name(plate, self._ocr_dict[plate[index]], index)
                self._result_list.append(new_plate)
                self.__plate_combinations(new_plate, index + 1, result_list)
            self.__plate_combinations(plate, index + 1, result_list)
            return result_list


class TransactionFile:
    """
    Class to process transaction files from Kapsch toll system. Can process
    both excel and csv files, excel files need to be in xlsx or xlsm format.
    """
    _filename: str = ''
    _df = None
    _header_row: int = -1
    _sheet_name: str = ''
    _input_is_csv: bool = False
    _sheet_names_list: list = ['transaction', 'Transaction', 'trans', 'TrxnDetail',
                               'Sheet1', 'tran', 'trip']
    _header_values: list = ['Trx ID', 'CSC Lane']
    _ocr_header_names: list = ['Ocr Info', 'Plate Info']
    _tag_header_names: list = ['Number']
    _agency_header_names: list = ['Ag']
    _excel_file_types: list = ['xlsx', 'xlsm']
    _payment_header_names: list = ['Pmnt Type']
    _trx_id_names: list = ['Trx ID']

    def __init__(self, filename: str):
        self._filename = filename
        print('Processing: ' + filename)
        if filename.split('.')[1] in self._excel_file_types:
            self.__process_excel_file()
        elif filename.split('.')[1] == 'csv':
            self.__process_csv_file()
            self._input_is_csv = True
        else:
            raise TypeError('Input input, must be xlsx or csv')

        self.__create_tag_fields()
        self.__create_plate_field()
        self.__create_trx_id_field()

    def __create_trx_id_field(self):
        complete: bool = False
        for i in self._trx_id_names:
            if complete:
                break
            try:
                self._df['TRX_ID'] = self._df[i]
                complete = True
            except KeyError:
                continue
        if not complete:
            raise ValueError('Missing TrxID field')

    def __create_plate_field(self):
        columns = self._df.columns
        for i in self._ocr_header_names:
            if i in columns:
                self._df['PLATE'] = self._df[i].str.split(pat='-', expand=True)[0]

    def to_csv(self):
        """
        Output dataframe to csv
        """
        if self._input_is_csv:
            raise ValueError('Input file is a csv file')
        out_filename = self._filename.split('.')[0] + '.csv'
        self._df.to_csv(out_filename)

    def __select_worksheet(self, workbook: opxl):
        """
        Select worksheet from all worksheets. Uses sheet_names_list
        :param workbook: Workbook to search
        """
        for sheet in workbook:
            for i in self._sheet_names_list:
                if i in sheet.title:
                    self._sheet_name = sheet.title

    def __set_excel_header_row(self, wb: opxl):
        """
        Finds header row in workbook. Uses header_values for search.
        :param wb: workbook
        """
        ws: opxl = wb[self._sheet_name]
        header_row: int = 0
        found: bool = False
        for row in ws:
            if found:
                break
            for cell in row:
                if cell.value in self._header_values:
                    found = True
                    self._header_row = header_row
                    break
            header_row += 1

    def __process_excel_file(self):
        """
        Process excel data file info dataframe
        """
        wb: opxl = opxl.load_workbook(filename=self._filename, read_only=True)
        self.__select_worksheet(wb)
        self.__set_excel_header_row(wb)
        self._df = pd.read_excel(self._filename, sheet_name=self._sheet_name,
                                 skiprows=self._header_row)

    def __create_tag_fields(self):
        columns = self._df.columns
        for i in self._tag_header_names:
            if i in columns:
                self._df['TAG_ID'] = self._df[i]

        for i in self._agency_header_names:
            if i in columns:
                self._df['AG'] = self._df[i]

    def get_df(self) -> pd.DataFrame:
        """
        :return: dataframe
        """
        return self._df

    def __get_csv_header(self):
        with open(self._filename) as csvfile:
            reader = csv.reader(csvfile)
            header_row: int = 0
            row_found: bool = False

            for row in reader:
                if row_found:
                    break
                for value in row:
                    if value in self._header_values:
                        self._header_row = header_row
                header_row += 1

    def __process_csv_file(self):
        """
        Wrapper method to identify csv header row and read as
        pandas dataframe.
        """
        self.__get_csv_header()
        self._df = pd.read_csv(self._filename, skiprows=self._header_row, low_memory=False)


class TripFile(TransactionFile):
    _header_values = ['id', 'dt', 'lane', 'agency', 'Plaza']
    _ocr_header_names = ['plate', 'Review Type', 'Plate Info']
    _tag_header_names = ['Ag-Tag', 'Prime']

    def __init__(self, filename):
        super(TripFile, self).__init__(filename)
        self.__create_tag_fields()

    def __create_tag_fields(self):
        """
        overloaded method to create tag and agency fields for
        toll trip files
        """
        columns = self._df.columns
        for i in self._tag_header_names:
            if i in columns:
                tag_field: pd.Series = self._df[i].str.split(pat='-', expand=True)
                self._df['AG'] = pd.to_numeric(tag_field[0])
                self._df['TAG_ID'] = pd.to_numeric(tag_field[1])


class AVIValidation:
    """
    Class to test whether plate is read without a tag. The read threshold
    can be set to constrain which transactions are flagged. The input
    dataframe is required to have the TAG_ID, PLATE, and TRX_ID fields.
    The input dataframe is modified with new fields AVI_MISMATCH (True or False)
     and MISSED_TAG_ID for the missed tag, when the find_and_mark_missed_avi_reads
     method is executed.

    An csv file can be used to create the lookup dictionary, or it can
    be created automatically.
    """
    _df: pd.DataFrame = None
    _plate_tag_dict: dict = {}  # plate (tag, reads, [trx_ids])
    _plate_tag_filename: str = ''
    _pickle_filename: str = 'plate_tag.pkl'
    _required_dataframe_fields: tuple = ('TAG_ID', 'PLATE', 'TRX_ID')
    _static_dict: bool = False
    _read_threshold: int = 0
    _exact_plates: bool = True
    _error_indices: set = set([])
    _export_dict: bool = True

    def plate_tag_dict_to_csv(self):
        """
        Export tag dictionary as a csv file
        """
        out = pd.DataFrame(self._plate_tag_dict)
        out.T.to_csv('Plate_Tag_Dictionary.csv')

    def find_and_mark_missed_avi_reads(self):
        """
        Method to find and mark missed avi reads. Exporting the
        tag dictionary is an optional parameter.
        """
        self.__find_missed_avi_reads()
        self.__mark_missed_avi_reads()
        self.__export_tag_dict()

    def set_export_dict(self, value: bool):
        """
        Set whether dictionary is exported to a pickle file after
        completing analysis.
        :param value: bool value
        """
        self._export_dict = value

    def __export_tag_dict(self):
        """
        Export tag dictionary to pickle file
        """
        if self._export_dict:
            self.__save_pickle()

    def __find_missed_avi_reads(self):
        """
        Method to find instances where plate is read without tag. Constrained
        by threshold value and whether to use a static or dynamic dictionary.
        """
        plates = self._df['PLATE'].tolist()
        tags = self._df['TAG_ID'].tolist()
        error_index = set([])

        for c, i in enumerate(plates):
            # if plate value blank continue
            if isinstance(i, str) and i == '':
                continue

            plate_combinations = []
            if not self._exact_plates:
                combos = PlateCombinatorics(i)
                plate_combinations = combos.get_plate_combinations()
            else:
                plate_combinations.append(i)

            for j in plate_combinations:
                # plate and tag not in dict, dictionary NOT static
                # add plate tag to dictionary
                if j not in self._plate_tag_dict:
                    if self._static_dict:
                        continue
                    self._plate_tag_dict[j] = [float(tags[c]), 0]
                # plate and tag match
                elif self._plate_tag_dict[j][0] == tags[c]:
                    self._plate_tag_dict[j][1] += 1
                # plate match, tag DOES NOT match
                elif self._plate_tag_dict[j] != tags[c]:
                    if self._plate_tag_dict[j][1] >= self._read_threshold:
                        error_index.add(c)
        self._error_indices = error_index

    def __mark_missed_avi_reads(self):
        """
        Method to add pd.Series to input DataFrame marking instances
        where plate/tag mismatches found. Adds AVI_MISMATCH (True/False)
        and the missed tag as MISSED_TAG_ID.
        """
        avi_missed: list = []
        n = self._df.shape[0]
        for i in range(n):
            if i in self._error_indices:
                avi_missed.append(True)
            else:
                avi_missed.append(False)

        self._df['AVI_MISMATCH'] = pd.Series(avi_missed)

        plates = self._df['PLATE'].tolist()
        missed_tag_value: list = []
        for c, i in enumerate(plates):
            if c in self._error_indices:
                missed_tag_value.append(self._plate_tag_dict[i][0])
            else:
                missed_tag_value.append('')

        self._df['MISSED_TAG_ID'] = pd.Series(missed_tag_value)

    def __load_pickle(self):
        """
        Read pickle file from working directory
        """
        with open(self._plate_tag_filename, 'rb') as f:
            self._plate_tag_dict = pickle.load(f)

    def __save_pickle(self):
        """
        Save pickle file to working directory
        """
        with open(self._pickle_filename, 'wb') as f:
            pickle.dump(self._plate_tag_dict, f, pickle.HIGHEST_PROTOCOL)

    def set_csv_plate_tag(self, filename: str):
        """
        CSV file should have a header row and the follow the format:
        PLATE, TAG, READS. The READS field record the number of times
        the plate/tag combination was recorded. This value is used to
        determine whether it meets the threshold for flagging an error.
        :param filename: filename of csv
        """
        with open(filename) as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if 'PLATE' in row:
                    continue
                else:
                    self._plate_tag_dict[row[0]] = [float(row[1]), int(row[2])]

    def __validate_dataframe(self, dataframe: pd.DataFrame):
        """
        Method to validate whether dataframe contains the required fields
        used in this class.
        :param dataframe: input datframe
        """
        if dataframe is None:
            return
        columns = dataframe.columns
        for i in self._required_dataframe_fields:
            if i not in columns:
                raise ValueError('Missing field: ' + str(i))
        self._df = dataframe

    def set_dataframe(self, dataframe: pd.DataFrame):
        """
        Set dataframe
        :param dataframe: input dataframe
        """
        self.__validate_dataframe(dataframe)

    def get_dataframe(self) -> pd.DataFrame:
        """
        :return: pd.DataFrame
        """
        return self._df

    def set_read_threshold(self, value: int):
        """
        Set the read threshold for the number of times a plate/tag
        has to be recorded before errors are recorded. Must be greater
        than 1.
        :param value:
        """
        if value < 1:
            raise ValueError('Cannot use value less than 1')
        self._read_threshold = value

    def get_read_threshold(self) -> int:
        """
        :return: read threshold
        """
        return self._read_threshold

    def set_static_dict(self, value: bool):
        """
        Set to control whether dictionary is used when file(s) are processed.
        :param value: bool
        """
        self._static_dict = value

    def __init__(self, filename: str = '', dataframe: pd.DataFrame = None,
                 static_dict: bool = False, read_threshold: int = 5,
                 exact_plates: bool = True, export_dict: bool = True):
        """
        :param filename: filename for plate/tag dictionary. Can use a
        pickle or csv file
        :param dataframe: dataframe for analysis
        :param static_dict: bool. Default False. Use a
        dynamic or static dictionary file for analysis
        :param read_threshold: Default 5. Constrains the number of
        plate/tag reads required before an error is recorded.
        :param exact_plates: Default True. Whether to build dictionary and run
        search using exact plate values, or whether to use
        combinatorics based on common OCR character errors.
        :param export_dict: bool. Default True. Export dictionary to pkl
        file
        """
        self._plate_tag_filename = filename
        self._static_dict = static_dict
        self._read_threshold = read_threshold
        self._exact_plates = exact_plates
        self._export_dict = export_dict
        self.__validate_dataframe(dataframe)

        if 'pkl' in self._plate_tag_filename:
            self.__load_pickle()
        elif 'csv' in filename:
            self.set_csv_plate_tag(filename)


class RateAssign520:
    """
    Class to assign rates to fixed time-of-day toll facilities.

    Rate tables used for rate assignment
    rate1 weekday rate for 2 axle vehicle
    rate2 weekday rate for 3 axle vehicle
    rate3 weekday rate for 4 axle vehicle
    """
    holidays: list = []
    pbm: bool = False
    pbm_status: bool = False
    base_rate: float = 0.0
    final_rate: float = 0.0
    trx_type: str = ''
    non_valid_tag_status: list = ['', 'I', 'L', 'S', 'U']
    pbm_percent: float = 0.60  # estimate based on previous reports

    rate1 = {0: 1.25, 1: 1.25, 2: 1.25, 3: 1.25, 4: 1.25, 5: 2.00,
             6: 3.4, 7: 4.30, 8: 4.30, 9: 3.4, 10: 2.7, 11: 2.7, 12: 2.7,
             13: 2.7, 14: 3.4, 15: 4.3, 16: 4.3, 17: 4.3, 18: 3.4,
             19: 2.7, 20: 2.7, 21: 2, 22: 2, 23: 1.25
             }

    rate2 = {0: 1.90, 1: 1.90, 2: 1.90, 3: 1.90, 4: 1.90, 5: 3.00,
             6: 5.1, 7: 6.45, 8: 6.45, 9: 5.1, 10: 4.05, 11: 4.05, 12: 4.05,
             13: 4.05, 14: 5.1, 15: 6.45, 16: 6.45, 17: 6.45, 18: 5.1,
             19: 4.05, 20: 4.05, 21: 3, 22: 3, 23: 1.90
             }

    rate3 = {0: 2.50, 1: 2.50, 2: 2.50, 3: 2.50, 4: 2.50, 5: 4.00,
             6: 6.80, 7: 8.60, 8: 8.60, 9: 6.8, 10: 5.40, 11: 5.40, 12: 5.40,
             13: 5.40, 14: 6.8, 15: 8.60, 16: 8.60, 17: 8.60, 18: 6.8,
             19: 5.40, 20: 5.40, 21: 4, 22: 4, 23: 2.50
             }

    rate4 = {0: 3.15, 1: 3.15, 2: 3.15, 3: 3.15, 4: 3.15, 5: 5,
             6: 8.5, 7: 10.75, 8: 10.75, 9: 8.5, 10: 6.75, 11: 6.75, 12: 6.75,
             13: 6.75, 14: 8.5, 15: 10.75, 16: 10.75, 17: 10.75, 18: 8.5,
             19: 6.75, 20: 6.75, 21: 5, 22: 5, 23: 3.15
             }

    rate5 = {0: 3.75, 1: 3.75, 2: 3.75, 3: 3.75, 4: 3.75, 5: 6,
             6: 10.2, 7: 12.9, 8: 12.9, 9: 10.2, 10: 8.1, 11: 8.1, 12: 8.1,
             13: 8.1, 14: 10.2, 15: 12.9, 16: 12.9, 17: 12.9, 18: 10.2,
             19: 8.1, 20: 8.1, 21: 6, 22: 6, 23: 3.75
             }

    rate1_wknd = {0: 1.25, 1: 1.25, 2: 1.25, 3: 1.25, 4: 1.25,
                  5: 1.40, 6: 1.40, 7: 1.40,
                  8: 2.05, 9: 2.05, 10: 2.05,
                  11: 2.65, 12: 2.65, 13: 2.65, 14: 2.65, 15: 2.65, 16: 2.65, 17: 2.65,
                  18: 2.05, 19: 2.05, 20: 2.05,
                  21: 1.40, 22: 1.40,
                  23: 1.25
                  }

    rate2_wknd = {0: 1.90, 1: 1.90, 2: 1.90, 3: 1.90, 4: 1.90,
                  5: 2.10, 6: 2.10, 7: 2.10,
                  8: 3.10, 9: 3.10, 10: 3.10,
                  11: 4.00, 12: 4.00, 13: 4.00, 14: 4.00, 15: 4.00, 16: 4.00, 17: 4.00,
                  18: 3.10, 19: 3.10, 20: 3.10,
                  21: 2.10, 22: 2.10,
                  23: 1.90
                  }

    rate3_wknd = {0: 2.50, 1: 2.50, 2: 2.50, 3: 2.50, 4: 2.50,
                  5: 2.80, 6: 2.80, 7: 2.80,
                  8: 4.10, 9: 4.10, 10: 4.10,
                  11: 5.30, 12: 5.30, 13: 5.30, 14: 5.30, 15: 5.30, 16: 5.30, 17: 5.30,
                  18: 4.10, 19: 4.10, 20: 4.10,
                  21: 2.80, 22: 2.80,
                  23: 2.50
                  }

    rate4_wknd = {0: 3.15, 1: 3.15, 2: 3.15, 3: 3.15, 4: 3.15,
                  5: 3.50, 6: 3.50, 7: 3.50,
                  8: 5.15, 9: 5.15, 10: 5.15,
                  11: 6.65, 12: 6.65, 13: 6.65, 14: 6.65, 15: 6.65, 16: 6.65, 17: 6.65,
                  18: 5.15, 19: 5.15, 20: 5.15,
                  21: 3.50, 22: 3.50,
                  23: 3.15
                  }

    rate5_wknd = {0: 3.75, 1: 3.75, 2: 3.75, 3: 3.75, 4: 3.75,
                  5: 4.20, 6: 4.20, 7: 4.20,
                  8: 6.15, 9: 6.15, 10: 6.15,
                  11: 7.95, 12: 7.95, 13: 7.95, 14: 7.95, 15: 7.95, 16: 7.95, 17: 7.95,
                  18: 6.15, 19: 6.15, 20: 6.15,
                  21: 4.20, 22: 4.20,
                  23: 3.75
                  }

    # {axles:rate}. if axles > 6, use 6
    rate_dict = {2: rate1, 3: rate2, 4: rate3, 5: rate4, 6: rate5}
    rate_dict_wknd = {2: rate1_wknd, 3: rate2_wknd, 4: rate3_wknd, 5: rate4_wknd, 6: rate5_wknd}

    def __init__(self, datetime_value: datetime, trx_type: str,
                 axles: int, status: str, pbm: bool = False,
                 holidays: list = None):
        """
        :param datetime_value: datetime value to assign rate
        :param trx_type: str, transaction type
        :param axles: int, number of axles
        :param status: str, status of transponder
        :param pbm: bool, pay-by-mail
        :param holidays: list, holidays
        """
        self.trx_type = trx_type
        self.set_holidays(holidays)
        self.pbm = pbm
        self.__calculate_base_rate(datetime_value, axles)
        self.__tag_status_adjustment(status)
        self.__pbm_adjustment(self.base_rate, axles)

    def __pbm_adjustment(self, base_rate, axles):
        """
        :param base_rate: float, base rate
        :param axles: int, number of axles
        """
        rand_float = random.random()
        pbm_dict = {3: 3, 4: 4, 5: 5, 6: 6}
        if self.trx_type != 'IMG':
            self.final_rate = base_rate
        elif rand_float < self.pbm_percent and self.pbm is True:
            self.final_rate = base_rate + .25
            self.pbm_status = True
        elif 2 < axles < 6:
            self.final_rate = base_rate + pbm_dict[axles]
        elif axles > 6:
            self.final_rate = base_rate + 6
        else:
            self.final_rate = base_rate + 2

    def get_final_rate(self):
        """
        :return: float, final rate
        """
        return self.final_rate

    def get_base_rate(self):
        """
        :return: float, base rate
        """
        return self.base_rate

    def __tag_status_adjustment(self, status: str):
        """
        If tag is not a valid status, set rate based on an
        image transaction
        :param status: str, status
        """
        if status in self.non_valid_tag_status:
            self.trx_type = 'IMG'

    def __calculate_base_rate(self, date_value: datetime, axles: int):
        """
        Calculate base rate using datetime and axle information
        :param date_value: datetime
        :param axles: int, axle count
        """
        hour = self.floor_hour(date_value)
        axles = self.set_axles(axles)
        rate_table = self.__set_rate_table(date_value)[axles]
        rate = rate_table[hour]

        self.base_rate = rate

    def set_holidays(self, holidays):
        """
        Set holidays as list of datetime values
        :param holidays: list
        """
        if holidays is None:
            holidays = []
        elif len(holidays) == 0:
            return
        elif not isinstance(holidays, list):
            raise TypeError('Holidays must be a list type')

        for i in holidays:
            if not isinstance(i, datetime.date):
                raise TypeError('Element is not datetime.date object: ' + str(i))

        self.holidays = holidays

    def __set_rate_table(self, datetime_value: datetime) -> dict:
        """
        Set rate tables to be used for base rate assignment
        :param datetime_value:
        :return: rate table dict to use
        """
        if datetime_value.date() in self.holidays:
            return self.rate_dict_wknd
        elif datetime_value.weekday() > 4:
            return self.rate_dict_wknd
        else:
            return self.rate_dict

    @staticmethod
    def floor_hour(datetime_value: datetime) -> int:
        """
        :param datetime_value: datetime value
        :return: int, value between 0 and 23 for floor of hour
        """
        if not isinstance(datetime_value, datetime.datetime):
            raise TypeError('Input is not datetime: ' + str(datetime_value))

        td_value = datetime.timedelta(
            minutes=datetime_value.minute,
            seconds=datetime_value.second,
            microseconds=datetime_value.microsecond)
        return (datetime_value - td_value).hour

    @staticmethod
    def set_axles(axles):
        """
        Constrains the number of axles based on rate assignment parameters.
        If less than 2 set to 2, if more than 6 set to 6.
        :param axles: int, input number of axles
        :return: int, axle count
        """
        axles = int(axles)
        if not isinstance(axles, int):
            raise TypeError('Axle input is not int: ' + str(axles))
        if axles < 2:
            return 2
        elif axles > 6:
            return 6
        else:
            return axles


class RateAssign99(RateAssign520):
    rate1 = {0: 1.00, 1: 1.00, 2: 1.00, 3: 1.00, 4: 1.00, 5: 1.00,
             6: 1.25, 7: 1.50, 8: 1.50, 9: 1.25, 10: 1.25, 11: 1.25,
             12: 1.25, 13: 1.25, 14: 1.25, 15: 2.25, 16: 2.25, 17: 2.25,
             18: 1.25, 19: 1.25, 20: 1.25, 21: 1.25, 22: 1.25, 23: 1.00
             }

    rate2 = {0: 1.50, 1: 1.50, 2: 1.50, 3: 1.50, 4: 1.50, 5: 1.50,
             6: 1.90, 7: 2.25, 8: 2.25, 9: 1.90, 10: 1.90, 11: 1.90,
             12: 1.90, 13: 1.90, 14: 1.90, 15: 3.40, 16: 3.40, 17: 3.40,
             18: 1.90, 19: 1.90, 20: 1.90, 21: 1.90, 22: 1.90, 23: 1.50
             }

    rate3 = {0: 2.00, 1: 2.00, 2: 2.00, 3: 2.00, 4: 2.00, 5: 2.00,
             6: 2.50, 7: 3.00, 8: 3.00, 9: 2.50, 10: 2.50, 11: 2.50,
             12: 2.50, 13: 2.50, 14: 2.50, 15: 4.50, 16: 4.50, 17: 4.50,
             18: 2.50, 19: 2.50, 20: 2.50, 21: 2.50, 22: 2.50, 23: 2.00
             }

    rate4 = {0: 2.50, 1: 2.50, 2: 2.50, 3: 2.50, 4: 2.50, 5: 2.50,
             6: 3.15, 7: 3.75, 8: 3.75, 9: 3.15, 10: 3.15, 11: 3.15,
             12: 3.15, 13: 3.15, 14: 3.15, 15: 5.65, 16: 5.65, 17: 5.65,
             18: 3.15, 19: 3.15, 20: 3.15, 21: 3.15, 22: 3.15, 23: 2.50
             }

    rate5 = {0: 3.00, 1: 3.00, 2: 3.00, 3: 3.00, 4: 3.00, 5: 3.00,
             6: 3.75, 7: 4.50, 8: 4.50, 9: 3.75, 10: 3.75, 11: 3.75,
             12: 3.75, 13: 3.75, 14: 3.75, 15: 6.75, 16: 6.75, 17: 6.75,
             18: 3.75, 19: 3.75, 20: 3.75, 21: 3.75, 22: 3.75, 23: 3.00
             }

    rate1_wknd = {0: 1.00, 1: 1.00, 2: 1.00, 3: 1.00, 4: 1.00,
                  5: 1.00, 6: 1.00, 7: 1.00, 8: 1.00, 9: 1.00, 10: 1.00,
                  11: 1.00, 12: 1.00, 13: 1.00, 14: 1.00, 15: 1.00,
                  16: 1.00, 17: 1.00, 18: 1.00, 19: 1.00, 20: 1.00,
                  21: 1.00, 22: 1.00, 23: 1.00
                  }

    rate2_wknd = {0: 1.50, 1: 1.50, 2: 1.50, 3: 1.50, 4: 1.50,
                  5: 1.50, 6: 1.50, 7: 1.50, 8: 1.50, 9: 1.50, 10: 1.50,
                  11: 1.50, 12: 1.50, 13: 1.50, 14: 1.50, 15: 1.50,
                  16: 1.50, 17: 1.50, 18: 1.50, 19: 1.50, 20: 1.50,
                  21: 1.50, 22: 1.50, 23: 1.50
                  }

    rate3_wknd = {0: 2.00, 1: 2.00, 2: 2.00, 3: 2.00, 4: 2.00,
                  5: 2.00, 6: 2.00, 7: 2.00, 8: 2.00, 9: 2.00, 10: 2.00,
                  11: 2.00, 12: 2.00, 13: 2.00, 14: 2.00, 15: 2.00,
                  16: 2.00, 17: 2.00, 18: 2.00, 19: 2.00, 20: 2.00,
                  21: 2.00, 22: 2.00, 23: 2.00
                  }

    rate4_wknd = {0: 2.50, 1: 2.50, 2: 2.50, 3: 2.50, 4: 2.50,
                  5: 2.50, 6: 2.50, 7: 2.50, 8: 2.50, 9: 2.50, 10: 2.50,
                  11: 2.50, 12: 2.50, 13: 2.50, 14: 2.50, 15: 2.50,
                  16: 2.50, 17: 2.50, 18: 2.50, 19: 2.50, 20: 2.50,
                  21: 2.50, 22: 2.50, 23: 2.50
                  }

    rate5_wknd = {0: 3.00, 1: 3.00, 2: 3.00, 3: 3.00, 4: 3.00,
                  5: 3.00, 6: 3.00, 7: 3.00, 8: 3.00, 9: 3.00, 10: 3.00,
                  11: 3.00, 12: 3.00, 13: 3.00, 14: 3.00, 15: 3.00,
                  16: 3.00, 17: 3.00, 18: 3.00, 19: 3.00, 20: 3.00,
                  21: 3.00, 22: 3.00, 23: 3.00
                  }

    rate_dict = {2: rate1, 3: rate2, 4: rate3, 5: rate4, 6: rate5}
    rate_dict_wknd = {2: rate1_wknd, 3: rate2_wknd, 4: rate3_wknd, 5: rate4_wknd, 6: rate5_wknd}

    def __set_rate_table(self, datetime_value: datetime):
        """
        :return: dict, rate dictionary
        """
        if datetime_value.date() in self.holidays:
            return self.rate_dict_wknd
        elif datetime_value.weekday() > 4:
            return self.rate_dict_wknd
        else:
            return self.rate_dict

    def __init__(self, datetime_value: datetime, trx_type: str,
                 axles: int, status: str, pbm: bool = False,
                 holidays: list = None):
        """
        :param datetime_value: datetime.datetime
        :param trx_type: str, transaction type
        :param axles: int, axle count
        :param status: str, status
        self.assertEqual(hour, 9)
        :param pbm: bool, pay-by-mail status
        :param holidays: list datetime.datetime, list of holiday dates
        """
        super().__init__(datetime_value, trx_type, axles, status, pbm, holidays)
        self.trx_type = trx_type
        self.set_holidays(holidays)
        self.pbm = pbm
        self.__calculate_base_rate(datetime_value, axles)
        self.__tag_status_adjustment(status)
        self.__pbm_adjustment(self.base_rate, axles)


if __name__ == '__main__':
    print('Test is the toll data module')