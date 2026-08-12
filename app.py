import os
import tempfile
import pandas as pd
import streamlit as st
import ezdxf

# Page configuration
st.set_page_config(page_title="CSV to DXF Converter", page_icon="📐", layout="centered")

st.title("📐 CSV to DXF 3D Coordinate Converter")

# File uploader
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

# CAD Color Mapping (ACI Index)
CAD_COLORS = {
    "White (Default)": 7, "Red": 1, "Yellow": 2, "Green": 3, 
    "Cyan": 4, "Blue": 5, "Magenta": 6, "Gray": 8,
}

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    columns = list(df.columns)

    def get_default_index(keywords, cols):
        for kw in keywords:
            for idx, col in enumerate(cols):
                if kw.lower() in col.lower():
                    return idx
        return 0

    col1, col2 = st.columns(2)
    with col1:
        x_col = st.selectbox("Select X Coordinate", columns, index=get_default_index(["x"], columns))
        z_col = st.selectbox("Select Z Coordinate", columns, index=get_default_index(["z", "elev", "height"], columns))
    with col2:
        y_col = st.selectbox("Select Y Coordinate", columns, index=get_default_index(["y"], columns))
        id_col = st.selectbox("Select ID", columns, index=get_default_index(["id", "name", "point", "label"], columns))

    # --- 新增：更加灵活的选择组合 ---
    st.write("### ⚙️ Label Display Customization")
    display_options = st.multiselect(
        "Select what to display in the label (order will be kept):",
        ["ID", "X Coordinate", "Y Coordinate", "Elevation (EL)"],
        default=["ID", "Elevation (EL)"]
    )

    with st.expander("⚙️ Advanced Settings (Color, Size, Style)"):
        text_height = st.number_input("Text Height", value=1.0, step=0.1)
        decimal_places = st.selectbox("Decimal Places", [3, 4], index=0)
        point_color = st.selectbox("Point Color", list(CAD_COLORS.keys()), index=0)
        text_color = st.selectbox("Text Color", list(CAD_COLORS.keys()), index=0)
        
        point_style_options = {"Dot (.)": 0, "Plus (+)": 2, "X Shape": 3, "Circle (○)": 32, "Square (□)": 64}
        pdmode_val = st.selectbox("Point Symbol Type", list(point_style_options.keys()), index=1)
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

                # 绘制点
                msp.add_point((x_val, y_val, z_val), dxfattribs={"color": CAD_COLORS[point_color]})

                # 动态组装文本
                lines = []
                if "ID" in display_options: lines.append(f"{id_val}")
                if "X Coordinate" in display_options: lines.append(f"X:\t{fmt.format(x_val)}")
                if "Y Coordinate" in display_options: lines.append(f"Y:\t{fmt.format(y_val)}")
                if "Elevation (EL)" in display_options: lines.append(f"EL:\t{fmt.format(z_val)}")

                # 使用 \P 拼接
                if lines:
                    text_str = "\\P".join(lines)
                    msp.add_mtext(
                        text_str,
                        dxfattribs={
                            "insert": (x_val + 0.5, y_val + 0.5, z_val),
                            "char_height": text_height,
                            "color": CAD_COLORS[text_color]
                        },
                    )
            except: continue

        with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
            doc.saveas(tmp.name)
            with open(tmp.name, "rb") as f:
                dxf_data = f.read()
        os.unlink(tmp.name)
        st.download_button("⬇️ Download DXF", data=dxf_data, file_name="converted_output.dxf", mime="application/dxf")
