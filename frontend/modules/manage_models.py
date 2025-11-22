import time
import utils as u
import streamlit as st


class ManageModels:

    def __init__(self, country):
        self.country = country
        self.key_fuels = "rest"
        self.template_path = "upload-{model}.xlsx"

    def model_creator(self, models):
        st.markdown("#### ➕ Create New Techno-Economic Model")

        bau_exists = any(model.lower().startswith("bau") for model in models)

        if not bau_exists:
            st.info("First create the BAU (Business As Usual) model.")
            with st.form("create_bau_form"):
                start_year = st.number_input("Start Year (BAU)", step=1, format="%d")
                end_year = st.number_input("End Year (BAU)", step=1, format="%d")

                # Hidden consumer functionality
                """
                st.markdown("##### Define Consumer Types for BAU")
                if "bau_consumers" not in st.session_state:
                    st.session_state.bau_consumers = []
                for i, consumer in enumerate(st.session_state.bau_consumers):
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
                    if consumer not in st.session_state.bau_consumers:
                        st.session_state.bau_consumers.append(consumer)
                        success = u.add_consumer_to_backend(self.country, "BAU", consumer)
                        if not success:
                            st.error("Could not save consumer to backend.")
                        st.rerun()

                if clear_consumers:
                    for consumer in st.session_state.bau_consumers:
                        u.delete_consumer_from_backend(self.country, "BAU", consumer)
                    st.session_state.bau_consumers = []
                    st.rerun()
                """

                create_bau = st.form_submit_button("Create BAU Model")

            if 'create_bau' in locals() and create_bau:
                if not start_year or not end_year:
                    st.error("Fill in both start year and end year.")
                elif start_year >= end_year:
                    st.error("Start year must be less than end year.")
                else:
                    success, msg = u.create_model_in_backend("BAU", start_year, end_year)
                    if success:
                        # Hidden consumer functionality
                        # st.session_state.bau_consumers = []
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
                elif not start_year or not end_year:
                    st.error("Fill in both start year and end year.")
                elif start_year >= end_year:
                    st.error("Start year must be less than end year.")
                elif name.strip().lower() == "bau":
                    st.error("The model name 'BAU' is reserved for the Business As Usual model.")
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
        deleted_model = None
        
        for model in models:
            col1, col2, col3, col4, col5 = st.columns([0.6, 0.1, 0.1, 0.1, 0.1])
            
            with col1:
                if st.button(f"📄 {model}"):
                    st.session_state.section = "technoeconomic_models"
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
                template_content = u.download_template_file_from_backend(self.country, self.template_path, model, self.key_fuels)
                if template_content:
                    st.download_button(
                        "📝",
                        data=template_content,
                        file_name=self.template_path.format(model=model),
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
                        deleted_model = model
                        st.session_state.models = u.get_models_from_backend()

            if st.session_state.get(f"show_uploader_{model}", False):
                st.markdown(f"---")
                st.markdown(f"**Upload file for {model}**")
                uploaded_file = st.file_uploader(
                    f"Choose file for {model}",
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

        if not st.session_state.models:
            st.info("No techno-economic models available.")
        else:
            self.show_models(st.session_state.models)

        self.model_creator(st.session_state.models)