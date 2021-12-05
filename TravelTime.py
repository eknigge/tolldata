import pandas as pd
import logging
import TollData as td
from tqdm import tqdm
import datetime


class TravelTime:
    df = None
    fields = {'datetime_field': 'DATETIME', 'plaza_field': 'Plaza', 'trip_field': 'Trip ID'}

    def __init__(self, df: pd.DataFrame, datetime_field=None, plaza_field=None,
                 trip_field=None):
        self.df = df
        if datetime_field is not None:
            self.set_field('datetime_field', datetime_field)
        if plaza_field is not None:
            self.set_field('plaza_field', plaza_field)
        if trip_field is not None:
            self.set_field('trip_field', trip_field)
        pairs = self.calculate_travel_pairs()
        avg_pairs = self.average_travel_times(pairs)
        temp_df = self.create_summary_dataframe(avg_pairs)
        temp_df.to_csv('temp.csv')

    def create_summary_dataframe(self, avg_pairs: dict) -> pd.DataFrame:
        series_list = []
        first_pair = list(avg_pairs.keys())[0]
        data_date = list(avg_pairs[first_pair].keys())[0]
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

    def calculate_travel_pairs(self) -> dict:
        df_temp = self.df
        unique_trips = df_temp[self.fields['trip_field']].drop_duplicates()
        plaza_field = self.fields['plaza_field']
        datetime_field = self.fields['datetime_field']
        output = {}
        for trip in tqdm(unique_trips):
            df_trip = df_temp[df_temp[self.fields['trip_field']] == trip]
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
    test_file = '_hashed_export_test_data_trip.csv'
    df = pd.read_csv(test_file)
    datetime_format = '%m/%d/%Y %H.%M.%S.%f'
    df['DATETIME'] = pd.to_datetime(df['Trans Time'], format=datetime_format)
    TravelTime(df)
