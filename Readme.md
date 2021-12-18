# Introduction
The purpose of this module is to automate and standardize processing of toll data by using `Pandas`,
 `Numpy`, and standard Python libraries. The classes contained in the `TollData` module include:
- **Transaction**. This class processes transaction files and standardizes the input. 
- **Trip**. This class processes transaction files and standardizes the input. 
- **Rate Assignment**. This set of classes can assign time-of-day rates for SR 520 and 99 toll facilities. The rates assigned depend on the holiday schedule, number of axles, status of the transponder used, and time of day.
- **AVI Validation**. This class performs an AVI analysis given a known set of plate/tags (key:value) pairs. If a tag/transponder is missed during a read it is noted in the output.
- **AVI Test**. This class extends the functionality of the `AVI Validation` class by conducting statistically validated random tests to find the standard deviation from random sample sets. 
- **Plate Combinatorics**. This helper class computes plate combinatorics, and is useful for other classes in determining common OCR errors found in other classes. 

# Transaction Files
Transaction files are one of the most common data formats for toll data. This class can process both excel and csv files, and works for both xlsm or xls files. The processed files can be exported as `DataFrames` or a `csv` file.

# Trip Files
Trip files are similar to transaction files, but there are a few differences. For single-point toll facilities there is the addition of an assigned fare, but little else is changed. For multi-point facilities
information will be grouped by trips, so the transactions that make up a trip will be grouped together. Multi-point toll facility trip files will also contain information about the entry/exit point, the assigned rate, and final trip level OCR value assigned. 

This class inherits the methods and functionality from the `TransactionFile` class, but uses a different dictionary for some processing values since the naming conventions between the two files are dissimilar. 


# Rate Assignment
Rate assignment is relatively straightforward for time-of-day facilities. If you know some basic parameters it is possible to calculate the rate that should be assigned. The relevant parameters are as follows:
- Datetime
- Transaction type
- Axles
- Transponder/Tag Status
- Pay-by-Mail status
- Holidays 

The rate assignment classes allow you to determine both a `base rate` and `final rate`. The `base rate` is the rate without adjustment for time-of-day or pay-by-mail for vehicles that do not have a valid/active transponder. 
## Rate Assign 520
This class allows you to determine the rate for transactions occuring on the SR 520 bridge. 

## Rate Assign 99
This class inherits from the 520 class but uses the rate table information for the SR 99 facility. Since these two roadways operate nearly identically there are no other changes between these classes.

The rates are updated to be the latest rates, effective October 1, 2021.

## Rate Assign 99 Legacy
This class inherits from the 520 class and uses the rate information prior to October 1, 2021. This class should only be used to validate rates prior to this effective date. 

# Plate Combinatorics
This class provides a simple way of determining a set of possible OCR mistakes from common errors. For example, the value of `B` is often mistaken for the numerical value of `8`. A plate with a value of `88` would return the combinations of `BB`, `B8`, `8B`, and `88`. This process is executed for arbitrarily complex plates, using a lookup table of common errors. 

# AVI Validation
This class tests whether a plate is read without a tag. The read threshold, which represents the number of times a plate and tag are seen together can be set to constrain which transactions are flagged. The input `DataFrame` is required to have the following fields:
- TAG_ID, represending the transponder ID
- PLATE, for the plate value without state identifier
- TRX_ID, for the transaction identification number

The output `DataFrame` includes the new fields `AVI_MISMATCH` set to `True` or `False` based on the result of the test, and the field `MISSED_TAG_ID` for the ID of the missed tag, if applicable.

A `csv` file can be used to as a lookup `dictionary`, or it can be generated automatically. The API also allows users to state whether they want to use a static dictionary that is not updated as the test progress, or one that continuously updated. 

# AVI Test
This class performs an AVI validation test, which is similar to the `AVI Validation`, but made to be more extensible and easier to repeat tests. A minimum of 30 days of data is required, without modifying the source. This is based on previous experience, and that a large statistical sample is required for validation. 

The test takes some time to execute since it imports a large number of files to create a single `DataFrame` object. The results of the first run are exported ot a `.pkl` file. If an existing `.pkl` file exists this step can be skipped, and the runtime is reduced. 

The process works as follows: 
1. Import files for analysis, or using existing data
2. Select random start date
3. Build plate/tag dictionary
4. Run AVI Validation test and compute metrics

This analysis can be repeated a desired number of times and the `get_test_result` method can be used to aggregate this information.

# Testing 
To test this module run `python -m pytest` which will execute the `test_TollData` script. The script is not an exhaustive set of tests, but it should be sufficient to validate major errors. 

# Travel Time
This module provides accurate travel times for user-defined trips. It does so by calculating all node-to-node
travel, and then the total travel time based on the specified trip. The provided dataframe needs to include:
unique trip identifiers, datetime information, and node names. Once a `TravelTime` object is created, travel 
 times can be calculated using `get_travel_time_all_day` or `get_travel_time`. 

The module also has a data from a real-world example. 

Import the test file as a dataframe, then parse the datetime information. 
```python
    df = pd.read_csv('_hashed_export_test_data_trip.csv')
    datetime_format = '%m/%d/%Y %H.%M.%S.%f'
    df['DATETIME'] = pd.to_datetime(df['Trans Time'], format=datetime_format)
```

Create a travel time object. 
```python
    sample_travel_time = TravelTime(df)
```

Define the trip. 
```python
    trip_def = ['SB01', 'SB02', 'SB03', 'SB04', 'SB08', 'SB09', 'SB10']
```

Get travel times for the entire day.
```python
    travel_times = sample_travel_time.get_travel_time_all_day(trip_def)
```
