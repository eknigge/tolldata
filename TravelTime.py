import pandas as pd
import logging
from tqdm import tqdm
import datetime
import numpy as np


class TravelTime:
    df_travel_time = None
    FREE_FLOW_SPEED = 3600 / 65 / 5280  # seconds / foot
    MINUTES_IN_DAY = 60 * 24 - 1
    _data_date = None
    _default_log_level = logging.INFO
    _default_field_names = {'datetime_field': 'DATETIME', 'plaza_field': 'Plaza', 'trip_field': 'Trip ID'}
    _toll_locations_in_feet = {
        'NB01': 389809, 'NB02': 389809, 'NB03': 405301, 'NB04': 421240, 'NB05': 425175,
        'NB06': 426828, 'NB07': 433800, 'NB08': 453800, 'NB09': 465100, 'NB10': 471090
        , 'SB01': 468200, 'SB02': 459870, 'SB03': 451800, 'SB04': 433770, 'SB05': 428820,
        'SB06': 426798, 'SB07': 425145, 'SB08': 410272, 'SB09': 399420, 'SB10': 389779,
        'SB11': 389779
    }

    def __init__(self, df: pd.DataFrame, datetime_field_name=None,
                 plaza_field_name=None, trip_field_name=None, enable_logging=False,
                 default_logging_level=logging.INFO, toll_locations=None):
        """
        Constructor travel time object. Must create before travel times can be calculated.
        :param df: Pandas Dataframe
        :param datetime_field_name: Name of datetime value field of dataframe
        :param plaza_field_name: Name of plaza field, node name, toll point name
        :param trip_field_name: Name of trip field in dataframe
        :param enable_logging: Bool.
        :param default_logging_level: Int. Set logging level, default to INFO
        :param toll_locations: Dict. Name: Location (ft). Used to calculate baseline values
        for free flow traffic, and travel time between toll points.
        """
        self._initialize_logging(enable_logging, default_logging_level)

        # Set constructor args
        constructor_fields = {'datetime_field': datetime_field_name, 'plaza_field': plaza_field_name,
                              'trip_field': trip_field_name}
        self._set_field_names(constructor_fields)
        self._set_toll_locations(toll_locations)

        # Build trips
        pairs = self._calculate_travel_pairs(df)
        avg_pairs = self.average_travel_times(pairs)
        df_travel_time = self._create_summary_dataframe_skeleton(avg_pairs)
        self.df_travel_time = self._interpolate_missing_travel_times(df_travel_time)

    @staticmethod
    def _initialize_logging(value: bool, log_level: int):
        if value:
            logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                datefmt='%m/%d/%Y %H:%M:%S', filename='travel_time_log.log',
                                level=log_level)

    def _set_toll_locations(self, toll_locations: dict):
        if toll_locations is not None:
            self._toll_locations_in_feet = toll_locations

    def _set_field_names(self, field_value_dict: dict):
        logging.debug('Set constructor Field Names: ' + str(field_value_dict))
        for field_name in field_value_dict:
            if field_value_dict[field_name] is not None:
                self._default_field_names[field_name] = field_value_dict[field_name]

    def _add_datetime_within_day(self, datetime_value: datetime.datetime,
                                 timedelta_value: datetime.timedelta) -> datetime.datetime:
        """
        Add datetime and timedelta value. If values falls out of range in the day, return last minute.
        :param datetime_value: datetime.datetime start value
        :param timedelta_value: datetime.timedelta increment value
        :return: datetime.datetime
        """
        result = datetime_value + timedelta_value
        data_date_last_minute_in_day = datetime.datetime(self._data_date.year, self._data_date.month,
                                                         self._data_date.day, hour=23, minute=59)
        if result > data_date_last_minute_in_day:
            return data_date_last_minute_in_day
        else:
            return result

    def get_travel_time_all_day(self, trip_definition: list) -> list:
        logging.info('Get travel times for entire day for trip: ' + str(trip_definition))
        # Start date will be removed, any arbitrary date may be used
        minutes_in_day_list = [datetime.datetime(2021, 1, 1)]
        start_time = minutes_in_day_list[0]
        # Generate list of all minutes in day
        for i in range(self.MINUTES_IN_DAY):
            start_time = start_time + datetime.timedelta(minutes=1)
            minutes_in_day_list.append(start_time)
        # Get travel times and return output
        output = []
        for time in minutes_in_day_list:
            output.append(self.get_travel_time(time, trip_definition))
        return output

    def get_travel_time(self, start_time: datetime.datetime, trip_definition: list) -> float:
        """
        Return travel time for particular datetime instnaces. Requires creation of TravelTime
        Object and trip definition list.
        :param start_time: datetime.datetime value
        :param trip_definition: list of toll trip points
        :return: Float. Travel times in seconds.
        """
        logging.debug('Get travel time. Start time ' + str(start_time) +
                      '. Trip Def: ' + str(trip_definition))
        start_time = datetime.datetime(self._data_date.year, self._data_date.month,
                                       self._data_date.day, hour=start_time.hour,
                                       minute=start_time.minute, second=start_time.second,
                                       microsecond=start_time.microsecond)
        start_time_min = datetime.datetime(self._data_date.year, self._data_date.month,
                                           self._data_date.day, hour=start_time.hour,
                                           minute=start_time.minute)
        total_time = 0.0
        prev_node = trip_definition[0]
        n = len(trip_definition)

        for i in range(1, n):
            node = trip_definition[i]
            pair = prev_node + '-' + node
            pair_series = self.df_travel_time[pair]
            pair_travel_time = pair_series.get(start_time_min)
            logging.debug('Pair: ' + str(pair) + ' Travel Time: ' + str(pair_travel_time))
            total_time += pair_travel_time
            logging.debug('Total travel time: ' + str(total_time))

            # Reset counters
            prev_node = node
            start_time = self._add_datetime_within_day(start_time,
                                                       datetime.timedelta(seconds=pair_travel_time))
            start_time_min = TravelTimeUtil.round_minutes(TravelTimeUtil.round_seconds(start_time))
        return total_time

    def _interpolate_missing_travel_times(self, input_df: pd.DataFrame) -> pd.DataFrame:
        logging.info('Interpolate missing travel times')
        columns = input_df.columns
        for column in columns:
            logging.debug('Interpolate times for pair: ' + str(columns))
            series = input_df[column]
            input_df[column] = self._add_boundary_and_interpolate(series)
        return input_df

    def _compute_pair_distance_feet(self, value: str) -> float:
        start = value.split('-')[0]
        end = value.split('-')[1]
        return abs((self._toll_locations_in_feet[end] - self._toll_locations_in_feet[start]))

    def _add_boundary_and_interpolate(self, input_series: pd.Series) -> pd.Series:
        """
        Add start and end elements to data series. This is necessary since some trips
        do not occur late at night, and can safely be assumed to have free flow
        speed conditions.
        :return: Pandas Series
        """
        pair = input_series.name
        pair_distance = self._compute_pair_distance_feet(pair)
        logging.debug('Pair distance (mi): ' + str(pair_distance))

        # Update first and last elements with free flow condition
        free_flow_travel_time = datetime.timedelta(seconds=pair_distance * self.FREE_FLOW_SPEED)
        logging.debug('Free flow time (s): ' + str(free_flow_travel_time))
        input_series.iloc[0] = free_flow_travel_time
        last_element = input_series.shape[0] - 1
        input_series.iloc[last_element] = free_flow_travel_time

        # Interpolate missing values
        output_series = input_series.dt.seconds + input_series.dt.microseconds / 1_000_000
        output_series = output_series.interpolate()

        return output_series

    def _create_summary_dataframe_skeleton(self, avg_pairs: dict) -> pd.DataFrame:
        """
        Creates a summary skeleton with available data, likely to include missing values.
        :param avg_pairs:
        :return:
        """
        logging.info('Start create summary skeleton')
        first_pair = list(avg_pairs.keys())[0]
        data_date = list(avg_pairs[first_pair].keys())[0]
        self._data_date = data_date
        start_time = datetime.datetime(data_date.year, data_date.month, data_date.day)
        end_time = datetime.datetime(data_date.year, data_date.month, data_date.day,
                                     hour=23, minute=59)
        date_index = pd.date_range(start=start_time, end=end_time, freq='min')
        df_out = pd.DataFrame(index=date_index)

        for pair in avg_pairs:
            logging.debug('Add data for' + str(pair))
            self.check_single_date(list(avg_pairs[pair].keys()))
            new_series = pd.Series(avg_pairs[pair])
            df_out[pair] = new_series
        logging.info('Finish summary skeleton creation')
        return df_out

    @staticmethod
    def check_single_date(datetime_value_list: list):
        logging.debug('Validate single date')
        if not isinstance(datetime_value_list, list):
            raise TypeError(str(type(datetime_value_list)) +
                            ' is not a \'list\' type')
        base_date = datetime_value_list[0].date()
        for datetime_value in datetime_value_list:
            if datetime_value.date() != base_date:
                raise ValueError('Input files contains multiple dates')

    @staticmethod
    def average_travel_times(input_dict: dict) -> dict:
        logging.info('Average travel time data')
        output = {}
        for pair in tqdm(input_dict):
            for time in input_dict[pair]:
                avg_time = TravelTimeUtil.average_timedelta_list(input_dict[pair][time])
                if pair not in output:
                    output.update({pair: {time: avg_time}})
                elif pair in output:
                    output[pair].update({time: avg_time})
        return output

    def _calculate_travel_pairs(self, input_df: pd.DataFrame) -> dict:
        logging.info('Start travel time pair calculation')
        unique_trips = input_df[self._default_field_names['trip_field']].drop_duplicates()
        plaza_field = self._default_field_names['plaza_field']
        datetime_field = self._default_field_names['datetime_field']
        output = {}
        for trip in tqdm(unique_trips):
            logging.debug('Decompose Trip: ' + str(trip))
            df_trip = input_df[input_df[self._default_field_names['trip_field']] == trip]
            df_trip = df_trip.sort_values(by=self._default_field_names['datetime_field'])

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
                logging.debug('Trip and travel time: ' + str(pair) + ': ' + str(time_delta))

                # Create new entry for pair and new entry for time
                if pair not in output:
                    logging.debug('Pair not in output, creating new entry')
                    output.update({pair: {start_time_rounded: []}})
                    output[pair][start_time_rounded].append(time_delta)
                # Create new entry for time, use existing pair entry
                elif pair in output and start_time_rounded not in output[pair]:
                    logging.debug('Pair in output, travel time not in output. Create new entry')
                    output[pair].update({start_time_rounded: []})
                    output[pair][start_time_rounded].append(time_delta)
                # Update pair and time information
                elif pair in output and start_time_rounded in output[pair]:
                    logging.debug('Travel time and pair in output, add data')
                    output[pair][start_time_rounded].append(time_delta)
        logging.info('Finish travel time pair calculation')
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
    def average_timedelta_list(values: list):
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
    sample_travel_time = TravelTime(df)
    trip_def = ['SB01', 'SB02', 'SB03', 'SB04', 'SB08', 'SB09', 'SB10']
    travel_times = sample_travel_time.get_travel_time_all_day(trip_def)
