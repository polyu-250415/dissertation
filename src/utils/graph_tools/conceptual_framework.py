#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import sys
import os
import re
from pathlib import Path
from neo4j import GraphDatabase
from collections import defaultdict

# ----------------------------- Excel 读取与数据预处理 -----------------------------

def read_excel_sheet(excel_path, sheet_name, required_columns):
    df = pd.read_excel(excel_path, sheet_name=sheet_name, dtype=str)
    df.columns = df.columns.str.strip()
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Sheet '{sheet_name}' missing required columns: {missing}")
    df = df.dropna(how='all')
    if 'Node Name' in df.columns:
        df = df[df['Node Name'].notna() & (df['Node Name'].str.strip() != '')]
    return df

def split_or(value):
    if pd.isna(value):
        return []
    s = str(value).strip()
    if s == '':
        return []
    parts = re.split(r'\s*OR \s*', s, flags=re.IGNORECASE)
    return [p.strip() for p in parts if p.strip() != '']

def generate_nodes_data(entity_df):
    """返回节点列表，每个节点为字典，包含 :ID, :LABEL, name, Category, Description, Example"""
    entity_df = entity_df.drop_duplicates(subset=['Node Name'], keep='first')
    nodes = []
    for _, row in entity_df.iterrows():
        node = {
            'id': row['Node Name'],          # 用做唯一标识
            'label': row['Category'],
            'name': row['Node Name'],
            'Category': row.get('Category', ''),
            'Description': row.get('Description', ''),
            'Example': row.get('Example', '')
        }
        nodes.append(node)
    return nodes

def generate_relations_data(edge_df, valid_node_ids):
    """返回关系列表，每个关系为字典，包含 :START_ID, :END_ID, :TYPE, Description, Example"""
    relations = []
    for _, row in edge_df.iterrows():
        src_list = split_or(row.get('Src Node Name', ''))
        dst_list = split_or(row.get('Dst Node Name', ''))
        if not src_list or not dst_list:
            continue
        for src in src_list:
            for dst in dst_list:
                if src in valid_node_ids and dst in valid_node_ids:
                    rel = {
                        'start_id': src,
                        'end_id': dst,
                        'type': row.get('Relation Type', ''),
                        'Description': row.get('Description', ''),
                        'Example': row.get('Example', '')
                    }
                    relations.append(rel)
    return relations

# ----------------------------- API 导入函数 -----------------------------

def clear_database(driver):
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
        print("Database cleared.")

def import_nodes_via_api(driver, nodes, batch_size=1000):
    """
    按标签分组，批量创建节点。
    使用 MERGE 来避免重复（基于 id 属性），若想强制创建可用 CREATE。
    """
    # 按标签分组
    label_groups = defaultdict(list)
    for node in nodes:
        label_groups[node['label']].append(node)

    with driver.session() as session:
        for label, node_list in label_groups.items():
            print(f"Importing {len(node_list)} nodes with label '{label}'...")
            # 分批提交
            for i in range(0, len(node_list), batch_size):
                batch = node_list[i:i+batch_size]
                # 构建 Cypher：MERGE (n:Label {id: row.id}) SET n += row
                # 注意：row 中要排除 'label' 字段，因为标签不能作为属性
                # 我们使用 UNWIND $batch AS row
                query = f"""
                UNWIND $batch AS row
                MERGE (n:`{label}` {{id: row.id}})
                ON CREATE SET n = row
                ON MATCH SET n = row
                """
                # 但 row 包含 'label' 键，我们不想把它设为属性，可以在 SET 前删除
                # 或在 SET 时使用排除，但简单做法：在 Python 中去除 'label'
                for node in batch:
                    node.pop('label', None)   # 移除标签字段，因为它是动态的
                result = session.run(query, batch=batch)
                # 可以获取统计信息
                summary = result.consume()
                print(f"  Batch {i//batch_size + 1} done. "
                      f"Nodes created/updated: {summary.counters.nodes_created + summary.counters.nodes_created}")

