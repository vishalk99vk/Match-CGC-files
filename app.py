import streamlit as st
import pandas as pd
from io import BytesIO
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

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

    st.write("### 🔎 Apply Filters on Main File")
    gb_main = GridOptionsBuilder.from_dataframe(df_main)
    gb_main.configure_default_column(filter=True, sortable=True, resizable=True)
    grid_main = AgGrid(df_main, gridOptions=gb_main.build(), update_mode=GridUpdateMode.FILTERING_CHANGED)
    df_main_filtered = pd.DataFrame(grid_main["data"])

    st.write("### 🔎 Apply Filters on Client File")
    gb_client = GridOptionsBuilder.from_dataframe(df_client)
    gb_client.configure_default_column(filter=True, sortable=True, resizable=True)
    grid_client = AgGrid(df_client, gridOptions=gb_client.build(), update_mode=GridUpdateMode.FILTERING_CHANGED)
    df_client_filtered = pd.DataFrame(grid_client["data"])

    # Column selection
    st.sidebar.header("⚙️ Matching Settings")
    main_cols = st.sidebar.multiselect("Select column(s) from Main file", df_main_filtered.columns)
    client_cols = st.sidebar.multiselect("Select column(s) from Client file", df_client_filtered.columns)

    if st.sidebar.button("Submit"):
        if not main_cols or not client_cols:
            st.error("⚠️ Please select at least one column from both files.")
        else:
            # Create concat keys on filtered data
            df_main_filtered["_merge_key"] = df_main_filtered[main_cols].astype(str).agg("||".join, axis=1)
            df_client_filtered["_merge_key"] = df_client_filtered[client_cols].astype(str).agg("||".join, axis=1)

            # Find differences
            client_not_in_main = df_client_filtered[~df_client_filtered["_merge_key"].isin(df_main_filtered["_merge_key"])].drop(columns=["_merge_key"])
            main_not_in_client = df_main_filtered[~df_main_filtered["_merge_key"].isin(df_client_filtered["_merge_key"])].drop(columns=["_merge_key"])

            # Display counts
            st.success(f"✅ Found {len(client_not_in_main)} rows in Client not in Main")
            st.success(f"✅ Found {len(main_not_in_client)} rows in Main not in Client")

            # --- Create Summary Sheet ---
            summary_data = {
                "Metric": [
                    "Total rows in Main file (after filter)",
                    "Total rows in Client file (after filter)",
                    "Rows in Client not in Main",
                    "Rows in Main not in Client",
                    "Columns used for matching (Main)",
                    "Columns used for matching (Client)"
                ],
                "Value": [
                    len(df_main_filtered),
                    len(df_client_filtered),
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

                    # Apply formatting
                    for col_num, value in enumerate(summary.columns.values):
                        worksheet.write(0, col_num, value, header_format)

                    worksheet.set_column(0, 0, 45, value_format)  # Metric column
                    worksheet.set_column(1, 1, 55, value_format)  # Value column

                return buffer.getvalue()

            excel_file = convert_to_excel(client_not_in_main, main_not_in_client, df_summary)

            st.download_button(
                "📥 Download Comparison_Result.xlsx",
                data=excel_file,
                file_name="Comparison_Result.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
