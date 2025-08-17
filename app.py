import streamlit as st
import pandas as pd
from io import BytesIO

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

    st.write("### Preview - Main File")
    st.dataframe(df_main.head())
    st.write("### Preview - Client File")
    st.dataframe(df_client.head())

    # Column selection
    st.sidebar.header("⚙️ Matching Settings")
    main_cols = st.sidebar.multiselect("Select column(s) from Main file", df_main.columns)
    client_cols = st.sidebar.multiselect("Select column(s) from Client file", df_client.columns)

    if st.sidebar.button("Submit"):
        if not main_cols or not client_cols:
            st.error("⚠️ Please select at least one column from both files.")
        else:
            # Create concat keys
            df_main["_merge_key"] = df_main[main_cols].astype(str).agg("||".join, axis=1)
            df_client["_merge_key"] = df_client[client_cols].astype(str).agg("||".join, axis=1)

            # Find differences
            client_not_in_main = df_client[~df_client["_merge_key"].isin(df_main["_merge_key"])].drop(columns=["_merge_key"])
            main_not_in_client = df_main[~df_main["_merge_key"].isin(df_client["_merge_key"])].drop(columns=["_merge_key"])

            # Display counts
            st.success(f"✅ Found {len(client_not_in_main)} rows in Client not in Main")
            st.success(f"✅ Found {len(main_not_in_client)} rows in Main not in Client")

            # --- Excel with 2 sheets ---
            def convert_to_excel(df1, df2):
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                    df1.to_excel(writer, index=False, sheet_name="Client_Not_in_Main")
                    df2.to_excel(writer, index=False, sheet_name="Main_Not_in_Client")
                return buffer.getvalue()

            excel_file = convert_to_excel(client_not_in_main, main_not_in_client)

            st.download_button(
                "📥 Download Comparison_Result.xlsx",
                data=excel_file,
                file_name="Comparison_Result.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
