from unittest import TestCase
import TravelTime as tt
import pandas as pd
import datetime


class TestUtil(TestCase):
    TEST_DATETIME = datetime.datetime(2021, 1, 1)

    def test_average_list_function_int(self):
        test_list = [datetime.timedelta(seconds=3),
                     datetime.timedelta(seconds=3),
                     datetime.timedelta(seconds=5),
                     datetime.timedelta(seconds=5)]
        expected_value = datetime.timedelta(seconds=4)
        function_value = tt.TravelTimeUtil.average_timedelta_list(test_list)
        self.assertEqual(expected_value, function_value)

    def test_aver_list_function_float(self):
        test_list = [datetime.timedelta(seconds=1.2),
                     datetime.timedelta(seconds=3.5),
                     datetime.timedelta(seconds=8.4),
                     datetime.timedelta(seconds=3.3)]
        expected_value = datetime.timedelta(seconds=4.1)
        function_value = tt.TravelTimeUtil.average_timedelta_list(test_list)
        self.assertAlmostEqual(expected_value, function_value)

    def test_travel_time_baseline(self):
        """
        Test boundary conditions for travel times. These values set the start and end
        conditions for interpolating missing values.
        """
        travel_time = self.create_test_dataframe()
        free_flow_speed = 3600 / 65 / 5280  # seconds / foot
        default_distance = 1000  # feet
        expect_travel_time = default_distance * free_flow_speed
        non_standard_distance = 2000
        expect_travel_time_non_standard = non_standard_distance * free_flow_speed

        # Standard distance test
        self.assertAlmostEqual(expect_travel_time, travel_time.df_travel_time['NB01-NB03'].iloc[0],
                               places=3)
        self.assertAlmostEqual(expect_travel_time, travel_time.df_travel_time['NB03-NB04'].iloc[0],
                               places=3)
        # Non-standard distance test
        self.assertAlmostEqual(expect_travel_time_non_standard, travel_time.df_travel_time['NB09-NB10'].iloc[0],
                               places=3)

    def test_travel_time_trips(self):
        """
        Test travel time trips defined by the input file.
        """
        travel_time = self.create_test_dataframe()
        nb01_nb03_start_time = datetime.datetime(self.TEST_DATETIME.year,
                                                 self.TEST_DATETIME.month,
                                                 self.TEST_DATETIME.day,
                                                 minute=4)
        trip = ['NB01', 'NB03']
        calculated_travel_time = travel_time.get_travel_time(nb01_nb03_start_time, trip_definition=trip)
        all_day = travel_time.get_travel_time_all_day(trip_definition=trip)

        self.assertAlmostEquals(calculated_travel_time, 60, places=0)

    def create_test_dataframe(self) -> tt.TravelTime:
        # Add datetime data
        time_delta_minute = datetime.timedelta(seconds=60)
        time_delta_20_sec = datetime.timedelta(seconds=20)
        t1 = datetime.datetime(self.TEST_DATETIME.year,
                               self.TEST_DATETIME.month,
                               self.TEST_DATETIME.day,
                               minute=5)
        t2 = t1 + time_delta_minute
        t3 = t2 + time_delta_minute
        t4 = t3 + time_delta_minute
        t5 = t4 + time_delta_minute
        t6 = t5 + time_delta_minute
        t7 = t6 + time_delta_minute
        t8 = t2 + time_delta_20_sec + time_delta_minute
        t9 = t6 + time_delta_20_sec + time_delta_minute

        # Trip Dataframe
        all_data = {'TRIP_ID': [1, 1, 1, 1, 1, 1, 1, 2, 2, 3, 3, 4, 4],
                    'PLAZA': ['NB01', 'NB03', 'NB04', 'NB07', 'NB08', 'NB09', 'NB10',
                              'NB03', 'NB04', 'NB03', 'NB04', 'NB09', 'NB10'],
                    'DATETIME': [t1, t2, t3, t4, t5, t6, t7, t2, t8, t2, t8, t6, t9]
                    }
        df = pd.DataFrame(all_data)

        # Create travel time object
        trip_definition_test = ['NB01', 'NB03', 'NB04', 'NB07', 'NB08',
                                'NB09', 'NB10']
        toll_location_definition = {"NB01": 0, "NB03": 1000, "NB04": 2000,
                                    "NB07": 3000, "NB08": 4000, "NB09": 5000,
                                    "NB10": 7000}
        travel_time = tt.TravelTime(df, plaza_field_name='PLAZA', trip_field_name='TRIP_ID',
                                    toll_locations=toll_location_definition)
        return travel_time
