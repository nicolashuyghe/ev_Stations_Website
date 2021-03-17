import pandas as pd
import openrouteservice as ors
import folium
import geocoder
import streamlit as st
import requests
import datetime
from datetime import timedelta, time
from streamlit_folium import folium_static
from haversine import haversine

map_box_key = 'pk.eyJ1IjoiYmFraTU1IiwiYSI6ImNrbTIyc2J3ZDJhYm8ydnBsb3E2ODByejYifQ.xS8DYo0Hmvf9cIo5ptSeJw'
ors_key = '5b3ce3597851110001cf624830305b9b81ae4d4483dc86b374a6cc40'

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
    padding: 2rem 1rem;
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

data = pd.read_csv('tests/info_stations.csv')
dist_info = data.copy()

### Add new column distance
dist_info['distance'] = -1.0


###############################
######### SIDEBAR #############
###############################

st.sidebar.markdown("## Get directions")

#### Get adresse close to this point
paris_coord = [48.836743, 2.353442]  # [latitude, longitude]

start_address = st.sidebar.text_input("Start", "Le Wagon Paris")
geo_start = geocoder.mapbox(start_address, proximity=paris_coord, key=map_box_key)   # Conversion adresse en lat, lng (param proximity permet d'affiner le résultat)
start_longitude = geo_start.json['lng']
start_latitude = geo_start.json['lat']

dest_address = st.sidebar.text_input("Destination", "Le Louvre")
geo_dest = geocoder.mapbox(dest_address, proximity=paris_coord, key=map_box_key)
dest_longitude = geo_dest.json['lng']
dest_latitude = geo_dest.json['lat']

st.sidebar.markdown("## Schedule your departure")
date_util = st.sidebar.date_input("Time of departure", datetime.date(2021, 3, 20))
time_util = st.sidebar.time_input("Heure de prédiction de la disponibilité", datetime.time(hour=20, minute=00))


###############################
#### DISTANCE COMPUTATION #####
###############################

start_pos = ([start_latitude, start_longitude])
dest_pos = ([dest_latitude, dest_longitude])

# Compute distance as the crow flies between destination and each EV stations
for s_id in dist_info.index:
    dist_info['distance'][s_id] = haversine(dest_pos, (dist_info['latitude'][s_id], dist_info['longitude'][s_id]))

dist_info = dist_info.sort_values(by=['distance']).reset_index()

station1 = (dist_info['longitude'][0], dist_info['latitude'][0])
station2 = (dist_info['longitude'][1], dist_info['latitude'][1])
station3 = (dist_info['longitude'][2], dist_info['latitude'][2])

client = ors.Client(key=ors_key)
route_coord = [[start_longitude, start_latitude], [dest_longitude, dest_latitude]]

###############################
############ MAP ##############
###############################

# Title
st.markdown("<h1 style='text-align: center;'>Itinary to your destination</h1>", unsafe_allow_html=True)
st.markdown("<i class='far fa-charging-station'></i>", unsafe_allow_html=True)

# Location zoom map
center_long = (start_longitude + dest_longitude) / 2
center_lat = (start_latitude + dest_latitude) / 2

# Factor zoom_start
dist_zoom = haversine(start_pos, dest_pos)

# Display map
map_directions = folium.Map(location=[center_lat, center_long], zoom_start=13+(1/(dist_zoom)))
folium.TileLayer('cartodbpositron').add_to(map_directions)

# Add markers for start and destination on the map
folium.Marker([start_latitude, start_longitude], icon=folium.Icon(color='darkblue', icon='home')).add_to(map_directions)
folium.Marker([dest_latitude, dest_longitude], icon=folium.Icon(color='green', icon='glyphicon-screenshot')).add_to(map_directions)

# Add markers for closest stations
year = date_util.year
month = date_util.month
day = date_util.day
s_id = dist_info['s_id']
nb_terminal = []

# Terminal type choice
choice = st.sidebar.selectbox('Select your terminal type', ['Standard charging', 'Fast charging', 'Both'])

