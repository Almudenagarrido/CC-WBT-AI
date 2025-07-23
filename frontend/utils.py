import requests
import streamlit as st

API_URL = "http://localhost:8001"

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
    
def delete_country_from_backend(country):
    try:
        response = requests.delete(f"{API_URL}/countries", json={"name": country})
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error deleting country: {e}")
        return None
    
