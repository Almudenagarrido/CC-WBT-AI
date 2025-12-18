import os
import streamlit as st

class SummaryFinancing:
    
    def __init__(self, country):
        self.country = country
        # Usa el directorio actual donde está el script
        self.charts_folder = "chanchullo"
        
    def _get_available_charts(self):
        """Get all chart images from the charts folder"""
        try:
            # Debug: mostrar el path actual
            current_dir = os.getcwd()
            st.write(f"**Current directory:** {current_dir}")
            st.write(f"**Looking in folder:** {self.charts_folder}")
            
            # Ver si la carpeta existe
            folder_exists = os.path.exists(self.charts_folder)
            st.write(f"**Folder exists:** {folder_exists}")
            
            if not folder_exists:
                os.makedirs(self.charts_folder, exist_ok=True)
                st.write(f"Created folder: {self.charts_folder}")
                return []
            
            # Listar contenido de la carpeta
            folder_contents = os.listdir(self.charts_folder)
            st.write(f"**Folder contents ({len(folder_contents)} items):**")
            for item in folder_contents:
                st.write(f"  - {item}")
            
            # Get all image files
            image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg')
            charts = []
            
            for file in folder_contents:
                file_path = os.path.join(self.charts_folder, file)
                is_file = os.path.isfile(file_path)
                st.write(f"  Checking '{file}': is_file={is_file}, extension={os.path.splitext(file)[1].lower()}")
                
                if is_file and file.lower().endswith(image_extensions):
                    charts.append(file)
            
            st.write(f"**Found {len(charts)} chart files:** {charts}")
            return sorted(charts)
            
        except Exception as e:
            st.error(f"Error accessing charts folder: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            return []
    
    def __call__(self):
        # Title
        st.subheader("📊 Summary Financing Charts")
        
        # Get available charts
        available_charts = self._get_available_charts()
        
        if not available_charts:
            st.info(f"No charts found in '{self.charts_folder}'. Add some images to display them here.")
            
            # Opción para subir imágenes manualmente
            st.markdown("---")
            st.write("### 📤 Upload a chart image")
            uploaded_file = st.file_uploader(
                "Upload a chart image (PNG, JPG, etc.):",
                type=['png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg'],
                key="chart_uploader"
            )
            
            if uploaded_file is not None:
                # Guardar la imagen en la carpeta
                file_path = os.path.join(self.charts_folder, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                st.success(f"Chart '{uploaded_file.name}' saved successfully!")
                st.rerun()
                
            return
        
        # Display each chart
        for chart_file in available_charts:
            chart_path = os.path.join(self.charts_folder, chart_file)
            
            try:
                # Verificar que el archivo existe
                if not os.path.exists(chart_path):
                    st.error(f"File not found: {chart_path}")
                    continue
                    
                # Display chart title (filename without extension)
                chart_name = os.path.splitext(chart_file)[0]
                st.write(f"### {chart_name.replace('_', ' ').title()}")
                
                # Display the image
                st.image(
                    chart_path,
                    caption=f"Chart: {chart_name}",
                    use_container_width=True
                )
                
                # Optional download button
                with open(chart_path, "rb") as img_file:
                    img_bytes = img_file.read()
                    
                    st.download_button(
                        label="📥 Download this chart",
                        data=img_bytes,
                        file_name=chart_file,
                        mime="image/png",
                        key=f"download_{chart_file}"
                    )
                
                # Opción para eliminar
                col1, col2 = st.columns([0.9, 0.1])
                with col2:
                    if st.button("🗑️", key=f"delete_{chart_file}"):
                        os.remove(chart_path)
                        st.success(f"Deleted {chart_file}")
                        st.rerun()
                
                st.markdown("---")
                
            except Exception as e:
                st.error(f"Could not load chart '{chart_file}': {str(e)}")
                import traceback
                st.code(traceback.format_exc())