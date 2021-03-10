# -*- coding: utf-8 -*-
# Copyright 2018-2019 Streamlit Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""An example of showing geographic data."""

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import pydeck as pdk

# SETTING PAGE CONFIG TO WIDE MODE
st.set_page_config(layout="wide")

# LOADING DATA
DATE_TIME = "date/time"
DATA_URL = (
    "http://s3-us-west-2.amazonaws.com/streamlit-demo-data/uber-raw-data-sep14.csv.gz"
)

DATA_PATH = 'data/historical_nb_charging.csv'
DATE_COL = 'timestamp'

@st.cache(persist=True)
def load_data(nrows):
    data = pd.read_csv(DATA_PATH, nrows=nrows)
    lowercase = lambda x: str(x).lower()
    data.rename(lowercase, axis="columns", inplace=True)
    data[DATE_COL] = pd.to_datetime(data[DATE_COL])
    return data

data = load_data(24*4*7)

# CREATING FUNCTION FOR MAPS

def map(data, lat, lon, zoom):
    st.write(pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
        initial_view_state={
            "latitude": lat,
            "longitude": lon,
            "zoom": zoom,
            "pitch": 50,
        },
        layers=[
            pdk.Layer(
                "HexagonLayer",
                data=data,
                get_position=["longitude", "latitude"],
                radius=100,
                elevation_scale=10000,
                elevation_range=[0, 3],
                pickable=True,
                extruded=True,
            ),
        ]
    ))

# LAYING OUT THE TOP SECTION OF THE APP
row1_1, row1_2 = st.beta_columns((2,3))

with row1_1:
    st.title("EV Stations - Number of vehicules charging")
    hour_selected = st.slider("Select hour", 0, 23)

with row1_2:
    st.write(
    """
    ##
    Examining how the evolution of the number of terminals charging by EV stations in Paris.
    By sliding the slider on the left you can view different slices of time.
    """)

# FILTERING DATA BY HOUR SELECTED
data = data[data[DATE_COL].dt.hour == hour_selected]

# LAYING OUT THE MIDDLE SECTION OF THE APP WITH THE MAPS
row2_1, row2_2, row2_3 = st.beta_columns((3,1,1))

# SETTING THE ZOOM LOCATIONS FOR THE AIRPORTS
paris_center = [48.8534, 2.3488]
paris_16 = [48.853575, 2.2685297]
eiffel_tower = [48.8582602, 2.2944991]
zoom_level = 12

with row2_1:
    st.write("**Paris from %i:00 and %i:00**" % (hour_selected, (hour_selected + 1) % 24))
    map(data, paris_center[0], paris_center[1], 11)

with row2_2:
    st.write("**Paris 16e**")
    map(data, paris_16[0],paris_16[1], zoom_level)

with row2_3:
    st.write("**Eiffel Towar**")
    map(data, eiffel_tower[0], eiffel_tower[1], zoom_level)

# # FILTERING DATA FOR THE HISTOGRAM
# filtered = data[
#     (data[DATE_TIME].dt.hour >= hour_selected) & (data[DATE_TIME].dt.hour < (hour_selected + 1))
#     ]

# hist = np.histogram(filtered[DATE_TIME].dt.minute, bins=60, range=(0, 60))[0]

# chart_data = pd.DataFrame({"minute": range(60), "pickups": hist})

# # LAYING OUT THE HISTOGRAM SECTION

# st.write("")

# st.write("**Breakdown of rides per minute between %i:00 and %i:00**" % (hour_selected, (hour_selected + 1) % 24))

# st.altair_chart(alt.Chart(chart_data)
#     .mark_area(
#         interpolate='step-after',
#     ).encode(
#         x=alt.X("minute:Q", scale=alt.Scale(nice=False)),
#         y=alt.Y("pickups:Q"),
#         tooltip=['minute', 'pickups']
#     ).configure_mark(
#         opacity=0.5,
#         color='red'
#     ), use_container_width=True)
