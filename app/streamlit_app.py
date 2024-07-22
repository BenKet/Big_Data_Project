import streamlit as st
import psycopg2
import folium
from streamlit_folium import folium_static
import random
import openrouteservice
import matplotlib.colors as mcolors
import matplotlib.cm as cm
from dotenv import load_dotenv
import os
import json
from api import Route, insert_route # Importing the Route class and insert_route function from the API file

# Load environment variables
load_dotenv()

# OpenRouteService Client initialization
client = openrouteservice.Client(key=os.getenv('OPENROUTESERVICE_API_KEY'))

# Database connection parameters
db_params = {
    'dbname': os.getenv('DATABASE_NAME'),
    'user': os.getenv('DATABASE_USER'),
    'host': os.getenv('DATABASE_HOST'),
    'password': os.getenv('DATABASE_PASSWORD'),
    'port': os.getenv('DATABASE_PORT')
}

# Defining the area for random latitude and longitude in Berlin Kreuzberg/Friedrichshain
latitude_range = (52.49, 52.52)
longitude_range = (13.40, 13.45)

# Possible rating options
ratings = [1, 2, 3, 4, 5]

# Function that generates random coordinates within the specified area
def generate_random_coordinates():
    latitude = random.uniform(*latitude_range)
    longitude = random.uniform(*longitude_range)
    return latitude, longitude

# Function to generate a random rating based on the rating options
def generate_random_rating():
    return random.choice(ratings)

# Function to determine color based on weight
def get_color(weight, vmin, vmax):
    norm = mcolors.TwoSlopeNorm(vmin=vmin, vcenter=0, vmax=vmax)
    cmap = cm.RdYlGn  
    return mcolors.to_hex(cmap(norm(weight)))

# Connection to our PostgreSQL database
def get_db_connection():
    conn = psycopg2.connect(**db_params)
    return conn

# Function to fetch edges from the database
def fetch_edges():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT ns.latitude, ns.longitude, ne.latitude, ne.longitude, e.weight
        FROM edges e
        JOIN nodes ns ON e.node_id_start = ns.id
        JOIN nodes ne ON e.node_id_end = ne.id
    """)
    edges = cur.fetchall()
    cur.close()
    conn.close()
    return edges

# Calculate the center of a set of coordinates
def calculate_center(coords):
    lats, lons = zip(*coords)
    return sum(lats) / len(lats), sum(lons) / len(lons)

# Main function to create the Streamlit app
def main():
    st.title("Bike Route Application")

    # Create tabs so the visualization part and generating route part can be separated
    tabs = st.tabs(["Bike Route Visualization", "Generate API Request", "Last API Call"])

    with tabs[0]:
        st.header("Bike Route Visualization")

        # Initialize map and specifying the center of Berlin, so the map coalways opens at the same location
        map_center = [52.50306, 13.42470]  
        mymap = folium.Map(location=map_center, zoom_start=14)

        # Fetch and display existing edges from database
        edges = fetch_edges()
        weights = [edge[4] for edge in edges] if edges else [0]
        vmin = min(weights) if weights else 0
        vmax = max(weights) if weights else 1
        for edge in edges:
            start_lat, start_lon, end_lat, end_lon, weight = edge
            color = get_color(weight, vmin, vmax)
            folium.PolyLine(
                locations=[(start_lat, start_lon), (end_lat, end_lon)],
                color=color,
                weight=5,
                opacity=0.8
            ).add_to(mymap)

        folium_static(mymap)

    with tabs[1]:
        st.header("Generate API Request")

        if st.button("Generate Route"):
            start_lat, start_lon = generate_random_coordinates()
            end_lat, end_lon = generate_random_coordinates()
            rating = generate_random_rating()

            response = client.directions(coordinates=[[start_lon, start_lat], [end_lon, end_lat]], profile='driving-car', format='geojson')
            data = response['features'][0]['geometry']['coordinates']

            # Calculating center of the route
            route_center = calculate_center([(coord[1], coord[0]) for coord in data])

            # Display the details of generated route
            st.markdown(f"**Start Point:** ({start_lat}, {start_lon})")
            st.markdown(f"**End Point:** ({end_lat}, {end_lon})")
            st.markdown("**Intermediate Nodes:**")
            for node in data:
                st.write(f"({node[1]}, {node[0]})")
            st.markdown(f"**Rating:** {rating}")

            # Visualizing the generated route on map
            route_map = folium.Map(location=route_center, zoom_start=14)
            folium.Marker(location=[start_lat, start_lon], popup="Start").add_to(route_map)
            folium.Marker(location=[end_lat, end_lon], popup="End").add_to(route_map)
            folium.PolyLine(locations=[(coord[1], coord[0]) for coord in data], color="blue", weight=5, opacity=0.8).add_to(route_map)
            folium_static(route_map)

            # Create API request example
            api_request = {
                "start_lat": start_lat,
                "start_lon": start_lon,
                "end_lat": end_lat,
                "end_lon": end_lon,
                "rating": rating,
                "nodes": data
            }

            # Call insert_route function directly
            route = Route(**api_request)
            response = insert_route(route)

            if response["status"] == "success":
                st.success("Route inserted successfully.")
            else:
                st.error("Failed to insert route.")

            st.session_state.last_api_call = {
                "request": api_request,
                "response": response
            }

    with tabs[2]:
        st.header("Last API Call")

        if "last_api_call" in st.session_state:
            last_api_call = st.session_state.last_api_call

            st.markdown("**Last API Request:**")
            st.json(last_api_call["request"])

            st.markdown("**Last API Response:**")
            st.json(last_api_call["response"])
        else:
            st.write("No API call has been received yet.")

if __name__ == "__main__":
    main()

