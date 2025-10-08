import streamlit as st
import tempfile
import os
import pyvista as pv
import plotly.graph_objects as go
from megapyx import Mega

# ------------------------------------------------------------
# STREAMLIT PAGE CONFIGURATION
# ------------------------------------------------------------
st.set_page_config(page_title="MEGA CAD Viewer", layout="wide")
st.title("🔗 MEGA-Connected SolidWorks / CAD Viewer")

st.markdown("""
Upload, browse, and visualize your CAD / SolidWorks models directly from your **MEGA.nz** cloud account.  
Supported formats: `.stl`, `.obj`, `.ply`, `.step`, `.glb`, `.gltf`
""")

# ------------------------------------------------------------
# MEGA CONNECTION
# ------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def connect_mega():
    """Authenticate with MEGA.nz using credentials from Streamlit Secrets."""
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

# ------------------------------------------------------------
# PLOTLY VISUALIZATION (for browser safety)
# ------------------------------------------------------------
def render_mesh_plotly(mesh):
    """Render a PyVista mesh using Plotly (no OpenGL required)."""
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
    fig.update_layout(
        scene=dict(aspectmode="data"),
        margin=dict(l=0, r=0, b=0, t=0),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)


# ------------------------------------------------------------
# FETCH USER FILES FROM MEGA
# ------------------------------------------------------------
st.sidebar.header("📂 Your MEGA Files")

try:
    files = m.get_files()
    file_map = {
        data["a"]["n"]: key
        for key, data in files.items()
        if "a" in data and "n" in data
    }

    supported_ext = (".stl", ".obj", ".ply", ".step", ".glb", ".gltf")
    cad_files = {
        name: fid for name, fid in file_map.items() if name.lower().endswith(supported_ext)
    }

    if not cad_files:
        st.warning("⚠️ No supported 3D files found in your MEGA account.")
        st.stop()

    selected_file = st.sidebar.selectbox("Select a file to visualize", list(cad_files.keys()))

except Exception as e:
    st.error(f"Error fetching MEGA files: {e}")
    st.stop()

# ------------------------------------------------------------
# DOWNLOAD AND VISUALIZE FILE
# ------------------------------------------------------------
if selected_file and st.sidebar.button("🔍 Load 3D Model"):
    try:
        ext = os.path.splitext(selected_file)[1].lower()
        tmp_path = tempfile.NamedTemporaryFile(delete=False, suffix=ext).name

        st.sidebar.info(f"📥 Downloading **{selected_file}** from MEGA...")
        m.download(cad_files[selected_file], tmp_path)
        st.success(f"✅ File downloaded: {selected_file}")

        # Mesh-based visualization
        if ext in [".stl", ".obj", ".ply", ".step"]:
            mesh = pv.read(tmp_path)
            render_mesh_plotly(mesh)

        # GLTF/GLB models (browser-native WebGL)
        elif ext in [".glb", ".gltf"]:
            st.markdown("### 🌐 WebGL Model Viewer")
            st.components.v1.html(f"""
                <model-viewer src="file://{tmp_path}" camera-controls auto-rotate style="width:100%;height:600px;">
                </model-viewer>
                <script type="module" src="https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js"></script>
            """, height=650)

        else:
            st.warning("⚠️ Unsupported file type selected.")

        os.remove(tmp_path)

    except Exception as e:
        st.error(f"❌ Could not visualize file: {e}")
