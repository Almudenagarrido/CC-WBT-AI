import os
import json
import streamlit as st
from itertools import product


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.dirname(BASE_DIR)
PROJECT_ROOT = os.path.dirname(FRONTEND_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
CONFIG_FILE = os.path.join(BACKEND_DIR, "config.json")
VISUALIZATIONS_JSON = os.path.join(BASE_DIR, "visualizations_map.json")


class SummaryFinancing:
    
    def __init__(self, country):
        self.country = country
        self.charts_folder = "chanchullo2"
        self.formulas_json_path = VISUALIZATIONS_JSON
        self.config = self._load_config()
    
    def _load_config(self):
        
        with open(CONFIG_FILE, "r", encoding='utf-8') as f:
            return json.load(f)
    
    def _show_graphs_basic_design(self):
        
        st.subheader("📊 Summary Financing Charts (Basic Design)")
        
        if not os.path.exists(self.charts_folder):
            return
        
        images = []
        for file in os.listdir(self.charts_folder):
            if file.lower().endswith('.png'):
                images.append(file)
        
        if not images:
            return
        
        preferred_order = [
            "Sources_Financing_Electricity",
            "Revenues_Electricity", 
            "Capex_Electricity",
            "Sources_Financing_LPG",
            "Revenues_LPG",
            "Capex_LPG"
        ]
        
        def get_sort_key(filename):
            name_without_ext = os.path.splitext(filename)[0]
            for i, pattern in enumerate(preferred_order):
                if pattern in name_without_ext:
                    return i
            return 999
        
        sorted_images = sorted(images, key=get_sort_key)
        
        for img in sorted_images:
            path = os.path.join(self.charts_folder, img)
            
            chart_name = os.path.splitext(img)[0]
            chart_name_display = chart_name.replace('_', ' ')
            
            st.write(f"**{chart_name_display}**")
            st.image(path, use_container_width=True)
            
            with open(path, "rb") as img_file:
                img_bytes = img_file.read()
                
                st.download_button(
                    label="⬇️ Download",
                    data=img_bytes,
                    file_name=img,
                    mime="image/png"
                )
            
            st.markdown("---")
    
    def _expand_visualizations_json(self, visualizations_json):
        
        expanded_graphs = {}
        
        models = self.config.get("MODELS", {}).get(self.country, [])
        fuels = self.config.get("FUELS", {}).get(self.country, {}).get("normal", [])
        
        for graph_raw_name, graph_data in visualizations_json.items():
            
            needs_country = "{country}" in graph_raw_name
            needs_fuel = "{fuel}" in graph_raw_name
            
            if needs_country and needs_fuel:
                for fuel in fuels:
                    expanded_name = graph_raw_name.replace("{country}", self.country)
                    expanded_name = expanded_name.replace("{fuel}", fuel)
                    expanded_graphs[expanded_name] = graph_data
            elif needs_country:
                expanded_name = graph_raw_name.replace("{country}", self.country)
                expanded_graphs[expanded_name] = graph_data
            else:
                expanded_graphs[graph_raw_name] = graph_data
        
        return expanded_graphs
    
    def _calculate_values(self):

        try:
            with open(self.formulas_json_path, "r", encoding='utf-8') as f:
                visualizations_json = json.load(f)
            
            expanded_graphs = self._expand_visualizations_json(visualizations_json)
            
            st.write(f"**Expanded Graphs for {self.country}:**")
            for graph_name, graph_data in expanded_graphs.items():
                with st.expander(f"📈 {graph_name}"):
                    st.write(f"Chart Type: {graph_data.get('chart_type', 'N/A')}")
                    
                    sources = graph_data.get("sources", {})
                    st.write(f"Number of sources: {len(sources)}")
                    
                    for source_name, source_data in sources.items():
                        st.write(f"- {source_name}:")
                        st.write(f"  Formula steps: {len(source_data.get('formula_steps', []))}")
                        st.write(f"  Source files: {source_data.get('sources', [])}")
            
            return expanded_graphs
            
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError as e:
            return {}
    
    def __call__(self):
        
        tab1, tab2 = st.tabs(["🎨 View Design", "⚙️ Calculate Values"])
        
        with tab1:
            
            self._show_graphs_basic_design()
        
        with tab2:
            
            st.write("### 🔧 Calculate Chart Values")
            st.info("This section will process the JSON and calculate values from Excel files.")
            
            if st.button("🚀 Process Visualizations JSON"):
                with st.spinner("Processing JSON and expanding formulas..."):
                    expanded_data = self._calculate_values()
                    
                    if expanded_data:
                        st.success(f"✅ Successfully processed {len(expanded_data)} graph definitions")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Graphs Found", len(expanded_data))
                        with col2:
                            total_sources = sum(
                                len(graph.get("sources", {})) 
                                for graph in expanded_data.values()
                            )
                            st.metric("Total Sources", total_sources)