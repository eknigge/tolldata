import sys
import os
sys.path.append(os.getcwd() + '\\tolldata')

from unittest import TestCase
import pandas as pd
import numpy as np
import random
import datetime

# PyCharm Tests, uncomment to run
# from tolldata import TripBuilder as tb

# Pytest, uncomment to run
import TripBuilder as tb

class TestTripBuilder(TestCase):
    test_data_filename = os.getcwd() + '\\Tests\\trip_build_test_data.csv'

    def test_get_related_trips_1(self):
        expected_transactions = {1, 2, 3, 4, 5, 6, 7}
        df = self.get_test_dataframe()
        sample_transaction_id = 1
        trip_build = tb.TripBuilder(df)
        df_result = trip_build._get_related_trips(sample_transaction_id)
        result_transactions = set(df_result['TRANSACTION_ID'].tolist())
        self.assertEqual(expected_transactions, result_transactions)

    def test_get_related_trips_2(self):
        expected_transactions = {8, 9, 10, 11, 12, 13}
        df = self.get_test_dataframe()
        sample_transaction_id = 10
        trip_build = tb.TripBuilder(df)
        df_result = trip_build._get_related_trips(sample_transaction_id)
        result_transactions = set(df_result['TRANSACTION_ID'].tolist())
        self.assertEqual(expected_transactions, result_transactions)

    def test_get_related_trips_3(self):
        expected_transactions = {46, 47, 48, 49, 50, 51, 52}
        df = self.get_test_dataframe()
        sample_transaction_id = 49
        trip_build = tb.TripBuilder(df)
        df_result = trip_build._get_related_trips(sample_transaction_id)
        result_transactions = set(df_result['TRANSACTION_ID'].tolist())
        self.assertEqual(expected_transactions, result_transactions)

    def test_time_delta_calculation(self):
        random_int_list = [random.randint(1, 60) for i in range(10)]
        start_time = datetime.datetime.now()
        time_list = [start_time]

        for c, i in enumerate(random_int_list):
            time_list.append(time_list[c] + datetime.timedelta(seconds=i))
        df = self.get_test_dataframe().iloc[0:11]
        df['DATETIME'] = pd.Series(time_list)
        build = tb.TripBuilder(df)
        df_result = build._calculate_time_deltas(df)
        result = df_result['TIME_DELTA'].dt.seconds.tolist()

        expected_time_delta = [0] + random_int_list

        self.assertEqual(result, expected_time_delta)

    def test_directional_change(self):
        df = self.get_test_dataframe().iloc[38:42]
        df = df.reset_index()
        expected_result = [False, False, True, False]
        build = tb.TripBuilder(df)
        df_result = build._calculate_directional_changes(df)
        result = df_result['DIR_CHANGE'].tolist()

        self.assertEqual(expected_result, result)

    def test_break_point_exit_node(self):
        expected_result = [False, False, True, False]
        exit_nodes = ['SB06']
        df = self.get_test_dataframe().iloc[24:28]
        df = df.reset_index()
        build = tb.TripBuilder(df, exit_nodes=exit_nodes)
        df = build._calculate_time_deltas(df)
        df = build._calculate_directional_changes(df)
        df = build._calculate_trip_breaks(df)
        result = df['BREAK_TRIP'].tolist()

        self.assertEqual(expected_result, result)

    def test_break_point_timeout(self):
        expected_result = [False, False, True, False]
        exit_nodes = ['SB06']
        df = self.get_test_dataframe().iloc[34:38]
        df = df.reset_index()
        build = tb.TripBuilder(df, exit_nodes=exit_nodes)
        df = build._calculate_time_deltas(df)
        df = build._calculate_directional_changes(df)
        df = build._calculate_trip_breaks(df)
        result = df['BREAK_TRIP'].tolist()

        self.assertEqual(expected_result, result)

    def test_break_point_timeout_trip_id_check(self):
        expected_result = [0, 0, 1, 1]
        exit_nodes = ['SB06']
        df = self.get_test_dataframe().iloc[34:38]
        df = df.reset_index()
        build = tb.TripBuilder(df, exit_nodes=exit_nodes)
        df = build._calculate_time_deltas(df)
        df = build._calculate_directional_changes(df)
        df = build._calculate_trip_breaks(df)
        df = build._assign_trip_id(df)
        result = df['TRIP_ID_BUILD'].tolist()

        self.assertEqual(expected_result, result)

    def test_drop_transactions(self):
        df_full_size = self.get_test_dataframe()
        df_sample = self.get_test_dataframe().iloc[7:11]
        expected_result = df_full_size.shape[0] - df_sample.shape[0]
        build = tb.TripBuilder(df_full_size)
        df_filtered = build._remove_built_transactions(df_full_size, df_sample)
        result = df_filtered.shape[0]

        # Validate size
        self.assertEqual(expected_result, result)

        # Validate elements removed
        removed_transactions = df_sample['TRANSACTION_ID'].tolist()
        remaining_transactions = df_filtered['TRANSACTION_ID'].tolist()

        for item in removed_transactions:
            self.assertTrue(item not in remaining_transactions)

    def test_build_all_trips(self):
        df = self.get_test_dataframe()
        expected_trip_ids = df['TRIP_ID'].tolist()
        exit_nodes = ['NB10', 'NB05', 'SB06', 'SB10', 'SB11']
        build = tb.TripBuilder(df, exit_nodes=exit_nodes)
        build.build_trips()
        df_output = build.get_dataframe()
        build_trip_ids = df_output['TRIP_ID_BUILD'].tolist()

        self.assertEqual(expected_trip_ids, build_trip_ids)

    def get_test_dataframe(self):
        df = pd.read_csv(self.test_data_filename)
        df['DATETIME'] = pd.to_datetime(df['DATETIME'])
        df['TRANSPONDER_ID'] = df['TRANSPONDER_ID'].replace(0, np.nan)
        return df
