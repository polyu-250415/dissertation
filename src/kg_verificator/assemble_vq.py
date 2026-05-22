import pandas as pd
import os
import random

from src.utils.llm_mgmt.deepseek_local_api import chat_with_deepseek


class AssembleVQ(object):
    def __init__(self):
        self.kg_case_path = "../data/graph/case_study/cases/"
        self.kg_rag_path = "../data/graph/case_study/rag_vq/"
        self.node_template = """describe this entity <node: {{node}}, label: {{label}}> as a sentence without 
        explanation. """
        self.relation_template = """describe this relation <src_node: {{src_node}}, relation_type: {{relation_type}}, dst_node: {{dst_node}} > as a sentence without explanation."""
        pass

    @staticmethod
    def get_random_except(key_array, exclude_key, default="you see"):
        vals = [v for v in key_array if v != exclude_key]
        return random.choice(vals) if vals else default

    def assemble_entity_vq(self):
        for root, dirs, files in os.walk(self.kg_case_path):
            for file in files:
                if not file.endswith("nodes.csv"):
                    continue

                csv_path = os.path.join(root, file)
                output_path = os.path.join(self.kg_rag_path, file.replace("nodes","nodes_vq"))
                df = pd.read_csv(csv_path)

                # Define label mapping
                label_map = {
                    'E': 'explicitly defined',
                    'I': 'implicitly defined'
                }

                category_list = df['category'].unique().tolist()

                # Store generated questions
                questions = []

                # Iterate through each row
                for idx, row in df.iterrows():
                    name = str(row['node_name']).strip()
                    category = str(row['category']).strip()
                    label_code = str(row['evidence_label']).strip().upper()

                    # Get the English label description; keep original if not in mapping
                    label_desc = label_map.get(label_code, label_code)

                    evidence_statement = row['evidence_statement']
                    questions.append({
                        'node_id': row['node_id'],
                        'group': idx,
                        'question': evidence_statement,
                        'verification_label': 1

                    })

                    positive_sample =  f"'{name}' is an instance of '{category}'"
                    questions.append({
                        'node_id': row['node_id'],
                        'group': idx,
                        'question': positive_sample,
                        'verification_label': 1

                    })

                    fake_category = self.get_random_except(category_list, category)
                    negative_sample = f"'{name}' is an instance of '{fake_category}'"
                    questions.append({
                        'node_id': row['node_id'],
                        'group': idx,
                        'question': negative_sample,
                        'verification_label': 0
                    })

                # Save to output CSV if path is provided
                if output_path:
                    result_df = pd.DataFrame(questions)
                    result_df.to_csv(output_path, index=False)
                    print(f"\n✓ Generated {len(questions)} questions. Saved to: {output_path}")

        return

    def choose_entity_samples(self):

        for root, dirs, files in os.walk(self.kg_rag_path):

            for file in files:

                if not file.endswith("nodes_vq.csv"):
                    continue

                all_selected = []
                try:
                    df = pd.read_csv(os.path.join(root, file))

                    # Randomly select 1 row per GROUP (core logic)
                    selected = df.groupby('group', group_keys=False).apply(
                        lambda group: group.sample(n=1)  # Direct random 1 row
                    ).reset_index(drop=True)

                    # Save to combined list
                    all_selected.append(selected)

                except Exception as e:
                    print(f"❌ Failed to process {file}: {str(e)}")

                sample_path = os.path.join(self.kg_rag_path, file.replace("nodes_vq", "nodes_vq_selected"))

                if all_selected:
                    final_df = pd.concat(all_selected, ignore_index=True)

                    # Save to one single CSV
                    final_df.to_csv(sample_path, index=False, encoding="utf-8")

                    # Print summary
                    print("\n" + "-" * 50)
                    print(f"🎉 DONE! Combined results saved to: {file}")
                    print(f"Total rows selected: {len(final_df)}")
                    print(f"Total groups across all files: {final_df['group'].nunique()}")
                    print("\nPreview of final data:")
                    print(final_df.head())
                else:
                    print("⚠️ No CSV files found or processed!")

    def assemble_relation_vq(self):

        for root, dirs, files in os.walk(self.kg_case_path):
            for file in files:
                if not file.endswith("relations.csv"):
                    continue

                source_csv = os.path.join(root, file.replace("relations","nodes"))
                relation_csv = os.path.join(self.kg_case_path, file)
                output_csv = os.path.join(self.kg_rag_path, file.replace("relations","relations_vq"))

                # ---------------- 1. Load Source & Build ID->Name Mapping ----------------
                if not os.path.exists(source_csv):
                    raise FileNotFoundError(f"Source CSV not found: {source_csv}")

                src = pd.read_csv(source_csv)

                # Create fast lookup dictionary: {id: name}
                id_to_name = dict(zip(src['node_id'], src['node_name']))

                # ---------------- 2. Load Relation CSV ----------------
                if not os.path.exists(relation_csv):
                    raise FileNotFoundError(f"Relation CSV not found: {relation_csv}")

                df_rel = pd.read_csv(relation_csv)

                label_map = {
                    'E': 'explicitly',
                    'I': 'implicitly'
                }

                relation_type_array = df_rel['relation_type'].unique().tolist()

                questions = []
                for idx, row in df_rel.iterrows():
                    src_name = id_to_name[row['src_node_id']]
                    dst_name = id_to_name[row['dst_node_id']]
                    relation_type = row['relation_type']
                    evidence_label = label_map[row['evidence_label']]

                    evidence_statement = row['evidence_statement']
                    questions.append({
                        'src_node_id': row['src_node_id'],
                        'dst_node_id': row['dst_node_id'],
                        'relation_type': row['relation_type'],
                        'group': idx,
                        'question': evidence_statement,
                        'verification_label': 1
                    })

                    # Concatenate question in the specified format
                    positive_sample = f"'{src_name}' {relation_type} '{dst_name}' {evidence_label}"
                    questions.append({
                        'src_node_id': row['src_node_id'],
                        'dst_node_id': row['dst_node_id'],
                        'relation_type': row['relation_type'],
                        'group': idx,
                        'question': positive_sample,
                        'verification_label': 1
                    })

                    fake_relation = self.get_random_except(relation_type_array, row['relation_type'],
                                                                  default= "isn't related to ")
                    negative_sample = f"'{src_name}' {fake_relation} '{dst_name}' {evidence_label}"
                    questions.append({
                        'src_node_id': row['src_node_id'],
                        'dst_node_id': row['dst_node_id'],
                        'relation_type': row['relation_type'],
                        'group': idx,
                        'question': negative_sample,
                        'verification_label': 0
                    })

                result_df = pd.DataFrame(questions)
                result_df.to_csv(output_csv, index=False)

    def choose_relation_samples(self):

        for root, dirs, files in os.walk(self.kg_rag_path):

            for file in files:

                if not file.endswith("relations_vq.csv"):
                    continue

                file_path = os.path.join(self.kg_rag_path, file)
                all_selected = []
                try:
                    # Read the CSV
                    df = pd.read_csv(file_path)

                    # Randomly select 1 row per GROUP (core logic)
                    selected = df.groupby('group', group_keys=False).apply(
                        lambda group: group.sample(n=1)  # Direct random 1 row
                    ).reset_index(drop=True)

                    # Save to combined list
                    all_selected.append(selected)

                except Exception as e:
                    print(f"❌ Failed to process {file}: {str(e)}")

                sample_path = os.path.join(self.kg_rag_path, file.replace("relations_vq", "relations_vq_selected"))

                if all_selected:
                    final_df = pd.concat(all_selected, ignore_index=True)

                    # Save to one single CSV
                    final_df.to_csv(sample_path, index=False, encoding="utf-8")

                    # Print summary
                    print("\n" + "-" * 50)
                    print(f"🎉 DONE! Combined results saved to: {sample_path}")
                    print(f"Total rows selected: {len(final_df)}")
                    print(f"Total groups across all files: {final_df['group'].nunique()}")
                    print("\nPreview of final data:")
                    print(final_df.head())
                else:
                    print("⚠️ No CSV files found or processed!")


if __name__ == '__main__':
    vq=AssembleVQ()
    vq.assemble_entity_vq()
    vq.choose_entity_samples()

    vq.assemble_relation_vq()
    vq.choose_relation_samples()
