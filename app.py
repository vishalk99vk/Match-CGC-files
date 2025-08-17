import streamlit as st
import pandas as pd
import traceback
from io import BytesIO

st.set_page_config(page_title="File Comparison Tool", layout="wide")
st.title("🔍 File Comparison Tool")

# Upload files
main_file = st.file_uploader("Upload Main File", type=["csv", "xlsx"])
client_file = st.file_uploader("Upload Client File", type=["csv", "xlsx"])

def load_file(uploaded_file):
    if uploaded_file.name.endswith(".csv"):
        return pd.read_csv(uploaded_file, dtype=str, low_memory=False)
    else:
        return pd.read_excel(uploaded_file, dtype=str)

try:
    if main_file and client_file:
        df_main = load_file(main_file)
        df_client = load_file(client_file)

        st.write("### 📄 Main File Preview")
        st.dataframe(df_main.head(20), use_container_width=True)

        st.write("### 📄 Client File Preview")
        st.dataframe(df_client.head(20), use_container_width=True)

        # Excel-like filter panel
        st.sidebar.header("🔽 Filter Data (like Excel)")
        filter_column = st.sidebar.selectbox("Choose column to filter (Main file)", [""] + list(df_main.columns))
        if filter_column:
            unique_vals = df_main[filter_column].dropna().unique().tolist()
            selected_vals = st.sidebar.multiselect(f"Select values for {filter_column}", unique_vals)
            if selected_vals:
                df_main = df_main[df_main[filter_column].isin(selected_vals)]

        # Column selection
        st.sidebar.header("⚙️ Matching Settings")
        main_cols = st.sidebar.multiselect("Select column(s) from Main file", df_main.columns)
        client_cols = st.sidebar.multiselect("Select column(s) from Client file", df_client.columns)

        if st.sidebar.button("Submit"):
            if not main_cols or not client_cols:
                st.error("⚠️ Please select at least one column from both files.")
            else:
                df_main["_merge_key"] = df_main[main_cols].astype(str).agg("||".join, axis=1)
                df_client["_merge_key"] = df_client[client_cols].astype(str).agg("||".join, axis=1)

                client_not_in_main = df_client[~df_client["_merge_key"].isin(df_main["_merge_key"])].drop(columns=["_merge_key"])
                main_not_in_client = df_main[~df_main["_merge_key"].isin(df_client["_merge_key"])].drop(columns=["_merge_key"])

                st.success(f"✅ Found {len(client_not_in_main)} rows in Client not in Main")
                st.success(f"✅ Found {len(main_not_in_client)} rows in Main not in Client")

                # Show results inline
                st.write("### 🔹 Client Not in Main")
                st.dataframe(client_not_in_main, use_container_width=True)

                st.write("### 🔹 Main Not in Client")
                st.dataframe(main_not_in_client, use_container_width=True)

                # Summary sheet
                summary_data = {
                    "Metric": [
                        "Total rows in Main file",
                        "Total rows in Client file",
                        "Rows in Client not in Main",
                        "Rows in Main not in Client",
                        "Columns used for matching (Main)",
                        "Columns used for matching (Client)"
                    ],
                    "Value": [
                        len(df_main),
                        len(df_client),
                        len(client_not_in_main),
                        len(main_not_in_client),
                        ", ".join(main_cols),
                        ", ".join(client_cols)
                    ]
                }
                df_summary = pd.DataFrame(summary_data)

                # Excel export
                def convert_to_excel(df1, df2, summary):
                    buffer = BytesIO()
                    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                        summary.to_excel(writer, index=False, sheet_name="Summary")
                        df1.to_excel(writer, index=False, sheet_name="Client_Not_in_Main")
                        df2.to_excel(writer, index=False, sheet_name="Main_Not_in_Client")
                    return buffer.getvalue()

                excel_file = convert_to_excel(client_not_in_main, main_not_in_client, df_summary)

                st.download_button(
                    "📥 Download Comparison_Result.xlsx",
                    data=excel_file,
                    file_name="Comparison_Result.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

except Exception as e:
    error_details = traceback.format_exc()
    st.error(f"❌ An error occurred: {e}")
    with st.expander("🔎 Show full error details"):
        st.code(error_details, language="python")
