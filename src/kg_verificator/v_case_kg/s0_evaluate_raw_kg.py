import pandas as pd
import networkx as nx
from datetime import datetime
from typing import List, Dict
from src.utils.graph_tools.create_paper_graph_by_id import create_kg_by_case
from src.kg_verificator.v_case_kg.s0_verify_schema import VerifySchema


class CSVGraphQualityInspector:
    def __init__(self, node_csv_path: str, edge_csv_path: str):
        self.node_csv = node_csv_path
        self.edge_csv = edge_csv_path
        self.report = {
            "check_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "node_metrics": {},
            "edge_metrics": {},
            "graph_topology": {},
            "node_type_degree_metrics": {},   # 新增：按节点类别出入度度量
            "warnings": []
        }
        # 加载数据
        self.nodes_df = self._load_and_validate_nodes()
        self.edges_df = self._load_and_validate_edges()
        # 节点ID集合（用于快速匹配）
        self.node_id_set = set(self.nodes_df["node_id"].dropna().unique())
        # 建图（【重点修改】使用有向图，支持入度出度）
        self.G = self._build_graph()
        # 构建 node_id -> category 映射
        self.node_cat_map = dict(
            self.nodes_df[["node_id", "category"]].dropna(subset=["category"]).values
        )
        self.relation_type_map = {
            "be_documented_partially_by": 0,
            "translate_into": 0,
            "be_shared_by": 0,
            "be_absorbed_by": 0,
            "be_captured_by": 0,
            "be_transferred_by": 0,
            "be_derived_from": 0,
            "participate_in": 0,
            "depend_on": 0,
            "evaluate": 0,
            "adopt": 0,
            "be_constrained_by": 0,
            "resolve": 0,
            "mitigate": 0,
            "complement": 0,
            "cannot_fully_replace": 0,
            "be_difficult_to_capture_due_to": 0,
            "be_composed_of": 0,
        }
        self.entity_category_map = {
            "Explicit Knowledge":0,
            "Tacit Knowledge":0,
            "Knowledge Holder":0,
            "Traditional Human-central Practice":0,
            "Technology-enable Practice":0,
            "Digital Technology":0,
            "Organizational Dependency":0,
            "Environmental Dependency":0,
            "Limitation":0,
            "Knowledge Learner":0
        }

    def _load_and_validate_nodes(self) -> pd.DataFrame:
        """加载节点CSV并做基础校验"""
        try:
            df = pd.read_csv(self.node_csv)
            # 校验必填列存在
            required_cols = ["node_id", "node_name", "category"]
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                self.report["warnings"].append(f"节点CSV缺失必填列: {missing_cols}")
                return pd.DataFrame()
            # 去重空行
            df = df.dropna(how="all").reset_index(drop=True)
            # 统一node_id为字符串，避免类型不匹配
            df["node_id"] = df["node_id"].astype(str).str.strip()
            return df
        except Exception as e:
            self.report["warnings"].append(f"节点CSV加载失败: {str(e)}")
            return pd.DataFrame()

    def _load_and_validate_edges(self) -> pd.DataFrame:
        """加载关系CSV并做基础校验"""
        try:
            df = pd.read_csv(self.edge_csv)
            # 校验必填列存在
            required_cols = ["src_node_id", "dst_node_id", "relation_type"]
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                self.report["warnings"].append(f"关系CSV缺失必填列: {missing_cols}")
                return pd.DataFrame()
            # 去重空行
            df = df.dropna(how="all").reset_index(drop=True)
            # 统一ID为字符串，和节点表对齐
            df["src_node_id"] = df["src_node_id"].astype(str).str.strip()
            df["dst_node_id"] = df["dst_node_id"].astype(str).str.strip()
            return df
        except Exception as e:
            self.report["warnings"].append(f"关系CSV加载失败: {str(e)}")
            return pd.DataFrame()

    def _build_graph(self) -> nx.DiGraph:
        """【修改】构建有向图DiGraph，支持入度、出度计算"""
        G = nx.DiGraph()
        # 添加节点
        G.add_nodes_from(self.node_id_set)
        # 添加边（去重，避免重复边影响拓扑计算）
        valid_edges = self.edges_df[
            (self.edges_df["src_node_id"].isin(self.node_id_set)) &
            (self.edges_df["dst_node_id"].isin(self.node_id_set))
        ][["src_node_id", "dst_node_id"]].values.tolist()
        G.add_edges_from(valid_edges)
        return G

    # ========== 1. 新增：按节点类别统计入度、出度指标 ==========
    def stat_degree_by_node_category(self):
        """
        按category分组，度量每个节点类型：
        节点数量、总入度、总出度、平均入度、平均出度
        """
        G = self.G
        cat_metrics = {}

        # 遍历所有节点，获取入度、出度 + 所属类别
        for n in G.nodes():
            in_deg = G.in_degree(n)
            out_deg = G.out_degree(n)
            category = self.node_cat_map.get(n, "unknown")

            if category not in cat_metrics:
                cat_metrics[category] = {
                    "node_count": 0,
                    "total_in_degree": 0,
                    "total_out_degree": 0,
                    "avg_in_degree": 0.0,
                    "avg_out_degree": 0.0
                }
            cat_metrics[category]["node_count"] += 1
            cat_metrics[category]["total_in_degree"] += in_deg
            cat_metrics[category]["total_out_degree"] += out_deg

        # 计算均值
        for cat, info in cat_metrics.items():
            cnt = info["node_count"]
            if cnt > 0:
                info["avg_in_degree"] = round(info["total_in_degree"] / cnt, 4)
                info["avg_out_degree"] = round(info["total_out_degree"] / cnt, 4)

        self.report["node_type_degree_metrics"] = cat_metrics

    # ========== 1. 节点质量指标 ==========
    def stat_node_basic(self):
        """节点总量、分类分布、空值基础统计"""
        total_nodes = len(self.nodes_df)
        # 按category分布
        category_dist = self.nodes_df["category"].value_counts().to_dict()
        # 空category节点
        empty_category_cnt = self.nodes_df["category"].isna().sum()

        self.report["node_metrics"]["total_nodes"] = total_nodes
        self.report["node_metrics"]["category_distribution"] = category_dist
        self.report["node_metrics"]["empty_category_nodes"] = empty_category_cnt
        self.report["node_metrics"]["empty_category_ratio"] = round(empty_category_cnt / total_nodes, 4) if total_nodes > 0 else 0.0

    def check_duplicate_nodes(self) -> Dict:
        """检测node_id主键重复的节点"""
        total_nodes = len(self.nodes_df)
        # 重复node_id统计
        dup_id_stats = self.nodes_df["node_id"].value_counts()
        dup_id_groups = dup_id_stats[dup_id_stats > 1]
        dup_node_count = dup_id_groups.sum() - len(dup_id_groups)  # 重复的行数
        dup_ratio = dup_node_count / total_nodes if total_nodes > 0 else 0.0

        self.report["node_metrics"]["duplicate_nodes"] = {
            "duplicate_group_count": len(dup_id_groups),
            "duplicate_node_count": dup_node_count,
            "duplicate_ratio": round(dup_ratio, 4),
            "detail": dup_id_groups.head(200).to_dict()  # 限制明细条数
        }
        return self.report["node_metrics"]["duplicate_nodes"]

    def check_node_missing_required_prop(self, required_props: List[str]):
        """节点必填属性缺失统计"""
        total_nodes = len(self.nodes_df)
        missing_stats = {}
        for prop in required_props:
            if prop not in self.nodes_df.columns:
                self.report["warnings"].append(f"节点表不存在属性: {prop}")
                continue
            # 统计空值/空字符串/全空格的缺失值
            missing_mask = self.nodes_df[prop].isna() | (self.nodes_df[prop].astype(str).str.strip() == "")
            missing_cnt = missing_mask.sum()
            missing_ratio = missing_cnt / total_nodes if total_nodes > 0 else 0.0
            missing_stats[prop] = {
                "missing_count": missing_cnt,
                "total_nodes": total_nodes,
                "missing_ratio": round(missing_ratio, 4)
            }
        self.report["node_metrics"]["required_prop_missing"] = missing_stats

    def check_isolated_nodes(self):
        """孤立节点统计（在关系表中无任何入边/出边的节点）"""
        total_nodes = len(self.nodes_df)
        # 所有出现在关系中的节点ID
        all_related_nodes = set(self.edges_df["src_node_id"]).union(set(self.edges_df["dst_node_id"]))
        # 孤立节点 = 节点表中不在关系中的节点
        isolated_nodes = self.node_id_set - all_related_nodes
        isolated_cnt = len(isolated_nodes)
        isolated_ratio = isolated_cnt / total_nodes if total_nodes > 0 else 0.0

        self.report["node_metrics"]["isolated_nodes"] = {
            "isolated_count": isolated_cnt,
            "isolated_ratio": round(isolated_ratio, 4),
            "isolated_node_ids": list(isolated_nodes)[:200]  # 限制明细
        }

    # ========== 2. 关系质量指标 ==========
    def stat_edge_basic(self):
        """关系总量、类型分布、自环边统计"""
        total_edges = len(self.edges_df)
        # 按关系类型分布
        rel_type_dist = self.edges_df["relation_type"].value_counts().to_dict()
        # 自环边（src==dst）
        self_loop_mask = self.edges_df["src_node_id"] == self.edges_df["dst_node_id"]
        self_loop_cnt = self_loop_mask.sum()
        self_loop_ratio = self_loop_cnt / total_edges if total_edges > 0 else 0.0

        self.report["edge_metrics"]["total_edges"] = total_edges
        self.report["edge_metrics"]["rel_type_distribution"] = rel_type_dist
        self.report["edge_metrics"]["self_loop_edges"] = {
            "self_loop_count": self_loop_cnt,
            "self_loop_ratio": round(self_loop_ratio, 4)
        }

    def check_dangling_edges(self):
        """悬挂边统计（起点/终点不在节点表中的边）"""
        total_edges = len(self.edges_df)
        # 起点不存在
        src_not_exist_mask = ~self.edges_df["src_node_id"].isin(self.node_id_set)
        # 终点不存在
        dst_not_exist_mask = ~self.edges_df["dst_node_id"].isin(self.node_id_set)
        # 任意一端不存在的悬挂边
        dangling_mask = src_not_exist_mask | dst_not_exist_mask
        dangling_cnt = dangling_mask.sum()
        dangling_ratio = dangling_cnt / total_edges if total_edges > 0 else 0.0

        self.report["edge_metrics"]["dangling_edges"] = {
            "dangling_count": dangling_cnt,
            "dangling_ratio": round(dangling_ratio, 4),
            "detail": self.edges_df[dangling_mask].head(200).to_dict("records")
        }

    def check_duplicate_relationships(self):
        """重复三元组统计（相同起点、关系类型、终点的重复边）"""
        total_edges = len(self.edges_df)
        # 按三元组分组计数
        dup_stats = self.edges_df.groupby(["src_node_id", "dst_node_id", "relation_type"]).size()
        # 重复的三元组（出现次数>1）
        dup_groups = dup_stats[dup_stats > 1]
        dup_edge_count = (dup_groups - 1).sum()  # 重复的边总数
        dup_ratio = dup_edge_count / total_edges if total_edges > 0 else 0.0

        self.report["edge_metrics"]["duplicate_relationships"] = {
            "duplicate_group_count": len(dup_groups),
            "duplicate_edge_count": dup_edge_count,
            "duplicate_ratio": round(dup_ratio, 4),
            "detail": dup_groups.head(200).to_dict()
        }

    def check_schema_violation(self, schema_rules: List[Dict]):
        """
        Schema合规性校验
        规则示例: [{"rel_type": "涉案", "start_category": "案件", "end_category": "证据"}]
        """
        total_edges = len(self.edges_df)
        schema_violations = []
        total_error_cnt = 0

        for rule in schema_rules:
            rel_type = rule["rel_type"]
            start_cat = rule["start_category"]
            end_cat = rule["end_category"]
            # 筛选该关系类型的所有边
            rel_edges = self.edges_df[self.edges_df["relation_type"] == rel_type].copy()
            if len(rel_edges) == 0:
                continue
            # 关联起点/终点的category
            rel_edges = rel_edges.merge(
                self.nodes_df[["node_id", "category"]].rename(columns={"node_id": "src_node_id", "category": "src_category"}),
                on="src_node_id",
                how="left"
            )
            rel_edges = rel_edges.merge(
                self.nodes_df[["node_id", "category"]].rename(columns={"node_id": "dst_node_id", "category": "dst_category"}),
                on="dst_node_id",
                how="left"
            )
            # 校验不符合规则的边
            error_mask = (rel_edges["src_category"] != start_cat) | (rel_edges["dst_category"] != end_cat)
            error_cnt = error_mask.sum()
            total_error_cnt += error_cnt
            if error_cnt > 0:
                schema_violations.append({
                    "rule": f"({start_cat})-[:{rel_type}]->({end_cat})",
                    "violation_count": error_cnt,
                    "error_detail": rel_edges[error_mask][["src_node_id", "dst_node_id", "src_category", "dst_category"]].head(100).to_dict("records")
                })

        self.report["edge_metrics"]["schema_violations"] = {
            "total_violation_count": total_error_cnt,
            "violation_details": schema_violations
        }

    def check_edge_missing_required_prop(self, required_props: List[str]):
        """关系必填属性缺失统计"""
        total_edges = len(self.edges_df)
        missing_stats = {}
        for prop in required_props:
            if prop not in self.edges_df.columns:
                self.report["warnings"].append(f"关系表不存在属性: {prop}")
                continue
            missing_mask = self.edges_df[prop].isna() | (self.edges_df[prop].astype(str).str.strip() == "")
            missing_cnt = missing_mask.sum()
            missing_ratio = missing_cnt / total_edges if total_edges > 0 else 0.0
            missing_stats[prop] = {
                "missing_count": missing_cnt,
                "total_edges": total_edges,
                "missing_ratio": round(missing_ratio, 4)
            }
        self.report["edge_metrics"]["required_prop_missing"] = missing_stats

    # ========== 3. 图拓扑结构指标 ==========
    def calc_graph_topology(self):
        """计算图密度、平均度、E/V比等核心拓扑指标（适配有向图）"""
        total_nodes = self.report["node_metrics"]["total_nodes"]
        total_edges = self.report["edge_metrics"]["total_edges"]
        G = self.G

        # 有向图全局平均度（总度数=入度+出度）
        if total_nodes <= 1:
            avg_degree = 0.0
            graph_density = 0.0
        else:
            avg_degree = G.number_of_edges() * 2 / total_nodes
            max_possible_edges = total_nodes * (total_nodes - 1)
            graph_density = G.number_of_edges() / max_possible_edges if max_possible_edges > 0 else 0.0

        self.report["graph_topology"]["avg_degree"] = round(avg_degree, 4)
        self.report["graph_topology"]["graph_density"] = round(graph_density, 6)
        self.report["graph_topology"]["E/V_ratio"] = round(total_edges / total_nodes, 4) if total_nodes > 0 else 0.0

        # 全局入度、出度分布
        in_degree_list = [d for n, d in G.in_degree()]
        out_degree_list = [d for n, d in G.out_degree()]
        deg_list = [G.degree(n) for n in G.nodes()]

        in_series = pd.Series(in_degree_list)
        out_series = pd.Series(out_degree_list)
        deg_series = pd.Series(deg_list)

        self.report["graph_topology"]["degree_distribution"] = {
            "min_degree": int(deg_series.min()),
            "max_degree": int(deg_series.max()),
            "median_degree": float(deg_series.median()),
            "avg_in_degree": round(in_series.mean(),4),
            "avg_out_degree": round(out_series.mean(),4),
            "degree_1_ratio": round((deg_series == 1).sum() / total_nodes, 4),
            "degree_2_ratio": round((deg_series == 2).sum() / total_nodes, 4),
            "hub_node_count": (deg_series >= 10).sum()
        }

        # 注意：有向图连通分量需要用弱连通
        if total_nodes > 0:
            connected_components = list(nx.weakly_connected_components(G))
            component_count = len(connected_components)
            max_component_size = max([len(c) for c in connected_components]) if component_count > 0 else 0
            max_component_ratio = max_component_size / total_nodes if total_nodes > 0 else 0.0
            self.report["graph_topology"]["connected_components"] = {
                "component_count": component_count,
                "max_component_size": max_component_size,
                "max_component_ratio": round(max_component_ratio, 4)
            }

    def print_summary(self, case_id, model):
        """控制台打印核心质量汇总"""
        print("=" * 70)
        print("📊 CSV图谱质量巡检核心汇总")
        print("=" * 70)
        nm = self.report["node_metrics"]
        em = self.report["edge_metrics"]
        tp = self.report["graph_topology"]
        type_deg = self.report["node_type_degree_metrics"]

        # 节点核心指标
        print(f"【节点】总数量: {nm['total_nodes']} | 孤立节点: {nm['isolated_nodes']['isolated_count']}({nm['isolated_nodes']['isolated_ratio']:.2%})")
        print(f"【节点】主键重复: {nm['duplicate_nodes']['duplicate_group_count']}组({nm['duplicate_nodes']['duplicate_ratio']:.2%})")
        if "required_prop_missing" in nm:
            miss_summary = [f"{k}:{v['missing_ratio']:.2%}" for k, v in nm["required_prop_missing"].items()]
            print(f"【节点】必填属性缺失: {', '.join(miss_summary)}")

        # ============ 新增：打印各节点类型出入度 ============
        print("\n【按节点类别出入度统计】")
        print(f"{'节点类别':<16}{'节点数':<8}{'平均入度':<10}{'平均出度':<10}")
        print("-" * 45)
        cat_warning_dict = {}
        for cat, info in type_deg.items():
            print(f"{cat:<16}{info['node_count']:<8}{info['avg_in_degree']:<10.3f}{info['avg_out_degree']:<10.3f}")
            self.entity_category_map[cat] = info['node_count']
            if info['avg_in_degree'] + info['avg_out_degree'] < 2:
                cat_warning_dict[cat] = info['avg_in_degree'] + info['avg_out_degree']

        # 关系核心指标
        print(f"\n【关系】总数量: {em['total_edges']} | 悬挂边: {em['dangling_edges']['dangling_count']}({em['dangling_edges']['dangling_ratio']:.2%})")
        print(f"【关系】重复三元组: {em['duplicate_relationships']['duplicate_group_count']}组({em['duplicate_relationships']['duplicate_ratio']:.2%})")
        print(f"【关系】自环边: {em['self_loop_edges']['self_loop_count']}({em['self_loop_edges']['self_loop_ratio']:.2%})")
        if "schema_violations" in em:
            print(f"【关系】Schema违规: {em['schema_violations']['total_violation_count']}条")
        print('\nDistribution of relations:')
        for key in em['rel_type_distribution'].keys():
            self.relation_type_map[key] = em['rel_type_distribution'][key]
            print(f"relation type - {key}: {em['rel_type_distribution'][key]}")

        # 拓扑核心指标
        print(f"\n【拓扑】全局平均度: {tp['avg_degree']:.2f} | 全局平均入度：{tp['degree_distribution']['avg_in_degree']:.3f} | 全局平均出度：{tp['degree_distribution']['avg_out_degree']:.3f}")
        print(f"【拓扑】图密度: {tp['graph_density']:.6f} | E/V比: {tp['E/V_ratio']:.2f}")
        if "connected_components" in tp:
            print(f"【拓扑】弱连通分量: {tp['connected_components']['component_count']}个 | 最大分量占比: {tp['connected_components']['max_component_ratio']:.2%}")

        # 警告
        if self.report["warnings"]:
            print("\n⚠️  巡检警告:")
            for w in self.report["warnings"][:10]:
                print(f"- {w}")
        print("=" * 70)

        recommend = []
        recommend.append('1. Check the outline of the knowledge graph\n')
        if tp['connected_components']['component_count'] > 1:
            recommend.append(
                f"The number of the weakly connected components （{tp['connected_components']['component_count']}) is "
                f"too high, please check whether you missed some relations")

        if nm['isolated_nodes']['isolated_ratio'] >= 0.1:
            recommend.append(f"The isolated node ratio ({nm['isolated_nodes']['isolated_ratio']}) is too high, "
                             f"check whether all relations among nodes have been identified")

        if tp['avg_degree'] < 2.5:
            recommend.append(
                f"The average degree ({tp['avg_degree']}) is too low, check whether all "
                f"relations among nodes have been identified")

        recommend.append('\n2. Check the nodes of the knowledge graph\n')
        recommend.append('Check each node, the node name should present domain character, avoid direct using concept')
        for key in self.entity_category_map.keys():
            if self.entity_category_map[key]:
                continue
            recommend.append(
                f'There is no entity category named {key}. Please check if they have been omitted.')

        recommend.append('\n3. Check the edges of the knowledge graph\n')
        if VerifySchema().validate_raw_kg_schema(case_id, model):
            recommend.append('Check the relations, some records misused the relation type between the src node and the dst node')

        for key in self.relation_type_map.keys():
            if self.relation_type_map[key]:
                continue
            recommend.append(
                f'There is no relationship type named "{key}". Please check if they have '
                f'been omitted.')

        recommend.append('\n4. Check the triplets of the knowledge graph\n')
        for key in cat_warning_dict.keys():
            recommend.append(f'The nodes belonging to {key} demonstrated a low average degree: '
                             f'"{cat_warning_dict[key]}", check whether all relations associated with these nodes have been identified')

        print("\nRecommendations:")
        for reco in recommend:
            print(reco)


