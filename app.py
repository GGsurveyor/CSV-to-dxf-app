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
    # 读取并显示数据预览
    df = pd.read_csv(uploaded_file)
    
    with st.expander("👁️ View CSV Data (Use this to match columns correctly)", expanded=True):
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
        "Select what to display in the label (order will be kept):",
        ["ID", "X Coordinate", "Y Coordinate", "Elevation (EL)"],
        default=["ID", "Elevation (EL)"]
    )

    # 💡 核心升级：为 ID, X, Y, EL 各自独立配置样式、字高、偏移与颜色
    with st.expander("⚙️ Advanced Settings (Individual Heights, Offsets, Colors & Point Style)"):
        decimal_places = st.selectbox("Decimal Places for Coordinates / EL", [3, 4], index=0)
        point_color = st.selectbox("Point Color", list(CAD_COLORS.keys()), index=0)
        
        st.markdown("---")
        st.write("🎛️ **Individual Field Configurations (Height, Offset & Color)**")
        
        # 建立四个标签各自的参数面板
        field_configs = {}
        
        # 为了排版美观，用 columns 展示
        for field in ["ID", "X Coordinate", "Y Coordinate", "Elevation (EL)"]:
            if field in display_options:
                st.markdown(f"**📌 {field} Settings**")
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    h_val = st.number_input(f"{field} Height", value=1.0, step=0.1, key=f"h_{field}")
                with c2:
                    ox_val = st.number_input(f"{field} X Offset", value=0.5, step=0.1, key=f"ox_{field}")
                with c3:
                    oy_val = st.number_input(f"{field} Y Offset", value=0.5, step=0.1, key=f"oy_{field}")
                with c4:
                    # 默认颜色分配
                    default_c_idx = 2 if field == "Elevation (EL)" else 0 # EL 默认给黄色
                    c_val = st.selectbox(f"{field} Color", list(CAD_COLORS.keys()), index=default_c_idx, key=f"c_{field}")
                
                field_configs[field] = {
                    "height": h_val,
                    "offset_x": ox_val,
                    "offset_y": oy_val,
                    "color": CAD_COLORS[c_val]
                }
                st.markdown("")

        st.markdown("---")
        st.write("📍 **CAD Point Symbol Settings**")
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

                # 1. 绘制基准 3D 点
                msp.add_point((x_val, y_val, z_val), dxfattribs={"color": CAD_COLORS[point_color]})

                # 2. 逐项独立绘制文本（支持各自独立的字高、偏移与颜色）
                # 为了防止多行重叠，通过累加行高进行纵向偏移微调
                line_spacing_offset = 0.0
                
                for field in display_options:
                    if field not in field_configs:
                        continue
                    
                    cfg = field_configs[field]
                    
                    # 准备当前行的文本内容
                    if field == "ID":
                        text_content = id_val
                    elif field == "X Coordinate":
                        text_content = f"X:\t{fmt.format(x_val)}"
                    elif field == "Y Coordinate":
                        text_content = f"Y:\t{fmt.format(y_val)}"
                    elif field == "Elevation (EL)":
                        text_content = f"EL:\t{fmt.format(z_val)}"
                    else:
                        continue

                    # 计算当前行的最终插入坐标（基础坐标 + 独立偏移量 - 自动累加行高防止挤压）
                    final_x = x_val + cfg["offset_x"]
                    final_y = y_val + cfg["offset_y"] - line_spacing_offset
                    
                    # 添加单行或多行文本实体
                    msp.add_text(
                        text_content,
                        dxfattribs={
                            "insert": (final_x, final_y, z_val),
                            "height": cfg["height"],
                            "color": cfg["color"]
                        }
                    )
                    
                    # 为下一行预留垂直间距（根据当前字高动态决定行间距）
                    line_spacing_offset += cfg["height"] * 1.3

            except Exception as e:
                continue

        with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
            doc.saveas(tmp.name)
            with open(tmp.name, "rb") as f:
                dxf_data = f.read()
        os.unlink(tmp.name)
        
        st.success("✅ DXF generation complete!")
        st.download_button("⬇️ Download DXF", data=dxf_data, file_name="converted_output.dxf", mime="application/dxf")
