# SatSpy 1.0
A simple GUI implementation of the popular Satellite tracking website [N2YO.com](N2YO.com)

_**Note:**_ [N2YO.com](N2YO.com) provides a REST API used in this project that requires an API Key obtained through the website. (However, an API key is provided by default with a maximum of 1000 requests/hour)

![Screen Shot 2023-07-09 at 1 02 33 AM](https://github.com/MinaBasem/SatSpy/assets/42482261/f3227968-1a9b-4e05-bef6-2f28dd60d8ed)

## Features:
  - Search for satellites by Name or NORAD ID
  - Provide a brief description of the satellite, mission objectives, etc.
  - Provide a range of identification information such as International Code, Period (time of 1 spin taken by satellite around earth) and general information such as launch site
  - Realtime satellite tracking through a widget made by N2YO which utilizes Folium (a LeafletJS Wrapper for Python) [openly available on their website]
      - N2YO widget displays the Map as well as telemetric information of satellite being tracked, and a table that displays the next satellite sightings around the user's location
  - More features will be added in the following versions

## Upcoming features:
  - API input text box to allow individual users to link personal API key
  - Threading might be considered to reduce map load time
  - Switching between different map tiles (styles)
  - Watchlist
  - Projected telemetry graphs for the next N hours

## How it works:
### Libraries:
  - JSON
  - OS
  - RE
  - SYS
  - GeoCoder
  - Pandas
  - PyQt5 (and other branching libraries)
  - Matplotlib
  - Functools
  - Operator
  - BeautifulSoup

### Functions:
A few functions are used to obtain different information and load the map into PyQt5 GUI elements

  - `searchButtonFunc()`:
      - Extracts text typed (or option from dropdown) in GUI searchbox element
      - NORAD ID from selected option is passed down to argument `obtainData()` (referred to below)
      - 2 files are created:
        - `telemetry.txt`: stores a list of projected coordinates for the next 3 hours
        - `altitudes.txt`: stores a list of projected altitude for the next 3 hours

  - `get_satellite_details(url)`:
      - Takes an argument of 1 url:  "https://www.n2yo.com/satellite/?s=NORAD_ID" where satellite NORAD ID is concatenated at the end to obtain the following data:
        - Description
        - Name
        - NORAD ID
        - International Code
        - Period (time taken for 1 loop around orbit)
        - Launch site
      - The above details are then stored into several variables which are later used to update GUI table placeholders.
   
  - `obtainData(NORAD_ID)`:
      - Retrieves user location
      - A request is made to the following url: "https://api.n2yo.com/rest/v1/satellite/positions/NORAD_ID/USER_LOCATION_LATITUDE/USER_LOCATION_LONGITUDE/0/10800/&apiKey=API_KEY"
        - The above API request returns a JSON response that is saved in `'location.json`, the response is as follows:
```          {
  "info": {
    "satname": "SPACE STATION",
    "satid": 25544,
    "transactionscount": 5
  },
  "positions": [
    {
      "satlatitude": -39.90318514,
      "satlongitude": 158.28897924,
      "sataltitude": 417.85,
      "azimuth": 254.31,
      "elevation": -69.09,
      "ra": 44.77078138,
      "dec": -43.99279118,
      "timestamp": 1521354418
    },
    {
      "satlatitude": -39.86493451,
      "satlongitude": 158.35261287,
      "sataltitude": 417.84,
      "azimuth": 254.33,
      "elevation": -69.06,
      "ra": 44.81676119,
      "dec": -43.98086419,
      "timestamp": 1521354419
    }
  ]
}
```
  - Note that the 10800 in the request url denotes the number of seconds for projected trajectory a user would need (in project case 3 hours)
  - The results are then filtered and broken down into 3 variables: `sat_latitudes`, `sat_longitudes` and `sat_altitude`.


Any contributions are appreciated.









