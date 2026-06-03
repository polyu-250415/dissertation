import streamlit as st
import pandas as pd

# -------------------
# Page Config
# -------------------
st.set_page_config(page_title="CSV Label Tool", layout="wide")

def main():
    st.title("📄 CSV Manual Labeling Tool")
    st.write("Upload CSV → Select columns → Edit labels with pagination → Export")

    # Upload CSV
    csv_file = st.file_uploader("Upload CSV File", type=["csv"])

    if csv_file is not None:
        df = pd.read_csv(csv_file)
        total_rows = len(df)
        st.success(f"✅ Loaded: {csv_file.name} | Total rows: {total_rows}")

        # Select columns
        all_cols = df.columns.tolist()
        selected_cols = st.multiselect("Select columns to display", all_cols, default=all_cols)
        display_df = df[selected_cols].copy()

        # Add editable columns if not exist
        if "review_label" not in display_df:
            display_df["review_label"] = ""
        if "label_reason" not in display_df:
            display_df["label_reason"] = ""

        # Pagination
        st.subheader("Pagination")

        col1, col2, col3 = st.columns(3)
        with col1:
            per_page = st.selectbox("Rows per page", [10, 20, 50, 100], index=1)
            total_pages = max(1, (len(display_df) + per_page - 1) // per_page)
        with col2:
            page = st.number_input("Page", min_value=1, max_value=total_pages, value=1)
        with col3:
            Total = st.number_input("Total pages", min_value=total_pages, max_value=total_pages, value=total_pages)

        start = (page - 1) * per_page
        end = start + per_page
        current_df = display_df.iloc[start:end].copy()

        # Editable table
        st.subheader(f"Editable Table - Page {page}/{total_pages}")
        edited_df = st.data_editor(current_df, height=500, use_container_width=True)

        # Save edits back to full data
        display_df.iloc[start:end] = edited_df.values

        # Export
        st.subheader("Export Result")
        csv_data = display_df.to_csv(index=False)
        st.download_button(
            label="Download Labeled CSV",
            data=csv_data,
            file_name="labeled_output.csv",
            mime="text/csv"
        )

# -------------------
# STABLE RUN (NO INFINITE LOOPS)
# -------------------
if __name__ == "__main__":
    main()