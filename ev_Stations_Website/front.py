import pandas as pd
import numpy as np
import openrouteservice as ors
import folium
import geocoder
import streamlit as st
import requests
import datetime
from streamlit_folium import folium_static
from haversine import haversine

map_box_key = 'pk.eyJ1Ijoibmh1eWdoZSIsImEiOiJja21lbjUyemUyd2w4MnlrbjMwMXkxMXJoIn0.cBH6JH_95xnmzms6phgI_g'
ors_key = '5b3ce3597851110001cf6248f94c4c0b04c64137b28f69cbff5fe979'

st.set_page_config(layout="centered")

st.markdown('<style>.stAlert{display:none;}</style>', unsafe_allow_html=True)

CSS = """
.st-dn {
    border-color: rgb(0,0,138);
}
.css-1y0tads {
    flex: 1 1 0%;
    width: 100%;
    padding: 0rem 5rem 0rem ;
}
.css-hi6a2p {
    flex: 1 1 0%;
    width: 100%;
    padding: 0rem 1rem 5rem;
    max-width: 730px;
}
.css-1aumxhk {
    background-color: rgb(0,0,138);
    background-image: linear-gradient(rgb(240, 242, 246), rgb(250, 250, 250));
    background-attachment: fixed;
    flex-shrink: 0;
    height: 100vh;
    overflow: auto;
    padding: 0rem 1rem;
    position: relative;
    transition: margin-left 300ms ease 0s, box-shadow 300ms ease 0s;
    width: 21rem;
    z-index: 100;
    margin-left: 0px;
}
"""

st.write(f'<style>{CSS}</style>', unsafe_allow_html=True)


###############################
######### LOAD DATA ###########
###############################

data = pd.read_csv('ev_Stations_Website/data/info_stations.csv')
dist_info = data.copy()

### Add new column distance
dist_info['distance'] = -1.0


###############################
######### SIDEBAR #############
###############################

st.sidebar.markdown("## Get directions")

#### Get adresse close to this point
paris_coord = [48.836743, 2.353442]  # [latitude, longitude]

# Start point
start_address = st.sidebar.text_input("Start", "Le Wagon Paris")
geo_start = geocoder.mapbox(start_address, proximity=paris_coord, key=map_box_key)
start_longitude = geo_start.json['lng']
start_latitude = geo_start.json['lat']

# Destination
dest_address = st.sidebar.text_input("Destination", "156 rue marcadet, 75018 Paris")
geo_dest = geocoder.mapbox(dest_address, proximity=paris_coord, key=map_box_key)
dest_longitude = geo_dest.json['lng']
dest_latitude = geo_dest.json['lat']

# Date and time
st.sidebar.markdown("## Schedule your departure")

row2_1, row2_2 = st.sidebar.beta_columns(2)
with row2_1:
    date_inputer = st.empty()
    date_start = date_inputer.date_input("Time of departure", datetime.date(2021, 3, 19))
with row2_2:
    time_inputer = st.empty()
    time_start = time_inputer.time_input("Hour of departure", datetime.time(hour=20, minute=00))

# Terminal choice
terminal_choice = st.sidebar.radio('Select your terminal type', ['Standard charging', 'Fast charging', 'Both'])

# Number of options and option choice
row2_1, row2_2 = st.sidebar.beta_columns(2)
with row2_1:
    nb_option_inputer = st.empty()
    n = nb_option_inputer.number_input("Number of options", min_value= 3, max_value= 10, step=1)
with row2_2:
    option_choice_inputer = st.empty()
    option_choice = option_choice_inputer.selectbox("Choose option", range(1, n+1))


###############################
#### DISTANCE COMPUTATION #####
###############################

start_pos = ([start_latitude, start_longitude])
dest_pos = ([dest_latitude, dest_longitude])

# Compute distance as the crow flies between destination and each EV stations
for s_id in dist_info.index:
    dist_info['distance'][s_id] = haversine(dest_pos, (dist_info['latitude'][s_id], dist_info['longitude'][s_id]))

# Define the three closest stations from destination
dist_info = dist_info.sort_values(by=['distance']).reset_index()


