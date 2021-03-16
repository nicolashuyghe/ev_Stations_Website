import pandas as pd
import datetime
import openrouteservice as ors
import folium
import geocoder
import streamlit as st
import requests
from streamlit_folium import folium_static
from haversine import haversine

map_box_key = 'pk.eyJ1IjoiYmFraTU1IiwiYSI6ImNrbTIyc2J3ZDJhYm8ydnBsb3E2ODByejYifQ.xS8DYo0Hmvf9cIo5ptSeJw'
ors_key = '5b3ce3597851110001cf624830305b9b81ae4d4483dc86b374a6cc40'

st.set_page_config(layout="centered")

# Données 91 stations:


data = pd.read_csv('info_stations.csv')
dist_info = data.copy()
dist_info['distance'] = -1.0

# Load fichier css


# def local_css(file_name):
#     with open(file_name) as f:
#         st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


# local_css("test.css")


st.sidebar.markdown("## Itinéraire")
paris_coord = [48.836743, 2.353442]  # [latitude, longitude]


emp_adresse = st.sidebar.text_input("Départ ", "74 Av. des Champs-Élysées, 75008 Paris, France")
geo = geocoder.mapbox(emp_adresse, proximity=paris_coord, key=map_box_key)   # Conversion adresse en lat, lng (param proximity permet d'affiner le résultat)
emp_longitude = geo.json['lng']
emp_latitude = geo.json['lat']

dest_adresse = st.sidebar.text_input("Arrivée", "26 Avenue New York, 75016 Paris")
geo2 = geocoder.mapbox(dest_adresse, proximity=paris_coord, key=map_box_key)
dest_longitude = geo2.json['lng']
dest_latitude = geo2.json['lat']

st.sidebar.text(" \n")
st.sidebar.text(" \n")
st.sidebar.text(" \n")
st.sidebar.text(" \n")

st.sidebar.markdown("## Prédiction")
date_util = st.sidebar.date_input("Date de prédiction de la disponibilité",
                                  datetime.date(2021, 3, 20))
station_util = st.sidebar.number_input('Station', 0, 3, 0, 1)


# Calcul distance entre point arrivé et les 91 stations:


client_pos = ([dest_latitude, dest_longitude])

for i in dist_info.index:
    res = haversine(client_pos, (dist_info['latitude'][i], dist_info['longitude'][i]))
    dist_info['distance'][i] = res

dist_info = dist_info.sort_values(by=['distance']).reset_index()
station1 = (dist_info['longitude'][0], dist_info['latitude'][0])
station2 = (dist_info['longitude'][1], dist_info['latitude'][1])
station3 = (dist_info['longitude'][2], dist_info['latitude'][2])

client = ors.Client(key=ors_key)

coord = [[emp_longitude, emp_latitude], [dest_longitude, dest_latitude]]

# route = client.directions(coordinates=coord,
#                           profile='driving-car',
#                           format='geojson')

st.markdown("<h1 style='text-align: center;'>Itinéraire du trajet</h1>", unsafe_allow_html=True)

st.text(" \n")
st.text(" \n")


# map


long = (emp_longitude + dest_longitude) / 2
lat = (emp_latitude + dest_latitude) / 2

map_directions = folium.Map(location=[lat, long],
                            zoom_start=14)
folium.TileLayer('cartodbpositron').add_to(map_directions)


# route dans map


#folium.GeoJson(route, name='route').add_to(map_directions)


# ajout points emplacement + destination


folium.Marker([emp_latitude, emp_longitude]).add_to(map_directions)
folium.Marker([dest_latitude, dest_longitude]).add_to(map_directions)


# ajoute points stations plus proches (haversine)


year = date_util.year
month = date_util.month
day = date_util.day
s_id = dist_info['s_id']
nbr_ter = []

for i in range(3):
    rep = requests.get(f'https://ev-stations-docker-image-gcp-dzi5homvkq-ew.a.run.app/predict?station_id={s_id[i][1:]}&year={year}&month={month}&day={day}&hour=0&minute=0').json()
    if rep['number_terminals_available'] == 0:
        nbr_ter.append(0)
        folium.Marker([dist_info['latitude'][i], dist_info['longitude'][i]],
                      popup=("0 terminal disponible"),
                      icon=folium.Icon(color='red')).add_to(map_directions)
    elif rep['number_terminals_available'] == 1:
        nbr_ter.append(1)
        folium.Marker([dist_info['latitude'][i], dist_info['longitude'][i]],
                      popup=("1 terminal disponible"),
                      icon=folium.Icon(color='red')).add_to(map_directions)
    elif rep['number_terminals_available'] == 2:
        nbr_ter.append(2)
        folium.Marker([dist_info['latitude'][i], dist_info['longitude'][i]],
                      popup=("2 terminals disponible"),
                      icon=folium.Icon(color='orange')).add_to(map_directions)
    elif rep['number_terminals_available'] == 3:
        nbr_ter.append(3)
        folium.Marker([dist_info['latitude'][i], dist_info['longitude'][i]],
                      popup=("3 terminals disponible"),
                      icon=folium.Icon(color='green')).add_to(map_directions)

