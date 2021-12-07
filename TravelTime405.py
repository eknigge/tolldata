import pandas as pd
import logging
import TollData as td
from tqdm import tqdm
import datetime


class TravelTime405:
    df_travel_time = None
    FREE_FLOW_SPEED = 3600 / 65  # miles / second
    data_date = None
    fields = {'datetime_field': 'DATETIME', 'plaza_field': 'Plaza', 'trip_field': 'Trip ID'}
    toll_location_feet = \
        {"NB01": 389809, "NB02": 389809, "NB03": 405301, "NB04": 421240, "NB05": 425175,
         "NB06": 426828, "NB07": 433800, "NB08": 453800, "NB09": 465100, "NB10": 471090,
         "SB01": 468200, "SB02": 459870, "SB03": 451800, "SB04": 433770, "SB05": 428820,
         "SB06": 426798, "SB07": 425145, "SB08": 410272, "SB09": 399420, "SB10": 389779,
         "SB11": 389779
         }

    def __init__(self, df: pd.DataFrame, datetime_field=None, plaza_field=None,
                 trip_field=None):
        if datetime_field is not None:
            self.set_field('datetime_field', datetime_field)
        if plaza_field is not None:
            self.set_field('plaza_field', plaza_field)
        if trip_field is not None:
            self.set_field('trip_field', trip_field)
        pairs = self.calculate_travel_pairs(df)
        avg_pairs = self.average_travel_times(pairs)
        df_travel_time = self.create_summary_dataframe(avg_pairs)
        self.df_travel_time = self.interpolate_missing_travel_times(df_travel_time)

    def get_travel_time(self, start_time: datetime.time, trip_definition: list):
        start_time = datetime.datetime(self.data_date.year, self.data_date.month,
                                       self.data_date.day, hour=start_time.hour,
                                       minute=start_time.minute, second=start_time.second,
                                       microsecond=start_time.microsecond)
        start_time_min = datetime.datetime(self.data_date.year, self.data_date.month,
                                           self.data_date.day, hour=start_time.hour,
                                           minute=start_time.minute)
        total_time = 0.0
        prev_node = trip_definition[0]
        n = len(trip_definition)

        for i in range(1, n):
            node = trip_definition[i]
            pair = prev_node + '-' + node
            pair_series = self.df_travel_time[pair]
            pair_travel_time = pair_series.get(start_time_min)
            total_time += pair_travel_time

            # Reset counters
            prev_node = node
            start_time = datetime.timedelta(seconds=pair_travel_time) + start_time
            start_time_min = datetime.datetime(self.data_date.year, self.data_date.month,
                                               self.data_date.day, hour=start_time.hour,
                                               minute=start_time.minute, second=start_time.second)
            start_time_min = TravelTimeUtil.round_minutes(TravelTimeUtil.round_seconds(start_time_min))
        return total_time


    def interpolate_missing_travel_times(self, input_df: pd.DataFrame) -> pd.DataFrame:
        columns = input_df.columns
        for column in columns:
            series = input_df[column]
            input_df[column] = self.add_travel_time_boundary_conditions(series)
        return input_df

    def compute_pair_distance_miles(self, value: str) -> float:
        start = value.split('-')[0]
        end = value.split('-')[1]
        return abs((self.toll_location_feet[end] - self.toll_location_feet[start]) / 5820)

    def add_travel_time_boundary_conditions(self, input_series: pd.Series) -> pd.Series:
        pair = input_series.name
        pair_distance = self.compute_pair_distance_miles(pair)

        # Update first and last elements with free flow condition
        free_flow_travel_time = datetime.timedelta(seconds=pair_distance * self.FREE_FLOW_SPEED)
        input_series.iloc[0] = free_flow_travel_time
        last_element = input_series.shape[0] - 1
        input_series.iloc[last_element] = free_flow_travel_time

        # Interpolate missing values
        input_series = input_series.dt.seconds
        input_series = input_series.interpolate()

        return input_series

    def create_summary_dataframe(self, avg_pairs: dict) -> pd.DataFrame:
        series_list = []
        first_pair = list(avg_pairs.keys())[0]
        data_date = list(avg_pairs[first_pair].keys())[0]
        self.data_date = data_date
        start_time = datetime.datetime(data_date.year, data_date.month, data_date.day)
        end_time = datetime.datetime(data_date.year, data_date.month, data_date.day,
                                     hour=23, minute=59)
        date_index = pd.date_range(start=start_time, end=end_time, freq='min')
        df_out = pd.DataFrame(index=date_index)

        for pair in avg_pairs:
            self.check_single_date(list(avg_pairs[pair].keys()))
            new_series = pd.Series(avg_pairs[pair])
            df_out[pair] = new_series
        return df_out

    @staticmethod
    def check_single_date(datetime_value_list: list):
        if not isinstance(datetime_value_list, list):
            raise TypeError(str(type(datetime_value_list)) +
                            ' is not a \'list\' type')
        base_date = datetime_value_list[0].date()
        for datetime_value in datetime_value_list:
            if datetime_value.date() != base_date:
                raise ValueError('Input files contains multiple dates')

    @staticmethod
    def average_travel_times(input_dict: dict) -> dict:
        output = {}
        for pair in tqdm(input_dict):
            for time in input_dict[pair]:
                avg_time = TravelTimeUtil.average_list(input_dict[pair][time])
                if pair not in output:
                    output.update({pair: {time: avg_time}})
                elif pair in output:
                    output[pair].update({time: avg_time})
        return output

    def set_field(self, field: str, field_value: str):
        if field not in self.df.columns:
            raise ValueError(field_value + 'for field ' + field + ' not found in DataFrame')
        self.fields[field] = field_value

    def calculate_travel_pairs(self, input_df: pd.DataFrame) -> dict:
        unique_trips = input_df[self.fields['trip_field']].drop_duplicates()
        plaza_field = self.fields['plaza_field']
        datetime_field = self.fields['datetime_field']
        output = {}
        for trip in tqdm(unique_trips):
            df_trip = input_df[input_df[self.fields['trip_field']] == trip]
            df_trip = df_trip.sort_values(by=self.fields['datetime_field'])

            df_trip = df_trip.reset_index()
            n = df_trip.shape[0] - 1
            for i in range(n):
                start_time = df_trip.iloc[i][datetime_field]
                start_time_rounded = TravelTimeUtil.round_minutes(TravelTimeUtil.round_seconds(start_time))
                end_time = df_trip.iloc[i + 1][datetime_field]
                start_plaza = str(df_trip.iloc[i][plaza_field])
                end_plaza = str(df_trip.iloc[i + 1][plaza_field])

                pair = start_plaza + '-' + end_plaza
                time_delta = end_time - start_time

                if pair not in output:
                    output.update({pair: {start_time_rounded: []}})
                    output[pair][start_time_rounded].append(time_delta)
                elif pair in output and start_time_rounded not in output[pair]:
                    output[pair].update({start_time_rounded: []})
                    output[pair][start_time_rounded].append(time_delta)
                elif pair in output and start_time_rounded in output[pair]:
                    output[pair][start_time_rounded].append(time_delta)
                else:
                    continue
        return output