closest_stations = []
for i in range(n):
    closest_stations.append((dist_info['longitude'][i], dist_info['latitude'][i]))


###############################
############ MAP ##############
###############################

client = ors.Client(key=ors_key)
route_coord = [[start_longitude, start_latitude], [dest_longitude, dest_latitude]]

# Title
st.markdown("<h1 style='text-align: center;'>Itinary to your destination</h1>", unsafe_allow_html=True)

# Location zoom map
center_long = (start_longitude + dest_longitude) / 2
center_lat = (start_latitude + dest_latitude) / 2
dist_zoom = haversine(start_pos, dest_pos)

# Display map
map_directions = folium.Map(location=[center_lat, center_long], zoom_start=13+(1/(dist_zoom)))
folium.TileLayer('cartodbpositron').add_to(map_directions)

# Add markers for start and destination on the map
folium.Marker([start_latitude, start_longitude], icon=folium.Icon(color='darkblue', icon='home')).add_to(map_directions)
folium.Marker([dest_latitude, dest_longitude], icon=folium.Icon(color='green', icon='glyphicon-screenshot')).add_to(map_directions)


###############################
####### COMPUTATION ###########
###############################

# Compute driving routes
driving_routes = []
for i in range(n):
    driving_routes.append(client.directions(coordinates=[[start_longitude, start_latitude], [closest_stations[i][0], closest_stations[i][1]]],
                                   profile='driving-car',
                                   format='geojson'))

# Compute walking routes
walking_routes = []
for i in range(n):
    walking_routes.append(client.directions(coordinates=[[closest_stations[i][0], closest_stations[i][1]], [dest_longitude, dest_latitude]],
                                  profile='foot-walking',
                                  format='geojson'))

# Computation driving, walking and total times
times_drive = []
times_walk = []
times_total = []
for i in range(n):
    t_drive = round((driving_routes[i]['features'][0]['properties']['summary']['duration'])/60)
    t_walk = round((walking_routes[i]['features'][0]['properties']['summary']['duration'])/60)
    t_total = t_drive + t_walk
    times_drive.append(t_drive)
    times_walk.append(t_walk)
    times_total.append(t_total)


# Compute ETA
etas = []
start_datetime = datetime.datetime.combine(date_start, time_start)
for i in range(n):
    etas.append(start_datetime + datetime.timedelta(minutes=times_total[i]))

print(etas[0])

# Add markers for closest stations
s_id = dist_info['s_id']
nb_terminals = []

if terminal_choice == 'Standard charging':
    for i in range(n):
        resp = requests.get(f'https://ev-stations-docker-image-gcp-2-dzi5homvkq-ew.a.run.app/predict-type?station_id={s_id[i][1:]}&terminal_type=normal&year={etas[i].year}&month={etas[i].month}&day={etas[i].day}&hour={etas[i].hour}&minute={etas[i].minute}').json()
        if resp['number_terminals_available'] == 0:
            number_terminals_available = resp['number_terminals_available']
            nb_terminals.append(number_terminals_available)
            folium.Marker([dist_info['latitude'][i], dist_info['longitude'][i]],
                          tooltip=(f"Estimated number of terminal(s) available: {number_terminals_available}"),
                          icon=folium.Icon(color='red', icon='glyphicon-remove-circle'))\
                .add_to(map_directions)
        elif resp['number_terminals_available'] > 0:
            number_terminals_available = resp['number_terminals_available']
            nb_terminals.append(number_terminals_available)
            folium.Marker([dist_info['latitude'][i], dist_info['longitude'][i]],
                          tooltip=(f"Estimated number of terminal(s) available: {number_terminals_available}"),
                          icon=folium.Icon(icon='glyphicon-ok-circle'))\
                .add_to(map_directions)

