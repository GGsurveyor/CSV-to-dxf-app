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
st.markdown(
    "Upload a CSV file containing **ID, X, Y, and Z** data to instantly convert"
    " it into a CAD-ready DXF file."
)

# Sample format expander
with st.expander("ℹ️ Click here to view the expected CSV format"):
  st.markdown("""
        Your CSV file must include these columns (headers can have any names as you can match them manually later):
        
        **Example CSV Structure:**
        ```csv
        ID,X,Y,Z
        P1,500.25,1000.50,15.20
        P2,501.10,1002.30,15.85
        ```
    """)

# File uploader widget
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file is not None:
  try:
    # Read the CSV file
    df = pd.read_csv(uploaded_file)

    st.success("File uploaded successfully!")
    st.write("### Data Preview:", df.head())

    st.write("### Match Your Table Columns")
    columns = list(df.columns)


    # Helper function to auto-guess column indices
    def get_default_index(keywords, cols):
      for kw in keywords:
        for idx, col in enumerate(cols):
          if kw.lower() in col.lower():
            return idx
      return 0


    # Two-column layout
    col1, col2 = st.columns(2)
    with col1:
      x_col = st.selectbox(
          "Select X Coordinate (Easting / Longitude)",
          columns,
          index=get_default_index(["x"], columns),
      )
      z_col = st.selectbox(
          "Select Z Coordinate (Elevation / Height)",
          columns,
          index=get_default_index(["z", "elev", "height"], columns),
      )

    with col2:
      y_col = st.selectbox(
          "Select Y Coordinate (Northing / Latitude)",
          columns,
          index=get_default_index(["y"], columns),
      )
      id_col = st.selectbox(
          "Select ID (Point Name / Number)",
          columns,
          index=get_default_index(["id", "name", "point", "label"], columns),
      )

    # CAD label display options
    st.write("### ⚙️ CAD Text Label Options")
    label_display_mode = st.radio(
        "Choose what to display next to the point:",
        [
            "Show ID Only",
            "Show ID + X, Y, Z",
            "Show X Coordinate Only",
            "Show Y Coordinate Only",
            "Show Elevation / Height Only",
            "No Text (Draw Points Only)",
        ],
    )

    # Advanced text settings
    with st.expander("⚙️ Advanced Settings (Font Size & Offsets)"):
      text_height = st.number_input("Text Height", value=1.0, step=0.1)
      offset_x = st.number_input("Text X Offset", value=0.5, step=0.1)
      offset_y = st.number_input("Text Y Offset", value=0.5, step=0.1)

    # Generation button
    if st.button("🚀 Generate DXF File"):
      # 💡 改用 R2010 现代工业级标准，对复杂多点、大批量数据和特殊文本兼容性极强
      doc = ezdxf.new(dxfversion="R2010")
      msp = doc.modelspace()

      point_count = 0
      skipped_count = 0

      for _, row in df.iterrows():
        try:
          # 1. 强力清洗坐标：过滤非数字
          x_val = float(str(row[x_col]).replace(",", "").strip())
          y_val = float(str(row[y_col]).replace(",", "").strip())
          z_val = float(str(row[z_col]).replace(",", "").strip())

          # 2. 极致安全清洗 ID：把所有换行、制表符、非法符号变成安全单行文本
          if id_col in row and pd.notna(row[id_col]):
            id_raw = str(row[id_col])
            # 将任何潜在的回车、换行、Tab直接替换为空格，彻底杜绝 DXF 结构断行
            id_val = (
                id_raw.replace("\r", " ")
                .replace("\n", " ")
                .replace("\t", " ")
                .replace('"', "")
                .strip()
            )
            if not id_val:
              id_val = f"Pt_{point_count+1}"
          else:
            id_val = f"Pt_{point_count+1}"

          # 3. 在 CAD 中添加 3D 点
          msp.add_point((x_val, y_val, z_val))

          # 4. 确定文字内容
          text_to_show = ""
          if label_display_mode == "Show ID Only":
            text_to_show = id_val
          elif label_display_mode == "Show ID + X, Y, Z":
            text_to_show = f"{id_val} (X:{x_val}, Y:{y_val}, Z:{z_val})"
          elif label_display_mode == "Show X Coordinate Only":
            text_to_show = str(x_val)
          elif label_display_mode == "Show Y Coordinate Only":
            text_to_show = str(y_val)
          elif label_display_mode == "Show Elevation / Height Only":
            text_to_show = str(z_val)
          elif label_display_mode == "No Text (Draw Points Only)":
            text_to_show = ""

          # 5. 添加文字标签（如果文本不为空）
          if text_to_show:
            msp.add_text(
                text_to_show,
                dxfattribs={
                    "insert": (x_val + offset_x, y_val + offset_y, z_val),
                    "height": text_height,
                },
            )

          point_count += 1
        except Exception:
          skipped_count += 1
          continue

      # 自动审计并修复任何微小结构问题
      auditor = doc.audit()
      if len(auditor.errors) > 0:
        auditor.fix_errors()

      # 使用临时文件安全保存
      with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp_file:
        tmp_filename = tmp_file.name

      doc.saveas(tmp_filename)

      with open(tmp_filename, "rb") as f:
        dxf_bytes = f.read()

      os.unlink(tmp_filename)

      st.success(
          f"🎉 Successfully converted {point_count} points! (Skipped"
          f" {skipped_count} invalid rows)"
      )

      # Download button
      st.download_button(
          label="⬇️ Click to Download DXF File",
          data=dxf_bytes,
          file_name="converted_output.dxf",
          mime="application/dxf",
      )

  except Exception as e:
    st.error(f"An error occurred while processing the file: {e}")
