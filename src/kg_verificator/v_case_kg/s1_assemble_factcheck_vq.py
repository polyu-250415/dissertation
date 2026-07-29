import pandas as pd
import os
import random


class AssembleVQ(object):
    def __init__(self, data_base_path="../../data/graph/case_study/"):
        self.kg_case_path = f"{data_base_path}/case_3_unite/"
        self.kg_rag_path = f"{data_base_path}/case_4_v_kg/"

        self.assemble_relation_template = {
            "be_documented_partially_by": "is documented partially by",
            "translate_into":"translate into",
            "be_held_by": "is held by",
            "be_absorbed_by": "is absorbed by",
            "be_captured_by": "is captured by",
            "be_transferred_by": "is transferred by",
            "be_derived_from": "is derived from",
            "participate_in": "participant in",
            "depend_on": "depend on",
            "evaluate": "evaluate",
            "adopt": "adopt",
            "be_constrained_by": "is constrained by",
            "resolve": "resolve",
            "mitigate": "mitigate",
            "complement": "complement",
            "cannot_fully_replace": "cannot fully replace",
            "be_difficult_to_capture_due_to": "is difficult to capture due to"
        }

    @staticmethod
    def get_random_except(key_array, exclude_key, default="you see"):
        vals = [v for v in key_array if v != exclude_key]
        return random.choice(vals) if vals else default

    def assemble_entity_vq(self, case_ids):
        for case_id in case_ids:

            file = f'{self.kg_rag_path}{case_id}_nodes.csv'

            output_path = f'{self.kg_rag_path}{case_id}_nodes_vq.csv'
            df = pd.read_csv(file)

            # Store generated questions
            questions = []

            # Iterate through each row
            for idx, row in df.iterrows():
                name = str(row['node_name']).strip()
                category = str(row['category']).strip()

                evidence_statement = row['evidence_statement']
                questions.append({
                    'node_id': row['node_id'],
                    'group': idx,
                    'sample_type': 'evidence',
                    'question': evidence_statement,
                    'verification_label': 1

                })

                positive_sample = f"{name} has been discussed."
                questions.append({
                    'node_id': row['node_id'],
                    'group': idx,
                    'sample_type': 'assemble',
                    'question': positive_sample,
                    'verification_label': 1

                })

                """fake_category = self.get_random_except(category_list, category)
                negative_sample = f"'{name}' is an instance of '{fake_category}'"
                questions.append({
                    'node_id': row['node_id'],
                    'group': idx,
                    'sample_type': 'assemble',
                    'question': negative_sample,
                    'verification_label': 0
                })"""

            # Save to output CSV if path is provided
            if output_path:
                result_df = pd.DataFrame(questions)
                result_df.to_csv(output_path, index=False)
                print(f"\n✓ Generated {len(questions)} questions. Saved to: {output_path}")


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

    def assemble_relation_vq(self, case_ids):

        for case_id in case_ids:

            source_csv = f'{self.kg_rag_path}{case_id}_nodes.csv'
            relation_csv = f'{self.kg_rag_path}{case_id}_edges.csv'
            output_csv = f'{self.kg_rag_path}{case_id}_edges_vq.csv'

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

            questions = []
            for idx, row in df_rel.iterrows():
                src_name = id_to_name[row['src_node_id']]
                dst_name = id_to_name[row['dst_node_id']]
                relation_type = row['relation_type']

                evidence_statement = row['evidence_statement']
                questions.append({
                    'src_node_id': row['src_node_id'],
                    'dst_node_id': row['dst_node_id'],
                    'relation_type': row['relation_type'],
                    'group': idx,
                    'sample_type': 'evidence',
                    'question': evidence_statement,
                    'verification_label': 1
                })

                # Concatenate question in the specified format
                positive_sample = f"{src_name} {self.assemble_relation_template[relation_type]} {dst_name}"
                questions.append({
                    'src_node_id': row['src_node_id'],
                    'dst_node_id': row['dst_node_id'],
                    'relation_type': row['relation_type'],
                    'group': idx,
                    'sample_type': 'assemble',
                    'question': positive_sample,
                    'verification_label': 1
                })

                """fake_relation = self.get_random_except(relation_type_array, row['relation_type'],
                                                              default= "isn't related to ")
                negative_sample = f"'{src_name}' {fake_relation} '{dst_name}'"
                questions.append({
                    'src_node_id': row['src_node_id'],
                    'dst_node_id': row['dst_node_id'],
                    'relation_type': row['relation_type'],
                    'group': idx,
                    'sample_type': 'assemble',
                    'question': negative_sample,
                    'verification_label': 0
                })"""

            result_df = pd.DataFrame(questions)
            result_df.to_csv(output_csv, index=False)

    def choose_relation_samples(self, case_ids):

        for root, dirs, files in os.walk(self.kg_rag_path):

            file_path = f'{self.kg_case_path}{case_ids}_edges.csv'
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
                print(f"❌ Failed to process {file_path}: {str(e)}")

            sample_path = file_path.replace("relations_vq", "relations_vq_selected")

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
    #vq.choose_entity_samples()

    vq.assemble_relation_vq()
    #vq.choose_relation_samples()
