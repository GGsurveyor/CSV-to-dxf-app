import io
import pandas as pd
import streamlit as st
import ezdxf

# Page configuration
st.set_page_config(
    page_title="CSV to DXF 3D Converter", page_icon="📐", layout="centered"
)

st.title("📐 CSV to DXF Converter (X, Y, Z & ID)")
st.markdown(
    "Upload a CSV file containing 3D coordinate data (**ID, X, Y, Z**) to convert it into a 3D CAD-ready DXF file."
)

# Instructions / Expected Format
with st.expander("ℹ️ Expected CSV Format & Instructions"):
  st.markdown("""
        Your CSV file must include columns representing coordinates and an identifier. 
        
        **Example CSV structure:**
        ```csv
        ID,X,Y,Z
        Point1,100.5,200.0,15.2
        Point2,150.0,250.5,18.4
        ```
    """)

# File uploader widget
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file is not None:
  try:
    # Read the CSV file
    df = pd.read_csv(uploaded_file)

    st.success("CSV file successfully uploaded!")
    st.write("### Data Preview:", df.head())

    # Column mappings
    st.write("### Map Your Columns")
    columns = list(df.columns)

    # Helper function to auto-guess column indices
    def get_default_index(keywords, cols):
      for kw in keywords:
        for idx, col in enumerate(cols):
          if kw.lower() in col.lower():
            return idx
      return 0

    col1, col2 = st.columns(2)
    with col1:
      x_col = st.selectbox(
          "Select X (Easting / Longitude) Column",
          columns,
          index=get_default_index(["x"], columns),
      )
      z_col = st.selectbox(
          "Select Z (Elevation / Height) Column",
          columns,
          index=get_default_index(["z", "elev", "height"], columns),
      )

    with col2:
      y_col = st.selectbox(
          "Select Y (Northing / Latitude) Column",
          columns,
          index=get_default_index(["y"], columns),
      )
      id_col = st.selectbox(
          "Select ID / Name Column",
          columns,
          index=get_default_index(["id", "name", "point", "label"], columns),
      )

    # Optional configuration for text formatting
    with st.expander("⚙️ Advanced Settings (Text Label Options)"):
      text_height = st.number_input(
          "Text Height for ID", min_value=0.1, max_value=100.0, value=1.0
      )
      offset_x = st.number_input(
          "Label Offset X", min_value=-10.0, max_value=10.0, value=0.5
      )
      offset_y = st.number_input(
          "Label Offset Y", min_value=-10.0, max_value=10.0, value=0.5
      )

    if st.button("Generate DXF File"):
      # Create DXF document using ezdxf (R2000 supports 3D coordinates)
      doc = ezdxf.new(dxfversion="R2000")
      msp = doc.modelspace()

      point_count = 0
      for _, row in df.iterrows():
        try:
          x_val = float(row[x_col])
          y_val = float(row[y_col])
          z_val = float(row[z_col])
          id_val = str(row[id_col]) if id_col in row else ""

          # Add 3D Point entity
          msp.add_point((x_val, y_val, z_val))

          # Add Text label (ID) near the point
          if id_val:
            msp.add_text(
                id_val,
                dxfattribs={
                    "insert": (x_val + offset_x, y_val + offset_y, z_val),
                    "height": text_height,
                },
            )

          point_count += 1
        except ValueError:
          continue  # Skip rows with invalid numeric coordinates

      # Save DXF to an in-memory buffer
      dxf_buffer = io.StringIO()
      doc.write(dxf_buffer)
      dxf_bytes = dxf_buffer.getvalue().encode("utf-8")

      st.success(
          f"Successfully converted {point_count} 3D points with IDs into DXF"
          " format!"
      )

      # Download button
      st.download_button(
          label="⬇️ Download 3D DXF File",
          data=dxf_bytes,
          file_name="converted_3d_output.dxf",
          mime="application/dxf",
      )

  except Exception as e:
    st.error(f"An error occurred while processing the file: {e}")