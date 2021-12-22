import pandas as pd
import logging


class TripBuilder:
    _df = None
    _toll_point_location_feet = {}
    _toll_points = []
    _toll_end_points = []
    _field_names = {'transaction_id_field': 'TRANSACTION_ID', 'datetime_id_field': 'DATETIME',
                    'plaza_id_field': 'PLAZA', 'transponder_id_field': 'TRANSPONDER_ID',
                    'trip_id_field': 'TRIP_ID', 'plate_id_field': 'PLATE'}
    _TRIP_TIMEOUT_MIN = 30

    def __init__(self, data: pd.DataFrame, transaction_id=None, datetime_id=None,
                 plaza=None, transponder_id=None, trip_id=None, plate_id=None,
                 enable_logging=False, log_level=logging.INFO, trip_timeout=None):

        self._initialize_logging(enable_logging, log_level)
        logging.info('Create TripBuilder')
        self._df = data
        field_names = {'transaction_id_field': transaction_id, 'datetime_id_field': datetime_id,
                       'plaza_id_field': plaza, 'transponder_id_field': transponder_id,
                       'trip_id_field': trip_id, 'plate_id_field': plate_id}
        logging.debug('Field Name Values: ' + self._field_names)
        self._set_field_names(field_names)
        self._validate_fields()
        self._set_trip_timeout(trip_timeout)

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
                logging.debug('field name ' + self._field_names[field] + ' not found')
                raise ValueError('')

    def _set_field_names(self, field_names: dict):
        """
        Set field names for input dataframe. If none are provided will use default values.
        :param field_names:
        """
        logging.info('set field names')
        for field in field_names:
            if field is not None:
                logging.debug('set field: ' + field + ' to ' + field_names[field])
                self._field_names[field] = field_names[field]


if __name__ == '__main__':
    pass
