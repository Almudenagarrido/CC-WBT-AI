import time
import uuid
import requests
import utils as u
import streamlit as st


class ManageModels:

    def __init__(self):
        self.upload_extensions = ["xlsx", "xlsm", "xls", "xltx", "xltm"]

    ## ALGORIOTMO PARA CARGAR ARCHIVOS
    """def upload_technoeconomic_model(self, name, file):
        files = {"file": (file.name, file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        res = requests.post(f"{self.upload_url}/{name}", files=files)

        if res.status_code == 200:
            return True
        else:
            try:
                error_detail = res.json().get("detail", res.text)
            except ValueError:
                error_detail = res.text
            st.error(f"Upload failed: {error_detail}")
            return False
    """

    def model_creator(self, models):
        st.markdown("#### ➕ Create New Techno-Economic Model")

        bau_exists = any(model.lower().startswith("bau") for model in models)

        if not bau_exists:
            st.info("First create the BAU (Business As Usual) model.")
            with st.form("create_bau_form"):
                start_year = st.number_input("Start Year (BAU)", step=1, format="%d")
                end_year = st.number_input("End Year (BAU)", step=1, format="%d")

                upload_file = st.file_uploader("Upload Excel file for BAU (optional)", type=self.upload_extensions)

                create = st.form_submit_button("Create BAU Model")

                if create:
                    if start_year >= end_year:
                        st.error("Start year must be less than end year.")
                    else:
                        u.create_model_in_backend("BAU", start_year, end_year)
                        st.success(f"BAU model created succesfully.")
                        st.session_state.models = u.get_models_from_backend()

                        ### ALGORITMO PARA CARGAR ARCHIVO BAU
                        """if upload_file:
                            upload_success = self.upload_technoeconomic_model("BAU", upload_file)
                            if upload_success:
                                st.success("Excel file successfully uploaded for BAU.")
                            else:
                                st.error("Failed to upload Excel file for BAU.")"""
                        
                        time.sleep(1)
                        st.rerun()

        else:
            with st.form("create_model_form"):
                name = st.text_input("Model Name")
                col1, col2 = st.columns(2)
                with col1:
                    start_year = st.number_input("Start Year", step=1, format="%d")
                with col2:
                    end_year = st.number_input("End Year", step=1, format="%d")
                create = st.form_submit_button("Create")

                if create:
                    if not name.strip():
                        st.error("Model name cannot be empty.")
                    elif start_year >= end_year:
                        st.error("Start year must be less than end year.")
                    elif name.strip().lower() == "bau":
                        st.error("The model name 'BAU' is reserved for the Business As Usual model.")
                    elif name.strip().lower() in (m.lower() for m in models):
                        st.error(f"The model '{name.strip()}' already exists. Please choose a different name.")
                    else:
                        success, msg = u.create_model_in_backend(name.strip(), start_year, end_year)
                        if success:
                            st.success(msg)
                            st.session_state.models = u.get_models_from_backend()
                        else:
                            st.error(msg)
                        time.sleep(1)
                        st.rerun()

    def show_models(self, models):
        for model in models:
            col1, col2, col3, col4 = st.columns([0.7, 0.1, 0.1, 0.1])
            
            with col1:
                if st.button(f"📄 {model}"):
                    st.session_state.section = "technoeconomic_models"
                    if model == "BAU":
                        st.session_state.subsection = "carbon_credits"
                    else:
                        st.session_state.subsection = "technoeconomic_inputs"
                    st.session_state.model = model
                    st.rerun()

            with col2:
                country = st.session_state.country
                content = u.download_model_files_from_backend(country, model)
                if content:
                    st.download_button(
                        "⬇️",
                        data=content,
                        file_name=f"{country}_{model}_files.zip",
                        mime="application/zip"
                    )

            with col3:
                if st.button("📤", key=f"trigger_upload_{model}"):
                    st.session_state[f"show_uploader_{model}"] = True

            with col4:
                if st.button("❌", key=f"delete_{model}"):
                    success = u.delete_model_from_backend(model)
                    if success:
                        st.success(f"'{model}' was deleted successfully.")
                        st.session_state.models = u.get_models_from_backend()
                    st.rerun()

            ## ALGORITMO PARA CARGAR ARCHIVOS PARA MODELO
            """ if st.session_state.get(f"show_uploader_{model}", False):
                file = st.file_uploader(
                    f"Upload file for {model}",
                    type=self.upload_extensions,
                    key=f"upload_{model}",
                    label_visibility="collapsed"
                )
                if file:
                    if any(file.name.lower().endswith(f".{ext}") for ext in self.upload_extensions):
                        upload_success = self.upload_technoeconomic_model(model, file)
                        if upload_success:
                            st.success(f"Information uploaded to 'Techno-Economic Inputs' file for model '{model}'")
                            st.session_state[f"show_uploader_{model}"] = False
                            time.sleep(2)
                            st.rerun()
                    else:
                        st.error(f"Only Excel files are allowed: {', '.join(self.upload_extensions)}")
            """
    
    def __call__(self):
        st.subheader("Manage Techno-Economic Inputs")
        if "models" not in st.session_state or not st.session_state.models:
            st.session_state.models = u.get_models_from_backend()

        if not st.session_state.models:
            st.info("No techno-economic models available.")
        else:
            self.show_models(st.session_state.models)

        self.model_creator(st.session_state.models)