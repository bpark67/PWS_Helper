from geopy.geocoders import Nominatim
import pandas as pd
import numpy as np
import pgeocode
import pws_helper.parser as parser

locator = Nominatim(user_agent="myGeocoder")


def latlonger(address):
    """This function takes an address as an input and returns the latitude and longitude into a list"""
    latlong_tuple = locator.geocode(address, timeout=None)

    return (
        [latlong_tuple.point[0], latlong_tuple.point[1]]
        if latlong_tuple != None
        else np.nan
    )


def get_address(frame, state):
    """This function returns address info from a Data Frame containing PWS IDs"""
    address = {}
    for id in frame.PWSID:
        address[id] = parser.pandafier(id, state)
    return address


def convert(address_str):
    """This function returns a data frame of PWS ID and Lat Long"""
    convert = {k: latlonger(v[0]) for k, v in address_str.items() if v[0] != None}

    converted = pd.DataFrame(convert).T

    converted["PWSID"] = converted.index

    converted.columns = ["Latitude", "Longitude", "PWSID"]

    return converted


def frame_latlonger(frame, stateabb, statefull):
    """This function takes the data frame with PWSID, and the corresponding statenames
    In turn, it first retrieves the lat long data corresponding to the PWSID
    If there are any missing Lat Longs, it reformats the address to the county/city level
    If there are still missing entries, it returns those as well for manual formatting.
    """
    address = get_address(frame, stateabb)
    address_str = {}

    ## Format Addresses so that P.O. Boxes are removed
    for item in address:
        if isinstance(address[item], pd.DataFrame):
            if (
                address[item]
                .iloc[1]
                .str.lower()
                .str.replace(".", "")
                .str.replace(" ", "")
                .str.contains("po")[0]
            ):
                address_str[item] = (
                    address[item].iloc[2].str.replace(", " + stateabb, ", " + statefull)
                )
            elif (address[item].iloc[1] == "")[0]:
                address_str[item] = (
                    address[item].iloc[2].str.replace(", " + stateabb, ", " + statefull)
                )
            else:
                address_str[item] = (
                    address[item].iloc[1]
                    + ", "
                    + address[item]
                    .iloc[2]
                    .str.replace(", " + stateabb, ", " + statefull)
                )

    ## Get Initial Lat Long
    converted = convert(address_str)

    ## Join the Lat Long to the input frame
    with_location = frame.merge(converted, on="PWSID", how="left")

    ## Check if there are missing entries
    missing = with_location[with_location.Latitude.isnull()]

    if len(missing) == 0:
        return with_location

    else:
        for pws in missing.PWSID:
            if isinstance(address_str[pws], pd.DataFrame):
                address_str[pws] = (
                    address[pws].iloc[2].str.replace(", " + stateabb, ", " + statefull)
                )
        converted = convert(address_str)
        with_location = frame.merge(converted, on="PWSID", how="left")

        still_missing = with_location[with_location.Latitude.isnull()]
        if len(still_missing) == 0:
            return with_location
        else:
            print(
                "There are missing entries. Please fill spots with the postalcoder function"
            )
            return [with_location, still_missing]


def manual_filler(frame, manual_dict):
    """This function takes a dictionary in the form of {PWSID: "Address that works"} and fills in missing spots in the given frame"""
    for key in manual_dict:
        latlong = latlonger(manual_dict[key])
        frame.Latitude[frame.PWSID == key] = latlong[0]
        frame.Longitude[frame.PWSID == key] = latlong[1]

    return frame


def postalcoder(frame, missing, stateabb):
    """This function takes the entire frame(with missing pieces), the missing frame, and the state ID
    In turn, it fills in the missing spots with postal code if applicabl
    """
    nomi = pgeocode.Nominatim("us")

    address = get_address(missing, stateabb)

    for pwsid in address:
        postal_code = address[pwsid].iloc[2][0][-5:]
        # Deal with 9 digit zip codes
        if postal_code.startswith("-"):
            postal_code = address[pwsid].iloc[2][0][-10:-5]
        if len(postal_code) == 5 and postal_code.isdigit():
            info = nomi.query_postal_code(postal_code)
            frame.Latitude[frame.PWSID == pwsid] = info.latitude
            frame.Longitude[frame.PWSID == pwsid] = info.longitude

    still_missing = frame[frame.Latitude.isnull()]

    if len(still_missing) == 0:
        return frame
    else:
        print(
            "There are still missing entries. Please fill manually with manual_filler"
        )
        return [frame, still_missing]
