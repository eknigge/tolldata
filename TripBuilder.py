import pandas as pd
import logging
import TollData as td
import datetime
import numpy as np


class TripBuilder:
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
        return self._df

    def _get_related_trips(self, transaction_id: int):
        plates = set({})
        tags = set({})
        position = 0
        elements = 1
        df = self._df[self._df['TRANSACTION_ID'] == transaction_id]

        while position < elements:
            plate_position = df['PLATE'].iloc[position]
            tag_position = df['TRANSPONDER_ID'].iloc[position]

            plate_combinations = td.PlateCombinatorics(plate_position).get_plate_combinations()
            for plate in plate_combinations:
                if plate not in plates:
                    plates.add(plate)
                    df_add = self._df[self._df['PLATE'] == plate]
                    if df_add.shape[0] > 0:
                        df = pd.concat([df, df_add])
                        df = df.drop_duplicates(subset='TRANSACTION_ID')
                    elements = df.shape[0]

            if tag_position not in tags and tag_position != np.nan:
                tags.add(tag_position)
                df_add = self._df[self._df['TRANSPONDER_ID'] == tag_position]
                if df_add.shape[0] > 0:
                    df = pd.concat([df, df_add])
                    df = df.drop_duplicates(subset='TRANSACTION_ID')
                elements = df.shape[0]

            position += 1
        return df

    def _set_exit_nodes(self, node_list: list):
        if node_list is not None:
            self._exit_nodes = node_list

    def _calculate_directional_changes(self, df: pd.DataFrame):
        cardinal_directions = ['NB', 'SB', 'WB', 'EB']
        direction_list = []
        output = [False]
        plaza_list = df[self._field_names['plaza_id_field']].tolist()

        for plaza in plaza_list:
            for direction in cardinal_directions:
                if direction in plaza:
                    direction_list.append(direction)
                    break

        for i in range(1, len(direction_list)):
            output.append(direction_list[i] != direction_list[i - 1])

        df['DIR_CHANGE'] = pd.Series(output, dtype='bool')
        return df

    def _calculate_time_deltas(self, df: pd.DataFrame):
        time_deltas = [datetime.timedelta(seconds=0)]
        time_list = df[self._field_names['datetime_id_field']].tolist()

        for i in range(1, len(time_list)):
            time_diff = time_list[i] - time_list[i - 1]
            time_deltas.append(time_diff)
        df['TIME_DELTA'] = pd.Series(time_deltas)
        return df

    def build_trips(self):
        df_build = self._df
        df_out = None

        while df_build.shape[0] > 0:
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
                df_out = pd.concat([df_out, df_related_transactions])

            # Remove transactions from build dataframe
            df_build = self._remove_built_transactions(df_build, df_related_transactions)
            df_build = df_build.reset_index()

        self._df = df_out

    def _remove_built_transactions(self, df_full: pd.DataFrame, df_built: pd.DataFrame):
        transaction_ids = df_built[self._field_names['transaction_id_field']].tolist()
        df_full = df_full[~df_full[self._field_names['transaction_id_field']].isin(transaction_ids)]
        return df_full

    def _calculate_trip_breaks(self, df: pd.DataFrame):
        """
        TODO
            trip breaks need to occur in consideration of the previous transaction data, not a single
            transaction like this current version. Need to update to handle more of the edge case scenarios.
            Also need to check code on _assign_trip_id to ensure that it follows this logic.
        """
        trip_breaks = []

        for i in range(df.shape[0]):
            time_delta = df['TIME_DELTA'].iloc[i]
            directional_change = df['DIR_CHANGE'].iloc[i]
            node = df[self._field_names['plaza_id_field']].iloc[i]
            if directional_change or node in self._exit_nodes or \
                    time_delta > self._TRIP_TIMEOUT_MIN:
                trip_breaks.append(True)
            else:
                trip_breaks.append(False)

        df['BREAK_TRIP'] = pd.Series(trip_breaks, dtype='bool')
        return df

    def _assign_trip_id(self, df: pd.DataFrame):
        output = []
        break_list = df['BREAK_TRIP'].tolist()

        for i in range(len(break_list)):
            if i == len(break_list)-1:
                output.append(self._current_trip_id)
            elif break_list[i]:
                self._current_trip_id += 1
                output.append(self._current_trip_id)
            else:
                output.append(self._current_trip_id)
        df['TRIP_ID_BUILD'] = pd.Series(output)
        return df

    @staticmethod
    def _initialize_logging(value: bool, log_level: int):
        if value:
            logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                datefmt='%m/%d/%Y %H:%M:%S', filename='trip_builder_log.log',
                                level=log_level)

    def _set_trip_timeout(self, value: int):
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
        :param field_names:
        """
        logging.info('set field names')
        for field in field_names:
            if field_names[field] is not None:
                logging.debug('set field: ' + str(field) + ' to ' + str(field_names[field]))
                self._field_names[field] = field_names[field]


if __name__ == '__main__':
    pass
