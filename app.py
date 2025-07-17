import streamlit as st
import json
import xmltodict
from deepdiff import DeepDiff
import pandas as pd
from collections.abc import Mapping

# ---------- Utility Functions ----------

def load_file(uploaded_file, file_type):
    content = uploaded_file.read()
    if file_type == "JSON":
        return json.loads(content), content.decode()
    elif file_type == "XML":
        parsed = xmltodict.parse(content)
        return parsed, content.decode()
    else:
        st.error("Unsupported file format")
        return None, None

def compare_data(data1, data2):
    return DeepDiff(data1, data2, ignore_order=True)

def is_base64_string(s):
    return isinstance(s, str) and len(s) > 80 and all(c.isalnum() or c in '+/=' for c in s)

def expandable_text(label, value):
    if len(str(value)) > 50:
        with st.expander(label):
            st.code(str(value))
    else:
        st.code(f"{label}: {value}")

def get_type(val):
    return type(val).__name__

def flatten_json(y, prefix='root'):
    out = {}
    def flatten(x, name=''):
        if isinstance(x, Mapping):
            for a in x:
                flatten(x[a], f"{name}['{a}']")
        elif isinstance(x, list):
            for i, a in enumerate(x):
                flatten(a, f"{name}[{i}]")
        else:
            out[name] = x
    flatten(y, prefix)
    return out

# ---------- Streamlit UI ----------

st.set_page_config(layout="wide")
st.title("🧮 Multi-Format File Comparison Tool (JSON / XML)")

file_type = st.selectbox("Select file format", ["JSON", "XML"])

file1 = st.file_uploader("Upload File 1", type=["json", "xml"])
file2 = st.file_uploader("Upload File 2", type=["json", "xml"])

if file1 and file2:
    try:
        col1, col2 = st.columns(2)
        
        data1, raw1 = load_file(file1, file_type)
        data2, raw2 = load_file(file2, file_type)

        with col1:
            st.subheader("📂 File 1: " + file1.name)
            st.code(raw1, language="json" if file_type == "JSON" else "xml")

        with col2:
            st.subheader("📂 File 2: " + file2.name)
            st.code(raw2, language="json" if file_type == "JSON" else "xml")

        st.markdown("---")
        st.subheader("🔍 Detailed Differences")

        result = compare_data(data1, data2)
        if result:
            st.error("🚨 Differences found!")

            # 🔁 Values Changed Section
            if 'values_changed' in result:
                st.subheader("🔁 Values Changed")

                name1 = file1.name
                name2 = file2.name

                table_rows = []
                for key, val in result['values_changed'].items():
                    row = {
                        "Key": key,
                        f"{name1} Value": val['old_value'],
                        f"{name1} Type": get_type(val['old_value']),
                        f"{name2} Value": val['new_value'],
                        f"{name2} Type": get_type(val['new_value']),
                    }
                    table_rows.append(row)

                df = pd.DataFrame(table_rows)
                st.dataframe(df, use_container_width=True)

            # 🟢 Added Items
            if 'dictionary_item_added' in result:
                st.subheader("🟢 Keys Added in File 2")
                for key in result['dictionary_item_added']:
                    expandable_text("Added Key", key)

            # 🔴 Removed Items
            if 'dictionary_item_removed' in result:
                st.subheader("🔴 Keys Missing in File 2")
                for key in result['dictionary_item_removed']:
                    expandable_text("Removed Key", key)

            # ⚠️ Type Mismatches
            if 'type_changes' in result:
                st.subheader("⚠️ Type Mismatches")
                type_mismatch_data = []
                for key, val in result['type_changes'].items():
                    type_mismatch_data.append({
                        "Key": key,
                        f"{file1.name} Type": str(val['old_type'].__name__),
                        f"{file2.name} Type": str(val['new_type'].__name__)
                    })
                df_type = pd.DataFrame(type_mismatch_data)
                st.dataframe(df_type, use_container_width=True)

        else:
            st.success("✅ Files are identical!")

        # ---------- Full Variable Table (Side by Side) ----------
        st.markdown("---")
        st.subheader("📊 Full Variable Comparison Table")

        flat1 = flatten_json(data1)
        flat2 = flatten_json(data2)

        all_keys = list(flat1.keys())  # Preserve File 1's order

        table_rows = []
        for key in all_keys:
            val1 = flat1.get(key, '')
            val2 = flat2.get(key, '')
            row = {
                "Key": key,
                f"{file1.name} Value": val1,
                f"{file1.name} Type": get_type(val1) if val1 != '' else '',
                f"{file2.name} Value": val2,
                f"{file2.name} Type": get_type(val2) if val2 != '' else '',
            }
            table_rows.append(row)

        df_full = pd.DataFrame(table_rows)
        st.dataframe(df_full, use_container_width=True)

    except Exception as e:
        st.exception(f"❌ Error occurred: {e}")
        # ---------- Footer ----------
st.markdown(
    """
    <hr style="margin-top: 40px; margin-bottom: 10px; border: none; border-top: 1px solid #eee;">
    <div style="text-align: center;">
        Developed by <strong>WaqasBinhussain</strong> | 
        <a href="https://www.linkedin.com/in/waqasbinhussain/
" target="_blank" style="text-decoration: none;">
            <img src="https://cdn-icons-png.flaticon.com/512/174/174857.png" width="20" style="vertical-align: middle; margin-bottom: 3px;">
            LinkedIn
        </a>
    </div>
    """,
    unsafe_allow_html=True
)