elif terminal_choice == 'Fast charging':
    for i in range(n):
        resp = requests.get(f'https://ev-stations-docker-image-gcp-2-dzi5homvkq-ew.a.run.app/predict-type?station_id={s_id[i][1:]}&terminal_type=fast&year={etas[i].year}&month={etas[i].month}&day={etas[i].day}&hour={etas[i].hour}&minute={etas[i].minute}').json()
        if resp['number_terminals_available'] == 0:
            number_terminals_available = resp['number_terminals_available']
            nb_terminals.append(number_terminals_available)
            folium.Marker([dist_info['latitude'][i], dist_info['longitude'][i]],
                          tooltip=(f"Estimated number of terminal(s) available: {number_terminals_available}"),
                          icon=folium.Icon(color='red', icon='glyphicon-remove-circle'))\
                .add_to(map_directions)
        elif resp['number_terminals_available'] > 0:
            number_terminals_available = resp['number_terminals_available']
            nb_terminals.append(number_terminals_available)
            folium.Marker([dist_info['latitude'][i], dist_info['longitude'][i]],
                          tooltip=(f"Estimated number of terminal(s) available: {number_terminals_available}"),
                          icon=folium.Icon(icon='glyphicon-ok-circle'))\
                .add_to(map_directions)

elif terminal_choice == 'Both':
    for i in range(n):
        resp = requests.get(f'https://ev-stations-docker-image-gcp-2-dzi5homvkq-ew.a.run.app/predict?station_id={s_id[i][1:]}&year={etas[i].year}&month={etas[i].month}&day={etas[i].day}&hour={etas[i].hour}&minute={etas[i].minute}').json()
        if resp['number_terminals_available'] == 0:
            number_terminals_available = resp['number_terminals_available']
            nb_terminals.append(number_terminals_available)
            folium.Marker([dist_info['latitude'][i], dist_info['longitude'][i]],
                          tooltip=(f"Estimated number of terminal(s) available: {number_terminals_available}"),
                          icon=folium.Icon(color='red', icon='glyphicon-remove-circle'))\
                .add_to(map_directions)
        elif resp['number_terminals_available'] == 1:
            number_terminals_available = resp['number_terminals_available']
            nb_terminals.append(number_terminals_available)
            folium.Marker([dist_info['latitude'][i], dist_info['longitude'][i]],
                          tooltip=(f"Estimated number of terminal(s) available: {number_terminals_available}"),
                          icon=folium.Icon(icon='glyphicon-ok-circle'))\
                .add_to(map_directions)

# Define index order given number of terminals available and total time
sort_index = []
unavailable_index = []
for i in np.argsort(times_total):
    if nb_terminals[i] > 0:
        sort_index.append(i)
    elif nb_terminals[i] == 0:
        unavailable_index.append(i)
sort_index += unavailable_index


# Reorder lists
driving_routes_sorted = []
walking_routes_sorted = []
times_drive_sorted = []
times_walk_sorted = []
times_total_sorted = []
etas_sorted = []
nb_terminals_sorted = []
for i in sort_index:
    driving_routes_sorted.append(driving_routes[i])
    walking_routes_sorted.append(walking_routes[i])
    times_drive_sorted.append(times_drive[i])
    times_walk_sorted.append(times_walk[i])
    times_total_sorted.append(times_total[i])
    etas_sorted.append(etas[i])
    nb_terminals_sorted.append(nb_terminals[i])


###############################
######## PLOT ROUTES ##########
###############################

# Definition to change route color
def style_function(color):
    return lambda feature: dict(color=color,
                                opacity=0.5,
                                weight=4)

st.markdown(f"Your estimated time of arrival is **{etas_sorted[option_choice-1].hour}:{etas_sorted[option_choice-1].minute}**.\
    To get to your destination, you will have {times_drive_sorted[option_choice-1]}min car :car: and {times_walk_sorted[option_choice-1]}min walk :walking:")

folium.GeoJson(driving_routes_sorted[option_choice-1], name='driving_route').add_to(map_directions)
folium.GeoJson(walking_routes_sorted[option_choice-1], name='walking_route', style_function=style_function('green')).add_to(map_directions)

dict_df = {'Option': [f'Option {i+1}' for i in range(n)],
            'Drive (in min)': times_drive_sorted,
            'Walk (in min)': times_walk_sorted,
            'Total (in min)': times_total_sorted,
            'Est. nb term.': nb_terminals_sorted,
            'ETA': [f'{eta.hour}:{eta.minute}' for eta in etas_sorted]}

df_stations = pd.DataFrame(data=dict_df).set_index('Option')

folium_static(map_directions)

st.write(df_stations)
