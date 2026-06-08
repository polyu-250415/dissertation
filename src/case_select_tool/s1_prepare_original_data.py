import os
import re
import json
import pandas as pd
import uuid
from collections import Counter


class AcademicPaper:
    def __init__(self, original_file_name='knowledge_capture_plus_retention.csv'):
        self.original_selected_columns = {
            'Title': 'The title of paper',
            'Author': '',
            'Abstract': '',
            'Keywords': '',
            'Publication title': '',
            'Country of publication' : '',
            'Publication year': '',
            'Source type': '',
            'Language of publication': '',
            'DOI Link': '',
        }
        self.original_file_name = original_file_name


class PrepareProQuest(AcademicPaper):

    def __init__(self):
        super().__init__()

        self.column_name_mapping = {
            'DOI': 'DOI Link',
        }

        self.additional_selected_columns = ['Database']

    @staticmethod
    def parse_document(doc_text):
        """将单个文档文本解析为字典"""
        lines = doc_text.strip().split('\n')
        doc_dict = {}

        dict_mapping = {
            'Publication date' : 'Publication year',
            'Language': 'Language of publication',
            'Identifier / keyword': 'Keywords',
            'Identifier (keyword)': 'Keywords',
        }

        for line in lines:
            line = line.strip()
            if not line:
                continue
            # 检查是否包含冒号，并且冒号不在行首（避免 URL 中的 : 被误判）
            if ':' in line and not line.startswith(':'):
                # 只分割第一个冒号（防止 Abstract 或 Links 中的冒号干扰）
                key, value = line.split(':', 1)
                key = key.strip()

                if len(key.split()) > 5:
                    continue

                value = value.strip()
                if key and value:
                    if key in dict_mapping.keys():
                        key = dict_mapping[key]
                    doc_dict[key] = value
        return doc_dict

    def semi_structure_papers(self, input_file, output_file):
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 使用下划线分隔符分割文档（支持前后空白）
        # 注意：你的分隔符是 60 个或更多下划线（实际是 120+），我们用正则匹配
        separator = r'\n_{60,}\s*\n'
        raw_docs = re.split(separator, content)

        # 过滤空文档
        raw_docs = [doc.strip() for doc in raw_docs if doc.strip()]

        # 解析每个文档为字典
        all_docs = []
        for doc in raw_docs:
            parsed = self.parse_document(doc)
            if parsed:  # 只保留非空字典
                all_docs.append(parsed)

        # 保存为 JSON 文件
        with open(output_file, 'w', encoding='utf-8') as out_f:
            json.dump(all_docs, out_f, ensure_ascii=False, indent=2)

        print(f"成功解析 {len(all_docs)} 个文档，已保存至 {output_file}")

    def select_fields(self, input_file, output_dir):

        enhanced_docs = []

        with open(input_file, 'r', encoding='utf-8') as f:
            documents = json.load(f)

        for i, doc in enumerate(documents):
            enhanced_docs.append(doc)

        df = pd.DataFrame(enhanced_docs).fillna("Empty")

        print(f"ProQuest initial shape: {df.shape}")

        df = df.rename(columns=self.column_name_mapping)

        df['Title'] = df['Title'].str.split('; [')[0].title()
        df['Last updated'] = df['Last updated'] = pd.to_datetime(df['Last updated'], errors='coerce')
        df = (df.sort_values('Last updated', ascending=True)
                     .drop_duplicates(subset=['Title'], keep='last')
                     .sort_values('Last updated', ascending=False)
                     .reset_index(drop=True))

        # Apply logic
        cols_to_drop = [
            col for col in df.columns
            if df[col].dropna().nunique() == 2 and 'Empty' in df[col].dropna().unique()
        ]

        print("Columns to drop:", cols_to_drop)  # Output: ['A', 'E']

        df_cleaned = df.drop(columns=cols_to_drop)
        df_cleaned.to_csv(f'{output_dir}/ProQuest-original-fields.csv')

        print(list(df_cleaned.columns))

        cols_to_keep = list(self.original_selected_columns.keys()) + self.additional_selected_columns
        df_final = df[cols_to_keep].copy()

        df_final = df_final.drop_duplicates(subset=['Title'])

        print(f"ProQuest final shape: {df_final.shape}")

        df_final.to_csv(f'{output_dir}/ProQuest-selected-fields.csv', index=None)
        df_final.to_json(f'{output_dir}/ProQuest-selected-fields.json', orient='records')


