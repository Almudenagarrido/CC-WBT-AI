import time
import utils as u
import streamlit as st


class ManageModels:

    def __init__(self, country):
        self.country = country
        self.key_fuels = "rest"
        self.template_files = {
            "BAU": "upload-BAU.xlsx",
            "default": "upload-{model}.xlsx"
        }

    def model_creator(self, models):
        st.markdown("#### ➕ Create New Techno-Economic Model")

        bau_exists = any(model.lower().startswith("bau") for model in models)

        if not bau_exists:
            st.info("First create the BAU (Business As Usual) model.")
            with st.form("create_bau_form"):
                start_year = st.number_input("Start Year (BAU)", step=1, format="%d")
                end_year = st.number_input("End Year (BAU)", step=1, format="%d")
                create_bau = st.form_submit_button("Create BAU Model")

                if create_bau:
                    if start_year >= end_year:
                        st.error("Start year must be less than end year.")
                    else:
                        success, msg = u.create_model_in_backend("BAU", start_year, end_year)
                        if success:
                            st.success(msg)

                            st.session_state.models = u.get_models_from_backend()
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(msg)

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
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(msg)

    def show_models(self, models):
        for model in models:
            col1, col2, col3, col4, col5 = st.columns([0.6, 0.1, 0.1, 0.1, 0.1])
            
            with col1:
                if st.button(f"📄 {model}"):
                    st.session_state.section = "technoeconomic_models"
                    if model == "BAU":
                        st.session_state.subsection = "carbon_credits"
                    else:
                        st.session_state.subsection = "technoeconomic_inputs"
                        st.session_state.fuel = st.session_state.fuels_rest[0]
                    st.session_state.model = model
                    st.rerun()

            with col2:
                content = u.download_model_files_from_backend(self.country, model)
                if content:
                    st.download_button(
                        "⬇️",
                        data=content,
                        file_name=f"{self.country}_{model}_files.zip",
                        mime="application/zip",
                        help="Download files"
                    )
            
            with col3:
                template_path = self.template_files["BAU"] if model == "BAU" else self.template_files["default"]
                template_content = u.download_template_file_from_backend(self.country, template_path, model, self.key_fuels)
                if template_content:
                    st.download_button(
                        "📝",
                        data=template_content,
                        file_name=template_path.format(model=model),
                        mime="application/vnd.ms-excel",
                        key=f"download_template_{model}",
                        help="Download template"
                    )

            with col4:
                if st.button("📤", key=f"upload_{model}", help="Upload template"):
                    st.session_state[f"show_uploader_{model}"] = True

            with col5:
                if st.button("❌", key=f"delete_{model}", help="Delete model"):
                    success = u.delete_model_from_backend(model)
                    if success:
                        st.success(f"Model '{model}' deleted successfully from country '{self.country}'.")
                        st.session_state.models = u.get_models_from_backend()
                    st.rerun()

            if st.session_state.get(f"show_uploader_{model}", False):
                uploaded_file = st.file_uploader(
                    f"Upload file for {model}",
                    type=["xlsx"],
                    key=f"uploader_{model}"
                )
                
                if uploaded_file:
                    expected_name = self.template_files["BAU"] if model == "BAU" else self.template_files["default"].format(model=model)
                    
                    if uploaded_file.name != expected_name:
                        st.error(f"Upload rejected. File must be named '{expected_name}' as the template downloaded for this model, , got {uploaded_file.name}.")
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
    
    def __call__(self):
        st.subheader("Manage Techno-Economic Inputs")
        if "models" not in st.session_state or not st.session_state.models:
            st.session_state.models = u.get_models_from_backend()

        if not st.session_state.models:
            st.info("No techno-economic models available.")
        else:
            self.show_models(st.session_state.models)

        self.model_creator(st.session_state.models)