if choice == 'Standard charging':
    for i in range(3):
        rep = requests.get(f'https://ev-stations-docker-image-gcp-2-dzi5homvkq-ew.a.run.app/predict-type?station_id={s_id[i][1:]}&terminal_type=normal&year={year}&month={month}&day={day}&hour={time_util.hour}&minute={time_util.minute}').json()
        if rep['number_terminals_available'] == 0:
            nb_terminal.append(0)
            folium.Marker([dist_info['latitude'][i], dist_info['longitude'][i]],
                          tooltip=("No charger available"),
                          icon=folium.Icon(color='red', icon='glyphicon-remove-circle'))\
            .add_to(map_directions)
        elif rep['number_terminals_available'] == 1:
            nb_terminal.append(1)
            folium.Marker([dist_info['latitude'][i], dist_info['longitude'][i]],
                          tooltip=("1 terminal available"),
                          icon=folium.Icon(icon='glyphicon-ok-circle'))\
            .add_to(map_directions)
        elif rep['number_terminals_available'] == 2:
            nb_terminal.append(2)
            folium.Marker([dist_info['latitude'][i], dist_info['longitude'][i]],
                          tooltip=("2 terminals available"),
                          icon=folium.Icon(icon='glyphicon-ok-circle'))\
            .add_to(map_directions)
        elif rep['number_terminals_available'] == 3:
            nbr_ter.append(3)
            folium.Marker([dist_info['latitude'][i], dist_info['longitude'][i]],
                          tooltip=("3 terminals available"),
                          icon=folium.Icon(icon='glyphicon-ok-circle'))\
            .add_to(map_directions)
elif choice == 'Fast charging':
    for i in range(3):
        rep = requests.get(f'https://ev-stations-docker-image-gcp-2-dzi5homvkq-ew.a.run.app/predict-type?station_id={s_id[i][1:]}&terminal_type=fast&year={year}&month={month}&day={day}&hour={time_util.hour}&minute={time_util.minute}').json()
        if rep['number_terminals_available'] == 0:
            nb_terminal.append(0)
            folium.Marker([dist_info['latitude'][i], dist_info['longitude'][i]],
                          tooltip=("No charger available"),
                          icon=folium.Icon(color='red', icon='glyphicon-remove-circle'))\
            .add_to(map_directions)
        elif rep['number_terminals_available'] == 1:
            nb_terminal.append(1)
            folium.Marker([dist_info['latitude'][i], dist_info['longitude'][i]],
                          tooltip=("1 terminal available"),
                          icon=folium.Icon(icon='glyphicon-ok-circle'))\
            .add_to(map_directions)
        elif rep['number_terminals_available'] == 2:
            nb_terminal.append(2)
            folium.Marker([dist_info['latitude'][i], dist_info['longitude'][i]],
                          tooltip=("2 terminals available"),
                          icon=folium.Icon(icon='glyphicon-ok-circle'))\
            .add_to(map_directions)
        elif rep['number_terminals_available'] == 3:
            nb_terminal.append(3)
            folium.Marker([dist_info['latitude'][i], dist_info['longitude'][i]],
                          tooltip=("3 terminals available"),
                          icon=folium.Icon(icon='glyphicon-ok-circle'))\
            .add_to(map_directions)
elif choice == 'Both':
    for i in range(3):
        rep = requests.get(f'https://ev-stations-docker-image-gcp-2-dzi5homvkq-ew.a.run.app/predict?station_id={s_id[i][1:]}&year={year}&month={month}&day={day}&hour={time_util.hour}&minute={time_util.minute}').json()
        if rep['number_terminals_available'] == 0:
            nb_terminal.append(0)
            folium.Marker([dist_info['latitude'][i], dist_info['longitude'][i]],
                          tooltip=("No charger available"),
                          icon=folium.Icon(color='red', icon='glyphicon-remove-circle'))\
            .add_to(map_directions)
        elif rep['number_terminals_available'] == 1:
            nb_terminal.append(1)
            folium.Marker([dist_info['latitude'][i], dist_info['longitude'][i]],
                          tooltip=("1 terminal available"),
                          icon=folium.Icon(icon='glyphicon-ok-circle'))\
            .add_to(map_directions)
        elif rep['number_terminals_available'] == 2:
            nb_terminal.append(2)
            folium.Marker([dist_info['latitude'][i], dist_info['longitude'][i]],
                          tooltip=("2 terminals available"),
                          icon=folium.Icon(icon='glyphicon-ok-circle'))\
            .add_to(map_directions)
        elif rep['number_terminals_available'] == 3:
            nb_terminal.append(3)
            folium.Marker([dist_info['latitude'][i], dist_info['longitude'][i]],
                          tooltip=("3 terminals available"),
                          icon=folium.Icon(icon='glyphicon-ok-circle'))\
            .add_to(map_directions)

# Add driving routes
s1_driving_route = client.directions(coordinates=[[start_longitude, start_latitude], [station1[0], station1[1]]],
                                   profile='driving-car',
                                   format='geojson')
s2_driving_route = client.directions(coordinates=[[start_longitude, start_latitude], [station2[0], station2[1]]],
                                   profile='driving-car',
                                   format='geojson')
