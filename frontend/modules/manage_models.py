import time
import requests
import streamlit as st

class ManageModels:

    def __init__(self, api_base):
        self.api_base = api_base
        self.list_url = f"{self.api_base}/technoeconomic-models"
        self.download_files_url = f"{self.api_base}/download-technoeconomic-model-files"
        self.create_url = f"{self.api_base}/create-technoeconomic-model"
        self.delete_url = f"{self.api_base}/delete-technoeconomic-model"
        self.upload_url = f"{self.api_base}/upload-technoeconomic-model"
        self.valid_extensions = ["xlsx", "xlsm", "xls", "xltx", "xltm"]

    def list_technoeconomic_models(self):
        try:
            res = requests.get(self.list_url)
            return res.json().get("models", []) if res.status_code == 200 else []
        except:
            st.error("Error loading models from server.")
            return []

    def remove_extension(self, filename):
        for ext in self.valid_extensions:
            if filename.lower().endswith(f".{ext}"):
                return filename[: -len(ext) - 1]
        return filename
    
    def download_technoeconomic_model_files(self, name):
        url = f"{self.download_files_url}/{name}"
        res = requests.get(url)
        return res.content if res.status_code == 200 else None

    def delete_technoeconomic_model(self, name):
        res = requests.delete(f"{self.delete_url}/{name}")
        if res.status_code == 200:
            return True, f"Model '{name}' deleted successfully."
        else:
            return False, "Failed to delete the model."

    def upload_technoeconomic_model(self, name, file):
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

    def create_technoeconomic_model(self, model, start_year, end_year):
        try:
            url = f"{self.create_url}/{model}"
            response = requests.post(
                url, params={"start_year": start_year, "end_year": end_year}
            )
            data = response.json()
            if "success" in data and data["success"]:
                return True, data["message"]
            else:
                return False, data.get("error", "Unknown error occurred.")
        except Exception as e:
            return False, str(e)

    def model_creator(self):
        st.markdown("#### ➕ Create New Techno-Economic Model")

        models = self.list_technoeconomic_models()
        bau_exists = any(self.remove_extension(m).lower() == "bau" for m in models)

        if not bau_exists:
            st.info("First create the BAU (Business As Usual) model.")
            with st.form("create_bau_form"):
                start_year = st.number_input("Start Year (BAU)", step=1, format="%d")
                end_year = st.number_input("End Year (BAU)", step=1, format="%d")

                upload_file = st.file_uploader("Upload Excel file for BAU (optional)", type=self.valid_extensions)

                create = st.form_submit_button("Create BAU Model")

                if create:
                    if start_year >= end_year:
                        st.error("Start year must be less than end year.")
                    else:
                        self.create_technoeconomic_model("bau", start_year, end_year)
                        st.success(f"BAU model created succesfully.")
                        if upload_file:
                            upload_success = self.upload_technoeconomic_model("BAU", upload_file)
                            if upload_success:
                                st.success("Excel file successfully uploaded for BAU.")
                            else:
                                st.error("Failed to upload Excel file for BAU.")
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
                    else:
                        success, msg = self.create_technoeconomic_model(name.strip(), int(start_year), int(end_year))
                        if success:
                            st.success(msg)
                            st.session_state["model_name_input"] = ""
                            st.session_state["start_year_input"] = 0
                            st.session_state["end_year_input"] = 0
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(msg)

    def show_technoeconomic_models(self, models):
        for model in models:
            clean_name = self.remove_extension(model)
            col1, col2, col3, col4 = st.columns([0.7, 0.1, 0.1, 0.1])

            with col1:
                if st.button(f"📄 {clean_name}"):
                    if clean_name == "BAU":
                        st.session_state.page = "Techno-Economic Inputs"
                        st.session_state.subsection = "Carbon Credits"
                    else:
                        st.session_state.page = "Techno-Economic Inputs"
                        st.session_state.subsection = "Techno-Economic Inputs"
                    st.session_state.model = clean_name
                    st.rerun()

            with col2:
                content = self.download_technoeconomic_model_files(clean_name)
                if content:
                    st.download_button(
                        "⬇️",
                        data=content,
                        file_name=f"{clean_name}_files.zip",
                        mime="application/zip"
                    )

            with col3:
                if st.button("📤", key=f"trigger_upload_{model}"):
                    st.session_state[f"show_uploader_{model}"] = True

            with col4:
                if st.button("❌", key=f"delete_{clean_name}"):
                    success, message = self.delete_technoeconomic_model(clean_name)
                    if success:
                        st.success(message)
                    st.rerun()

            if st.session_state.get(f"show_uploader_{model}", False):
                file = st.file_uploader(
                    f"Upload file for {model}",
                    type=self.valid_extensions,
                    key=f"upload_{model}",
                    label_visibility="collapsed"
                )
                if file:
                    if any(file.name.lower().endswith(f".{ext}") for ext in self.valid_extensions):
                        upload_success = self.upload_technoeconomic_model(clean_name, file)
                        if upload_success:
                            st.success(f"Information uploaded to 'Techno-Economic Inputs' file for model '{model}'")
                            st.session_state[f"show_uploader_{model}"] = False
                            time.sleep(2)
                            st.rerun()
                    else:
                        st.error(f"Only Excel files are allowed: {', '.join(self.valid_extensions)}")

    def __call__(self):
        st.subheader("Manage Techno-Economic Inputs")
        models = self.list_technoeconomic_models()
        if not models:
            st.info("No techno-economic inputs available.")
        else:
            self.show_technoeconomic_models(models)
        self.model_creator()