import Util
import os
import pandas as pd

all_files = os.listdir(os.getcwd())
filtered_file_list = []

#filter for 99 trxn files
for i in all_files:
	if 'SR99' in i and 'trip' in i and 'csv' in i:
		#change this line to filter for different files
		filtered_file_list.append(i)

#Process all 99 trxn files
for i in filtered_file_list:
	trxn_file = Util.TripFile(i)
	print("is ocr blank? ", trxn_file.ocrBlank())
	trxn_file.getdf().head(5).to_csv('temp.csv')
	print(trxn_file.getdf().head(5))


