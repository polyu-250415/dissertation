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
    "Limitation",
    "Knowledge Learner"
}

# --------------------------
# FIXED FOR PYTHON 3.9 (Tuple instead of ())
# --------------------------
RELATION_RULES: Dict[str, Tuple[List[str], List[str]]] = {
    "be_documented_partially_by": (["Tacit Knowledge"], ["Knowledge Holder"]),
    "be_derived_from": (["Explicit Knowledge"], ["Explicit Knowledge"]),
    "translate_into": (["Explicit Knowledge"], ["Tacit Knowledge"]),
    "be_shared_by": (["Tacit Knowledge", "Explicit Knowledge"], ["Knowledge Holder"]),
    "be_absorbed_by": (["Tacit Knowledge", "Explicit Knowledge"], ["Knowledge Learner"]),
    "be_captured_by": (["Tacit Knowledge"], ["Technology-enable Practice", "Traditional Human-central Practice"]),
    "be_transferred_by": (
        ["Explicit Knowledge", "Tacit Knowledge"],
        ["Traditional Human-central Practice", "Technology-enable Practice"]
    ),
    "participate_in": (
        ["Knowledge Holder","Knowledge Learner"],
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
        ["Limitation", "Organizational Dependency", "Environmental Dependency"]
    ),
    "complement": (
        ["Technology-enable Practice"],
        ["Traditional Human-central Practice"]
    ),
    "cannot_fully_replace": (
        ["Technology-enable Practice"],
        ["Traditional Human-central Practice"]
    ),
    "be_difficult_to_capture_due_to": (["Tacit Knowledge"], ["Limitation"]),
    "be_composed_of": (["Technology-enable Practice"], ["Technology-enable Practice"])
}


class VerifySchema:
    def __init__(self, data_base_path="../../data/graph/case_study/"):
        self.raw_kg_path = f"{data_base_path}/case_1_raw_kg_m/"
        self.kg_case_path = f"{data_base_path}/case_3_unite/"
        self.kg_rag_path = f"{data_base_path}/case_4_v_kg/"

    def validate_nodes(self, input_path, err_output_path, output_path):
        """
        Validate node CSV: each node must belong to one of the 9 fixed categories.
        """

        try:
            df = pd.read_csv(input_path)
        except Exception as e:
            print(f"Node validation: {e}")
            return

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
            print(f"Node validation: {len(df)} total, {len(valid_df)} valid, {len(invalid_df)} invalid.")
            invalid_df["error_reason"] = "Category not in fixed list"
            if len(err_output_path):
                invalid_df.to_csv(err_output_path, index=False)
            else:
                print(invalid_df[['node_id', 'node_name', 'category', 'error_reason']].to_string())

        if len(output_path):
            valid_df.to_csv(output_path, index=False)
        else:
            print(f"Node validation failed: \n {len(valid_df)} valid nodes")

    def validate_edges(self, input_path, valid_nodes_path, err_output_path, output_path):
        """
        Validate relation CSV against 13 relation rules.
        """

        try:
            df = pd.read_csv(input_path)
            valid_nodes_df = pd.read_csv(valid_nodes_path)
        except Exception as e:
            print(f"Edge validation: {e}")
            return

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
            print(f"Relation validation: {len(df)} total, {len(valid_df)} valid, {len(invalid_df)} invalid. The pass "
                  f"rate : {len(valid_df) / len(df): 2f}")
            if len(err_output_path):
                invalid_df.to_csv(err_output_path, index=False)
            else:
                print(invalid_df[['src_node_id', 'dst_node_id', 'relation_type','error_reason']].to_string())

        if len(output_path):
            valid_df.to_csv(output_path, index=False)
        else:
            print(f"Relation validation passed: \n {len(valid_df)} valid relations")

        return invalid_df.shape[0]

    def validate_schema(self, case_ids):
        for case_id in case_ids:
            print(f"\n===== Validating {case_id} =====")
            input_path = f"{self.kg_case_path}{case_id}_nodes.csv"
            err_output_path = f"{self.kg_case_path}{case_id}_nodes_schema_removed.csv"
            output_path = f"{self.kg_rag_path}{case_id}_nodes.csv"
            self.validate_nodes(input_path, err_output_path, output_path)

            input_path = f"{self.kg_case_path}{case_id}_edges.csv"
            valid_nodes_path = f"{self.kg_rag_path}{case_id}_nodes.csv"
            err_output_path = f"{self.kg_case_path}{case_id}_edges_schema_removed.csv"
            output_path = f"{self.kg_rag_path}{case_id}_edges.csv"
            self.validate_edges(input_path, valid_nodes_path, err_output_path, output_path)

    def validate_raw_kg_schema(self, case_id, model):
        print(f"\n===== Validating {case_id} =====")
        input_path = f"{self.raw_kg_path}{case_id}_{model}_nodes.csv"
        self.validate_nodes(input_path, "", "")

        input_path = f"{self.raw_kg_path}{case_id}_{model}_edges.csv"
        valid_nodes_path = f"{self.raw_kg_path}{case_id}_{model}_nodes.csv"
        err_edge_no = self.validate_edges(input_path, valid_nodes_path, "", "")
        return err_edge_no



if __name__ == "__main__":
    vs = VerifySchema()
    case_id = 'c001'
    model = "deepseek"
    vs.validate_raw_kg_schema(case_id, model)