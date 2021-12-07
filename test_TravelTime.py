from unittest import TestCase
import TravelTime405 as tt


class TestUtil(TestCase):
    def test_average_list_function_int(self):
        test_list = [3, 3, 5, 5]
        expected_value = 4
        function_value = tt.TravelTimeUtil.average_list(test_list)
        self.assertEqual(expected_value, function_value)

    def test_aver_list_function_float(self):
        test_list = [1.2, 3.5, 8.4, 3.3]
        expected_value = 4.1
        function_value = tt.TravelTimeUtil.average_list(test_list)
        self.assertAlmostEqual(expected_value, function_value)
