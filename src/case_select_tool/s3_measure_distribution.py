import re, os
from collections import Counter

import pandas as pd
import ast


import networkx as nx
import matplotlib.pyplot as plt
from networkx.algorithms.community import greedy_modularity_communities
import matplotlib.cm as cm  # 新增配色模块


from src.taxonomy import IndustryTaxonomy
from src.utils.llm_mgmt.deepseek_local_api import chat_with_deepseek


class MeasureDistribution(object):

    def __init__(self):
        self.annotation_path = "../data/papers/midput/screening_by_annotation/"
        self.selection_path = "../data/papers/midput/selection_cases/"
        self.raw_path = "../data/papers/midput/"

        if not os.path.exists(self.selection_path):
            os.makedirs(self.selection_path, exist_ok=True)

        pass

    @staticmethod
    def extract_country_name(address):
        prompt = (f'Please extract the country name from the following address:{address}'
                  f'Warning: Only return the country name, If you can not find the country name from the address, return "unknown"')
        return chat_with_deepseek(prompt)

    @staticmethod
    def standardise_journal_or_conference(name):
        prompt = (f'Please transfer the following journal or conference into to the official name.'
                  f'The journal or conference :{name}'
                  f'Warning: Only return the official name, If you can not find the name, return "unknown"')
        return chat_with_deepseek(prompt)

    def supplement_attributes(self, file1: str, file2: str, output_file: str):
        # Columns to match from the second CSV file
        match_columns = [
            "Author",
            "Publication title",
            "Country of publication",
            "Publication year",
            "Source type",
            "Language of publication",
            "DOI Link"
        ]

        # Read two CSV files as string type to avoid data distortion
        df1 = pd.read_csv(f'{self.annotation_path}{file1}', dtype=str)
        df2 = pd.read_csv(f'{self.raw_path}{file2}', dtype=str)

        # Check required columns exist
        if not all(col in df1.columns for col in ["uuid"]):
            raise ValueError("The first CSV must contain columns: uuid")
        if "Title" not in df2.columns:
            raise ValueError("The second CSV must contain column: Title for matching")

        # Clean titles: remove spaces and unify lowercase for higher matching accuracy
        df1["clean_uuid"] = df1["uuid"].fillna("").astype(str).str.strip().str.lower()
        df2["clean_uuid"] = df2["uuid"].fillna("").astype(str).str.strip().str.lower()

        # Remove duplicate titles, keep the first matched record
        df2_unique = df2.drop_duplicates(subset="clean_uuid", keep="first")

        # Build mapping dictionary between cleaned title and target fields
        title_mapping = df2_unique.set_index("clean_uuid")[match_columns].to_dict("index")

        # Match supplementary information by cleaned title
        def get_matched_data(clean_t):
            return title_mapping.get(clean_t, {col: "" for col in match_columns})

        matched_data = df1["clean_uuid"].apply(get_matched_data)
        matched_df = pd.DataFrame(matched_data.tolist(), columns=match_columns)

        # Combine original data and matched columns, drop auxiliary clean title column
        final_dataframe = pd.concat([df1.drop(columns="clean_uuid"), matched_df], axis=1)

        final_dataframe['country'] = final_dataframe['Country of publication'].apply(self.extract_country_name)

        """final_dataframe['publication'] = final_dataframe['Publication title'].apply(
            self.standardise_journal_or_conference)"""

        # Export merged CSV file with Chinese compatible encoding
        final_dataframe.to_csv(f'{self.annotation_path}{output_file}', index=False)
        print(f"Merging completed. Result saved to {output_file}, total {len(final_dataframe)} records")


    def illustrate_sector_distribution(self):
        input_file = f'{self.annotation_path}annotate_combined_statistics.csv'
        statistic_file = f'{self.selection_path}annotate_sector_statistics.csv'

        df = pd.read_csv(input_file)

        # Initialize counter
        counter = Counter()

        # Process each non-null cell in the 'sector_taxonomy' column
        for cell in df['sector_taxonomy'].dropna():
            # Convert string representation of list (e.g., "['84']") to actual list
            codes = ast.literal_eval(cell)
            counter.update(str(code) for code in codes)

        sic_desc = []
        sic_id = []
        counts = []
        for code, count in sorted(counter.items(), key=lambda x: x[1], reverse=False):
            if code in IndustryTaxonomy.sic_dict:
                raw_desc = IndustryTaxonomy.sic_dict[code]
            else:
                code = '0099'
                raw_desc = f"SIC {code}"
            sic_desc.append(raw_desc)
            sic_id.append(code)
            counts.append(count)

        df = pd.DataFrame({
            'sic_desc': sic_desc,
            'sic_id': sic_id,
            'count': counts
        })

        df.to_csv(statistic_file, index=False, encoding='utf-8')

    def illustrate_tacit_knowledge_type_distribution(self):
        input_file = f'{self.annotation_path}annotate_combined_statistics.csv'
        statistic_file = f'{self.selection_path}annotate_tacit_knowledge_statistics.csv'

        df = pd.read_csv(input_file)

        # Initialize counter
        counter = Counter()

        # Process each non-null cell in the 'sector_taxonomy' column
        for cell in df['tacit_taxonomy'].dropna():
            # Convert string representation of list (e.g., "['84']") to actual list
            tks = ast.literal_eval(cell)
            counter.update(re.sub(r'\([^()]*\)', '', tk) for tk in tks)

        tk_type = []
        counts = []
        for tk, count in sorted(counter.items(), key=lambda x: x[1], reverse=False):
            tk_type.append(tk)
            counts.append(count)

        df = pd.DataFrame({
            'tk_type': tk_type,
            'count': counts
        })

        df.to_csv(statistic_file, index=False, encoding='utf-8')
        pass

    def illustrate_digital_technologies_distribution(self):
        input_file = f'{self.annotation_path}annotate_combined_statistics.csv'
        statistic_file = f'{self.selection_path}annotate_digital_technology_statistics.csv'

        df = pd.read_csv(input_file)

        # Initialize counter
        counter = Counter()

        # Process each non-null cell in the 'sector_taxonomy' column
        for cell in df['digital_taxonomy'].dropna():
            # Convert string representation of list (e.g., "['84']") to actual list
            tks = ast.literal_eval(cell)
            counter.update(re.sub(r'\([^()]*\)', '', tk) for tk in tks)

        dt_type = []
        counts = []
        for tk, count in sorted(counter.items(), key=lambda x: x[1], reverse=False):
            dt_type.append(tk)
            counts.append(count)

        df = pd.DataFrame({
            'dt_type': dt_type,
            'count': counts
        })

        df.to_csv(statistic_file, index=False, encoding='utf-8')
        pass

    def illustrate_cross_distribution(self):

        input_file = f'{self.annotation_path}annotate_combined_statistics.csv'
        statistic_file = f'{self.selection_path}annotate_cross_sector_statistics.csv'

        def parse_sector_list(sector_str):
            try:
                lst = ast.literal_eval(str(sector_str))
                if not isinstance(lst, list):
                    return []
                return [str(s).strip() for s in lst if str(s).strip()]
            except:
                return []

        # ---------------------- 1. 读取数据 ----------------------
        df = pd.read_csv(input_file, encoding="utf-8")
        df["sector_parsed"] = df["sector_taxonomy"].apply(parse_sector_list)

        # 只保留非空行
        df_valid = df[df["sector_parsed"].str.len() > 0].copy()

        # ---------------------- 2. 提取所有唯一行业key ----------------------
        all_sectors = []
        for sectors in df_valid["sector_parsed"]:
            all_sectors += sectors
        unique_sectors = sorted(list(set(all_sectors)))

        # ---------------------- 3. 初始化统计 ----------------------
        sector_cross_count = {key: 0 for key in unique_sectors}  # 跨行业数量
        sector_single_count = {key: 0 for key in unique_sectors}  # 不跨行业数量

        # ---------------------- 4. 逐行统计 ----------------------
        for sectors in df_valid["sector_parsed"]:
            if len(sectors) == 1:
                # 不跨行业：给唯一的那个key +1
                key = sectors[0]
                if key in sector_single_count:
                    sector_single_count[key] += 1
            elif len(sectors) >= 2:
                # 跨行业：给所有key +1
                for key in sectors:
                    if key in sector_cross_count:
                        sector_cross_count[key] += 1

        # ---------------------- 5. 构建结果DataFrame ----------------------
        result_df = pd.DataFrame({"SIC": unique_sectors})
        result_df['sector_name'] = result_df['SIC'].map(IndustryTaxonomy.sic_dict)
        result_df['single_sector_count'] = [sector_single_count[k] for k in unique_sectors]
        result_df['cross_sector_count'] = [sector_cross_count[k] for k in unique_sectors]
        result_df['total_count'] = [sector_single_count[k] + sector_cross_count[k] for k in unique_sectors]
        result_df['rate'] = (result_df['cross_sector_count'] / result_df['total_count']).map(lambda x: f"{x:.2f}")
        result_df.sort_values(["total_count"], ascending=False, inplace=True)

        result_df.to_csv(statistic_file, index=False, encoding='utf-8')

    @staticmethod
    def read_authors_from_csv(csv_path, author_col, sep=";"):
        """
        从CSV读取作者列，转换为合作网络所需的双层列表格式
        :param csv_path: csv文件路径
        :param author_col: 作者所在列的列名
        :param sep: 同一篇论文多位作者之间的分隔符，常见 ; 或 ,
        :return: list[list]，每篇论文的作者列表
        """
        df = pd.read_csv(csv_path)
        paper_author_list = []
        for authors_str in df[author_col].dropna():
            # 拆分作者名，去除首尾空格，过滤空字符串
            authors = [a.strip() for a in str(authors_str).split(sep) if a.strip()]
            if authors:
                paper_author_list.append(authors)
        return paper_author_list

    @staticmethod
    def draw_coauthor_network(paper_author_list, figsize=(12, 9), seed=42, save_path=None):
        """
        绘制作者合作网络图，不同聚类使用不同颜色，输出网络指标、作者统计、聚类分组
        :param paper_author_list: list[list]，每篇论文作者列表
        :param figsize: 画布尺寸
        :param seed: spring_layout随机种子，固定布局
        :param save_path: 图片保存路径，为None则只展示不保存
        :return: G(网络图对象), author_df(作者统计表), clusters(聚类分组)
        """
        G = nx.Graph()
        author_pub_count = {}

        for authors in paper_author_list:
            unique_authors = list(set(authors))
            for au in unique_authors:
                author_pub_count[au] = author_pub_count.get(au, 0) + 1
            n = len(unique_authors)
            for i in range(n):
                for j in range(i + 1, n):
                    a1, a2 = unique_authors[i], unique_authors[j]
                    if G.has_edge(a1, a2):
                        G[a1][a2]["weight"] += 1
                    else:
                        G.add_edge(a1, a2, weight=1)

        # 作者统计表
        stat_data = []
        for node in G.nodes():
            stat_data.append({
                "Author": node,
                "Paper_Num": author_pub_count[node],
                "Cooperation_Degree": G.degree(node)
            })
        author_df = pd.DataFrame(stat_data).sort_values("Paper_Num", ascending=False)

        # 社区聚类
        clusters = list(greedy_modularity_communities(G))
        cluster_total = len(clusters)

        # 映射每个作者所属集群编号
        node_cluster_id = {}
        for c_id, cluster_members in enumerate(clusters):
            for author in cluster_members:
                node_cluster_id[author] = c_id

        # 分配不同配色
        cmap = cm.get_cmap("tab10", cluster_total)
        node_color_list = [cmap(node_cluster_id[node]) for node in G.nodes()]

        # 绘图
        plt.figure(figsize=figsize)
        pos = nx.spring_layout(G, seed=seed)
        node_sizes = [author_pub_count[node] * 300 for node in G.nodes()]

        # 节点传入分色列表
        nx.draw_networkx_nodes(
            G, pos,
            node_size=node_sizes,
            alpha=0.7,
            node_color=node_color_list
        )

        edge_weights = [d["weight"] for _, _, d in G.edges(data=True)]
        # 修复：color → edge_color
        nx.draw_networkx_edges(
            G, pos,
            width=[w * 1.2 for w in edge_weights],
            alpha=0.5,
            edge_color="#555555"
        )
        nx.draw_networkx_labels(G, pos, font_size=9)

        plt.title("Author Co-authorship Network (Different Colors for Each Cluster)", fontsize=14)
        plt.axis("off")
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
        plt.show()

        return G, author_df, clusters

    # ---------------- 调用示例 ----------------
    def draw_author_network(self):
        # 1. 从CSV读取作者列（修改路径、列名、分隔符即可）
        paper_authors = self.read_authors_from_csv(
            csv_path=f'{self.annotation_path}annotate_combined_addition.csv',  # 你的csv文件路径
            author_col="Author",  # 作者列的列名
            sep=";"  # 作者之间的分隔符，WoS导出通常是分号
        )

        # 2. 绘制合作网络图
        graph, author_stats, team_clusters = self.draw_coauthor_network(
            paper_author_list=paper_authors,
            figsize=(14, 10),
            save_path="co_author_network.png"
        )

        # 3. 输出分析指标
        print(f"总论文数：{len(paper_authors)}")
        print(f"总作者数：{graph.number_of_nodes()}")
        print(f"合作连线数：{graph.number_of_edges()}")
        print(f"独立研究团队数：{len(team_clusters)}")
        print("\n===== 高产作者TOP10 =====")
        print(author_stats.head(10))

if __name__ == '__main__':
    obj = MeasureDistribution()
    file1 = 'annotate_combined.csv'
    file2 = 'semi_structured_papers.csv'
    output_file = 'annotate_combined_addition.csv'
    obj.draw_author_network()
    """
    obj.supplement_attributes(file1, file2, output_file)
    obj.illustrate_sector_distribution()
    obj.illustrate_tacit_knowledge_type_distribution()
    obj.illustrate_digital_technologies_distribution()
    obj.illustrate_cross_distribution()"""