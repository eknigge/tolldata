from unittest import TestCase
import pandas as pd


class TestTripBuilder(TestCase):

    def test_create_test_dataframe(self):
        filename = 'trip_build_test_data.csv'
        df = pd.read_csv(filename)
        df['DATETIME'] = pd.to_datetime(df['DATETIME'])
        print(df)
