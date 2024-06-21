1. Create a DB in pg admin
2. Run this in DBeaver: 

-- Create the nodes table
CREATE TABLE nodes (
    id SERIAL PRIMARY KEY,
    latitude DECIMAL(10, 7) NOT NULL,
    longitude DECIMAL(10, 7) NOT NULL
);

-- Create the routes table
CREATE TABLE routes (
    id SERIAL PRIMARY KEY,
    start_latitude DECIMAL(10, 7) NOT NULL,
    start_longitude DECIMAL(10, 7) NOT NULL,
    end_latitude DECIMAL(10, 7) NOT NULL,
    end_longitude DECIMAL(10, 7) NOT NULL,
    rating INTEGER CHECK (rating BETWEEN 1 AND 5) NOT NULL
);

-- Create the route_way table
CREATE TABLE route_way (
    route_id INTEGER REFERENCES routes(id),
    node_id INTEGER REFERENCES nodes(id),
    sequence INTEGER NOT NULL,
    PRIMARY KEY (route_id, node_id)
);

-- Create the edges table
CREATE TABLE edges (
    node_id_start INTEGER REFERENCES nodes(id),
    node_id_end INTEGER REFERENCES nodes(id),
    weight FLOAT NOT NULL,
    PRIMARY KEY (node_id_small, node_id_big)
);



