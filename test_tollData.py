from unittest import TestCase
import TollData as td
import datetime
import TollData as ra
import pandas as pd


class TestplateCombinatorics(TestCase):
    def test_constructor(self):
        value = 'abc123'
        plate = td.PlateCombinatorics(value)
        self.assertEqual(value, plate.get_plate())

    def test_set_and_get(self):
        value = 'abc123'
        plate = td.PlateCombinatorics()
        plate.set_plate(value)
        self.assertEqual(value, plate.get_plate())

    def test_combination_2_chars(self):
        value = 'BB'
        ans = ['BB', '88', 'B8', '8B']
        combinations = td.PlateCombinatorics(value).get_plate_combinations()
        for i in ans:
            self.assertEqual(True, i in combinations)

    def test_combination_3_chars(self):
        value = 'BBB'
        ans = ['BBB', '8BB', '88B', '888', 'B8B', 'BB8', 'B88', '8B8']
        combinations = td.PlateCombinatorics(value).get_plate_combinations()
        for i in ans:
            self.assertEqual(True, i in combinations)


class TestRateAssign520(TestCase):
    _holiday_list = [datetime.date(2020, 7, 3),
                     datetime.date(2020, 9, 7),
                     datetime.date(2020, 1, 1)]

    def test_morning_valid_avi_2axle(self):
        time = datetime.datetime(2020, 10, 5, hour=8, minute=35, second=10)
        trx_type = 'AVI'
        axles = 2
        status = 'V'
        rate = ra.RateAssign520(time, trx_type, axles, status).get_final_rate()
        self.assertEqual(rate, 4.3)

    def test_morning_holiday_valid_avi_2axle(self):
        time = datetime.datetime(2020, 7, 3, hour=9, minute=15, second=8)
        trx_type = 'AVI'
        axles = 2
        status = 'V'
        rate = ra.RateAssign520(time, trx_type, axles, status,
                                holidays=self._holiday_list).get_final_rate()
        self.assertEqual(rate, 2.05)

    def test_morning_holiday_img_3axle(self):
        time = datetime.datetime(2020, 9, 7, hour=9, minute=15, second=8)
        trx_type = 'IMG'
        axles = 3
        status = ''
        rate = ra.RateAssign520(time, trx_type, axles, status,
                                holidays=self._holiday_list).get_final_rate()
        self.assertEqual(rate, 6.10)

    def test_evening_holiday_avi_lost_4axle(self):
        time = datetime.datetime(2020, 1, 1, hour=19, minute=15, second=8)
        trx_type = 'AVI'
        axles = 4
        status = 'L'
        rate = ra.RateAssign520(time, trx_type, axles, status,
                                holidays=self._holiday_list).get_final_rate()
        self.assertEqual(rate, 8.10)

    def test_floor_hour(self):
        time = datetime.datetime(2020, 9, 7, hour=9, minute=15, second=8)
        hour = ra.RateAssign520.floor_hour(time)
        self.assertEqual(hour, 9)


class TestAVIValidation(TestCase):
    _df = pd.DataFrame({'TRX_ID': [8024, 1379, 1435, 3946, 5883, 4208, 5375,
                                   1211, 1212],
                        'TAG_ID': [123, 123, 123, 123, 123, 123, 321, 217, 298],
                        'PLATE': ['ABC', 'ABC', 'ABC', 'ABC', 'ABC', 'ABC', 'ABC',
                                  'DF', 'DF']
                        })

    def test_single_error(self):
        avi_validation = td.AVIValidation(dataframe=self._df, export_dict=False)
        avi_validation.find_and_mark_missed_avi_reads()
        df_errors = avi_validation.get_dataframe()
        df_errors = df_errors[df_errors['AVI_MISMATCH'] == True]
        self.assertEqual(df_errors['TRX_ID'].values[0], 5375)

    def test_below_threshold(self):
        avi_validation = td.AVIValidation(dataframe=self._df, export_dict=False)
        avi_validation.find_and_mark_missed_avi_reads()
        df_errors = avi_validation.get_dataframe()
        df_errors = df_errors[df_errors['PLATE'] != 'ABC']
        df_errors = df_errors[df_errors['AVI_MISMATCH'] == True]
        self.assertEqual(df_errors.empty, True)
