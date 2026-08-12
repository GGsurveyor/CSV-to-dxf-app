import os
import tempfile
import pandas as pd
import streamlit as st
import ezdxf

# Page configuration
st.set_page_config(page_title="CSV to DXF Converter", page_icon="📐", layout="wide")

st.title("📐 CSV to DXF 3D Coordinate Converter")

# File uploader
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

# CAD Color Mapping
CAD_COLORS = {
    "White (Default)": 7, "Red": 1, "Yellow": 2, "Green": 3, 
    "Cyan": 4, "Blue": 5, "Magenta": 6, "Gray": 8,
}

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    with st.expander("👁️ View CSV Data", expanded=True):
        st.dataframe(df.head(10))

    columns = list(df.columns)

    def get_default_index(keywords, cols):
        for kw in keywords:
            for idx, col in enumerate(cols):
                if kw.lower() in col.lower():
                    return idx
        return 0

    st.write("### 🛠️ Step 1: Map Columns")
    col1, col2 = st.columns(2)
    with col1:
        x_col = st.selectbox("Select X Coordinate", columns, index=get_default_index(["x"], columns))
        z_col = st.selectbox("Select Z Coordinate", columns, index=get_default_index(["z", "elev", "height"], columns))
    with col2:
        y_col = st.selectbox("Select Y Coordinate", columns, index=get_default_index(["y"], columns))
        id_col = st.selectbox("Select ID", columns, index=get_default_index(["id", "name", "point", "label"], columns))

    st.write("### 🛠️ Step 2: Display Settings")
    display_options = st.multiselect(
        "Select what to display in the label:",
        ["ID", "X Coordinate", "Y Coordinate", "Elevation (EL)"],
        default=["ID", "X Coordinate", "Y Coordinate", "Elevation (EL)"]
    )

    with st.expander("⚙️ Advanced Settings (Individual Heights, Offsets, Colors & Point Style)"):
        decimal_places = st.selectbox("Decimal Places", [3, 4], index=0)
        point_color = st.selectbox("Point Color", list(CAD_COLORS.keys()), index=0)
        
        st.markdown("---")
        st.write("🎛️ **Individual Field Configurations**")
        
        field_configs = {}
        for field in ["ID", "X Coordinate", "Y Coordinate", "Elevation (EL)"]:
            if field in display_options:
                c1, c2, c3, c4 = st.columns(4)
                with c1: h_val = st.number_input(f"{field} Height", value=1.0, step=0.1, key=f"h_{field}")
                with c2: ox_val = st.number_input(f"{field} X Offset", value=0.5, step=0.1, key=f"ox_{field}")
                with c3: oy_val = st.number_input(f"{field} Y Offset", value=0.5, step=0.1, key=f"oy_{field}")
                with c4: c_val = st.selectbox(f"{field} Color", list(CAD_COLORS.keys()), index=0, key=f"c_{field}")
                field_configs[field] = {"height": h_val, "offset_x": ox_val, "offset_y": oy_val, "color": CAD_COLORS[c_val]}

        st.markdown("---")
        st.write("📍 **CAD Point Symbol Settings**")
        point_style_options = {
            "Dot (.)": 0, "Plus (+)": 2, "X Shape": 3, 
            "Circle (○)": 32, "Square (□)": 64, "Circle & Cross (◎)": 34
        }
        pdmode_val = st.selectbox("Point Symbol Type", list(point_style_options.keys()), index=5)
        pdsize_val = st.number_input("Point Size", value=1.5, step=0.2)

    if st.button("🚀 Generate DXF File"):
        doc = ezdxf.new(dxfversion="R2010")
        msp = doc.modelspace()
        doc.header["$PDMODE"] = point_style_options[pdmode_val]
        doc.header["$PDSIZE"] = pdsize_val

        for idx, row in df.iterrows():
            try:
                x_val, y_val, z_val = float(row[x_col]), float(row[y_col]), float(row[z_col])
                id_val = str(row.get(id_col, f"Pt_{idx+1}"))
                fmt = f"{{:.{decimal_places}f}}"

                msp.add_point((x_val, y_val, z_val), dxfattribs={"color": CAD_COLORS[point_color]})

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
                            "color": cfg["color"]
                        }
                    )
                    line_spacing_offset += cfg["height"] * 1.3
            except: continue

        with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
            doc.saveas(tmp.name)
            with open(tmp.name, "rb") as f:
                dxf_data = f.read()
        os.unlink(tmp.name)
        st.success("✅ DXF generation complete!")
        st.download_button("⬇️ Download DXF", data=dxf_data, file_name="converted_output.dxf", mime="application/dxf")

# --- 新增：底部 AutoCAD 成型效果演示视频窗口 ---
st.markdown("---")
st.markdown("### 📺 AutoCAD Rendering & Formation Preview")
st.markdown("以下为生成的 DXF 文件在 AutoCAD 中导入并成型的实际效果参考：")

demo_video_path = "autocad_demo.mp4" # 如果本地没有该文件，可换成在线视频网址
if os.path.exists(demo_video_path):
    st.video(demo_video_path)
else:
    # 默认提供一个占位提示或公共演示视频链接（可按需替换）
    st.info("💡 提示：在当前目录下放入名为 `autocad_demo.mp4` 的录屏文件即可在此处直接播放本地演示动画。")
