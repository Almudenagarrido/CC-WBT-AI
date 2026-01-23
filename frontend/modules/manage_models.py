import os
import json
import time
import utils as u
import streamlit as st


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.dirname(BASE_DIR)
PROJECT_ROOT = os.path.dirname(FRONTEND_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
CONFIG_FILE = os.path.join(BACKEND_DIR, "config.json")


class ManageModels:

    def __init__(self, country):
        self.country = country
        self.key_fuels = "expanded_carbon"
        self.template_path = "upload-{model}.xlsx"
        self.config = self._load_config()

    def _load_config(self):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    
    def _get_country_year_range(self):
        ranges = self.config.get("COUNTRY_YEAR_RANGES", {})

        if self.country in ranges:
            start = ranges[self.country].get("start")
            end = ranges[self.country].get("end")
            return start, end

        template = ranges.get("template", {})
        return template.get("start"), template.get("end")
    
    def model_creator(self, models):

        baseline_exists = any(model.lower().startswith("baseline") for model in models)

        if not baseline_exists:

            st.markdown("#### ➕ Define the Year Range for the Scenario")

            with st.form("create_baseline_form"):

                st.info(
                    "The selected year range defines the time horizon for this country. "
                    "All techno-economic models created afterwards will use the same year range."
                )

                start_year = st.number_input("Start year", step=1, format="%d")
                end_year = st.number_input("End year", step=1, format="%d")

                # Hidden consumer functionality
                """
                st.markdown("##### Define Consumer Types for Baseline")
                if "baseline_consumers" not in st.session_state:
                    st.session_state.baseline_consumers = []
                for i, consumer in enumerate(st.session_state.baseline_consumers):
                    st.markdown(f"{i+1}. {consumer}")

                col1, col2, col3 = st.columns([0.8, 0.1, 0.1])
                with col1:
                    new_consumer = st.text_input(
                        "Enter consumer type name",
                        placeholder="e.g., Residential, Commercial, Industrial..."
                    )
                with col2:
                    add_consumer = st.form_submit_button("➕")
                with col3:
                    clear_consumers = st.form_submit_button("🗑️")

                if add_consumer and new_consumer.strip():
                    consumer = new_consumer.strip()
                    if consumer not in st.session_state.baseline_consumers:
                        st.session_state.baseline_consumers.append(consumer)
                        success = u.add_consumer_to_backend(self.country, "Baseline", consumer)
                        if not success:
                            st.error("Could not save consumer to backend.")
                        st.rerun()

                if clear_consumers:
                    for consumer in st.session_state.baseline_consumers:
                        u.delete_consumer_from_backend(self.country, "Baseline", consumer)
                    st.session_state.baseline_consumers = []
                    st.rerun()
                """

                create_baseline = st.form_submit_button(f"Save year range for the scenario of '{self.country}'")

            if 'create_baseline' in locals() and create_baseline:
                if not start_year or not end_year:
                    st.error("Fill in both start year and end year.")
                elif start_year >= end_year:
                    st.error("Start year must be less than end year.")
                else:
                    success, msg = u.create_model_in_backend("Baseline", start_year, end_year)
                    if success:
                        # Hidden consumer functionality
                        # st.session_state.baseline_consumers = []
                        st.session_state.models = u.get_models_from_backend()
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(msg)

        else:

            start_year, end_year = self._get_country_year_range()
        
            col1, col2 = st.columns([0.4, 0.6])
            with col1:
                if st.button("🔄 Reset year range"):
                    st.session_state["confirm_reset"] = True
            
            with col2:
                st.markdown(f"**Current year range:** {start_year} - {end_year}")

            if st.session_state.get("confirm_reset", False):
                st.warning(
                    "The year range defined previously will be removed, and all techno-economic models associated with this scenario will be deleted."
                )

                col1, col2 = st.columns(2)

                with col1:
                    if st.button("✅ Confirm reset"):
                        
                        success = u.delete_model_from_backend("Baseline")
                        if success:
                            st.session_state.models = u.get_models_from_backend()
                            st.session_state.pop("confirm_reset", None)
                            time.sleep(1)
                            st.rerun()

                with col2:
                    if st.button("❌ Cancel"):
                        st.session_state.pop("confirm_reset", None)
                        st.rerun()

            non_baseline_models = [m for m in st.session_state.models if not m.lower().startswith("baseline")]

            if non_baseline_models:
                self.show_models(non_baseline_models)
            else:
                st.info("No techno-economic models available. Please define one.")

            st.markdown("#### ➕ Create New Techno-Economic Model")

            start_year, end_year = self._get_country_year_range()

            with st.form("create_model_form"):
                name = st.text_input("Model Name")
                
                # Hidden consumer section
                """
                if f"show_consumers_{name}" not in st.session_state:
                    st.session_state[f"show_consumers_{name}"] = False
                
                define_consumers = st.form_submit_button("Define Consumer Types")
                
                if define_consumers and name.strip():
                    st.session_state[f"show_consumers_{name}"] = True
                
                if st.session_state[f"show_consumers_{name}"] and name.strip():
                    st.markdown(f"##### Define Consumer Types for {name}")
                    if "model_consumers" not in st.session_state:
                        st.session_state.model_consumers = []
                    
                    for i, consumer in enumerate(st.session_state.model_consumers):
                        st.markdown(f"{i+1}. {consumer}")

                    col1, col2, col3 = st.columns([0.7, 0.15, 0.15])
                    with col1:
                        new_consumer = st.text_input(
                            "Enter consumer type name",
                            placeholder="e.g., Residential, Commercial, Industrial...",
                            key=f"consumer_input_{name}"
                        )
                    with col2:
                        add_consumer = st.form_submit_button("➕")
                    with col3:
                        clear_consumers = st.form_submit_button("🗑️")

                    if add_consumer and new_consumer.strip():
                        consumer = new_consumer.strip()
                        if consumer not in st.session_state.model_consumers:
                            st.session_state.model_consumers.append(consumer)
                            success = u.add_consumer_to_backend(self.country, name.strip(), consumer)
                            if not success:
                                st.error("Could not save consumer to backend.")
                            st.rerun()

                    if clear_consumers:
                        for consumer in st.session_state.model_consumers:
                            u.delete_consumer_from_backend(self.country, name.strip(), consumer)
                        st.session_state.model_consumers = []
                        st.rerun()
                
                elif define_consumers and not name.strip():
                    st.warning("Enter a model name first to define consumer types.")
                """

                create = st.form_submit_button("Create")

            if 'create' in locals() and create:
                if not name.strip():
                    st.error("Model name cannot be empty.")
                elif name.strip().lower() == "baseline":
                    st.error("The model name 'Baseline' is reserved for defining the scenario year range.")
                elif name.strip().lower() in (m.lower() for m in models):
                    st.error(f"The model '{name.strip()}' already exists. Please choose a different name.")
                else:
                    success, msg = u.create_model_in_backend(name.strip(), start_year, end_year)
                    if success:
                        # Hidden consumer functionality
                        #st.session_state.model_consumers = []
                        #if f"show_consumers_{name}" in st.session_state:
                            #st.session_state[f"show_consumers_{name}"] = False
                        st.success(msg)
                        st.session_state.models = u.get_models_from_backend()
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(msg)

    def show_models(self, models):

        for key in list(st.session_state.keys()):
            if key.startswith("show_uploader_"):
                st.session_state[key] = False

        deleted_model = None
        
        for model in models:
            col1, col2, col3, col4, col5 = st.columns([0.6, 0.1, 0.1, 0.1, 0.1])
            
            with col1:
                if st.button(f"📄 {model}"):
                    st.session_state.section = "technoeconomic_models"
                    st.session_state.subsection = "technoeconomic_inputs"
                    st.session_state.fuel = st.session_state.fuels_expanded[0]
                    st.session_state.model = model
                    st.rerun()

            with col2:
                if st.download_button(
                    label="⬇️",
                    data=u.download_model_files_from_backend(self.country, model),
                    file_name=f"{self.country}_{model}_files.zip",
                    mime="application/zip",
                    key=f"download_zip_{model}",
                    help="Download files"
                ):
                    pass
            
            with col3:

                st.download_button(
                    label="📝",
                    data=u.download_template_file_from_backend(
                        self.country,
                        self.template_path,
                        model,
                        self.key_fuels
                    ),
                    file_name=self.template_path.format(model=model),
                    mime="application/vnd.ms-excel",
                    key=f"download_template_{model}_final",
                    help="Download template"
                )

            with col4:
                with col4:
                    if st.button("📤", key=f"upload_{model}", help="Upload template"):
                        st.session_state[f"show_uploader_{model}"] = not st.session_state.get(
                            f"show_uploader_{model}", False
                        )

            with col5:
                if st.button("❌", key=f"delete_{model}", help="Delete model"):
                    st.session_state["confirm_delete_model"] = model

            if st.session_state.get("confirm_delete_model") == model:
                st.warning(f"⚠️ Are you sure you want to delete **{model}**? This action cannot be undone.")

                col_yes, col_no = st.columns(2)

                with col_yes:
                    if st.button("✅ Confirm delete", key=f"confirm_delete_{model}"):
                        success = u.delete_model_from_backend(model)
                        if success:
                            st.session_state.models = u.get_models_from_backend()
                            st.session_state.pop("confirm_delete_model", None)
                            time.sleep(1)
                            st.rerun()

                with col_no:
                    if st.button("❌ Cancel", key=f"cancel_delete_{model}"):
                        st.session_state.pop("confirm_delete_model", None)
                        st.rerun()

            if st.session_state.get(f"show_uploader_{model}", False):
                st.markdown("<hr style='margin:4px 0;'>", unsafe_allow_html=True)
                uploaded_file = st.file_uploader(f"##### Upload file for {model}",
                    type=["xlsx"],
                    key=f"uploader_{model}"
                )
                
                if uploaded_file:
                    expected_name = self.template_path.format(model=model)
                    
                    if uploaded_file.name != expected_name:
                        st.error(f"Upload rejected. File must be named '{expected_name}' as the template downloaded for this model, got {uploaded_file.name}.")
                    else:
                        success = u.upload_template_file_to_backend(
                            self.country,
                            model=model,
                            file_content=uploaded_file.getvalue(),
                            filename=uploaded_file.name
                        )
                        
                        if success:
                            st.success(f"File for '{model}' uploaded successfully.")
                            st.session_state[f"show_uploader_{model}"] = False
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Failed to upload file")
        
        if deleted_model:
            st.success(f"Model '{deleted_model}' deleted successfully from country '{self.country}'.")
            time.sleep(1)
            st.rerun()
    
    def __call__(self):
        
        st.subheader("Manage Techno-Economic Inputs")
        
        if "models" not in st.session_state or not st.session_state.models:
            st.session_state.models = u.get_models_from_backend()

        self.model_creator(st.session_state.models)