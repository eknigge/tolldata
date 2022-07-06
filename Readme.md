# Introduction
The purpose of this module is to import, summarize, analyze, and export toll data and analysis. Pandas and numpy libraries are used extensively. 

## Transaction Files
Transaction files are the most basic storage unit of toll data and contain information such as time of travel, axle count, transponder (if present), license plate, etc. Both Excel and csv files can be processed, and data is exported in memory as a DataFrame or to disk as a csv file. 

## Trip Files
Trip files contain similar information to transaction files, but have a few differences. The trip files contain the fare assigned to a trip, as well as the final OCR value that will be sent to the customer service system. Toll trips will multiple toll transactions have transaction information aggregated by a trip ID. 

## Rate Assignment
Rate assignment is relatively straightforward for time-of-day facilities. If you know the following parameters you can assign a value. 
- Datetime
- Transaction type
- Axles
- Transponder/Tag Status
- Pay-by-Mail status
- Holidays 

One exception is that it is not possible to know whether a vehicle will be pay by plate or pay by mail, so this can be assigned using a probability model, or assigned the default pay by mail rate. 

## Plate Combinatorics
This class provides a simple way of determining a set of possible OCR mistakes from common errors. For example, the value of `B` is often mistaken for the numerical value of `8`. A plate with a value of `88` would return the combinations of `BB`, `B8`, `8B`, and `88`. This process is executed for arbitrarily complex plates, using a lookup table of common errors. 

## AVI Validation
This class performs automated AVI testing, essentially whether a plate is read without its associated tag. The read threshold, which represents the number of times a plate and tag are seen together can be set to constrain the number of errors detected.  The input data is required to have the following fields and be in csv of excel format:
- **TAG_ID**, represending the transponder ID
- **PLATE**, for the plate value without state identifier
- **TRX_ID**, for the transaction identification number

The output includes the new fields **AVI_MISMATCH** set to `True` or `False` based on the result of the test, and the field **MISSED_TAG_ID** for the ID of the missed tag, if applicable.

A csv file can be used to as a lookup dictionary, or the dictionary can be genereated as the analysis is performed. The API also allows users to state whether they want to use a static dictionary that is **not** updated as the test progress, or one that is continuously updated. 

## AVI Test
This class performs an AVI validation test, which is similar to the `AVI Validation`, but made to be more extensible and easier to repeat tests. A minimum of 30 days of data is required, without modifying the source. This is based on previous experience, and that a large statistical sample is required for better validation. 

The test takes some time to execute since it imports a large number of files. The results of the first run are exported ot a `.pkl` file. If an existing `.pkl` file exists this step can be skipped, and the runtime is reduced. 

The process works as follows: 
1. Import files for analysis, or using existing data
2. Select random start date
3. Build plate/tag dictionary
4. Run AVI Validation test and compute metrics

This analysis can be repeated a desired number of times and the `get_test_result` method can be used to aggregate this information.


## Travel Time
This module provides accurate travel times for user-defined trips. It does so by calculating all node-to-node travel, and then the total travel time based on the specified trip. The provided dataframe needs to include: unique trip identifiers, datetime information, and node names. Once a `TravelTime` object is created, travel 
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

## Trip Builder
This module allows the grouping of transactions into trips. It takes in a Pandas DataFrame and requires transaction ID, datetime, plaza, transponder ID, and plate ID fields. This class includes detailed logging that can be enabled.

Using this class is very simple. First define a list of exit nodes. The exit nodes define locations where trips automatically end. The example exit notes are from a real-world system. 

```python
    import TripBuilder as tb
    df = [DataFrame]
    exit_nodes = ['NB10', 'NB05', 'SB06', 'SB10', 'SB11']
```

Import the dataframe and create a `TripBuilder` object
```python
    build = tb.TripBuilder(df, exit_nodes=exit_nodes)
```

Run the build and get the results
```python
    build = tb.TripBuilder(df, exit_nodes=exit_nodes)
    build.build_trips()
    df_result = build.get_dataframe()
```

# Testing
To test this module run `python -m pytest` in the toll level directory `tolldata`. This will execute the tests scripts for the various modules. While the tests are not very extensive they should be able to catch major errors from changes. 
