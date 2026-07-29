import pandas as pd
from typing import List, Dict, Tuple

# --------------------------
# Configuration (EN)
# --------------------------
FIXED_NODE_CATEGORIES = {
    "Explicit Knowledge",
    "Tacit Knowledge",
    "Knowledge Holder",
    "Traditional Human-central Practice",
    "Technology-enable Practice",
    "Digital Technology",
    "Organizational Dependency",
    "Environmental Dependency",
    "Limitation"
}

# --------------------------
# FIXED FOR PYTHON 3.9 (Tuple instead of ())
# --------------------------
RELATION_RULES: Dict[str, Tuple[List[str], List[str]]] = {
    "be_documented_partially_by": (["Tacit Knowledge"], ["Knowledge Holder"]),
    "be_derived_from": (["Explicit Knowledge"], ["Explicit Knowledge"]),
    "translate_into": (["Explicit Knowledge"], ["Tacit Knowledge"]),
    "be_held_by": (["Tacit Knowledge", "Explicit Knowledge"], ["Knowledge Holder"]),
    "be_absorbed_by": (["Tacit Knowledge", "Explicit Knowledge"], ["Knowledge Holder"]),
    "be_captured_by": (["Tacit Knowledge"], ["Technology-enable Practice"]),
    "be_transferred_by": (
        ["Tacit Knowledge", "Explicit Knowledge"],
        ["Traditional Human-central Practice", "Technology-enable Practice"]
    ),
    "participate_in": (
        ["Knowledge Holder"],
        ["Traditional Human-central Practice", "Technology-enable Practice"]
    ),
    "depend_on": (
        ["Traditional Human-central Practice", "Technology-enable Practice"],
        ["Organizational Dependency", "Environmental Dependency"]
    ),
    "evaluate": (
        ["Technology-enable Practice", "Traditional Human-central Practice"],
        ["Tacit Knowledge", "Explicit Knowledge"]
    ),
    "adopt": (
        ["Technology-enable Practice"],
        ["Digital Technology", "Explicit Knowledge"]
    ),
    "be_constrained_by": (
        ["Traditional Human-central Practice", "Technology-enable Practice"],
        ["Limitation"]
    ),
    "resolve": (["Technology-enable Practice"], ["Limitation"]),
    "mitigate": (
        ["Technology-enable Practice", "Traditional Human-central Practice"],
        ["Tacit Knowledge", "Limitation"]
    ),
    "complement": (
        ["Technology-enable Practice"],
        ["Traditional Human-central Practice"]
    ),
    "cannot_fully_replace": (
        ["Technology-enable Practice"],
        ["Traditional Human-central Practice"]
    ),
    "be_difficult_to_capture_due_to": (["Tacit Knowledge"], ["Limitation"])
}


