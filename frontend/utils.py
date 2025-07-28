import base64
import requests
import streamlit as st


API_URL = "http://localhost:8001"


# Images
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()


# Countries (GET, POST, COPY, DELETE)
def get_countries_from_backend():
    try:
        response = requests.get(f"{API_URL}/countries")
        return response.json().get("countries", [])
    except Exception as e:
        st.error(f"Error fetching countries: {e}")
        return []
    
def add_country_to_backend(country):
    try:
        response = requests.post(
            f"{API_URL}/countries",
            json={"name": country}
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error adding country: {e}")
        return None

def create_templates_if_missing(country):
    try:
        response = requests.post(f"{API_URL}/countries/{country}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error creating templates for {country}: {e}")
        return None

def delete_country_from_backend(country):
    try:
        response = requests.delete(f"{API_URL}/countries", json={"name": country})
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error deleting country: {e}")
        return None
    
