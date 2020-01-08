import Util
import os
import pandas as pd

all_files = os.listdir(os.getcwd())
filtered_file_list = []

#filter for 99 trxn files
for i in all_files:
	if 'SR99' in i and 'TrxnDetail' in i:
		filtered_file_list.append(i)

#Process all 99 trxn files
for i in filtered_file_list:
	trxn_file = Util.TransactionFile(i)
	trxn_file.regular_users()