class VerifySchema:
    def __init__(self, data_base_path="../../data/graph/case_study/"):
        self.kg_case_path = f"{data_base_path}/case_3_unite/"
        self.kg_rag_path = f"{data_base_path}/case_4_v_kg/"

    def validate_nodes(self, case_id):
        """
        Validate node CSV: each node must belong to one of the 9 fixed categories.
        """
        input_path = f"{self.kg_case_path}{case_id}_nodes.csv"
        err_output_path = f"{self.kg_case_path}{case_id}_nodes_schema_removed.csv"
        output_path = f"{self.kg_rag_path}{case_id}_nodes.csv"

        try:
            df = pd.read_csv(input_path)
        except Exception as e:
            raise RuntimeError(f"Failed to read node CSV: {e}")

        required_cols = ["node_id", "category"]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise ValueError(f"Node CSV missing columns: {missing}")

        df["node_id"] = df["node_id"].astype(str).str.strip()
        df["category"] = df["category"].astype(str).str.strip()

        invalid_mask = ~df["category"].isin(FIXED_NODE_CATEGORIES)
        invalid_df = df[invalid_mask].copy()
        valid_df = df[~invalid_mask].copy()

        if not invalid_df.empty:
            invalid_df["error_reason"] = "Category not in fixed list"
            invalid_df.to_csv(err_output_path, index=False)
            print(f"Node validation: {len(df)} total, {len(valid_df)} valid, {len(invalid_df)} invalid.")
        else:
            print(f"Node validation passed: {len(valid_df)} valid nodes")

        valid_df.to_csv(output_path, index=False)

    def validate_edges(self, case_id):
        """
        Validate relation CSV against 13 relation rules.
        """
        input_path = f"{self.kg_case_path}{case_id}_edges.csv"
        valid_nodes_path = f"{self.kg_rag_path}{case_id}_nodes.csv"
        err_output_path = f"{self.kg_case_path}{case_id}_edges_schema_removed.csv"
        output_path = f"{self.kg_rag_path}{case_id}_edges.csv"

        try:
            df = pd.read_csv(input_path)
            valid_nodes_df = pd.read_csv(valid_nodes_path)
        except Exception as e:
            raise RuntimeError(f"Failed to read CSV: {e}")

        required_cols = ["src_node_id", "dst_node_id", "relation_type"]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise ValueError(f"Relation CSV missing columns: {missing}")

        df["src_node_id"] = df["src_node_id"].astype(str).str.strip()
        df["dst_node_id"] = df["dst_node_id"].astype(str).str.strip()
        df["relation_type"] = df["relation_type"].astype(str).str.strip()

        node_cat = dict(zip(valid_nodes_df["node_id"], valid_nodes_df["category"]))
        df["src_cat"] = df["src_node_id"].map(node_cat)
        df["dst_cat"] = df["dst_node_id"].map(node_cat)
        df["error_reason"] = ""

        # Check relation type
        unknown_rel = ~df["relation_type"].isin(RELATION_RULES.keys())
        df.loc[unknown_rel, "error_reason"] += "Unknown relation type; "

        # Check node exists
        valid_ids = set(valid_nodes_df["node_id"])
        bad_src = ~df["src_node_id"].isin(valid_ids)
        bad_dst = ~df["dst_node_id"].isin(valid_ids)
        df.loc[bad_src, "error_reason"] += "Source node not found; "
        df.loc[bad_dst, "error_reason"] += "Target node not found; "

        # Check category matching
        for idx, row in df.iterrows():
            rel = row["relation_type"]
            sc = row["src_cat"]
            tc = row["dst_cat"]

            if df.loc[idx, "error_reason"]:
                continue
            if rel not in RELATION_RULES:
                continue

            allow_src, allow_dst = RELATION_RULES[rel]

            if pd.isna(sc) or sc not in allow_src:
                df.loc[idx, "error_reason"] += f"for relation type '{rel}', the source category must be {allow_src}; "
            if pd.isna(tc) or tc not in allow_dst:
                df.loc[idx, "error_reason"] += (f"for relation type '{rel}', the destination category must be {allow_dst}; ")

        valid_mask = df["error_reason"] == ""
        valid_df = df[valid_mask].copy()
        invalid_df = df[~valid_mask].copy()

        if not invalid_df.empty:
            invalid_df.to_csv(err_output_path, index=False)
            print(f"Relation validation: {len(df)} total, {len(valid_df)} valid, {len(invalid_df)} invalid. The pass "
                  f"rate : {len(valid_df) / len(df): 2f}")
        else:
            print(f"Relation validation passed: {len(valid_df)} valid relations")

        valid_df.to_csv(output_path, index=False)

    def validate_schema(self, case_ids):
        for case_id in case_ids:
            print(f"\n===== Validating {case_id} =====")
            self.validate_nodes(case_id)
            self.validate_edges(case_id)


if __name__ == "__main__":
    vs = VerifySchema()
    case_ids = ['c201']  # you can add more: ['c001', 'c002', 'c003']
    vs.validate_schema(case_ids)