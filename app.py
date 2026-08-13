import os
import pandas as pd
import streamlit as st
import ezdxf
import matplotlib.pyplot as plt

# Page configuration
st.set_page_config(page_title="CSV to DXF Converter & Layout Preview", page_icon="📐", layout="wide")

st.title("📐 CSV to DXF 3D Coordinate Converter & Layout Preview - Made by Ng Yit Fung")
st.markdown("Convert CSV data into CAD-ready DXF format and preview the layout live on the web.")

# File uploader
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

# CAD Color Mapping (Matplotlib color name, ACI Index)
CAD_COLORS = {
    "White (Default)": ("white", 7), 
    "Red": ("red", 1), 
    "Yellow": ("yellow", 2), 
    "Green": ("green", 3), 
    "Cyan": ("cyan", 4), 
    "Blue": ("blue", 5), 
    "Magenta": ("magenta", 6), 
    "Gray": ("gray", 8),
}

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    with st.expander("👁️ View CSV Data Preview", expanded=False):
        st.dataframe(df.head(10))

    columns = list(df.columns)

    def get_default_index(keywords, cols):
        for kw in keywords:
            for idx, col in enumerate(cols):
                if kw.lower() in col.lower():
                    return idx
        return 0

    st.write("### 🛠️ Step 1: Map Your Columns")
    col1, col2 = st.columns(2)
    with col1:
        x_col = st.selectbox("Select X Coordinate", columns, index=get_default_index(["x"], columns))
        z_col = st.selectbox("Select Z Coordinate", columns, index=get_default_index(["z", "elev", "height"], columns))
    with col2:
        y_col = st.selectbox("Select Y Coordinate", columns, index=get_default_index(["y"], columns))
        id_col = st.selectbox("Select ID / Point Name", columns, index=get_default_index(["id", "name", "point", "label"], columns))

    st.write("### 🛠️ Step 2: Label Display Settings")
    display_options = st.multiselect(
        "Select what to display in the label (order will be preserved):",
        ["ID", "X Coordinate", "Y Coordinate", "Elevation (EL)"],
        default=["ID", "X Coordinate", "Y Coordinate", "Elevation (EL)"]
    )

    with st.expander("⚙️ Advanced Settings (Heights, Offsets, Colors & Point Style)", expanded=True):
        decimal_places = st.selectbox("Decimal Places for Coordinates / EL", [3, 4], index=0)
        point_color = st.selectbox("Point Symbol Color", list(CAD_COLORS.keys()), index=0)
        
        st.markdown("---")
        st.write("🎛️ **Individual Field Configurations (Height, Offset & Color)**")
        
        field_configs = {}
        for field in ["ID", "X Coordinate", "Y Coordinate", "Elevation (EL)"]:
            if field in display_options:
                st.markdown(f"**📌 {field} Configuration**")
                c1, c2, c3, c4 = st.columns(4)
                with c1: h_val = st.number_input(f"{field} Height", value=1.0, step=0.1, key=f"h_{field}")
                with c2: ox_val = st.number_input(f"{field} X Offset", value=0.5, step=0.1, key=f"ox_{field}")
                with c3: oy_val = st.number_input(f"{field} Y Offset", value=0.5, step=0.1, key=f"oy_{field}")
                with c4: 
                    default_c_idx = 2 if field == "Elevation (EL)" else 0
                    c_val = st.selectbox(f"{field} Color", list(CAD_COLORS.keys()), index=default_c_idx, key=f"c_{field}")
                
                field_configs[field] = {
                    "height": h_val, 
                    "offset_x": ox_val, 
                    "offset_y": oy_val, 
                    "color_name": CAD_COLORS[c_val][0],
                    "color_idx": CAD_COLORS[c_val][1]
                }
                st.markdown("")

        st.markdown("---")
        st.write("📍 **CAD Point Symbol Settings**")
        point_style_options = {
            "Dot (.)": 0, 
            "Plus (+)": 2, 
            "X Shape": 3, 
            "Circle (○)": 32, 
            "Square (□)": 64, 
            "Circle & Cross (◎)": 34
        }
        pdmode_val = st.selectbox("Point Symbol Type", list(point_style_options.keys()), index=5)
        pdsize_val = st.number_input("Point Size", value=1.5, step=0.2)

    # Live Layout Preview Window
    st.markdown("---")
    st.markdown("### 🖥️ Live Layout Preview")
    st.info("💡 The chart below shows a live simulation of your layout configuration. Verify your settings before downloading.")

    fig, ax = plt.subplots(figsize=(10, 8))
    fig.patch.set_facecolor('#0e1117')
    ax.set_facecolor('#0e1117')

    has_valid_data = False
    for idx, row in df.iterrows():
        try:
            x_val, y_val, z_val = float(row[x_col]), float(row[y_col]), float(row[z_col])
            id_val = str(row.get(id_col, f"Pt_{idx+1}"))
            fmt = f"{{:.{decimal_places}f}}"
            has_valid_data = True

            # Plot point
            ax.scatter([x_val], [y_val], color=CAD_COLORS[point_color][0], s=pdsize_val * 20, marker='o')

            # Plot individual text labels
            line_spacing_offset = 0.0
            for field in display_options:
                if field not in field_configs: continue
                cfg = field_configs[field]
                
                if field == "ID": text_content = id_val
                elif field == "X Coordinate": text_content = f"X: {fmt.format(x_val)}"
                elif field == "Y Coordinate": text_content = f"Y: {fmt.format(y_val)}"
                else: text_content = f"EL: {fmt.format(z_val)}"

                fx = x_val + cfg["offset_x"]
                fy = y_val + cfg["offset_y"] - line_spacing_offset

                ax.text(fx, fy, text_content, color=cfg["color_name"], fontsize=max(8, cfg["height"] * 6))
                line_spacing_offset += cfg["height"] * 0.8
        except:
            continue

    if has_valid_data:
        ax.axhline(0, color="gray", linewidth=0.5, linestyle="--")
        ax.axvline(0, color="gray", linewidth=0.5, linestyle="--")
        ax.tick_params(colors='white')
        ax.xaxis.label.set_color('white')
        ax.yaxis.label.set_color('white')
        for spine in ax.spines.values():
            spine.set_edgecolor('gray')
        ax.set_xlabel("X Coordinate")
        ax.set_ylabel("Y Coordinate")
        ax.grid(True, linestyle=":", alpha=0.3, color="gray")
        ax.set_aspect('equal', adjustable='datalim')
        st.pyplot(fig)
    else:
        st.warning("No valid coordinate data available to render.")

    # Generate DXF file for download
    doc = ezdxf.new(dxfversion="R2010")
    msp = doc.modelspace()
    doc.header["$PDMODE"] = point_style_options[pdmode_val]
    doc.header["$PDSIZE"] = pdsize_val

    for idx, row in df.iterrows():
        try:
            x_val, y_val, z_val = float(row[x_col]), float(row[y_col]), float(row[z_col])
            id_val = str(row.get(id_col, f"Pt_{idx+1}"))
            fmt = f"{{:.{decimal_places}f}}"

            msp.add_point((x_val, y_val, z_val), dxfattribs={"color": CAD_COLORS[point_color][1]})

            line_spacing_offset = 0.0
            for field in display_options:
                if field not in field_configs: continue
                cfg = field_configs[field]
                
                if field == "ID": text_content = id_val
                elif field == "X Coordinate": text_content = f"X: {fmt.format(x_val)}"
                elif field == "Y Coordinate": text_content = f"Y: {fmt.format(y_val)}"
                else: text_content = f"EL: {fmt.format(z_val)}"

                msp.add_text(
                    text_content,
                    dxfattribs={
                        "insert": (x_val + cfg["offset_x"], y_val + cfg["offset_y"] - line_spacing_offset, z_val),
                        "height": cfg["height"],
                        "color": cfg["color_idx"]
                    }
                )
                line_spacing_offset += cfg["height"] * 1.3
        except: continue

    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
        doc.saveas(tmp.name)
        with open(tmp.name, "rb") as f:
            dxf_data = f.read()
    os.unlink(tmp.name)

    st.download_button("⬇️ Download DXF File", data=dxf_data, file_name="converted_output.dxf", mime="application/dxf")
