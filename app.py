import os
import tempfile
import pandas as pd
import streamlit as st
import ezdxf

# Page configuration
st.set_page_config(
    page_title="CSV to DXF Converter", page_icon="📐", layout="centered"
)

st.title("📐 CSV to DXF 3D Coordinate Converter")
st.markdown("Convert CSV coordinates to CAD-ready DXF with custom styling.")

# CAD Color Mapping (ACI Index)
CAD_COLORS = {
    "White (Default)": 7,
    "Red": 1,
    "Yellow": 2,
    "Green": 3,
    "Cyan": 4,
    "Blue": 5,
    "Magenta": 6,
    "Gray": 8,
}

# File uploader widget
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file is not None:
  try:
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

    label_display_mode = st.radio(
        "Choose what to display:",
        ["Show ID Only", "Show ID + X, Y, Z", "Show ID & Elevation", "No Text"],
    )

    # Advanced Settings
    with st.expander("⚙️ Advanced Settings (Point Style, Size, Color & Decimals)"):
      text_height = st.number_input("Text Height", value=1.0, step=0.1)
      offset_x = st.number_input("Text X Offset", value=0.5, step=0.1)
      offset_y = st.number_input("Text Y Offset", value=0.5, step=0.1)
      decimal_places = st.selectbox("Decimal Places", [3, 4], index=0)
      
      st.markdown("---")
      # Color Selection
      point_color_name = st.selectbox("Point Color", list(CAD_COLORS.keys()), index=0)
      text_color_name = st.selectbox("Text Label Color", list(CAD_COLORS.keys()), index=0)
      
      st.markdown("---")
      point_style_options = {"Dot (.)": 0, "Plus (+)": 2, "X Shape": 3, "Circle (○)": 32, "Square (□)": 64}
      pdmode_val = st.selectbox("Point Symbol Type", list(point_style_options.keys()), index=1)
      pdsize_val = st.number_input("Point Size (PDSIZE)", value=1.5, step=0.2)

    if st.button("🚀 Generate DXF File"):
      doc = ezdxf.new(dxfversion="R2010")
      msp = doc.modelspace()

      doc.header["$PDMODE"] = point_style_options[pdmode_val]
      doc.header["$PDSIZE"] = pdsize_val

      for idx, row in df.iterrows():
        try:
          x_val, y_val, z_val = float(row[x_col]), float(row[y_col]), float(row[z_col])
          
          fmt = f"{{:.{decimal_places}f}}"
          id_val = str(row.get(id_col, f"Pt_{idx+1}"))

          # 添加点 (应用选定颜色)
          msp.add_point((x_val, y_val, z_val), dxfattribs={"color": CAD_COLORS[point_color_name]})

          # 组装文本
          text_to_show = ""
          if label_display_mode == "Show ID Only":
            text_to_show = id_val
          elif label_display_mode == "Show ID + X, Y, Z":
            text_to_show = f"{id_val}\\PX:\t{fmt.format(x_val)}\\PY:\t{fmt.format(y_val)}\\PEL:\t{fmt.format(z_val)}"
          elif label_display_mode == "Show ID & Elevation":
            text_to_show = f"{id_val}\\PEL:\t{fmt.format(z_val)}"

          if text_to_show:
            msp.add_mtext(
                text_to_show,
                dxfattribs={
                    "insert": (x_val + offset_x, y_val + offset_y, z_val),
                    "char_height": text_height,
                    "color": CAD_COLORS[text_color_name]
                },
            )
        except: continue

      with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
        doc.saveas(tmp.name)
        with open(tmp.name, "rb") as f:
          dxf_data = f.read()
      os.unlink(tmp.name)

      st.download_button("⬇️ Download DXF", data=dxf_data, file_name="output.dxf", mime="application/dxf")
  except Exception as e:
    st.error(f"Error: {e}")
