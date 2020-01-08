import os
import pandas as pd
import openpyxl as opxl
import csv
import numpy as np
import pickle


#--------------------------------------------
# Set of utility classes and methods to 
# process detailed transaction and trip
# files. 
# 
#--------------------------------------------

#--------------------------------------------
# Development Notes: _variables are considered 
# private variable 
#
#
#--------------------------------------------

#--------------------------------------------
# Constant Class
#--------------------------------------------
class Constants:
	_common_ocr_errors = {'O':'Q','Q':'O','8':'B','B':'8','1':'I','I':'1',\
					'A':'4','4':'A','D':'O','O':'D','G':'6','6':'G',\
					'S':'5','5':'S'}

	def __init__(self):
		pass

	def get_common_ocr_errors():
		return Constants._common_ocr_errors

#--------------------------------------------
# Transaction File Class
#--------------------------------------------
class TransactionFile(object):

	#--------------------------------------------
	#Class Variables
	#--------------------------------------------
	sheet_names =['transaction' , 'Transaction','transa','TrxnDetail','Sheet1']
	header_values = ['Trx ID','CSC Lane']
	ocr_header_names = ['Ocr Info','Plate Info']
	tag_header_names = ['Number']
	excel_filetypes = ['xlsx','xls']

	#--------------------------------------------
	#Input Validation 
	#--------------------------------------------
	def importFile(self,filename):
		#instance variables
		print('PROCESSING ' + filename)
		self.setFilename(filename)

		#create df and find header row
		self._df = self.createDf(filename)
		header_row = self.findHeader(self._df,self.header_values)
		self._df = self.createDf(filename,header_row)

		#create OCR_VALUE column
		self.create_ocr_header()

		#create TAG_ID column
		self.create_tag_ids()

	#--------------------------------------------
	#Constructor
	#--------------------------------------------
	def __init__(self, filename):

		if isinstance(filename, pd.DataFrame):
			self._df = filename
		else:
			self.importFile(filename)

	#--------------------------------------------
	# Methods to determine near match plate value
	#--------------------------------------------
	def near_matches(self,input):
		input_list = list(input)
		combinations = [ input_list ]
		self.find_next_combination(input_list, 0, combinations)
		return map(lambda c: ''.join(c), combinations)

	def find_next_combination(self,input_list, index, combinations):
		if index < len(input_list):
			c = input_list[index]
			common_ocr_errors = Constants.get_common_ocr_errors()

			if c in common_ocr_errors.keys():

				permuted_list = input_list[:]
				permuted_list[index] = common_ocr_errors[c]

				combinations.append(permuted_list)
				self.find_next_combination(permuted_list, index+1, combinations)

			self.find_next_combination(input_list, index+1, combinations)

	def plate_combination(self,plate):
		out = []
		for i in self.near_matches(plate):
			out.append(i)
		return out
	#--------------------------------------------
	# Accessors
	#--------------------------------------------

	def getdf(self):
		return self._df
	def getFilename(self):
		return self._filename
	

	#--------------------------------------------
	# Mutators
	#--------------------------------------------
	def setFilename(self,filename):
		self._filename = filename

	def createDf(self,filename,header_row=None):
		if('xlsx' in filename or 'xls' in filename):
			print('READ EXCEL FILETYPE')
			#select sheet to import
			import_sheetname = self.findSheet(filename,TransactionFile.sheet_names)
			df = pd.read_excel(filename,sheet_name=import_sheetname,skiprows=header_row)
		elif('csv' in filename):
			print('READ CSV FILETYPE')
			header_row = self.selectCSVRow(filename)
			df = pd.read_csv(filename,skiprows = header_row)
		else:
			print('UNSUPPORTED FILETYPE')
		return df



	#--------------------------------------------
	# Other Methods
	#--------------------------------------------
	def save_obj(self,obj, name):
		with open(name, 'wb') as f:
			pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

	def load_obj(self,name):
		with open(name, 'rb') as f:
			return pickle.load(f)

	def create_tag_plate_dict(self,input_dict):
		df = self.getdf()
		tag_list = df['TAG_ID'].tolist()
		plate_list = df['OCR_VALUE'].tolist()
		index_of_errors = set([]) 
		missed_tag_list = ['']

		for c, i in enumerate(plate_list):
			#get list of possible plates
			possible_plates = self.plate_combination(str(i))

			#increment missed tag list
			missed_tag_list.append('')

			for j in possible_plates:
				#skip instances where OCR blank
				if j == '':
					continue
				#plate match, increment counter
				elif j in input_dict and tag_list[c] == input_dict[j]:
					input_dict[j][0] += 1
				#plate match, no tag. flag index values
				elif j in input_dict and \
						(np.isnan(tag_list[c])  or\
						tag_list[c] == ''):
					index_of_errors.add(c)
					missed_tag_list[c] = input_dict[j][1]
				#if not in dict and tag blank, skip
				elif j not in input_dict and\
						(tag_list[c] == '' or np.isnan(tag_list[c])):
					continue
				#add new entry
				else:
					input_dict[j] = [1,tag_list[c]]
		return input_dict, list(index_of_errors), missed_tag_list

	def findPlate(self,plate):
		possible_plates = self.plate_combination(plate)
		for i in self.ocr_header_names:
			if i in self.getdf().columns:
				df = self.getdf()
				df = df[df['OCR_VALUE'].isin(possible_plates)]
				return df

	def findTag(self,tag):
		df = self.getdf()
		columns = df.columns
		for i in self.tag_header_names:
			if i in columns:
				print(i,tag)
				return df[df[i] == tag]

	#create OCR_VALUE column
	def create_ocr_header(self):
		for i in self.ocr_header_names:
			if i in self.getdf().columns:
				df = self.getdf()
				df['OCR_VALUE'] = df[i].str.split(pat='-',expand=True)[0]
				self._df = df

	#create TAG_ID column
	def create_tag_ids(self):
		for i in self.tag_header_names:
			if i in self.getdf().columns:
				df = self.getdf()
				df['TAG_ID'] = df[i]
				self._df = df

	def toCSV(self):
		for i in self.excel_filetypes:
			if i in self.getFilename():
				outputFilename = self.getFilename().replace(i,'csv')
				break
		print('CREATING OUTPUT FILE: ' + outputFilename)
		self.getdf().to_csv(outputFilename)


	def findHeader(self, dataframe, header_values):
		search_attempts = 50
		df = dataframe
		print('HEADER ROW FUNCTION')

		#use row 0
		for i in header_values:
			if i in df.columns:
				print('HEADER ROW: 0')
				header_row = 0
				return header_row

		#search for header row
		for i in range(search_attempts):
			columns = df.loc[i].tolist()
			for j in header_values:
				if j in columns:
					print('HEADER ROW: ' + str(i + 1))
					header_row = i + 1
					break
			else:
				continue
			break
		#search attempts exceeded output msg
		if i == search_attempts:
			print('UNABLE TO FIND HEADER ROW, MADE ' + str(search_attempts) \
					+ 'ATTEMPTS')
		return header_row

	def findSheet(self,filename,name_list):
		#openpyxl open workbook 
		print('SELECTING WORKSHEET TO IMPORT:')
		wb = opxl.load_workbook(filename,read_only=True)
		workbook_sheets = wb.sheetnames

		#openpyxl select transaction worksheet 
		sheetname = None
		for i in name_list:
			for j in workbook_sheets:
				if i in j:
					sheetname = j
					print('SELECTED SHEET: ' + sheetname)
					break
			else:
				continue
			break

		#no result output
		if(sheetname == None):
			print('SHEET NAME SEARCH FAILED')

		return sheetname

	#select row to import
	def selectCSVRow(self,filename):
		with open(filename,'r') as csvfile:
			reader = csv.reader(csvfile)
			for i, value in enumerate(reader):
				for j in self.header_values:
					if j in value:
						header_row = i
						break
		csvfile.close()
		print('CSV HEADER ROW IS: ' + str(header_row))
		return header_row

	def regular_users(self):
		df = self.getdf()
		plate_tag_filename = 'plate_tag_dict.pkl'
		output_dict_pickle = 'flagged_transactions.pkl'
		output_dict_csv = 'flagged_transactions.csv'

		#read existing dictionary file
		try:
			plate_tag_master = self.load_obj(plate_tag_filename)
		except:
			print('COULD NOT LOCATE PLATE MASTER, CREATING NEW FILE')
			plate_tag_master = {}


		#update plate dictionary with object data
		print('size of dictionary:' + str(len(plate_tag_master)))
		plate_tag_master, error_index, missed_tag_list =\
				self.create_tag_plate_dict(plate_tag_master)
		self.save_obj(plate_tag_master, plate_tag_filename)
		df['MISSED_TAGS'] = pd.Series(missed_tag_list)
		df_obj_errors = df.iloc[error_index]

		#read or update results file
		try:
			df_regulars = pd.read_pickle(output_dict_pickle)
			df_regulars = pd.concat([df_regulars,df_obj_errors],sort=False)
			df_regulars.to_pickle(output_dict_pickle)
			print('size of output' + str(df_regulars.shape))
			df_regulars.to_csv('flagged_transactions.csv')
		except:
			df_obj_errors.to_pickle('flagged_transactions.pkl')
			df_obj_errors.to_csv('flagged_transactions.csv')

		return plate_tag_master

	#remove all pickle files in directory
	def removePkl(self):
		all_files = os.listdir(os.getcwd())
		for i in all_files:
			if 'pkl' in i:
				os.remove(i)



#--------------------------------------------
# Transaction File Class
#--------------------------------------------
class TripFile(TransactionFile):

	#--------------------------------------------
	#Class Variables
	#--------------------------------------------
	header_values = ['Trip ID', 'Entry Time','Fare']
	ocr_header_names = ['Plate Info']
	tag_header_names = ['Ag-Tag']

	#--------------------------------------------
	#Constructor
	#--------------------------------------------

	def __init__(self,filename):
		super(TripFile, self).__init__(filename)

	#--------------------------------------------
	#Methods
	#--------------------------------------------

	#override super method
	def create_ocr_header(self):
		for i in self.ocr_header_names:
			if i in self.getdf().columns:
				df = self.getdf()
				df['OCR_VALUE'] = df[i].str.split(pat='-',expand=True)[0]
				self._df = df


	#override super method
	def create_tag_ids(self):
		for i in self.tag_header_names:
			if i in self.getdf().columns:
				df = self.getdf()
				df['TAG_ID'] = df[i].str.split(pat='-',expand=True)[1]
				df['TAG_ID'] = pd.to_numeric(df['TAG_ID'])
				self._df = df


