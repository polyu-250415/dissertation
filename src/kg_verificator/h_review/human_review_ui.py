import streamlit as st
import pandas as pd

# -------------------
# Page Config
# -------------------
st.set_page_config(page_title="CSV Label Tool", layout="wide")

def main():
    st.title("📄 CSV Manual Labeling Tool")
    st.write("Upload CSV → Select columns → Edit labels with pagination & filtering → Export")

    # Upload CSV
    csv_file = st.file_uploader("Upload CSV File", type=["csv"])

    if csv_file is not None:
        # ---------------
        # 1. 读取原始数据（只读一次）
        # ---------------
        if "original_df" not in st.session_state:
            df = pd.read_csv(csv_file)
            st.session_state.original_df = df.copy()

        original = st.session_state.original_df.copy()
        total_rows = len(original)
        st.success(f"✅ Loaded: {csv_file.name} | Total rows: {total_rows}")

        # ---------------
        # 2. 选择要显示的列（完全正常可用）
        # ---------------
        all_cols = original.columns.tolist()
        selected_cols = st.multiselect("Select columns to display", all_cols, default=all_cols)

        # ---------------
        # 3. 构建当前视图（包含标注列）
        # ---------------
        current_view = original[selected_cols].copy()
        if "review_label" not in current_view:
            current_view["review_label"] = ""
        if "label_reason" not in current_view:
            current_view["label_reason"] = ""

        # ---------------
        # 4. 初始化编辑缓存（核心修复）
        # ---------------
        if "edited_data" not in st.session_state:
            st.session_state.edited_data = current_view.copy()

        # ---------------
        # 5. 同步结构：新增列自动加入缓存
        # ---------------
        for col in current_view.columns:
            if col not in st.session_state.edited_data.columns:
                st.session_state.edited_data[col] = current_view[col]

        # 只保留当前选择的列
        final_df = st.session_state.edited_data[current_view.columns].copy()

        # --------------------------
        # Filter (Same Row)
        # --------------------------
        st.subheader("Filter Options")
        filter_cols = st.multiselect("Filter by columns", final_df.columns.tolist())
        filtered_df = final_df.copy()

        if filter_cols:
            filter_cols_container = st.columns(len(filter_cols))
            for idx, col in enumerate(filter_cols):
                unique_vals = [""] + sorted([str(x) for x in filtered_df[col].dropna().unique()])
                with filter_cols_container[idx]:
                    selected_val = st.selectbox(f"Filter: {col}", unique_vals, index=0)
                if selected_val:
                    filtered_df = filtered_df[filtered_df[col].astype(str) == selected_val]

        # --------------------------
        # Pagination
        # --------------------------
        st.subheader("Pagination")
        col1, col2, col3 = st.columns(3)
        with col1:
            per_page = st.selectbox("Rows per page", [10, 20, 50, 100], index=1)
            total_pages = max(1, (len(filtered_df) + per_page - 1) // per_page)
        with col2:
            page = st.number_input("Page", min_value=1, max_value=total_pages, value=1)
        with col3:
            st.metric("Total pages", total_pages)

        start = (page - 1) * per_page
        end = start + per_page
        current_page = filtered_df.iloc[start:end].copy()

        # --------------------------
        # Editable Table
        # --------------------------
        st.subheader(f"Editable Table - Page {page}/{total_pages}")
        edited_df = st.data_editor(
            current_page,
            height=500,
            use_container_width=True,
            column_config={c: st.column_config.Column(width="medium") for c in current_page.columns}
        )

        # --------------------------
        # 保存编辑（永久不丢失）
        # --------------------------
        st.session_state.edited_data.update(edited_df)

        # --------------------------
        # Export
        # --------------------------
        st.subheader("Export Result")
        output_csv = st.session_state.edited_data.to_csv(index=False)
        st.download_button(
            label="Download Labeled CSV",
            data=output_csv,
            file_name="labeled_output.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()