s3_driving_route = client.directions(coordinates=[[start_longitude, start_latitude], [station3[0], station3[1]]],
                                   profile='driving-car',
                                   format='geojson')

# Add walking routes
s1_walking_route = client.directions(coordinates=[[station1[0], station1[1]], [dest_longitude, dest_latitude]],
                                  profile='foot-walking',
                                  extra_info=["green"],
                                  format='geojson')
s2_walking_route = client.directions(coordinates=[[station2[0], station2[1]], [dest_longitude, dest_latitude]],
                                  profile='foot-walking',
                                  format='geojson')
s3_walking_route = client.directions(coordinates=[[station3[0], station3[1]], [dest_longitude, dest_latitude]],
                                  profile='foot-walking',
                                  format='geojson')


###############################
########### TABLE #############
###############################

# Driving and walking time computation
time_drive_s1 = round((s1_driving_route['features'][0]['properties']['summary']['duration'])/60)
time_walk_s1 = round((s1_walking_route['features'][0]['properties']['summary']['duration'])/60)
time_drive_s2 = round((s2_driving_route['features'][0]['properties']['summary']['duration'])/60)
time_walk_s2 = round((s2_walking_route['features'][0]['properties']['summary']['duration'])/60)
time_drive_s3 = round((s3_driving_route['features'][0]['properties']['summary']['duration'])/60)
time_walk_s3 = round((s3_walking_route['features'][0]['properties']['summary']['duration'])/60)
time_s1 = time_drive_s1 + time_walk_s1
time_s2 = time_drive_s2 + time_walk_s2
time_s3 = time_drive_s3 + time_walk_s3

# Computation of the shortest time
if nb_terminal[0] != 0:
    if (time_s1 < time_s2) and (time_s1 < time_s3):
        station_opt = 1
    elif (time_s2 < time_s1) and (time_s2 < time_s3):
        station_opt = 2
    elif (time_s3 < time_s1) and (time_s3 < time_s2):
        station_opt = 3
elif nb_terminal[1] != 0:
    if time_s2 < time_s3:
        station_opt = 2
    else:
        station_opt = 3
elif nb_terminal[2] != 0:
    station_opt = 3

station_util = st.sidebar.selectbox("Choose option", [1,2,3])

# Ajout route voiture + pied choix station
td_start = timedelta(hours=time_util.hour, minutes=time_util.minute)
td_s1 = timedelta(minutes=time_s1)
td_s2 = timedelta(minutes=time_s2)
td_s3 = timedelta(minutes=time_s3)
eta_s1 = td_start + td_s1
eta_s2 = td_start + td_s2
eta_s3 = td_start + td_s3

def strfdelta(tdelta):
    hours, remainder = divmod(tdelta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f'{hours}:{minutes}'

###############################
########### ROUTE #############
###############################

# Definition to change route color
def style_function(color):
    return lambda feature: dict(color=color,
                                opacity=0.5,
                                weight=4)


if station_util == 1:
    folium.GeoJson(s1_driving_route, name='s1_driving_route').add_to(map_directions)
    folium.GeoJson(s1_walking_route, name='s1_walking_route', style_function=style_function('   green')).add_to(map_directions)
    st.write(f"Your estimated time of arrival is {eta_s1}")
elif station_util == 2:
    folium.GeoJson(s2_driving_route, name='s2_driving_route').add_to(map_directions)
    folium.GeoJson(s2_walking_route, name='s2_walking_route', style_function=style_function('green')).add_to(map_directions)
    st.write(f"Your estimated time of arrival is {eta_s2}")
elif station_util == 3:
    folium.GeoJson(s3_driving_route, name='s3_driving_route').add_to(map_directions)
    folium.GeoJson(s3_walking_route, name='s3_walking_route', style_function=style_function('green')).add_to(map_directions)
    st.write(f"Your estimated time of arrival is {eta_s3}")

d_stations = {'Station': ['Option 1', 'Option 2', 'Option 3'],
              'Drive (in min)': [time_drive_s1, time_drive_s2, time_drive_s3],
              'Walk (in min)': [time_walk_s1, time_walk_s2, time_walk_s3],
              'Total (in min)': [time_s1, time_s2, time_s3],
              'Est. nb term.': [nb_terminal[0], nb_terminal[1], nb_terminal[2]],
              'ETA': [strfdelta(eta_s1), strfdelta(eta_s2), strfdelta(eta_s3)]}

df_stations = pd.DataFrame(data=d_stations).set_index('Station')

folium_static(map_directions)

st.write(df_stations)