# Route S1, S2, S3 en voiture


s1_route_voitu = client.directions(coordinates=[[emp_longitude, emp_latitude], [station1[0], station1[1]]],
                                   profile='driving-car',
                                   format='geojson')

s2_route_voitu = client.directions(coordinates=[[emp_longitude, emp_latitude], [station2[0], station2[1]]],
                                   profile='driving-car',
                                   format='geojson')

s3_route_voitu = client.directions(coordinates=[[emp_longitude, emp_latitude], [station3[0], station3[1]]],
                                   profile='driving-car',
                                   format='geojson')

# Route S1, S2, S3 à pied


s1_route_pied = client.directions(coordinates=[[station1[0], station1[1]], [dest_longitude, dest_latitude]],
                                  profile='foot-walking',
                                  extra_info=["green"],
                                  format='geojson')

s2_route_pied = client.directions(coordinates=[[station2[0], station2[1]], [dest_longitude, dest_latitude]],
                                  profile='foot-walking',
                                  format='geojson')

s3_route_pied = client.directions(coordinates=[[station3[0], station3[1]], [dest_longitude, dest_latitude]],
                                  profile='foot-walking',
                                  format='geojson')


# Calcul temps par station


tmp_s1_voiture = (s1_route_voitu['features'][0]['properties']['summary']['duration'])/60
tmp_s1_pied = (s1_route_pied['features'][0]['properties']['summary']['duration'])/60

tmp_s2_voiture = (s2_route_voitu['features'][0]['properties']['summary']['duration'])/60
tmp_s2_pied = (s2_route_pied['features'][0]['properties']['summary']['duration'])/60

tmp_s3_voiture = (s3_route_voitu['features'][0]['properties']['summary']['duration'])/60
tmp_s3_pied = (s3_route_pied['features'][0]['properties']['summary']['duration'])/60

tmp_s1 = tmp_s1_voiture + tmp_s1_pied
tmp_s2 = tmp_s2_voiture + tmp_s2_pied
tmp_s3 = tmp_s3_voiture + tmp_s3_pied


# Temps le plus court


# if (tmp_s1 < tmp_s2) and (tmp_s1 < tmp_s3):
#     station_util = 1
# elif (tmp_s2 < tmp_s1) and (tmp_s2 < tmp_s3):
#     station_util = 2
# elif (tmp_s3 < tmp_s1) and (tmp_s3 < tmp_s2):
#     station_util = 3


# Ajout route voiture + pied choix station


if station_util == 1:
    folium.GeoJson(s1_route_voitu, name='s1_route_voitu').add_to(map_directions)
    folium.GeoJson(s1_route_pied, name='s1_route_pied').add_to(map_directions)
    st.write(f'Pour vous rendre à la station 1 et aller à votre destination il vous faudra {tmp_s1} minutes')
elif station_util == 2:
    folium.GeoJson(s2_route_voitu, name='s2_route_voitu').add_to(map_directions)
    folium.GeoJson(s2_route_pied, name='s2_route_pied').add_to(map_directions)
    st.write(f'Pour vous rendre à la station 2 et aller à votre destination il vous faudra {tmp_s2} minutes')
elif station_util == 3:
    folium.GeoJson(s3_route_voitu, name='s3_route_voitu').add_to(map_directions)
    folium.GeoJson(s3_route_pied, name='s3_route_pied').add_to(map_directions)
    st.write(f'Pour vous rendre à la station 3 et aller à votre destination il vous faudra {tmp_s3} minutes')

d_stations = {'Station': ['S1', 'S2', 'S3'],
              'Temps en voiture': [tmp_s1_voiture, tmp_s2_voiture, tmp_s3_voiture],
              'Temps à pied': [tmp_s1_pied, tmp_s2_pied, tmp_s3_pied],
              'Temps total': [tmp_s1, tmp_s2, tmp_s3],
              'Nombre de terminal disponible': [nbr_ter[0], nbr_ter[1], nbr_ter[2]]}

df_stations = pd.DataFrame(data=d_stations)


folium_static(map_directions)

st.text(" \n")
st.text(" \n")
st.text(" \n")
st.text(" \n")

st.write(df_stations)
