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
            "Show ID & Elevation / Height",
            "Show X Coordinate Only",
            "Show Y Coordinate Only",
            "Show Elevation / Height Only",
            "No Text (Draw Points Only)",
        ],
    )

    # Advanced text settings (已增加小数位数选择)
    with st.expander("⚙️ Advanced Settings (Font Size, Offsets & Decimals)"):
      text_height = st.number_input("Text Height", value=1.0, step=0.1)
      offset_x = st.number_input("Text X Offset", value=0.5, step=0.1)
      offset_y = st.number_input("Text Y Offset", value=0.5, step=0.1)
      # 👈 新增：选择保留 3 位还是 4 位小数
      decimal_places = st.selectbox(
          "Decimal Places for Coordinates / EL", [3, 4], index=0
      )

    # Generation button
    if st.button("🚀 Generate DXF File"):
      doc = ezdxf.new(dxfversion="R2010")
      msp = doc.modelspace()

      point_count = 0
      skipped_count = 0
      bad_rows_info = []

      for idx, row in df.iterrows():
        try:
          # 1. 坐标清洗与转换
          x_str = str(row[x_col]).replace(",", "").strip()
          y_str = str(row[y_col]).replace(",", "").strip()
          z_str = str(row[z_col]).replace(",", "").strip()

          x_val = float(x_str)
          y_val = float(y_str)
          z_val = float(z_str)

          # 2. 根据用户设置的小数位数格式化数值字符串
          format_str = f"{{:.{decimal_places}f}}"
          x_formatted = format_str.format(x_val)
          y_formatted = format_str.format(y_val)
          z_formatted = format_str.format(z_val)

          # 3. 清洗 ID 文本
          if id_col in row and pd.notna(row[id_col]):
            id_raw = str(row[id_col])
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

          # 4. 添加 3D 点
          msp.add_point((x_val, y_val, z_val))

          # 5. 确定文字内容（应用格式化后的数值及垂直堆叠换行符 \P）
          text_to_show = ""
          if label_display_mode == "Show ID Only":
            text_to_show = id_val
          elif label_display_mode == "Show ID + X, Y, Z":
            text_to_show = (
                f"{id_val}\\PX: {x_formatted}\\PY:"
                f" {y_formatted}\\PEL:{z_formatted}"
            )
          elif label_display_mode == "Show ID & Elevation / Height":
            text_to_show = f"{id_val}\\PEL:{z_formatted}"
          elif label_display_mode == "Show X Coordinate Only":
            text_to_show = f"X: {x_formatted}"
          elif label_display_mode == "Show Y Coordinate Only":
            text_to_show = f"Y: {y_formatted}"
          elif label_display_mode == "Show Elevation / Height Only":
            text_to_show = f"EL:{z_formatted}"
          elif label_display_mode == "No Text (Draw Points Only)":
            text_to_show = ""

          # 6. 添加多行文本 (MTEXT)
          if text_to_show:
            msp.add_mtext(
                text_to_show,
                dxfattribs={
                    "insert": (x_val + offset_x, y_val + offset_y, z_val),
                    "char_height": text_height,
                },
            )

          point_count += 1
        except Exception as e:
          skipped_count += 1
          bad_rows_info.append(f"Row {idx + 2}: {e}")
          continue

      # 审计并修复
      auditor = doc.audit()
      if len(auditor.errors) > 0:
        auditor.fix_errors()

      # 保存临时文件
      with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp_file:
        tmp_filename = tmp_file.name

      doc.saveas(tmp_filename)

      with open(tmp_filename, "rb") as f:
        dxf_bytes = f.read()

      os.unlink(tmp_filename)

      if skipped_count > 0:
        st.warning(
            f"⚠️ Successfully converted {point_count} points, but skipped"
            f" {skipped_count} invalid/corrupted rows."
        )
        with st.expander("🔍 Click to view skipped row details"):
          st.write("The following rows had errors and were safely bypassed:")
          for bad in bad_rows_info[:20]:
            st.text(bad)
      else:
        st.success(f"🎉 Successfully converted all {point_count} points!")

      # Download button
      st.download_button(
          label="⬇️ Click to Download DXF File",
          data=dxf_bytes,
          file_name="converted_output.dxf",
          mime="application/dxf",
      )

  except Exception as e:
    st.error(f"An error occurred while processing the file: {e}")
