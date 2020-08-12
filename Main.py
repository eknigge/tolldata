import Util
import os
import pandas as pd
import re
import random

all_files = os.listdir(os.getcwd())
filtered_file_list = []

#select and process files 
total_avi_trxns = 0

def select_random_files(n):
	"""
	param:
		n number of files 
	returns:
		list of random files
	"""
	out = set()

	#select trip files
	all_files = os.listdir(os.getcwd())
	trip_files = []
	for i in all_files:
		if 'csv' in i and 'TripTxnDetail' in i:
			trip_files.append(i)

	while len(out) < n:
		index = random.randint(0,len(trip_files)-1)
		out.add(trip_files[index])
	return out

def calculate_failure_rate(files):
	"""
	process series of files using static dictionary file
	returns failure rate

	param:
		files list of files to process
	returns:
		float failure rate 
	"""
	total_avi_trxns = 0
	for i in files:
		if 'csv' in i and 'TripTxnDetail' in i:
			trip_file = Util.TripFile(i)
			total_avi_trxns += trip_file.get_avi_count()
			trip_file.regular_users(static_dict=True)
	df_missed = pd.read_csv('flagged_transactions.csv')
	total_missed = df_missed.shape[0]
	failure_rate = 1 - (total_missed / (total_missed + total_avi_trxns))
	os.remove('flagged_transactions.pkl')
	return failure_rate

failure_rate_list = []
n_files = 15
for i in range(40):
	random_files = select_random_files(n_files)
	failure_rate = calculate_failure_rate(random_files)
	failure_rate_list.append(failure_rate)

#export data to csv
pd.Series(failure_rate_list).to_csv('simulations_failure_rate.csv')
