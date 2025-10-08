import streamlit as st
import tempfile
import os
import pyvista as pv
import plotly.graph_objects as go
from mega import Mega

# ---------------------- Streamlit Page Setup ----------------------
st.set_page_config(page_title="MEGA SolidWorks Viewer", layout="wide")
st.title("🔗 MEGA-Connected SolidWorks / CAD Viewer")

st.markdown("""
View your 3D CAD / SolidWorks models directly from your **MEGA.nz** cloud account.  
Supported formats: `.stl`, `.obj`, `.step`, `.ply`, `.glb`, `.gltf`
""")

# ---------------------- MEGA Connection ----------------------
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

# ---------------------- Helper: Plotly Mesh Viewer ----------------------
def show_plotly_mesh(mesh):
    """Render a PyVista mesh using Plotly (browser-safe)"""
    vertices = mesh.points
    faces = mesh.faces.reshape((-1, 4))[:, 1:4]
    fig = go.Figure(
        data=[
            go.Mesh3d(
                x=vertices[:, 0],
                y=vertices[:, 1],
                z=vertices[:, 2],
                i=faces[:, 0],
                j=faces[:, 1],
                k=faces[:, 2],
                color='lightblue',
                opacity=1.0,
            )
        ]
    )
    fig.update_layout(scene=dict(aspectmode="data"), margin=dict(l=0, r=0, b=0, t=0))
    st.plotly_chart(fig, use_container_width=True)

# ---------------------- Fetch MEGA Files ----------------------
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

    if not cad_files:
        st.warning("No supported CAD files found in your MEGA account.")
        st.stop()

    selected_file = st.sidebar.selectbox("Select a file to view", list(cad_files.keys()))

except Exception as e:
    st.error(f"Error fetching MEGA files: {e}")
    st.stop()

# ---------------------- Download and Visualize ----------------------
if selected_file and st.sidebar.button("🔍 Load Model"):
    try:
        ext = os.path.splitext(selected_file)[1].lower()
        temp_path = tempfile.NamedTemporaryFile(delete=False, suffix=ext).name

        st.sidebar.info(f"Downloading **{selected_file}** from MEGA...")
        m.download(cad_files[selected_file], temp_path)
        st.success(f"✅ Downloaded: {selected_file}")

        if ext in [".stl", ".obj", ".ply", ".step"]:
            mesh = pv.read(temp_path)
            show_plotly_mesh(mesh)

        elif ext in [".glb", ".gltf"]:
            st.markdown("### GLB / GLTF Model Viewer")
            st.components.v1.html(f"""
                <model-viewer src="file://{temp_path}" camera-controls auto-rotate style="width:100%;height:600px;">
                </model-viewer>
                <script type="module" src="https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js"></script>
            """, height=650)

        else:
            st.warning("Unsupported file format.")

        os.remove(temp_path)

    except Exception as e:
        st.error(f"❌ Could not visualize file: {e}")
