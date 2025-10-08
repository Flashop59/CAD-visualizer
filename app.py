import streamlit as st
import tempfile
import os
import pyvista as pv
import plotly.graph_objects as go
from megapyx import Mega    # ← updated import

st.set_page_config(page_title="MEGA CAD Viewer", layout="wide")
st.title("🔗 MEGA-Connected SolidWorks / CAD Viewer")

@st.cache_resource
def connect_mega():
    try:
        mega = Mega()
        return mega.login(st.secrets["mega_email"], st.secrets["mega_password"])
    except Exception as e:
        st.error(f"Login failed: {e}")
        return None

m = connect_mega()
if not m:
    st.stop()

st.sidebar.header("📂 Your MEGA Files")
files = m.get_files()
file_map = {data["a"]["n"]: key for key, data in files.items() if "a" in data and "n" in data}
supported = (".stl", ".obj", ".ply", ".step", ".glb", ".gltf")
cad_files = {n: fid for n, fid in file_map.items() if n.lower().endswith(supported)}

if not cad_files:
    st.warning("No supported CAD files found.")
    st.stop()

fname = st.sidebar.selectbox("Select file", list(cad_files.keys()))

if fname and st.sidebar.button("Load"):
    ext = os.path.splitext(fname)[1].lower()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext).name
    m.download(cad_files[fname], tmp)

    if ext in [".stl", ".obj", ".ply", ".step"]:
        mesh = pv.read(tmp)
        v, f = mesh.points, mesh.faces.reshape((-1, 4))[:, 1:4]
        fig = go.Figure([go.Mesh3d(
            x=v[:, 0], y=v[:, 1], z=v[:, 2],
            i=f[:, 0], j=f[:, 1], k=f[:, 2],
            color='lightblue'
        )])
        fig.update_layout(scene=dict(aspectmode="data"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.components.v1.html(f"""
        <model-viewer src="file://{tmp}" camera-controls auto-rotate style="width:100%;height:600px;">
        </model-viewer>
        <script type="module" src="https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js"></script>
        """, height=650)
    os.remove(tmp)
