import pandas as pd
import os
import random


class AssembleVQ(object):
    def __init__(self):
        self.kg_path = "../data/graph/case_study/cases"
        pass

    def assemble_entity_vq(self, id):
        case_id_list = []
        if len(id):
            case_id_list.append(id)

        for case_id in case_id_list:
            csv_path = os.path.join(self.kg_path, f"{case_id}_nodes.csv")
            output_path = os.path.join(self.kg_path, f"{case_id}_nodes_vq.csv")
            df = pd.read_csv(csv_path)

            # Define label mapping
            label_map = {
                'E': 'explicitly defined',
                'I': 'implicitly defined'
            }

            # Store generated questions
            questions = []

            # Iterate through each row
            for idx, row in df.iterrows():
                name = str(row['name']).strip()
                category = str(row['category']).strip()
                label_code = str(row['labels']).strip().upper()

                # Get the English label description; keep original if not in mapping
                label_desc = label_map.get(label_code, label_code)

                # Concatenate question in the specified format
                positive_sample = f"{name} is {label_desc} as one {category}"
                questions.append({
                    'id': row['id'],
                    'case_id': case_id,
                    'group': idx,
                    'question': positive_sample,
                    'verification_label': 1

                })

                negative_sample = f"{name} isn't {label_desc} as one {category}"
                questions.append({
                    'id': row['id'],
                    'case_id': case_id,
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

    def choose_entity_samples(self, id, sample_path):

        case_id_list = []
        if len(id):
            case_id_list.append(id)

        all_selected = []
        for case_id in case_id_list:
            file_path = os.path.join(self.kg_path, f"{case_id}_nodes_vq.csv")

            try:
                # Read the CSV
                df = pd.read_csv(file_path)

                # Randomly select 1 row per GROUP (core logic)
                selected = df.groupby('group', group_keys=False).apply(
                    lambda group: group.sample(n=1)  # Direct random 1 row
                ).reset_index(drop=True)

                # Add a column to track which file the row came from (optional but useful)
                selected["case_id"] = case_id

                # Save to combined list
                all_selected.append(selected)

            except Exception as e:
                print(f"❌ Failed to process {case_id}: {str(e)}")

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

    def assemble_relation_vq(self, id):
        """
        Reads a source CSV (id, name, ...) and a relation CSV (start_id, end_id, type, case_id).
        Looks up names for start_id and end_id, then assembles:
        "{start_name} {type} {end_name}"
        """
        case_id_list = []
        if len(id):
            case_id_list.append(id)

        label_map = {
            'E': 'explicitly defined',
            'I': 'implicitly defined'
        }

        for case_id in case_id_list:
            source_csv = os.path.join(self.kg_path, f"{case_id}_nodes.csv")
            relation_csv = os.path.join(self.kg_path, f"{case_id}_relations.csv")
            output_csv = os.path.join(self.kg_path, f"{case_id}_relations_vq.csv")

            # ---------------- 1. Load Source & Build ID->Name Mapping ----------------
            if not os.path.exists(source_csv):
                raise FileNotFoundError(f"Source CSV not found: {source_csv}")

            src = pd.read_csv(source_csv)

            # Create fast lookup dictionary: {id: name}
            id_to_name = dict(zip(src['id'], src['name']))

            # ---------------- 2. Load Relation CSV ----------------
            if not os.path.exists(relation_csv):
                raise FileNotFoundError(f"Relation CSV not found: {relation_csv}")

            relation_map = {
                'E': 'explicitly defined',
                'I': 'implicitly defined'
            }

            df_rel = pd.read_csv(relation_csv)

            questions = []
            for idx, row in df_rel.iterrows():
                src_name = id_to_name[row['start_id']]
                dst_name = id_to_name[row['end_id']]

                relation_desc = relation_map.get(row['type'], row['type'])

                # Concatenate question in the specified format
                positive_sample = f"{src_name} {relation_desc} {dst_name}"
                questions.append({
                    'start_id': row['start_id'],
                    'end_id': row['end_id'],
                    'relation_type': row['type'],
                    'group': idx,
                    'question': positive_sample,
                    'verification_label': 1
                })

                def get_random_except(exclude_key, default="isn't related to"):
                    vals = [v for k, v in relation_map.items() if k != exclude_key]
                    return random.choice(vals) if vals else default

                relation_desc_random = get_random_except(row['type'])
                negative_sample = f"{src_name} {relation_desc_random} {dst_name}"
                questions.append({
                    'start_id': row['start_id'],
                    'end_id': row['end_id'],
                    'relation_type': row['type'],
                    'group': idx,
                    'question': negative_sample,
                    'verification_label': 0
                })

            result_df = pd.DataFrame(questions)
            result_df.to_csv(output_csv, index=False)

    def choose_relation_samples(self, id, sample_path):

        case_id_list = []
        if len(id):
            case_id_list.append(id)

        all_selected = []
        for case_id in case_id_list:
            file_path = os.path.join(self.kg_path, f"{case_id}_relations_vq.csv")

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
                print(f"❌ Failed to process {case_id}: {str(e)}")

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
    sample_path = os.path.join(vq.kg_path, "entity_samples.csv")
    vq.assemble_entity_vq("c003")
    vq.choose_entity_samples("c003",sample_path)

    sample_path = os.path.join(vq.kg_path, "relation_samples.csv")
    vq.assemble_relation_vq("c003")
    vq.choose_relation_samples("c003",sample_path)