class TravelTimeUtil:
    @staticmethod
    def round_minutes(value: datetime.datetime):
        if value.second > 30:
            return value - datetime.timedelta(seconds=value.second) + datetime.timedelta(minutes=1)
        else:
            return value - datetime.timedelta(seconds=value.second) - datetime.timedelta(minutes=1)

    @staticmethod
    def round_seconds(value: datetime.datetime):
        value_microseconds = datetime.timedelta(microseconds=value.microsecond)
        if value.microsecond > 5E5:
            return value - value_microseconds + datetime.timedelta(seconds=1)
        else:
            return value - value_microseconds

    @staticmethod
    def average_list(values: list):
        n = len(values)
        value_sum = datetime.timedelta(seconds=0)
        for value in values:
            value_sum += value
        return value_sum / n


if __name__ == '__main__':
    # test_file = '_hashed_export_test_data_trip.csv'
    test_file = 'full_file_test.csv'
    df = pd.read_csv(test_file)
    datetime_format = '%m/%d/%Y %H.%M.%S.%f'
    df['DATETIME'] = pd.to_datetime(df['Trans Time'], format=datetime_format)
    sample_travel_time = TravelTime405(df)
    trip_def = ['SB01', 'SB02', 'SB03', 'SB04', 'SB08', 'SB09', 'SB10']
    travel_time_list = []

    start_time = datetime.datetime(2021, 1, 1, hour=6, minute=10)
    start_time_list = []

    for i in range(25):
        travel_time = sample_travel_time.get_travel_time(start_time, trip_def)
        travel_time_list.append(travel_time)
        start_time = start_time + datetime.timedelta(minutes=5)
    print(travel_time_list)
