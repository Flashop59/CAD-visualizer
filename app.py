import streamlit as st
import tempfile
import os
import pyvista as pv
from stpyvista import stpyvista
from mega import Mega

st.set_page_config(page_title="MEGA SolidWorks Viewer", layout="wide")

st.title("🔗 MEGA-Connected SolidWorks / CAD Viewer")

st.markdown("""
Upload, browse, or visualize your CAD / SolidWorks models directly from MEGA.nz.
Supported formats: `.stl`, `.obj`, `.step`, `.ply`, `.glb`, `.gltf`
""")

# --- 1️⃣ Connect to MEGA ---
@st.cache_resource(show_spinner=False)
def connect_mega():
    try:
        mega = Mega()
        m = mega.login(st.secrets["mega_email"], st.secrets["mega_password"])
        return m
    except Exception as e:
        st.error(f"❌ Could not connect to MEGA: {e}")
        return None

m = connect_mega()

if not m:
    st.stop()

# --- 2️⃣ List MEGA files ---
st.sidebar.header("📂 Your MEGA Files")

try:
    files = m.get_files()
    file_map = {
        data["a"]["n"]: key
        for key, data in files.items()
        if "a" in data and "n" in data
    }

    supported_ext = (".stl", ".obj", ".step", ".ply", ".glb", ".gltf")
    cad_files = {name: fid for name, fid in file_map.items() if name.lower().endswith(supported_ext)}

    if cad_files:
        selected_file = st.sidebar.selectbox("Select a file to view", list(cad_files.keys()))
    else:
        st.warning("No supported CAD files found in your MEGA account.")
        st.stop()
except Exception as e:
    st.error(f"Error fetching MEGA files: {e}")
    st.stop()

# --- 3️⃣ Load and visualize selected file ---
if selected_file and st.sidebar.button("🔍 Load Model"):
    try:
        ext = os.path.splitext(selected_file)[1].lower()
        temp_path = tempfile.NamedTemporaryFile(delete=False, suffix=ext).name

        st.sidebar.info(f"Downloading {selected_file} from MEGA...")
        m.download(cad_files[selected_file], temp_path)

        if ext in [".stl", ".obj", ".ply", ".step"]:
            mesh = pv.read(temp_path)
            plotter = pv.Plotter(window_size=[900, 700])
            plotter.add_mesh(mesh, color=True, smooth_shading=True)
            plotter.show_axes()
            plotter.show_grid()
            stpyvista(plotter)
        elif ext in [".glb", ".gltf"]:
            st.markdown("### GLB / GLTF Model Viewer:")
            st.components.v1.html(f"""
                <model-viewer src="file://{temp_path}" camera-controls auto-rotate style="width:100%;height:600px;">
                </model-viewer>
                <script type="module" src="https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js"></script>
            """, height=650)
        else:
            st.warning("Unsupported format.")

        os.remove(temp_path)

    except Exception as e:
        st.error(f"❌ Could not visualize file: {e}")
