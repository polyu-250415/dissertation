import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch


case_ids = {
        "s001": ['c001','c002','c003','c004','c005','c006','c007','c008','c009','c010','c011','c012','c013','c014','c015','c016','c017'],
        "s002": ['c101','c102','c103','c104','c105','c106','c107','c108','c109','c110','c111','c113','c114','c115','c117','c119','c120','c121','c122','c123','c124','c125','c126'],
        "s003": ['c201', 'c202', 'c203', 'c204', 'c205', 'c206', 'c207', 'c208', 'c209', 'c210', 'c211','c212','c213', 'c214', 'c215', 'c216', 'c217', 'c218', 'c219', 'c220', 'c221','c222','c223', 'c224', 'c225', 'c226', 'c227']
    }

class CaseMeasure():
    def __init__(self, case_ids=case_ids):
        self.case_ids = case_ids


    def calculate_dtv(self, file_path):
        valid_num = 0
        total_num = 0
        try:
            df = pd.read_csv(file_path)
            total_num = len(df)
            for _, row in df.iterrows():
                if 'Not Mention' in row["Answer"] or 'Exception' == row["Answer"]:
                    continue
                valid_num = valid_num + 1
        except Exception as e:
            print(e)

        if total_num:
            return valid_num / total_num
        else:
            return 0


    def calculate_kg_verification(self, sector_ids):
        for sector_id in sector_ids:
            print(f" ------------{sector_id}----------------\n")

            stat_dict_list = []
            for case_id in self.case_ids[sector_id]:

                print(f" ------------{case_id}----------------\n")

                try:
                    stat_dict = {'case_id': case_id}

                    initial_case_kg = "../data/graph/case_study/case_1_raw_kg_m/"
                    try:
                        stat_dict['Initial_deepseek_nodes'] = len(pd.read_csv(initial_case_kg + case_id + '_deepseek_nodes.csv'))
                        stat_dict['Initial_deepseek_edges'] = len(pd.read_csv(initial_case_kg + case_id + '_deepseek_edges.csv'))
                    except Exception as e:
                        stat_dict['Initial_deepseek_nodes'] = 0
                        stat_dict['Initial_deepseek_edges'] = 0
                        print(e)

                    try:
                        stat_dict['Initial_chatgpt_nodes'] = len(pd.read_csv(initial_case_kg + case_id +
                                                                            '_chatgpt_nodes.csv'))
                        stat_dict['Initial_chatgpt_edges'] = len( pd.read_csv(initial_case_kg + case_id +'_chatgpt_edges.csv'))
                    except Exception as e:
                        stat_dict['Initial_chatgpt_nodes'] = 0
                        stat_dict['Initial_chatgpt_edges'] = 0
                        print(e)

                    case_schema_check = "../data/graph/case_study/case_4_v_kg/"
                    stat_dict['r1_nodes'] = len(pd.read_csv(case_schema_check + case_id + '_nodes.csv'))
                    stat_dict['r1_edges'] = len(pd.read_csv(case_schema_check + case_id + '_edges.csv'))

                    case_fact_check = "../data/graph/case_study/case_5_v_ea/"
                    stat_dict['r2_nodes'] = len(pd.read_csv(case_fact_check + case_id + '_nodes.csv'))
                    stat_dict['r2_edges'] = len(pd.read_csv(case_fact_check + case_id + '_edges.csv'))

                    case_ea_alignment = "../data/graph/case_study/case_6_v_ds/"
                    stat_dict['r3_nodes'] = len(pd.read_csv(case_ea_alignment + case_id + '_nodes.csv'))
                    stat_dict['r3_edges'] = len(pd.read_csv(case_ea_alignment + case_id + '_edges.csv'))

                    stat_dict['node_accepted_rate'] = round(stat_dict['r3_nodes'] / (stat_dict['Initial_chatgpt_nodes'] +stat_dict['Initial_deepseek_nodes']), 2)
                    stat_dict['relation_accepted_rate'] = round(stat_dict['r3_edges'] / (
                                stat_dict['Initial_deepseek_edges'] + stat_dict['Initial_chatgpt_edges']),2)
                    stat_dict['node_expansion_coefficient'] = round(stat_dict['r3_nodes'] / max(
                                stat_dict['Initial_chatgpt_nodes'], stat_dict['Initial_deepseek_nodes']), 2)
                    stat_dict['relation_expansion_coefficient'] = round(stat_dict['r3_edges'] / max(
                            stat_dict['Initial_deepseek_edges'], stat_dict['Initial_chatgpt_edges']), 2)

                    stat_dict['dtv_valid'] = round(self.calculate_dtv(case_ea_alignment + case_id + '_ds_rag.csv'),2)

                    stat_dict_list.append(stat_dict)
                except Exception as e:
                    print(e)
                    pass

            pd.DataFrame(stat_dict_list).to_csv(f"../data/graph/case_study/case_7_stat/{sector_id}_stat.csv", index=False)

    def calc_ds_coverage(self, sector_ids, row_num=29):

        for sector_id in sector_ids:
            df_question = pd.read_excel("../conf/coding_schema/coding_schema.xlsx",
                                        sheet_name="downstream_task").dropna(how="all")
            total_count = [0 for i in range(row_num)]
            for case_id in self.case_ids[sector_id]:
                file_path = f"../data/graph/case_study/case_6_v_ds/{case_id}_ds_rag.csv"
                values = [0 for i in range(row_num)]
                try:
                    df = pd.read_csv(file_path)
                    if df.shape[0] != row_num:
                        print(f"{file_path} line no. {df.shape[0]}, drop")
                        continue

                    for index, row in df.iterrows():
                        if ('Not Mention' in row["Answer"]) or ('Exception' == row["Answer"]):
                            continue
                        values[index] = 1
                        total_count[index] += 1

                except Exception as e:
                    print(f"Read {file_path} failed: {str(e)}")
                    continue

                df_question[case_id] = values

            df_question['cross_cases'] = total_count

            df_question.to_csv(f"../data/graph/case_study/case_7_stat/{sector_id}_coverage_stat.csv", index=False)

    def read_coverage_csv(self, input_path, id_column="ID", case_pattern=r"^c\d+$"):

        frame = pd.read_csv(input_path)
        frame.columns = [str(column).strip() for column in frame.columns]
        if id_column not in frame.columns:
            raise ValueError(f"ID column {id_column!r} not found. Columns: {', '.join(frame.columns)}")

        case_columns = [c for c in frame.columns if re.fullmatch(case_pattern, c, re.I)]
        if not case_columns:
            raise ValueError(f"No case columns matched {case_pattern!r}; expected c001, c002, ...")

        ids = frame[id_column].astype("string").str.strip()
        keep = ids.notna() & ids.ne("") & ~ids.str.fullmatch(
            r"cross[\s_-]*case", case=False, na=False
        )
        question_ids = ids.loc[keep].astype(str).tolist()
        raw = frame.loc[keep, case_columns].apply(pd.to_numeric, errors="coerce")

        if raw.isna().any().any():
            locations = np.argwhere(raw.isna().to_numpy())
            examples = [f"{question_ids[r]} / {case_columns[c]}" for r, c in locations[:5]]
            raise ValueError("Blank or non-numeric values found at: " + ", ".join(examples))
        invalid = ~raw.isin([0, 1])
        if invalid.any().any():
            locations = np.argwhere(invalid.to_numpy())
            examples = [
                f"{question_ids[r]} / {case_columns[c]}={raw.iloc[r, c]}"
                for r, c in locations[:5]
            ]
            raise ValueError("Case values must be 0 or 1. Invalid values: " + ", ".join(examples))
        return question_ids, case_columns, raw.to_numpy(dtype=int)

    def calculate_coverage(self, matrix):
        """Return per-question, per-case, and cross-case-union coverage."""
        if matrix.ndim != 2 or matrix.size == 0:
            raise ValueError("The coverage matrix must contain at least one question and case.")
        question_coverage = matrix.mean(axis=1)
        single_case_coverage = matrix.mean(axis=0)
        # Cross-case: a question is covered if at least one case covers it.
        cross_case_coverage = float(matrix.any(axis=1).mean())
        return question_coverage, single_case_coverage, cross_case_coverage

    def draw_chart(self, question_ids, case_ids, matrix, output_dir, output_stem):
        _, single_case, cross_case = self.calculate_coverage(matrix)

        missed, covered = "#FFFFFF", "#D9DDE1"
        single_fill, single_edge = "#D9DDE1", "#858C93"
        cross_line, text = "#5F666D", "#263238"
        height = max(8.5, 4.3 + 0.23 * len(question_ids))
        fig = plt.figure(figsize=(11.5, height), facecolor="white", layout="constrained")
        gs = fig.add_gridspec(2, 1, height_ratios=[max(2.4, len(question_ids) / 8), 1.35])

        ax = fig.add_subplot(gs[0])
        # pcolormesh draws real vector cells in SVG. Medium-grey edges remain
        # visible around both the light-grey covered cells and white missed cells.
        ax.pcolormesh(
            matrix,
            cmap=ListedColormap([missed, covered]),
            vmin=0,
            vmax=1,
            edgecolors="#9AA1A7",
            linewidth=0.55,
            shading="flat",
        )
        ax.set_xlim(0, len(case_ids))
        ax.set_ylim(len(question_ids), 0)
        ax.set_aspect("auto")
        ax.set_xticks(np.arange(len(case_ids)) + 0.5, labels=case_ids, rotation=45, ha="right")
        ax.set_yticks(np.arange(len(question_ids)) + 0.5, labels=question_ids)
        ax.tick_params(axis="both", colors=text, labelsize=8.5, length=0)
        ax.set_xlabel("Individual case")
        ax.set_ylabel("Question / requirement", labelpad=12)
        ax.set_title("A. Single cases contain uneven coverage gaps", loc="left",
                     fontsize=13, fontweight="bold", color=text, pad=12)
        ax.legend(handles=[
            Patch(facecolor=covered, edgecolor="#858C93", label="Covered"),
            Patch(facecolor=missed, edgecolor="#B7BDC3", label="Missed"),
        ], frameon=False, ncol=2, loc="upper right", bbox_to_anchor=(1, 1.055))
        for spine in ax.spines.values():
            spine.set_color("#6F767D")
            spine.set_linewidth(0.9)

        ax = fig.add_subplot(gs[1])
        x = np.arange(len(case_ids))
        bars = ax.bar(x, single_case * 100, color=single_fill, edgecolor=single_edge,
                      linewidth=0.8, width=0.72)
        ax.axhline(cross_case * 100, color=cross_line, linewidth=2.2)
        ax.text(len(case_ids) - 0.55, cross_case * 100 - 1.8,
                f"Cross-case union: {cross_case:.0%}", ha="right", va="top",
                color=cross_line, fontsize=10, fontweight="bold")
        for bar, value in zip(bars, single_case):
            ax.text(bar.get_x() + bar.get_width() / 2, value * 100 + 1.2,
                    f"{value:.0%}", ha="center", va="bottom", fontsize=7.5, color=text)
        ax.set_xticks(x, labels=case_ids, rotation=45, ha="right")
        ax.set_ylim(0, 105)
        ax.set_yticks([0, 20, 40, 60, 80, 100],
                      labels=["0%", "20%", "40%", "60%", "80%", "100%"])
        ax.set(xlabel="Individual case", ylabel="Requirement coverage")
        ax.set_title(
            f"B. Combining cases raises coverage from {single_case.min():.0%}–"
            f"{single_case.max():.0%} to {cross_case:.0%}",
            loc="left", fontsize=13, fontweight="bold", color=text, pad=12)
        ax.grid(axis="y", color="#E3E7EA", linewidth=0.8)
        ax.set_axisbelow(True)
        ax.spines[["top", "right"]].set_visible(False)

        fig.suptitle("Cross-case analysis overcomes the limitations of relying on one case",
                     fontsize=16, fontweight="bold", color=text)
        svg_path = output_dir + f"{output_stem}.svg"
        # Keep text as editable text instead of converting glyphs to paths.
        with plt.rc_context({"svg.fonttype": "none"}):
            fig.savefig(svg_path, format="svg", bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return svg_path



    def analyze_dst(self, sector_ids):

        for sector_id in sector_ids:
            try:
                input_path = f"../data/graph/case_study/case_7_stat/{sector_id}_coverage_stat.csv"

                ids, cases, matrix = self.read_coverage_csv(input_path)
                _, single_case, cross_case = self.calculate_coverage(matrix)
                output_dir = f"../data/graph/case_study/case_7_stat/"
                output_stem = f"{sector_id}_coverage_stat"
                svg_path = self.draw_chart(ids, cases, matrix, output_dir, output_stem)
                print(f"Read {len(ids)} questions and {len(cases)} cases")
                print(f"Single-case coverage: {single_case.min():.1%}–{single_case.max():.1%}")
                print(f"Calculated cross-case union: {cross_case:.1%}")
                print(f"Saved {svg_path}")
            except Exception as e:
                print(e)



if __name__ == '__main__':
    sector_ids = ["s001", "s002", "s003"]
    obj = CaseMeasure()
    obj.calculate_kg_verification(sector_ids)
    obj.calc_ds_coverage(sector_ids)
    obj.analyze_dst(sector_ids)