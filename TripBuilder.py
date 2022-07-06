import pandas as pd
import logging
import TollData as td
import datetime
import numpy as np


class TripBuilder:
    """
    Class to build trips using Pandas DataFrame. Utilizes exit node and other standard transaction information.
    Trips are not built upon object creation, need to execute build method. 'test_tripBuilder' validates
    functionality of this class.
    """
    _df = None
    _toll_point_location_feet = {}
    _toll_points = []
    _exit_nodes = []
    _field_names = {'transaction_id_field': 'TRANSACTION_ID', 'datetime_id_field': 'DATETIME',
                    'plaza_id_field': 'PLAZA', 'transponder_id_field': 'TRANSPONDER_ID',
                    'trip_id_field': 'TRIP_ID', 'plate_id_field': 'PLATE'}
    _TRIP_TIMEOUT_MIN = datetime.timedelta(minutes=30)
    _current_trip_id = 0

    def __init__(self, data: pd.DataFrame, transaction_id=None, datetime_id=None,
                 plaza=None, transponder_id=None, trip_id=None, plate_id=None,
                 enable_logging=False, log_level=logging.INFO, trip_timeout=None,
                 exit_nodes=None):

        self._initialize_logging(enable_logging, log_level)
        logging.info('Create TripBuilder')
        self._df = data
        field_names = {'transaction_id_field': transaction_id, 'datetime_id_field': datetime_id,
                       'plaza_id_field': plaza, 'transponder_id_field': transponder_id,
                       'trip_id_field': trip_id, 'plate_id_field': plate_id}
        logging.debug('Field Name Values: ' + str(self._field_names))
        self._set_field_names(field_names)
        self._validate_fields()
        self._set_trip_timeout(trip_timeout)
        self._set_exit_nodes(exit_nodes)

    def get_dataframe(self):
        """
        Return dataframe. If build has not occured will return input DataFrame, otherwise will return
        DataFrame with built trips.
        :return: DataFrame
        """
        return self._df

    def _get_related_trips(self, transaction_id: int):
        """
        Get related trips based on transaction ID. This method is used to expand the search for related
        transactions by searching for related plates, and tag matches.
        :param transaction_id: int. Transaction ID of interest.
        :return: Dataframe. Related transactions.
        """
        logging.info('Start related trip search')
        plates = set({})
        tags = set({})
        position = 0
        elements = 1
        df = self._df[self._df['TRANSACTION_ID'] == transaction_id]

        while position < elements:
            logging.debug('Position: ' + str(position))
            plate_position = df['PLATE'].iloc[position]
            tag_position = df['TRANSPONDER_ID'].iloc[position]
            logging.debug('Use Plate: ' + str(plate_position))
            logging.debug('Use Tag: ' + str(tag_position))

            plate_combinations = td.PlateCombinatorics(plate_position).get_plate_combinations()
            for plate in plate_combinations:
                if plate not in plates:
                    logging.debug('Adding plate: ' + str(plate))
                    plates.add(plate)
                    df_add = self._df[self._df['PLATE'] == plate]
                    if df_add.shape[0] > 0:
                        logging.debug('Add additional records: ' + str(df_add.shape[0]))
                        df = pd.concat([df, df_add])
                        df = df.drop_duplicates(subset='TRANSACTION_ID')
                    elements = df.shape[0]

            if tag_position not in tags and tag_position != np.nan:
                logging.debug('Add tag: ' + str(tag_position))
                tags.add(tag_position)
                df_add = self._df[self._df['TRANSPONDER_ID'] == tag_position]
                if df_add.shape[0] > 0:
                    logging.debug('Add additional records: ' + str(df_add.shape[0]))
                    df = pd.concat([df, df_add])
                    df = df.drop_duplicates(subset='TRANSACTION_ID')
                elements = df.shape[0]

            position += 1
        logging.info('Related trip search complete')
        return df

    def _set_exit_nodes(self, node_list: list):
        """
        Set exit nodes if node_list is not null
        """
        logging.info('Set exit nodes')
        if node_list is not None:
            logging.debug('Exit node list set to ' + str(node_list))
            self._exit_nodes = node_list

    def _calculate_directional_changes(self, df: pd.DataFrame):
        """
        Add boolean Series 'DIR_CHANGE' on whether directional change occured.
        :param df: DataFrame. Input data.
        :return: DataFrame. Output with new 'DIR_CHANGE' Series.
        """
        logging.info('Calculate directional changes')
        cardinal_directions = ['NB', 'SB', 'WB', 'EB']
        direction_list = []
        output = [False]
        plaza_list = df[self._field_names['plaza_id_field']].tolist()

        # Convert to cardinal direction
        for plaza in plaza_list:
            for direction in cardinal_directions:
                if direction in plaza:
                    logging.debug('Use ' + str(direction) + ' for plaza ' + str(plaza))
                    direction_list.append(direction)
                    break

        # Calculate changes in direction
        for i in range(1, len(direction_list)):
            output.append(direction_list[i] != direction_list[i - 1])

        df['DIR_CHANGE'] = pd.Series(output, dtype='bool')
        logging.info('Directional change calculation complete')
        return df

    def _calculate_time_deltas(self, df: pd.DataFrame):
        """
        Calculate time deltas between transactions. Adds new 'TIME_DELTA_ Series.
        :param df: DataFrame. Input data.
        :return: DataFrame with 'TIME_DELTA' Series.
        """
        logging.info('Start time delta calculation')
        time_deltas = [datetime.timedelta(seconds=0)]
        time_list = df[self._field_names['datetime_id_field']].tolist()

        for i in range(1, len(time_list)):
            time_diff = time_list[i] - time_list[i - 1]
            logging.debug('Time difference' + str(time_diff))
            time_deltas.append(time_diff)
        df['TIME_DELTA'] = pd.Series(time_deltas)
        logging.info('End time delta calculation')
        return df

    def build_trips(self):
        """
        Build trips based on input DataFrame. Result saved to object and can be
        access with the get_dataframe method.
        """
        logging.info('Start trip building')
        df_build = self._df
        df_out = None

        while df_build.shape[0] > 0:
            logging.debug('Size of build dataframe: ' + str(df_build.shape[0]))
            self._current_trip_id += 1
            # Get related transaction
            df_related_transactions = self._get_related_trips(df_build['TRANSACTION_ID'].iloc[0])
            df_related_transactions = df_related_transactions.reset_index()

            # Sort by datetime
            datetime_name = self._field_names['datetime_id_field']
            df_related_transactions[datetime_name] = pd.to_datetime(df_related_transactions[datetime_name])
            df_related_transactions = df_related_transactions.sort_values(by=datetime_name)

            # Determine directional changes
            df_related_transactions = self._calculate_directional_changes(df_related_transactions)

            # Calculate time deltas
            df_related_transactions = self._calculate_time_deltas(df_related_transactions)

            # Determine trip break points
            df_related_transactions = self._calculate_trip_breaks(df_related_transactions)

            # Assign trip ID
            df_related_transactions = self._assign_trip_id(df_related_transactions)

            # Concat output results
            if df_out is None:
                df_out = df_related_transactions
            else:
                logging.debug('Concatenating results')
                df_out = pd.concat([df_out, df_related_transactions])

            # Remove transactions from build dataframe
            df_build = self._remove_built_transactions(df_build, df_related_transactions)
            df_build = df_build.reset_index(drop=True)

        logging.info('Complete building complete')
        self._df = df_out

    def _remove_built_transactions(self, df_full: pd.DataFrame, df_built: pd.DataFrame):
        """
        Remove df_built from df_full.
        :param df_full: DataFrame transactions will be removed from
        :param df_built: DataFrame used to remove transactions
        :return: DataFrame with removed transactions
        """
        logging.info('Remove built transactions')
        transaction_ids = df_built[self._field_names['transaction_id_field']].tolist()
        df_full = df_full[~df_full[self._field_names['transaction_id_field']].isin(transaction_ids)]
        return df_full

    def _calculate_trip_breaks(self, df: pd.DataFrame):
        """
        Calculation when trip breaks should occur. Utilizes time delta, directional
        changes, and exit plazas. Adds 'BREAK_TRIP' to DataFrame.
        :param df: Input Dataframe
        :return: Dataframe with 'BREAK_TRIP' Series added
        """
        logging.info('Start trip break calculation')
        trip_breaks = []
        n = df.shape[0]

        for i in range(n):
            if n == 1:
                continue

            time_delta = df['TIME_DELTA'].iloc[i]
            directional_change = df['DIR_CHANGE'].iloc[i]
            prev_node = df[self._field_names['plaza_id_field']].iloc[i-1]
            if i == 0:
                trip_breaks.append(False)
            elif i == n - 1:
                trip_breaks.append(False)
            elif directional_change or prev_node in self._exit_nodes or \
                    time_delta > self._TRIP_TIMEOUT_MIN:
                logging.debug('Break. Directional change: ' + str(directional_change))
                logging.debug('Break. Previous node: ' + str(prev_node))
                logging.debug('Break. Time Delta (min) : ' + str(time_delta))
                trip_breaks.append(True)
            else:
                trip_breaks.append(False)

        df['BREAK_TRIP'] = pd.Series(trip_breaks, dtype='bool')
        logging.info('End trip break calculation')
        return df

    def _assign_trip_id(self, df: pd.DataFrame):
        """
        Add 'TRIP_ID_BUILD' field to input DataFrame, where 'TRIP_ID_BUILD'
        is an int the represents the trip ID.
        :param df: Input DataFrame
        :return: DataFrame with 'TRIP_ID_BUILD' field
        """
        logging.info('Start assign trip ID')
        output = []
        break_list = df['BREAK_TRIP'].tolist()
        n = len(break_list)

        for i in range(n):
            if i == 0 or n == 1:
                output.append(self._current_trip_id)
                continue
            elif i == n - 1:
                output.append(self._current_trip_id)
            elif break_list[i]:
                self._current_trip_id += 1
                logging.debug('Increment trip ID: ' + str(self._current_trip_id))
                output.append(self._current_trip_id)
            else:
                output.append(self._current_trip_id)
        df['TRIP_ID_BUILD'] = pd.Series(output)
        logging.info('End assign trip ID')
        return df

    @staticmethod
    def _initialize_logging(value: bool, log_level: int):
        if value:
            logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                datefmt='%m/%d/%Y %H:%M:%S', filename='trip_builder_log.log',
                                level=log_level)

    def _set_trip_timeout(self, value: int):
        """
        Set trip timeout value in minutes.
        :param value: int, minutes
        """
        if value is not None and isinstance(value, int):
            logging.debug('Change trip timeout from ' + str(self._TRIP_TIMEOUT_MIN) + ' to ' +
                          str(value))
            self._set_trip_timeout(value)

    def _validate_fields(self):
        """
        Check whether default or provided fields exist in input dataframe.
       """
        logging.info('validate fields')
        columns = self._df.columns
        for field in self._field_names:
            if self._field_names[field] not in columns:
                logging.debug('field name ' + str(self._field_names[field]) + ' not found')
                raise ValueError('')

    def _set_field_names(self, field_names: dict):
        """
        Set field names for input dataframe. If none are provided will use default values.
        :param field_names: dict of input field names
        """
        logging.info('set field names')
        for field in field_names:
            if field_names[field] is not None:
                logging.debug('set field: ' + str(field) + ' to ' + str(field_names[field]))
                self._field_names[field] = field_names[field]


if __name__ == '__main__':
    pass
