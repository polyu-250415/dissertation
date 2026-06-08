import pandas as pd

template_path = "../conf/coding_schema/coding_schema.xlsx"


def generate_prompt(category):
    task_2 = ""
    try:
        if "Traditional Human-central Practice" == category:
            sheet_name = "Traditional Human-central Pract"
        else:
            sheet_name = category

        df = pd.read_excel(template_path, sheet_name=sheet_name).dropna(how="all")
        category_definition = ""
        for index, row in df.iterrows():
            eg = ''
            if len(str(row['Example'])) > 6:
                eg = "--e.g.," + str(row['Example'])
            item = f"{index+1}. '{row['Name']}'(Code : {row['ID']}): {row['Scope']} {eg}\n"
            category_definition = category_definition + item
        if len(category_definition):
            task_2 = (f"Task 2: {category}\n"
                      f"When expanding this category, you must map nodes into the following sub-categories:\n"
                      f"{category_definition}")
    except Exception as e:
        print(e)
        pass

    promt_template = f"""
Role & Objective
You are an expert Ontologist and Knowledge Management (KM) researcher specializing in construction informatics and socio-technical design. Your task is to expand an existing categorical dataset of research nodes by developing a precise, academically grounded sub-taxonomy and mapping each individual node row to this structure.

Input Data Format
You will be processing a CSV dataset containing research nodes. The input columns are:
* node_id: Unique identifier (e.g., c001M01N01)
* node_name: The specific entity, tool, practice, human agent, or constraint
* category: One of 9 high-level structural categories
* evidence_label: The type of evidence (e.g., E for explicit, I for implicit)
* case_title: The source of the node
* evidence_statement: The specific textual evidence of the node from literature
* object_definition: The functional or operational definition of the node
* evidence_location: Section or page number where the evidence resides

High-Level Categories
1. Explicit Knowledge
2. Tacit Knowledge
3. Knowledge Holder
4. Traditional Human-central Practice
5. Technology-enable Practice
6. Digital Technology
7. Organizational Dependency
8. Environmental Dependency
9. Limitation

CRITICAL CLASSIFICATION METHODOLOGY REMINDER
When mapping data rows to sub-categories, you must NOT rely solely on the text in the node_name column. You are strictly required to perform a semantic analysis of the evidence_statement and object_definition columns for every single node. Use these contextual clues, descriptions, and functional roles to determine the true semantic domain of the node and map it to the most accurate pre-defined sub-category.

Taxonomy Guidelines & Tasks
Task 1: General Category Sub-Taxonomy (Categories 1, 3, 7, 8)
For all categories NOT explicitly restricted or pre-defined in Tasks 2 below, you must:
1. Create a set of granular sub-categories based on established literature (e.g., Nonaka & Takeuchi's KM theory, Resource-Based View, and Contingency theory).
2. CRITICAL CARDINALITY CONSTRAINT: Every high-level category in this task must contain at least 6, but strictly LESS THAN 16 active sub-categories.
3. Assign a structured alphanumeric ID using the parent category's initials (e.g., Explicit Knowledge -> EK01, EK02).

{task_2}

Strategic Reasoning Process
Before generating the final output, execute and display your step-by-step reasoning under a "Strategic Reasoning Process" heading following these exact phases:
Phase 1: Theoretical Foundation & Base Taxonomy Derivation
* Document the academic literature and KM frameworks used to formalize the sub-taxonomies for the general categories (Categories 1, 3,8 9).
* Explicitly define the semantic boundaries, operational scope, and unique alphanumeric identifier prefix (e.g., EX, KH, TP, ED) for every newly created sub-category.
Phase 2: Structural Boundary & Cardinality Audit
* Enumerate and count the exact number of sub-categories active within each of the 9 high-level parent categories.
* Cross-reference these counts against the mathematical constraints established in the guidelines:
* Provide an explicit "Pass/Fail" statement confirming structural compliance before mapping data rows.
Phase 3: Edge-Case Resolution & Intersection Handling
* Identify any ambiguous nodes where the node_name could be misleading (e.g., human constraints vs. systemic limitations), and detail how you examined the evidence_statement and object_definition to resolve the classification.
* Formulate and explicitly state a deterministic domain-tiebreaking rule based on construction informatics principles to cleanly assign the node to a single, optimal sub-category without ambiguity.
Phase 4: Alphanumeric Mapping & Code-String Synthesis
* Synthesize the final structural combinations by verifying that each mapped node's parent category directly matches the alphabetical prefix of its assigned sub_category_id.
* Ensure that the text string in the final sub_category column perfectly corresponds to the formalized taxonomy definitions from Phase 1 & Tasks 2-6, removing any syntactic drift or formatting discrepancies.
Phase 5: CSV Integrity Pre-Check:
* Ensure that all rows have been processed in accordance with the unified standard.
* Verify that the total number of output rows matches the input file exactly.
* Verify that all fields are cleanly enclosed in double quotes to handle internal commas safely.

Output Format
Following the CoT log, output the final result as a cleanly formatted CSV file.
* The output data rows must include the two newly appended columns: sub_category_id and sub_category.
* The delimiter of CSV files should be a comma (,), with fields enclosed in double quotes to safely handle any commas inside node names or statements.
"""

    file_path = "../conf/sector_conceptualization/annotate_" + category.lower().replace(' ', '_')
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(promt_template)


if __name__ == '__main__':
    categories = [
        "Explicit Knowledge",
        "Tacit Knowledge",
        "Knowledge Holder",
        "Traditional Human-central Practice",
        "Technology-enable Practice",
        "Digital Technology",
        "Organizational Dependency",
        "Environmental Dependency",
        "Limitation"
    ]
    for category in categories:
        generate_prompt(category)