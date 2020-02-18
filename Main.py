import Util
import os
import pandas as pd
import re

all_files = os.listdir(os.getcwd())
filtered_file_list = []
filename = 'SB_go_live_trip_detailed_transaction_SR99_report_20200120070001_01-19-2020.csv'
tag_list = [6501401, 3318675]
plate_list = ['BNA0183','C68987L']

#select files using regular expression
for i in all_files:
	if i == filename:
		trip_file = Util.TripFile(i)
		df = trip_file.getPlates(plate_list)
		print(df)
		df.to_csv('temp.csv')

