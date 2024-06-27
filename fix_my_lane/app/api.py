from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
import psycopg2
from dotenv import load_dotenv
import os
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Database connection parameters
db_params = {
    'dbname': os.getenv('DATABASE_NAME'),
    'user': os.getenv('DATABASE_USER'),
    'host': os.getenv('DATABASE_HOST'),
    'password': os.getenv('DATABASE_PASSWORD')
}

# Authentication dependency
def authenticate(x_api_key: str = Header(None)):
    if x_api_key != "123456":
        raise HTTPException(status_code=403, detail="Invalid API token")

class Route(BaseModel):
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float
    rating: int
    nodes: list

@app.post("/insert_route")
def insert_route(route: Route, token: str = Depends(authenticate)):
    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail="Database connection error")

    try:
        rating_weight_adjustment = {
            1: -2,
            2: -1,
            3: 0,
            4: 1,
            5: 2
        }

        cur.execute("""
            INSERT INTO routes (start_latitude, start_longitude, end_latitude, end_longitude, rating) 
            VALUES (%s, %s, %s, %s, %s) RETURNING id
        """, (route.start_lat, route.start_lon, route.end_lat, route.end_lon, route.rating))
        route_id = cur.fetchone()[0]

        def get_node_id(latitude, longitude):
            cur.execute("SELECT id FROM nodes WHERE latitude = %s AND longitude = %s", (latitude, longitude))
            result = cur.fetchone()
            return result[0] if result else None

        sequence = 0
        coordinates = route.nodes

        node_ids = []
        for coordinate in coordinates:
            longitude, latitude = coordinate
            node_id = get_node_id(latitude, longitude)

            if not node_id:
                cur.execute("INSERT INTO nodes (latitude, longitude) VALUES (%s, %s) RETURNING id", (latitude, longitude))
                node_id = cur.fetchone()[0]

            if (route_id, node_id) not in node_ids:
                cur.execute("INSERT INTO route_way (route_id, node_id, sequence) VALUES (%s, %s, %s)", (route_id, node_id, sequence))
                sequence += 1
                node_ids.append((route_id, node_id))

        def get_edge_info(node_id_start, node_id_end):
            cur.execute("SELECT weight, usage_count FROM edges WHERE node_id_start = %s AND node_id_end = %s", (node_id_start, node_id_end))
            result = cur.fetchone()
            return result if result else None

        def update_edge(node_id_start, node_id_end, weight_adjustment):
            cur.execute("UPDATE edges SET weight = weight + %s, usage_count = usage_count + 1 WHERE node_id_start = %s AND node_id_end = %s", 
                        (weight_adjustment, node_id_start, node_id_end))

        for i in range(len(node_ids) - 1):
            start_node_id = node_ids[i][1]
            end_node_id = node_ids[i + 1][1]
            weight_adjustment = rating_weight_adjustment[route.rating]

            edge_info = get_edge_info(start_node_id, end_node_id)

            if edge_info is None:
                cur.execute("INSERT INTO edges (node_id_start, node_id_end, weight, usage_count) VALUES (%s, %s, %s, %s)", 
                            (start_node_id, end_node_id, weight_adjustment, 1))
            else:
                update_edge(start_node_id, end_node_id, weight_adjustment)

        conn.commit()

    except Exception as e:
        logger.error(f"Error inserting route: {e}")
        raise HTTPException(status_code=500, detail="Error inserting route")
    finally:
        cur.close()
        conn.close()

    return {"status": "success", "route_id": route_id}