def measure_kg_by_indicator(case_id, model='deepseek'):

    NODE_CSV_PATH = f"../../data/graph/case_study/case_1_raw_kg_m/{case_id}_{model}_nodes.csv"
    EDGE_CSV_PATH = f"../../data/graph/case_study/case_1_raw_kg_m/{case_id}_{model}_edges.csv"

    # 1. 初始化巡检器
    inspector = CSVGraphQualityInspector(NODE_CSV_PATH, EDGE_CSV_PATH)

    # 2. 节点质量检查
    inspector.stat_node_basic()
    inspector.check_duplicate_nodes()
    inspector.check_node_missing_required_prop(required_props=["node_id", "node_name", "category", "case_title"])
    inspector.check_isolated_nodes()

    # 3. 关系质量检查
    inspector.stat_edge_basic()
    inspector.check_dangling_edges()
    inspector.check_duplicate_relationships()
    inspector.check_edge_missing_required_prop(
        required_props=["src_node_id", "dst_node_id", "relation_type", "case_title"])
    # Schema合规规则（根据你的业务调整）
    schema_rules = [
        {"rel_type": "涉案", "start_category": "案件", "end_category": "证据"},
        {"rel_type": "包含", "start_category": "证据", "end_category": "证据片段"}
    ]
    inspector.check_schema_violation(schema_rules)

    # 4. 拓扑 +【新增】按类型出入度统计
    inspector.calc_graph_topology()
    inspector.stat_degree_by_node_category()   # 新增调用！

    # 5. 输出结果
    inspector.print_summary(case_id,model)


def evaluate_raw_kg_by_indicator(case_ids,model):
    for case_id in case_ids:
        measure_kg_by_indicator(case_id, model=model)


if __name__ == "__main__":
    case_id = 'c107'
    model = 'chatgpt'

    step = 3
    if step == 1:
        measure_kg_by_indicator(case_id, model=model)

    if step == 2:
        path_dir = "../../data/graph/case_study/case_1_raw_kg_m/"
        create_kg_by_case(case_id, path_dir=path_dir, mid_seg=f"_{model}")

    if step == 3:
        path_dir = "../../data/graph/case_study/case_6_v_ds/"
        create_kg_by_case(case_id)