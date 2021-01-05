import TollData as td
import pandas as pd
import datetime

if __name__ == '__main__':
    start_time_script = datetime.datetime.now()
    n: int = 30  # number of tests

    plate_tag_size_list = [100, 200, 400, 500, 1000, 2000, 5000]
    series_list = []

    for i in plate_tag_size_list:
        results = []
        for j in range(n):
            print('Plate/tag size: ' + str(i) + '\nTest number:' + str(j))
            test = td.AVITest(n_plates=i)
            test.run_analysis()
            test_result = test.get_test_result()
            results.append(test_result)
        series_list.append(pd.Series(results))

    pd.DataFrame(series_list).T.to_csv('Test_Results.csv')
    end_time_script = datetime.datetime.now()
    print('Elapsed Time: ' + str(end_time_script - start_time_script))
