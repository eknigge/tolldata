import os
import pandas as pd
import openpyxl as opxl
import csv
import numpy as np
import pickle
import math


#--------------------------------------------
# Set of utility classes and methods to 
# process detailed transaction and trip
# files. 
# 
#--------------------------------------------

#--------------------------------------------
# Development Notes: _variables are considered 
# private variable 
#--------------------------------------------

#--------------------------------------------
# Constant Class
#--------------------------------------------
class Constants:
	"""
	Constant class provides constants for transaction analysis
	"""
	_common_ocr_errors = {'O':'Q','Q':'O','8':'B','B':'8','1':'I','I':'1',\
					'A':'4','4':'A','D':'O','O':'D','G':'6','6':'G',\
					'S':'5','5':'S'}

	def __init__(self):
		"""
		Empty constructor, class cannot be constructed
		"""
		pass

	def get_common_ocr_errors():
		"""
		Returns dictionary of common OCR errors
		"""
		return Constants._common_ocr_errors

#--------------------------------------------
# Transaction File Class
#--------------------------------------------
class TransactionFile(object):

	#--------------------------------------------
	#Class Variables
	#--------------------------------------------
	_df = None
	sheet_names =['transaction' , 'Transaction','transa','TrxnDetail','Sheet1'] 
	header_values = ['Trx ID','CSC Lane']
	ocr_header_names = ['Ocr Info','Plate Info']
	tag_header_names = ['Number']
	ag_header_names = ['Ag']
	excel_filetypes = ['xlsx','xls']

	#--------------------------------------------
	#Input Validation 
	#--------------------------------------------
	def importFile(self,filename):
		"""
		Wrapper method for importing files
		"""
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
		"""
		Creates TransactionFile Object from csv or excel file
		"""

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
		"""
		Recursive method to search for plate permutations
		"""
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
		"""
		Wrapper method for returning plate combinations
		"""
		out = []
		for i in self.near_matches(plate):
			out.append(i)
		return out
	#--------------------------------------------
	# Accessors
	#--------------------------------------------

	def getdf(self):
		"""
		Returns dataframe
		"""
		return self._df

	def getFilename(self):
		"""
		Return filename
		"""
		return self._filename

	def getTags(self,tags):
		"""
		Accepts iterable object and return dataframe with tag matches
		"""
		df = self.getdf()
		columns = df.columns
		for i in self.tag_header_names:
			if i in columns:
				return df[df['TAG_ID'].isin(tags)]

	def getPlates(self,plates):
		"""
		Accepts iterable object and returns dataframe with plate matches
		"""
		possible_plate_list = []
		for i in plates:
			tmp = self.plate_combination(str(i))
			for j in tmp:
				possible_plate_list.append(j)
		for i in self.ocr_header_names:
			if i in self.getdf().columns:
				df = self.getdf()
				df = df[df['OCR_VALUE'].isin(possible_plate_list)]
				return df

	def findTagsInRange(self,start,end,ag_tag = 78):
		"""
		Returns dataframe with tags matching start and end of input range
		"""
		df = self.getdf()
		df['TAG_ID'] = pd.to_numeric(df['TAG_ID'])
		df = df[(df['TAG_ID'] >= start) & (df['TAG_ID'] <= end)]

		#filter by ag_tag
		df = df[df['AG'] == ag_tag]

		return df

	def findTagsInIter(self,range_list, ag_tag = 78):
		"""
		Filters dataframe based using iterable of tag tuples (start, end), retains None values
		"""
		#dataframe based on range_list
		df = pd.concat(self.findTagsInRange(range_list[i][0],range_list[i][1], ag_tag)\
				for i in range(0,len(range_list)))
		#empty tag dataframe
		df_noTag = self.getdf()
		df_noTag = df_noTag[df_noTag['TAG_ID'].isna()]
		
		#combine filtered and empty tag dataframes
		df_out = pd.concat([df_noTag,df])

		#set object data to filtered dataframe
		self.setDf(df_out)

	#--------------------------------------------
	# Mutators
	#--------------------------------------------
	def setFilename(self,filename):
		self._filename = filename

	def createDf(self,filename,header_row=None):
		"""
		Takes excel or csv file and return Pandas dataframe object
		"""
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

	def setDf(self,dataframe):
		"""
		Set object dataframe to input dataframe
		"""
		self._df = dataframe



	#--------------------------------------------
	# Other Methods
	#--------------------------------------------

	def ocrBlank(self):
		"""
		Returns true if OCR information is blank
		"""
		output = True
		for i in self.ocr_header_names:
			try:
				 
				if self.getdf()[i].describe()[0] != 0:
					output = False
			except:
				pass
		return output

	def save_obj(self,obj, name):
		"""
		Save python pickle objects
		"""
		with open(name, 'wb') as f:
			pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

	def load_obj(self,name):
		"""
		Read python pickle objects
		"""
		with open(name, 'rb') as f:
			return pickle.load(f)

	def create_tag_plate_dict(self,input_dict,exact_plates=False):
		"""
		Method to create tag/plate dictionary, requires OCR_VALUE and TAG_ID attributes.
		exact_plates attribute sets whether to turn on plate finding by permutations or exact matches
		"""

		#set plate threshold
		#number of read required before transactions with plate are flagged
		plate_count_threshold = 3


		df = self.getdf()
		tag_list = df['TAG_ID'].tolist()
		plate_list = df['OCR_VALUE'].tolist()
		index_of_errors = set([]) 
		missed_tag_list = ['']

		for c, i in enumerate(plate_list):
			#get list of possible plates
			if exact_plates == False:
				possible_plates = self.plate_combination(str(i))
			else:
				possible_plates = [str(i)]

			#increment missed tag list
			missed_tag_list.append('')

			for j in possible_plates:
				#skip instances where OCR blank
				if j == '':
					continue
				#plate match, increment counter
				elif j in input_dict and tag_list[c] == input_dict[j][1]:
					input_dict[j][0] += 1
				#plate match, no tag. flag index values
				elif j in input_dict and \
						(np.isnan(tag_list[c])  or\
						tag_list[c] == '') and\
						input_dict[j][0] >= plate_count_threshold:
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

	def create_ocr_header(self):
		"""
		Iterates over ocr_header_names to create OCR_VALUE attribute
		"""
		if not self.ocrBlank():
			for i in self.ocr_header_names:
				if i in self.getdf().columns:
					df = self.getdf()
					df['OCR_VALUE'] = df[i].str.split(pat='-',expand=True)[0]
					self._df = df
		else:
			for i in self.ocr_header_names:
				try:
					self._df['OCR_VALUE'] = self.getdf()[i]
				except:
					pass

	def create_tag_ids(self):
		"""
		Iterates over tag_header_names to create TAG_ID attribute
		"""
		for i in self.tag_header_names:
			if i in self.getdf().columns:
				df = self.getdf()
				df['TAG_ID'] = df[i]
				self._df = df

		#create ag ID
		for i in self.ag_header_names:
			if i in self.getdf().columns:
				df = self.getdf()
				df['AG'] = df[i]
				self._df = df

	def toCSV(self):
		"""
		Writes output csv file for TransactionFile objects
		"""
		for i in self.excel_filetypes:
			if i in self.getFilename():
				outputFilename = self.getFilename().replace(i,'csv')
				break
		print('CREATING OUTPUT FILE: ' + outputFilename)
		self.getdf().to_csv(outputFilename)


	def findHeader(self, dataframe, header_values):
		"""
		Find header row in dataframe object
		"""
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
		"""
		Iterate over sheets in workbook to find data source
		"""
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
		"""
		Selects which CSV row to import user header names
		"""
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
		"""
		Wrapper method for determining missed tag transactions
		"""
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
		plate_tag_master, error_index, missed_tag_list =\
				self.create_tag_plate_dict(plate_tag_master,exact_plates=True)
		print('size of dictionary:' + str(len(plate_tag_master)))
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

		pd.DataFrame(plate_tag_master).T.to_csv('dict_output.csv')
		return plate_tag_master

	#remove all pickle files in directory
	def removePkl(self):
		"""
		Method to remove all 'pkl' files from current working directory
		"""
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

	#override method
	def create_tag_ids(self):
		for i in self.tag_header_names:
			if i in self.getdf().columns:
				df = self.getdf()
				#set TAG_ID
				df['TAG_ID'] = df[i].str.split(pat='-',expand=True)[1]
				df['TAG_ID'] = pd.to_numeric(df['TAG_ID'])
				#set AG
				df['AG'] = df[i].str.split(pat='-',expand=True)[0]
				df['AG'] = pd.to_numeric(df['AG'])
				self._df = df

class TNBAnalysis(TransactionFile):

	#--------------------------------------------
	#Class Variables
	#--------------------------------------------
	header_values = ['id','dt','lane','agency']
	ocr_header_names = ['plate']
	tag_header_names = ['tag']

	#--------------------------------------------
	#Constructor
	#--------------------------------------------

	def __init__(self,filename):
		"""
		Construct TNBAnalysis object using csv or excel data, extends TripTransaction
		"""
		super(TNBAnalysis,self).__init__(filename)
