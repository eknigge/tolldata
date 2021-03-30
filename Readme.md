# Introduction
The purpose of this module is to automate and standardize process of toll data by using `Pandas` `DataFrames`. It consists of a `Transaction`, `Trip`, `Rate Assignment`, `AVI Validation`, `AVI Test`, and `Plate Combinatorics` classes. Those are described in `Docs.me` file.
# Transaction Files
Transaction files are one of the most common data formats for toll data. This class can process both excel and csv files, but xlsm or xls files. When the files are imported several private methods process the data fields and allow the files to be exported as `DataFrames` or as a `csv` file.

# Trip Files
This class inherits the methods and functionality from the `TransactionFile` class, but uses different dictionarys and naming conventions since the data fields are named different between the two files. 

# Rate Assign 520
This class allows the creation of a rate file object that computes and stores the rate for a particular transaction given the following values:
- Datetime
- Transaction type
- Axles
- Status
- Pay-by-Mail status
- Holidays 

Both the `base rate` and `final rate` can be queried. 

# Rate Assign 99
This class inherits from the 520 class but uses the rate table information for the SR 99 facility. Since these two roadways operate nearly identically there are no other changes between these classes.

# Plate Combinatorics
This class provides a simple way of determining a set of possible OCR mistakes from common errors. For example, the value of `B` is often mistaken for the numerical value of `8`. A plate with a value of `88` would return the combinations of `BB`, `B8`, `8B`, and `88`. This process is executed for arbitrarily complex plates, using a lookup table of common errors. 

# AVI Validation
This class tests whether a plate is read without a tag. The read threshold, which represents the number of times a plate and tag are seen together can be set to constrain which transactions are flagged. The input `DataFrame` is required to have the following fields:
- TAG_ID, represending the transponder ID
- PLATE, for the plate value without state identifier
- TRX_ID, for the transaction identification number

The output `DataFrame` includes the new fields `AVI_MISMATCH` set to `True` or `False`, and if the value of `AVI_MISMATCH` is `True`, the field `MISSED_TAG_ID` for the ID of the missed tag.

A `csv` file can be used to as a lookup `dictionary`, or it can be generated automatically. The API also allows users to state whether they want to use a static dictionary that is not updated based, or one that is updated with the data processed.

# AVI Test
This class performs an AVI validation test, which is similar to the `AVI Validation`, but made to be more extensible and repeatable since repeated tests are required for a statistically significant sample. A minimum of 30 days of data is required, but more is recommended. This recommendation is based on a test duration of at least two weeks and previous experience. 

The test takes some time to execute since it works by importing the data and creating a single `DataFrame` object, and exporting it to a `pkl` file. If a previous `pkl` file exists this process is skipped. 

The process works as follows: 
1. Import files for analysis, or using existing data
2. Select random start date
3. Build plate/tag dictionary
4. Run AVI Validation test and compute metrics

This analysis can be repeated a desired number of times and the `get_test_result` method can be used to aggregate this information.