class PrepareWoS(AcademicPaper):

    def __init__(self):
        super().__init__()

        self.column_name_mapping = {
            'Article Title': 'Title',
            'Authors': 'Author',
            'Abstract': 'Abstract',
            'Author Keywords': 'Keywords',
            'Publisher': 'Publication title',
            'Publisher City': 'Country of publication',
            'Publication Type': 'Source type',
            'Language': 'Language of publication',
            'Publication Year': 'Publication year',
            'Cited Reference Count': 'Cited Reference Count'
        }

        self.additional_selected_columns = ['Cited Reference Count',
                                            'Times Cited, WoS Core',
                                            'Times Cited, All Databases',
                                            '180 Day Usage Count',
                                            'Since 2013 Usage Count',
                                            'WoS Categories',
                                            'Web of Science Index',
                                            'Research Areas']


    def select_fields(self, input_file, output_dir):

        df = pd.read_csv(input_file)

        print(f"Wos initial shape: {df.shape}")

        df = df.rename(columns=self.column_name_mapping)
        df['Title'] = df['Title'].str.title()

        cols_to_keep = list(self.original_selected_columns.keys()) + self.additional_selected_columns
        df_final = df[cols_to_keep].copy()

        print(f"Wos final shape: {df_final.shape}")

        df_final.to_csv(f'{output_dir}/WoS-selected-fields.csv', index=None)
        df_final.to_json(f'{output_dir}/WoS-selected-fields.json', orient='records')


class PrepareScopus(AcademicPaper):

    def __init__(self):
        super().__init__()

        self.column_name_mapping = {
            'Title': 'Title',
            'Authors': 'Author',
            'Abstract': 'Abstract',
            'Publisher': 'Country of publication',
            'Source title': 'Publication title',
            'DOI': 'DOI Link',
            'Document Type': 'Source type',
            'Language of Original Document': 'Language of publication',
            'Year': 'Publication year',
            'Cited by': 'Cited Reference Count'
        }


        self.additional_selected_columns = []


    def select_fields(self, input_file, output_dir):

        df = pd.read_csv(input_file)

        print(f"Scopus initial shape: {df.shape}")

        df['Keywords'] = df['Author Keywords'].fillna(' ') + ';' + df['Index Keywords'].fillna(' ')+ ';'

        df = df.rename(columns=self.column_name_mapping)
        df['Title'] = df['Title'].str.split(r'; \[').str[0].str.title()

        cols_to_keep = list(self.original_selected_columns.keys()) + self.additional_selected_columns
        df_final = df[cols_to_keep].copy()

        print(f"Scopus final shape: {df_final.shape}")

        df_final.to_csv(f'{output_dir}/Scopus-selected-fields.csv', index=None)
        df_final.to_json(f'{output_dir}/Scopus-selected-fields.json', orient='records')


class PreparePubMed(AcademicPaper):

    def __init__(self):
        super().__init__()

        self.column_name_mapping = {
            'Article Title': 'Title',
            'Authors': 'Author',
            'Abstract': 'Abstract',
            'Keywords': 'Keywords',
            'Publisher': 'Publication title',
            'Publisher City': 'Country of publication',
            'Publication Type': 'Source type',
            'Language': 'Language of publication',
            'Publication Year': 'Publication year',
            'Cited Reference Count': 'Cited Reference Count'
        }

        self.additional_selected_columns = []


    def select_fields(self, input_file, output_dir):

        df = pd.read_csv(input_file)

        print(f"PubMed initial shape: {df.shape}")

        df = df.rename(columns=self.column_name_mapping)
        df['Title'] = df['Title'].str.title()

        cols_to_keep = list(self.original_selected_columns.keys()) + self.additional_selected_columns
        df_final = df[cols_to_keep].copy()

        print(f"PubMed final shape: {df_final.shape}")

        df_final.to_csv(f'{output_dir}/PubMed-selected-fields.csv', index=None)
        df_final.to_json(f'{output_dir}/PubMed-selected-fields.json', orient='records')


