import pandas as pd
import numpy as np
from collections import defaultdict
from typing import Set, Tuple, List, Dict
from itertools import combinations
from haystack_integrations.components.embedders.fastembed import FastembedTextEmbedder


class AssembleEAVQ:
    def __init__(self):
        self.model_name = 'BAAI/bge-small-en-v1.5'
        self.embedder = None
        self.path = '../../data/graph/case_study/case_5_v_ea/'
        pass

    def init_embedder(self):
        self.embedder = FastembedTextEmbedder(model=self.model_name,
                                        cache_dir="/Users/meimei/work/coding/dissertation/src/models/fastembed/bge-small-en-v1.5",
                                              local_files_only=True,
                                              parallel=0)

    @staticmethod
    def cosine_similarity(vec_a, vec_b):
        """Compute cosine similarity between two vectors."""
        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(vec_b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return np.dot(vec_a, vec_b) / (norm_a * norm_b)

    def find_best_pairs(self, call_idx):
        """
        For each category, compute cosine similarity between node names using Fastembed
        and return the best matching pair (highest similarity).
        """
        for call_id in call_idx:
            csv_path = f"{self.path}/{call_id}_nodes.csv"
            df = pd.read_csv(csv_path)
            df = df[['node_id', 'node_name', 'category']].dropna()

            results = []
            category_score_threshold = 0.85

            for category, group in df.groupby('category'):
                if len(group) < 2:
                    print(f"Skipping '{category}' (only {len(group)} node)")
                    continue

                node_ids = group['node_id'].tolist()
                node_names = group['node_name'].tolist()

                # Embed all texts in this category
                embeddings = []
                for name in node_names:
                    emb = self.embedder.run(text=name)['embedding']
                    embeddings.append(np.array(emb))

                best_score = -1.0
                best_pair = (None, None)
                score_threshold = -1
                n = len(node_ids)

                for i, j in combinations(range(n), 2):
                    score = self.cosine_similarity(embeddings[i], embeddings[j])
                    print(f"cosine_similarity {category}, {node_ids[i]}, {node_ids[j]}, {score}")
                    results.append({
                        'category': category,
                        'node_id_1': node_ids[i],
                        'node_name_1': node_names[i],
                        'node_id_2': node_ids[j],
                        'node_name_2': node_names[j],
                        'similarity_score': round(score, 4)})
                    if score > score_threshold:
                        score_threshold = score
                    """if score > best_score:
                        best_score = score
                        best_pair = (i, j)"""

                """if best_pair[0] is not None:
                    i, j = best_pair
                    results.append({
                        'category': category,
                        'node_id_1': node_ids[i],
                        'node_name_1': node_names[i],
                        'node_id_2': node_ids[j],
                        'node_name_2': node_names[j],
                        'similarity_score': round(best_score, 4)
                    })"""
                if category_score_threshold > score_threshold:
                    category_score_threshold = score_threshold

            result_df = pd.DataFrame(results)
            result_df = result_df.sort_values('similarity_score', ascending=False)
            result_df = result_df[result_df['similarity_score'] >= category_score_threshold]
            result_df.to_csv(f"{self.path}/{call_id}_nodes_similarity.csv", index=False)

    def map_similar_nodes(self):
        self.init_embedder()
        call_ids = ['c001', 'c002', 'c003', 'c004', 'c005', 'c006']
        self.find_best_pairs(call_ids)

    @staticmethod
    def load_similarity_pairs(filepath: str) -> List[Dict]:
        """Load node similarity pairs from CSV using pandas."""
        df = pd.read_csv(filepath)
        pairs = df.to_dict(orient='records')
        return pairs

    @staticmethod
    def load_relations(filepath: str) -> Tuple[List[Dict], Set[Tuple[str, str, str]]]:
        """Load relations using pandas and build a set of (src, dst, relation_type)."""
        df = pd.read_csv(filepath)
        relations = df.to_dict(orient='records')
        triple_set = set()
        for _, row in df.iterrows():
            triple_set.add((row['src_node_id'], row['dst_node_id'], row['relation_type']))
        return relations, triple_set

    @staticmethod
    def build_relations_by_node(relations: List[Dict]) -> Dict[str, List[Dict]]:
        """Map node_id -> list of relations where it appears as src or dst."""
        by_node = defaultdict(list)
        for rel in relations:
            src = rel['src_node_id']
            dst = rel['dst_node_id']
            by_node[src].append(rel)
            by_node[dst].append(rel)
        return by_node

    @staticmethod
    def validate_pair(id_to_name: Dict, pair: Dict, by_node: Dict, triple_set: Set[Tuple[str, str, str]]):
        """
        For a given similarity pair (node_id_1, node_id_2):
        - Retrieve all relations containing node_id_1.
        - Create new relations by replacing node_id_1 with node_id_2.
        - Count how many of these new relations already exist in triple_set.
        Return a dictionary with validation results.
        """
        id1 = pair['node_id_1']
        id2 = pair['node_id_2']

        relations_with_id1 = by_node.get(id1, [])

        ea_vq = []
        for rel in relations_with_id1:
            src = rel['src_node_id']
            dst = rel['dst_node_id']
            rel_type = rel['relation_type']

            if src == id1:
                new_src_id = id2
                new_dst_id = dst
            elif dst == id1:
                new_src_id = src
                new_dst_id = id2
            else:
                continue  # Should not happen

            new_triple = (new_src_id, new_dst_id, rel_type)
            exists = new_triple in triple_set
            positive_sample = f"'{id_to_name[new_src_id]}' {rel_type} '{id_to_name[new_dst_id]}"
            if not exists:
                ea_vq.append({
                    'node_id_1': id1,
                    'node_id_2': id2,
                    'src_node_id': src,
                    'dst_node_id': dst,
                    'relation_type': rel_type,
                    'new_src_id': new_src_id,
                    'new_dst_id': new_dst_id,
                    'question': positive_sample,
                    'verification_label':1
                })

        return ea_vq

    def assemble_ea_vq(self, call_idx):

        for call_id in call_idx:
            nodes_file = f'../../data/graph/case_study/case_5_v_ea/{call_id}_nodes.csv'
            similarity_file = f'../../data/graph/case_study/case_5_v_ea/{call_id}_nodes_similarity.csv'
            relations_file = f'../../data/graph/case_study/case_5_v_ea/{call_id}_relations.csv'

            src = pd.read_csv(nodes_file)

            # Create fast lookup dictionary: {id: name}
            id_to_name = dict(zip(src['node_id'], src['node_name']))

            print("Loading data with pandas...")
            pairs = self.load_similarity_pairs(similarity_file)
            relations, triple_set = self.load_relations(relations_file)
            by_node = self.build_relations_by_node(relations)

            print(f"Loaded {len(pairs)} similarity pairs and {len(relations)} relations.\n")

            results = []
            for pair in pairs:
                res = self.validate_pair(id_to_name, pair, by_node, triple_set)
                results.extend(res)

            pd.DataFrame(results).to_csv(f'{self.path}/{call_id}_ea_vq.csv', index=False)

if __name__ == '__main__':
    obj = AssembleEAVQ()

    call_ids = ['c002']
    obj.init_embedder()
    obj.find_best_pairs(call_ids)
    obj.assemble_ea_vq(call_ids)