def import_relations_via_api(driver, relations, batch_size=1000):
    """
    按关系类型分组，批量创建关系。
    使用 MERGE 避免重复，匹配节点基于 id 属性。
    """
    type_groups = defaultdict(list)
    for rel in relations:
        type_groups[rel['type']].append(rel)

    with driver.session() as session:
        for rel_type, rel_list in type_groups.items():
            print(f"Importing {len(rel_list)} relations with type '{rel_type}'...")
            for i in range(0, len(rel_list), batch_size):
                batch = rel_list[i:i+batch_size]
                query = f"""
                UNWIND $batch AS row
                MATCH (a {{id: row.start_id}})
                MATCH (b {{id: row.end_id}})
                MERGE (a)-[r:`{rel_type}`]->(b)
                ON CREATE SET r = row
                ON MATCH SET r = row
                """
                # 移除 type 键，不将其设为属性
                for rel in batch:
                    rel.pop('type', None)
                result = session.run(query, batch=batch)
                summary = result.consume()
                print(f"  Batch {i//batch_size + 1} done. "
                      f"Relations created/updated: {summary.counters.relationships_created + summary.counters.relationships_created}")

# ----------------------------- 主程序 -----------------------------

def main(excel_path, output_dir='.', neo4j_uri=None, neo4j_user=None, neo4j_password=None,
         clear_db=False, import_via_api=True, batch_size=1000):
    if not os.path.isfile(excel_path):
        print(f"Error: File '{excel_path}' does not exist.")
        sys.exit(1)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 读取 Excel
        entity_df = read_excel_sheet(excel_path, 'Entity', ['Node Name', 'Category', 'Description', 'Example'])
        print(f"Read {len(entity_df)} nodes.")
        edge_df = read_excel_sheet(excel_path, 'Edge',
                                   ['Relation Type', 'Src Node Name', 'Dst Node Name', 'Description', 'Example'])
        print(f"Read {len(edge_df)} raw relationship rows.")

        # 生成节点和关系数据
        nodes = generate_nodes_data(entity_df)
        valid_ids = set(node['id'] for node in nodes)
        relations = generate_relations_data(edge_df, valid_ids)
        print(f"Generated {len(nodes)} unique nodes and {len(relations)} valid relationship combinations.")

        # 可选：保存 CSV（供查看）
        nodes_df = pd.DataFrame(nodes)
        nodes_df.to_csv(output_dir / 'nodes.csv', index=False, encoding='utf-8-sig')
        if relations:
            rels_df = pd.DataFrame(relations)
            rels_df.to_csv(output_dir / 'relations.csv', index=False, encoding='utf-8-sig')
        print(f"CSV files saved to {output_dir} (optional).")

        # 通过 API 导入
        if import_via_api:
            if not all([neo4j_uri, neo4j_user, neo4j_password]):
                print("Error: Neo4j connection details missing.")
                sys.exit(1)
            driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
            try:
                if clear_db:
                    clear_database(driver)
                if nodes:
                    import_nodes_via_api(driver, nodes, batch_size)
                if relations:
                    import_relations_via_api(driver, relations, batch_size)
                print("Import completed successfully.")
            finally:
                driver.close()

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    # ========== 用户配置区域 ==========
    EXCEL_FILE = '../../conf/coding_schema/coding_schema.xlsx'
    OUTPUT_DIR = '../../conf/coding_schema/'
    NEO4J_URI = 'bolt://localhost:7687'
    NEO4J_USER = 'neo4j'
    NEO4J_PASSWORD = 'MyNewPass123!'
    CLEAR_DB = True          # 是否清空现有数据
    BATCH_SIZE = 1000        # 每批提交数量
    # ==================================

    main(EXCEL_FILE, OUTPUT_DIR, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD,
         clear_db=CLEAR_DB, import_via_api=True, batch_size=BATCH_SIZE)