class PreparePaper:

    def __init__(self):
        self.input_file_list = [
            '../data/papers/midput/Scopus-selected-fields.csv',
            '../data/papers/midput/WoS-selected-fields.csv',
            '../data/papers/midput/PubMed-selected-fields.csv',
        ]
        self.uuid_file_path = "../conf/case_selection/uuid.csv"
        self.output_dir = "../data/papers/midput/"
        self.unique_column = 'Title'
        self.fill_value = 'Empty'

        self.uuid_dict = {}
        self.init_uuid_dict()

    def init_uuid_dict(self):
        if os.path.isfile(self.uuid_file_path):
            df = pd.read_csv(self.uuid_file_path, sep='\t', quoting=3)
            self.uuid_dict = dict(zip(df['Title'], df['uuid']))

    @staticmethod
    def prepare_proquest():
        input_file = "../data/papers/input/bak/kc_proquest/ProQuestDocuments-2026-03-04.txt"
        output_file = "../data/papers/midput/ProQuest-original-text.json"
        PrepareProQuest().semi_structure_papers(input_file, output_file)

        output_dir = "../data/papers/midput/"
        PrepareProQuest().select_fields(output_file, output_dir)

    @staticmethod
    def prepare_wos():
        input_file = f"../data/papers/input/wos/knowledge_capture_plus_retention.csv"
        output_dir = "../data/papers/midput/"
        PrepareWoS().select_fields(input_file, output_dir)

    @staticmethod
    def prepare_scopus():
        input_file = "../data/papers/input/scopus/knowledge_capture_plus_retention.csv"
        output_dir = "../data/papers/midput/"
        PrepareScopus().select_fields(input_file, output_dir)

    @staticmethod
    def prepare_pubmed():
        input_file = "../data/papers/input/pubmed/knowledge_capture_plus_retention.csv"
        output_dir = "../data/papers/midput/"
        PreparePubMed().select_fields(input_file, output_dir)

    @staticmethod
    def standardize_date(date_value):
        """Convert various date formats to MMM-YY format"""
        if pd.isna(date_value):
            return date_value

        date_str = str(date_value).strip()
        from dateutil import parser
        try:
            # Handle year-only
            if date_str.isdigit() and len(date_str) == 4:
                return f"{date_str[:]}"

            # Handle date ranges - take first month
            if '-' in date_str and ' ' in date_str:
                # e.g., "Oct-Dec 2025"
                parts = date_str.split()
                month_part = parts[0].split('-')[0]
                year = parts[1]
                return f"{year[:]}"

            # Try parsing with dateutil
            parsed_date = parser.parse(date_str, fuzzy=True)
            return parsed_date.strftime('%Y')

        except:
            return date_str

    @staticmethod
    def standardize_country(country_str):

        """
        Standardizes a country string to a canonical name.
        Args:
            country_str (str): The case_1_raw_kg_m country string from the data.

        Returns:
            str: The standardized country name.
        """
        if pd.isna(country_str) or country_str == 'Empty':
            return country_str

        # Normalize the string: remove extra spaces, convert to title case for easier matching
        normalized = re.sub(r'\s+', ' ', country_str.strip()).title()

        # Handle specific case_2_norm_id for the United States
        us_patterns = [
            r'^U\.?S\.?A?\.?$',
            r'^United\s+States.*',
            r'^Un\s+Ited\s+States$',
            r'^Unite\s?D\s+States$',
            r'^Unit\s+Ed\s+States$',
            r'^United\s+Stat\s+Es$',
            r'^Usa$'
        ]
        for pattern in us_patterns:
            if re.match(pattern, normalized, re.IGNORECASE):
                return "United States"

        # Handle specific case_2_norm_id for the United Kingdom
        uk_patterns = [
            r'^U\.?K\.?$',
            r'^United\s+Kingdom.*',
            r'^Uni\s+Ted\s+Kingdom$',
            r'^United\s+Kingd\s+Om$',
            r'^England$',
            r'^Scotland$',
            r'^Wales$',
            r'^Northern\s+Ireland$',
            r'^Birmingham$',  # A major city in England
            r'^East\s+Sussex$',  # A county in England
            r'^Adapazari$',
            # This seems like a Turkish city, but in your data it's listed under UK. We'll keep it as UK per your data's context.
        ]
        for pattern in uk_patterns:
            if re.match(pattern, normalized, re.IGNORECASE):
                return "United Kingdom"

        # Handle specific case_2_norm_id for the Netherlands
        nl_patterns = [
            r'^Netherland[s]?$',
            r'^Nether\s+Lands$',
            r'^Netherl\s+Ands$',
            r'^The\s+Netherlands$'
        ]

        for pattern in nl_patterns:
            if re.match(pattern, normalized, re.IGNORECASE):
                return "Netherlands"

        # Handle Canada
        if re.match(r'^(Canada|Can)$', normalized, re.IGNORECASE):
            return "Canada"

        # Handle other specific countries that appear in your data
        # For these, we mostly just correct the casing
        known_countries = {
            'Japan': 'Japan',
            'Italy': 'Italy',
            'France': 'France',
            'Germany': 'Germany',
            'India': 'India',
            'Switzerland': 'Switzerland',
            'Australia': 'Australia',
            'Singapore': 'Singapore',
            'China (Republic : 1949- )': 'China',
            'South Africa': 'South Africa',
            'New Zealand': 'New Zealand',
            'Turkey': 'Turkey',
            'Malaysia': 'Malaysia',
            'Colombia': 'Colombia',
            'Brazil': 'Brazil',
            'Spain': 'Spain',
            'Portugal': 'Portugal',
            'Denmark': 'Denmark',
            'Austria': 'Austria',
            'Belgium': 'Belgium',
            'Norway': 'Norway',
            'Ireland': 'Ireland',
            'Israel': 'Israel',
            'Taiwan': 'China',
            'Hong Kong': 'China',
            'Korea (South)': 'Korea (South)',
            'Russia': 'Russia',
            'Ukraine': 'Ukraine',
            'Romania': 'Romania',
            'Bulgaria': 'Bulgaria',
            'Hungary': 'Hungary',
            'Czech Republic': 'Czech Republic',
            'Poland': 'Poland',
            'Greece': 'Greece',
            'Pakistan': 'Pakistan',
            'Lithuania': 'Lithuania',
            'Croatia': 'Croatia',
            'Slovenia': 'Slovenia',
            'Bosnia And Herzegovina': 'Bosnia And Herzegovina',
            'Mumbai': 'India',  # Mumbai is a city in India
            'Chandigarh': 'India',  # Chandigarh is a city in India
            'Punjab': 'India',  # Punjab is a state in India
            'Victoria': 'Australia',  # Victoria is a state in Australia
            'Princeton': 'United States',  # Princeton is a city in the US
            'Bridgetown': 'Barbados',  # Bridgetown is the capital of Barbados
            'Vilnius': 'Lithuania',  # Vilnius is the capital of Lithuania
        }

        # Check if the normalized string matches a known country key
        for key, value in known_countries.items():
            if normalized == key.title():
                return value

        # If none of the above, return the original string (or its title case)
        return normalized

    def allocate_uuid(self, title):

        if title not in self.uuid_dict.keys():
            self.uuid_dict[title] = uuid.uuid4()

        return self.uuid_dict[title]

    def combine_papers(self):

        df_list = []
        for file_path in self.input_file_list:
            try:
                df = pd.read_csv(file_path)
                df_list.append(df)
            except Exception as e:
                print(f"  - Error reading {file_path}: {e}")
                continue

        if not df_list:
            raise ValueError("No dataframes were successfully loaded.")

        # 3. Combine DataFrames (Row-wise)
        # join='outer' ensures all columns from all files are kept.
        # Missing columns in specific files will automatically be NaN.
        combined_df = pd.concat(df_list, axis=0, ignore_index=True, join='inner')

        print(f"Combined shape before processing: {combined_df.shape}")

        # 4. Fill absent columns/NaN values with the specified fill_value
        combined_df = combined_df.fillna(self.fill_value)

        combined_df['Country of publication'] = combined_df['Country of publication'].apply(self.standardize_country)
        combined_df['Publication year'] = combined_df['Publication year'].apply(self.standardize_date)

        if self.unique_column:
            if self.unique_column not in combined_df.columns:
                raise ValueError(
                    f"Unique column '{self.unique_column}' not found in the combined data. Available columns: {combined_df.columns.tolist()}")

            initial_count = len(combined_df)
            combined_df = combined_df.drop_duplicates(subset=[self.unique_column], keep='last')
            final_count = len(combined_df)
            print(f"Deduplicated based on '{self.unique_column}': Removed {initial_count - final_count} duplicate rows.")
        else:
            print("No unique column specified. Skipping deduplication.")

        combined_df['uuid'] = combined_df['Title'].apply(lambda x: str(self.allocate_uuid(x)))
        print(f"Final shape: {combined_df.shape}")

        combined_df.to_csv(f'{self.output_dir}/semi_structured_papers.csv', index=None)
        combined_df.to_json(f'{self.output_dir}/semi_structured_papers.json', orient='records')

        def concat_col_unique(col_series, sep=';'):

            clean_data = col_series.dropna()
            all_keywords = []
            for cell_value in clean_data:
                # 拆分当前单元格的关键词（按;分割）
                keywords = cell_value.split(sep)
                # 过滤拆分后可能出现的空字符串（比如单元格是"Python;;Java"的情况）
                keywords = [kw.title().strip() for kw in keywords if kw.strip()]
                # 添加到总列表
                all_keywords.extend(keywords)

            # 步骤3：统计每个关键词的出现次数（用Counter更高效）
            keyword_counter = Counter(all_keywords)

            # 步骤4：转换为普通字典（可选，Counter本身也支持字典操作）
            count_dict = dict(keyword_counter)

            return count_dict
        # 调用函数处理「关键词」列
        keyword_dict = concat_col_unique(combined_df['Keywords'], sep=';')

        print("Result：")

        def save_dict_to_json(data_dict, file_path=f'{self.output_dir}/keyword_count.json', ensure_ascii=False, indent=4):

            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data_dict, f, ensure_ascii=ensure_ascii, indent=indent)
                print(f"extract keywords successfully, store them in：{file_path}")
            except Exception as e:
                print(f"extract keywords failed：{e}")

        # 调用函数保存JSON文件
        save_dict_to_json(keyword_dict)


if __name__ == '__main__':

    PreparePaper.prepare_wos()
    PreparePaper.prepare_scopus()
    PreparePaper.prepare_pubmed()
    PreparePaper().combine_papers()





