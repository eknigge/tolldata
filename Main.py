import Util
import os
import pandas as pd
import re

all_files = os.listdir(os.getcwd())
filtered_file_list = []

#select files using regular expression
for i in all_files:
	m = re.match('\w{8}[\.csv]',i)
	try:
		filtered_file_list.append(m.string)
	except AttributeError:
		pass

#check all files
for i in filtered_file_list:
	trx = Util.TNBAnalysis(i)
	trx.regular_users()
