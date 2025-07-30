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
    

# Fuels (GET, DELETE)
def get_fuels_from_backend(key, country):
    try:
        response = requests.get(
            f"{API_URL}/fuels",
            params={"key": key, "country": country}
        )
        return response.json().get("fuels", [])
    except Exception as e:
        st.error(f"Error fetching fuels: {e}")
        return []

def add_fuel_to_backend():
    st.subheader("Add new fuel market")
    new_fuel = st.text_input("Enter name of the new technology: ")

    if st.button("Create market"):
        new_fuel = new_fuel.strip()
        country = st.session_state.country
        if new_fuel == "":
            st.warning("Fuel market name cannot be empty.")
        else:
            try:
                response = requests.post(
                    f"{API_URL}/fuels", 
                    json={"fuel": new_fuel, "country": country}
                )
                response.raise_for_status()
                st.session_state.fuel = new_fuel
                st.session_state.reload_fuels = True
                st.rerun()
                return True
            except Exception as e:
                st.error(f"Error adding fuel: {e}")
                return False
                
def delete_fuel_from_backend(fuel, country):
    try:
        response = requests.delete(
            f"{API_URL}/fuels", 
            json={"fuel": fuel, "country": country}
        )
        response.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Error deleting fuel: {e}")
        return False


# Models
def get_models_from_backend():
    try:
        country = st.session_state.country
        response = requests.get(
            f"{API_URL}/models",
            params={"country": country}
        )
        return response.json().get("models", [])
    except Exception as e:
        st.error(f"Error fetching models: {e}")
        return []

def create_model_in_backend(model, start_year, end_year):
    try:
        country = st.session_state.country
        response = requests.post(
            f"{API_URL}/model", 
            params={"country": country, "model": model, "start_year": start_year, "end_year": end_year}
        )
        response.raise_for_status()
        return True, f"Model '{model}' created successfully."
    except requests.exceptions.HTTPError as e:
        try:
            detail = response.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        return False, detail
    except Exception as e:
        return False, f"Unexpected error: {e}"

def download_model_files_from_backend(country, model):
    try:
        response = requests.get(
            f"{API_URL}/download-model",
            params={"country": country, "model": model}
        )
        if response.status_code == 200:
            return response.content
        else:
            st.error(f"Download failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Exception occurred: {e}")
        return None
    
def delete_model_from_backend(model):
    try:
        country = st.session_state.country
        response = requests.delete(
            f"{API_URL}/model", 
            json={"country": country, "model": model}
        )
        response.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Error deleting model: {e}")
        return False
