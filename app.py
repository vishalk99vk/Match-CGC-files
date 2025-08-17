import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="File Comparison Tool", layout="wide")
st.title("🔍 File Comparison Tool")

# Upload files
main_file = st.file_uploader("Upload Main File", type=["csv", "xlsx"])
client_file = st.file_uploader("Upload Client File", type=["csv", "xlsx"])

if main_file and client_file:
    # Read files
    if main_file.name.endswith(".csv"):
        df_main = pd.read_csv(main_file)
    else:
        df_main = pd.read_excel(main_file)

    if client_file.name.endswith(".csv"):
        df_client = pd.read_csv(client_file)
    else:
        df_client = pd.read_excel(client_file)

    st.write("### 🔎 Filter & Explore Data")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Main File (Filterable)")
        df_main_filtered = st.data_editor(df_main, use_container_width=True, num_rows="dynamic")

    with col2:
        st.subheader("Client File (Filterable)")
        df_client_filtered = st.data_editor(df_client, use_container_width=True, num_rows="dynamic")

    # Column selection
    st.sidebar.header("⚙️ Matching Settings")
    main_cols = st.sidebar.multiselect("Select column(s) from Main file", df_main.columns)
    client_cols = st.sidebar.multiselect("Select column(s) from Client file", df_client.columns)

    if st.sidebar.button("Submit"):
        if not main_cols or not client_cols:
            st.error("⚠️ Please select at least one column from both files.")
        else:
            # Work only on filtered datasets
            df_main_work = df_main_filtered.copy()
            df_client_work = df_client_filtered.copy()

            # Create concat keys
            df_main_work["_merge_key"] = df_main_work[main_cols].astype(str).agg("||".join, axis=1)
            df_client_work["_merge_key"] = df_client_work[client_cols].astype(str).agg("||".join, axis=1)

            # Find differences
            client_not_in_main = df_client_work[~df_client_work["_merge_key"].isin(df_main_work["_merge_key"])].drop(columns=["_merge_key"])
            main_not_in_client = df_main_work[~df_main_work["_merge_key"].isin(df_client_work["_merge_key"])].drop(columns=["_merge_key"])

            # Display counts
            st.success(f"✅ Found {len(client_not_in_main)} rows in Client not in Main (filtered data)")
            st.success(f"✅ Found {len(main_not_in_client)} rows in Main not in Client (filtered data)")

            # --- Create Summary Sheet ---
            summary_data = {
                "Metric": [
                    "Filtered rows in Main file",
                    "Filtered rows in Client file",
                    "Rows in Client not in Main",
                    "Rows in Main not in Client",
                    "Columns used for matching (Main)",
                    "Columns used for matching (Client)"
                ],
                "Value": [
                    len(df_main_work),
                    len(df_client_work),
                    len(client_not_in_main),
                    len(main_not_in_client),
                    ", ".join(main_cols),
                    ", ".join(client_cols)
                ]
            }
            df_summary = pd.DataFrame(summary_data)

            # --- Excel with 3 sheets + formatting ---
            def convert_to_excel(df1, df2, summary):
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                    # Write sheets
                    summary.to_excel(writer, index=False, sheet_name="Summary")
                    df1.to_excel(writer, index=False, sheet_name="Client_Not_in_Main")
                    df2.to_excel(writer, index=False, sheet_name="Main_Not_in_Client")

                    # Formatting for Summary sheet
                    workbook = writer.book
                    worksheet = writer.sheets["Summary"]
                    header_format = workbook.add_format({"bold": True, "bg_color": "#D9EAD3", "border": 1})
                    value_format = workbook.add_format({"border": 1})

                    for col_num, value in enumerate(summary.columns.values):
                        worksheet.write(0, col_num, value, header_format)

                    worksheet.set_column(0, 0, 40, value_format)
                    worksheet.set_column(1, 1, 50, value_format)

                return buffer.getvalue()

            excel_file = convert_to_excel(client_not_in_main, main_not_in_client, df_summary)

            st.download_button(
                "📥 Download Comparison_Result.xlsx",
                data=excel_file,
                file_name="Comparison_Result.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
