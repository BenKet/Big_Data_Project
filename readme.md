This project includes Docker configurations for setting up a web application with FastAPI and Streamlit, along with a PostgreSQL database.

Project Structure
.dockerignore: Specifies files and directories that should be ignored by Docker.
.gitignore: Specifies files and directories that should be ignored by Git.
captain-definition: Configuration for CapRover deployment.
docker-compose.yml: Docker Compose file to set up and manage multi-container applications.
Dockerfile.api: Dockerfile for building the FastAPI application.
Dockerfile.streamlit: Dockerfile for building the Streamlit application.
api.py: Python script for the FastAPI application. This code specifies how the generated route is stored in the database
streamlit_app.py: Python script for the Streamlit application. Generates a map visualization that retrieves data from our database and applies color to edges based on their rating. Additionally, it provides an interface for route generation.
requirements.txt:Requeride libraries that have to be installed in virtual environment

route_map.html and start_project.ipynb: These files were created at the beginning of the project to explore methods for generating and storing routes, and to visualize how they would look. They are not currently in use.



