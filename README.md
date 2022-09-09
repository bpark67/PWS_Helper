# PWS_Helper
This is a Python package that contains helper functions to process PWS(Public Water Systems) IDs and extract Latitude and Longitude information. It uses the `BeautifulSoup` package to retrieve addresses from the [EPA Safe Drinking Water Information System](https://www.epa.gov/enviro/sdwis-search). Then, using `GeoPy` and **Nominatim**, a geocoding software used by OpenStreetMap, it extracts Lat/Long from said address. If the address search fails at the street level, the package by default refers to the city/county level address. If that search fails as well, the package offers another function that uses the postal code instead. If all of these steps fail, addresses can be manually entered and translated into Lat/Long.

The package either allows users to enter a single **PWSID** or a `Pandas` dataframe with a column titled **PWSID**. In the former case, it returns a tuple of Latitude and Longitude, and in the latter case, it appends two columns, Latitude and Longitude, to the dataframe.

## Required Packages

- `GeoPy` and `Pgeocode`
- `Pandas`
- `NumPy`
- `BeautifulSoup`

## Documentation

### Parser

The `Parser` module consists of two functions: `parse_html_table()` and `pandafier()`. Users will not have to use this module. It contains functions necessary for the `Locator` module.

#### parse_html_table(table)

This function is cited from this [page](https://srome.github.io/Parsing-HTML-Tables-in-Python-with-BeautifulSoup-and-pandas/). It converts tables in HTML to a `pandas` dataframe.

#### pandafier(pwsid, state)

This function takes a PWSID and two letter state abbreviation as an input. It then searches the [EPA Safe Drinking Water Information System](https://www.epa.gov/enviro/sdwis-search) and returns a `pandas` dataframe of the tabulated address by invoking the `parse_html_table` function. If the connection fails, the function returns `None`.

### Locator

#### get_address(frame, state)

This function takes a dataframe **that contains a PWSID column**, and the corresponding two letter state abbreviation as an input. By invoking `parser.pandafier()`, it returns a Python dictionary with the PWSIDs as keys, and the addresses in `pandas` dataframe form as values. 

#### latlonger(address)

This function takes an address in string form and returns a tuple of (Latitude, Longitude). It uses the `GeoPy` package and Nominatim, a geocoding software that is used by OpenStreetMap. If the address search fails, it returns `nan`.

#### convert(address_str)

This function takes a Python dictionary with PWSIDs as keys and addresses in strings as values. By invoking the `latlonger()` function, it reassigns the (Latitude, Longitude) tuple to each key, and then converts the dictionary into a pandas dataframe with three columns: PWSID, Latitude, and Longitude

#### frame_latlonger(frame, stateabb, statefull)

This function takes a `pandas` dataframe with a PWSID column, a state abbreviation(e.g. "WI"), and the full name of that state(e.g. "Wisconsin"). Invoking the `get_address`, `latlonger`, and `convert` function, it appends two columns of Latitude and Longitude to the dataframe that is given.

If the street level address search fails, it automatically runs the search once more using only the city/county level address. If that fails as well, it will print out a message that there are still missing entries, and return a list. 

- The first entry of the list is the final dataframe with `nan` for missing Latitudes and Longitudes
- The second entry of the list is the "missing" dataframe, only containing the rows with missing Latitudes and Longitudes

#### postal_coder(frame, missing, stateabb)

This function takes the result of `frame_latlonger` as input. It takes `pandas` dataframe with a PWSID column (the first return value from `frame_latlonger`), a "missing" dataframe (the second return value from `frame_latlonger`), and the state abbreviation. 

For the missing entries, it re-searches the PWSID Safe Drinking Water Information System, and attempts to retrieve the 5 digit postal code of the water system. If that search succeeds, it uses the `Pgeocode` package and Nominatim to retrieve Latitude and Longitude information.

If this search fails, it will print out a message that there are still missing entries, and return a list. 

- The first entry of the list is the final dataframe with `nan` for missing Latitudes and Longitudes
- The second entry of the list is the "missing" dataframe, only containing the rows with missing Latitudes and Longitudes

#### manual_filler(frame, manual_dict)

In case all automatic searches failed, this function allows users to input addresses that are known to work on Nominatim(and OpenStreetMap). The function takes the dataframe(with missing entries) and a Python dictionary, having PWSIDs of missing entries as keys and working addresses as values. It then invokes the `latlonger` function to fill in the missing entries.
