import Util
import os
import pandas as pd
import re

all_files = os.listdir(os.getcwd())
filtered_file_list = []
filename = 'SB_go_live_trip_detailed_transaction_SR99_report_20200120070001_01-19-2020.csv'
tag_list = [6501401, 3318675,6640201]
plate_list = ['BNA0183','C68987L']
test_var = [(109,1309999)]


#select files using regular expression
for i in all_files:
	if i == filename:
		trip_file = Util.TripFile(i)
		trip_file.getdf().to_csv('temp.csv')
		trip_file.findTagsInIter(test_var)
		df = trip_file.getdf()
		df.to_csv('temp.csv')
