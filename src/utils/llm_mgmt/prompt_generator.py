class LiteratureReviewPrompt:
    def __init__(self, body=[]):
        self.prompt_template = {
            "Cmd_Screen_by_Abstract": f"""
You are an expert academic coding assistant with interdisciplinary expertise in knowledge management, emerging technologies for KM, and computer science research classification.

Task
Analyze the fields named `Title` and `Abstract` within each JSON object and code each entry into a single JSON object within a unified output JSON array, using a unified, conservative, evidence-based standard.

Input dataset format:
- The input will be a JSON array of objects.
- Each object contains at least the fields: `uuid`, `Title`, `Abstract`.

Input dataset:
{body}

- Return exactly one coded JSON object per input object, maintaining the original order.

Coding questions:
Answer the questions from Q1 to Q5 one by one.
- Q1: Whether the study explicitly discusses how to capture or retain knowledge from individuals or organizations
- Q2: If the answer to Q1 is yes, what tacit knowledge is captured or retained from individuals or organizations; If the answer to Q1 is no, return "None identified"
- Q3: Whether digital technologies are explicitly used to capture or retain tacit knowledge which marked in Q2
- Q4: If the answer to Q3 is yes, what technologies are adopted to capture or retain knowledge; If the answer to Q3 is no, return "None identified"
- Q5: What's the document type of this paper

Core rule:
– Use only information explicitly stated or strongly implied in the `Abstract` field.
– Do not invent unsupported information. When evidence is weak or ambiguous, reflect that in the relevant confidence field.
– Follow the coding question order. If the answer to Q1 is `No`, fill the remaining fields according to the missing-value rules and proceed to the next object.

General coding principles:
1. Apply a unified standard across all abstracts
2. Be conservative
3. Preserve original Abstract wording where useful, but normalize labels for consistency
4. Base each coded value on evidence from the Abstract
5. If multiple items appear, join them with "; "
6. Do not guess
7. Never confuse the tenses of the viewpoints in the paper. For example, do not extract a viewpoint to be verified as a confirmed one, and vice versa.

Q1 Coding rules:
kr_flag: `Yes` or `No`
- `Yes` only when the abstract clearly discusses preserving, capturing, retaining, transferring, or preventing loss of knowledge from individuals，group and organization environment.
- `No` when the abstract was about knowledge management without clear retention/capture. For example, employees learn from existing documents.
kr_evidence: Exact or closely paraphrased evidence from the original abstract supporting the kr_flag. Whether "Yes" or "No", you should explain your view.
kr_confidence: `high`, `medium`, or `low`

Q2 Coding rules:
tacit_knowledge: Extract all explicit or strongly implied tacit knowledge related to Q1, preserving the exact phrase. If Q1=`No`, use `"None identified"`.
TK_normalized: Use only one or more of the following categories; you may customize the items inside the parentheses for the `"Other"` category.
    - Somatic tacit knowledge ( Experiential know-how, Procedural know-how, Craft knowledge, Operational know-how, other)
    - Cognitive tacit knowledge (Expert judgment, Decision rules, Clinical know-how, other)
    - Collective and relational tacit knowledge (Teamwork know-how, other)
    - Adaptive tacit knowledge(Situational problem-solving, other)
    - Other(*)
TK_confidence: `high`, `medium`, or `low`

Q3 Coding rules:
DT_flag: `Yes` or `No`
- `Yes` only when one or more digital technologies were clearly used to preserve, capture, archive, transfer, or retain knowledge.
- `No` when digital technology was not used or discussed to preserve, capture, archive, transfer, or retain knowledge.
DT_evidence: Exact or closely paraphrased evidence from the original abstract supporting the DT_flag. Whether "Yes" or "No", you should explain your view.
DT_confidence: `high`, `medium`, or `low`

Q4 Coding rules:
Digital_Technologies: Extract all explicit or strongly implied technologies related to Q3, preserving the exact phrase. If Q3=`No`, use `"None identified"`.
DT_normalized: Use these ACM-aligned classes only; you may customize the items inside the parentheses for the `"Other"` category.
    - Artificial Intelligence and Intelligent Computation
    - Human–Computer Interaction and Immersive Technologies
    - Cyber-Physical Systems, IoT, and Smart Environments
    - Data, Information, and Knowledge Systems
    - Imaging, Sensing, and Perception Technologies
    - Distributed, Secure, and Trust Technologies
    - Mobile, Social, and Communication Technologies
    - Rule-Based, Decision, and Expert Systems
    - Others(*)

Q5 coding rules:
Doc_type: Use only one of the following categories;you may customize the items inside the parentheses for the `"Other"` category.
    - Literature review 
    - Empirical Study
    - Case Study
    - Conceptual Paper
    - Other(*)
Doc_type_confidence: `high`, `medium`, or `low`

Fixed output JSON structure:
Each output object must contain exactly these keys in this order:
{{
  "uuid": "string",
  "kr_flag": "string",
  "kr_evidence": "string",
  "kr_confidence": "string",
  "tacit_knowledge": "string",
  "TK_normalized": "string",
  "TK_confidence": "string",
  "DT_flag": "string",
  "DT_evidence": "string",
  "DT_confidence": "string",
  "Digital_Technologies": "string",
  "DT_normalized": "string",
  "Doc_type": "string",
  "Doc_type_confidence": "string"
}}
uuid: Use the `uuid` value from the input object.

Missing-value rules:
- If nothing is identified for a field that expects a value, write: `"None identified"`
- Use `"Yes"` or `"No"` only where the field explicitly requires a Yes/No flag.
- All values must be strings.

Decision rules for difficult cases:
- If the Abstract discusses knowledge sharing, learning, or KM systems but not clearly retention, do not automatically code it as a retention practice.
- If a technology is mentioned but not clearly linked to capture or retention, code cautiously and lower confidence.
- If retention is implied but not explicit, code conservatively.
- If no defensible evidence exists, write `"None identified"`.

Output instructions:
- Return ONLY a valid JSON array containing one coded object per input object.
- Do not wrap the output in markdown code blocks (e.g., ```json).
- Do not include explanations, notes, or additional text outside the JSON array.
""",
        "cmd_annotate_by_abstract": f"""
You are an expert academic coding assistant with interdisciplinary expertise in knowledge management (KM), emerging technologies for KM, and computer science research classification.

### Task
Analyze the fields named `Title` and `Abstract` within each JSON object in the input dataset. Code each entry into a single JSON object within a unified output JSON array, using a strict, conservative, evidence-based standard.

### Input Dataset Format
- The input is a JSON array of objects.
- Each object contains at least the fields: `uuid`, `Title`, and `Abstract`.

### Input Dataset
{body}

---

### Core Coding Rules & Principles
1. **Strict Evidence:** Use only information explicitly stated or strongly implied in the `Abstract` field. Do not invent unsupported information. If evidence is weak or ambiguous, reflect that in the confidence field or use missing-value defaults.
2. **Conservative Approach:** Do not guess. Do not confuse the tenses or viewpoints of the paper (e.g., do not extract a hypothesis/viewpoint to be verified as a confirmed factual result).
3. **Consistency:** Apply a unified standard across all abstracts. Preserve original wording where useful, but normalize categories exactly as specified.
4. **Formatting Multiple Items:** If multiple discrete items appear within a single string field, join them with "; ".

---

### Specific Domain Coding Rules

#### Q1: Tacit Knowledge Extraction (`tacit_knowledge_array`)
Extract all explicit or strongly implied domain tacit knowledge objects in this study. If none are present, return an empty array `[]`. Each object in the array must contain:
- `tacit_knowledge`: The tacit knowledge, retaining the original description from the study. Do not use generic conceptual descriptions like "knowledge acquisition" or "tacit knowledge". If no specific knowledge is found, do not return this object in tacit_knowledge_array.
- `tacit_knowledge_normalized`: Must be exactly ONE of the following categories (you may customize the specific sub-type inside the parentheses for the "Other" category if needed):
  - "Somatic tacit knowledge (Experiential know-how, Procedural know-how, Craft knowledge, Operational know-how, other)"
  - "Cognitive tacit knowledge (Expert judgment, Decision rules, Clinical know-how, other)"
  - "Collective and relational tacit knowledge (Teamwork know-how, other)"
  - "Adaptive tacit knowledge (Situational problem-solving, other)"
  - "Other(*)"
- `tacit_knowledge_confidence`: Must be exactly "high", "medium", or "low".

#### Q2: Digital Technology Extraction (`digital_technology_array`)
Extract all explicit or strongly implied technologies in this study. If none are present, return an empty array `[]`. Each object in the array must contain:
- `digital_technology`: The exact phrase/name of the technology used in the text.
- `digital_technology_normalized`: Must be exactly ONE of the following ACM-aligned classes (you may customize the items inside the parentheses for the "Others" category if needed):
  - "Artificial Intelligence and Intelligent Computation"
  - "Human–Computer Interaction and Immersive Technologies"
  - "Cyber-Physical Systems, IoT, and Smart Environments"
  - "Data, Information, and Knowledge Systems"
  - "Imaging, Sensing, and Perception Technologies"
  - "Distributed, Secure, and Trust Technologies"
  - "Mobile, Social, and Communication Technologies"
  - "Rule-Based, Decision, and Expert Systems"
  - "Others(*)"

#### Q3: Sector Classification (`sector`)
Extract the industry sector(s) to which the study's practice belongs, using the Standard Industrial Classification (SIC) Code Manual.
You MUST select the sector from the **Reference SIC Table** below. Do not invent new sector names or IDs.

**Reference SIC Table (Division (Major Group) → ID)**
- Agriculture, Forestry, And Fishing (Agriculture, Forestry, And Fishing) → SIC 01-09
- Mining (Mining) → SIC 10-14
- Construction (Building Construction—General Contractors And Operative Builders) → SIC 15
- Construction (Heavy Construction Other Than Building Construction—Contractors) → SIC 16
- Construction (Construction—Special Trade Contractors) → SIC 17
- Manufacturing (Food And Kindred Products) → SIC 20
- Manufacturing (Tobacco Products) → SIC 21
- Manufacturing (Textile Mill Products) → SIC 22
- Manufacturing (Apparel And Other Finished Products Made From Fabrics And Similar Materials) → SIC 23
- Manufacturing (Lumber And Wood Products, Except Furniture) → SIC 24
- Manufacturing (Furniture And Fixtures) → SIC 25
- Manufacturing (Paper And Allied Products) → SIC 26
- Manufacturing (Printing, Publishing, And Allied Industries) → SIC 27
- Manufacturing (Chemicals And Allied Products) → SIC 28
- Manufacturing (Petroleum Refining And Related Industries) → SIC 29
- Manufacturing (Rubber And Miscellaneous Plastics Products) → SIC 30
- Manufacturing (Leather And Leather Products) → SIC 31
- Manufacturing (Stone, Clay, Glass, And Concrete Products) → SIC 32
- Manufacturing (Primary Metal Industries) → SIC 33
- Manufacturing (Fabricated Metal Products, Except Machinery And Transportation Equipment) → SIC 34
- Manufacturing (Industrial And Commercial Machinery And Computer Equipment) → SIC 35
- Manufacturing (Electronic And Other Electrical Equipment And Components, Except Computer Equipment) → SIC 36
- Manufacturing (Transportation Equipment) → SIC 37
- Manufacturing (Measuring, Analyzing, And Controlling Instruments; Photographic, Medical And Optical Goods; Watches And Clocks) → SIC 38
- Manufacturing (Miscellaneous Manufacturing Industries) → SIC 39
- Transportation, Communications, Electric, Gas, And Sanitary Services (Railroad Transportation) → SIC 40
- Transportation, Communications, Electric, Gas, And Sanitary Services (Local And Suburban Transit And Interurban 
Highway Passenger Transportation) → SIC 41
- Transportation, Communications, Electric, Gas, And Sanitary Services (Motor Freight Transportation And Warehousing) → SIC 42
- Transportation, Communications, Electric, Gas, And Sanitary Services (United States Postal Service) → SIC 43
- Transportation, Communications, Electric, Gas, And Sanitary Services (Water Transportation) → SIC 44
- Transportation, Communications, Electric, Gas, And Sanitary Services (Transportation By Air) → SIC 45
- Transportation, Communications, Electric, Gas, And Sanitary Services (Pipelines, Except Natural Gas) → SIC 46
- Transportation, Communications, Electric, Gas, And Sanitary Services (Transportation Services) → SIC 47
- Transportation, Communications, Electric, Gas, And Sanitary Services (Communications) → SIC 48
- Transportation, Communications, Electric, Gas, And Sanitary Services (Electric, Gas, And Sanitary Services) → SIC 49
- Wholesale Trade (Wholesale Trade—Durable Goods) → SIC 50
- Wholesale Trade (Wholesale Trade—Nondurable Goods) → SIC 51
- Retail Trade (Building Materials, Hardware, Garden Supply, And Mobile Home Dealers) → SIC 52
- Retail Trade (General Merchandise Stores) → SIC 53
- Retail Trade (Food Stores) → SIC 54
- Retail Trade (Automotive Dealers And Gasoline Service Stations) → SIC 55
- Retail Trade (Apparel And Accessory Stores) → SIC 56
- Retail Trade (Home Furniture, Furnishings, And Equipment Stores) → SIC 57
- Retail Trade (Eating And Drinking Places) → SIC 58
- Retail Trade (Miscellaneous Retail) → SIC 59
- Finance, Insurance, And Real Estate (Depository Institutions) → SIC 60
- Finance, Insurance, And Real Estate (Nondepository Credit Institutions) → SIC 61
- Finance, Insurance, And Real Estate (Security And Commodity Brokers, Dealers, Exchanges, And Services) → SIC 62
- Finance, Insurance, And Real Estate (Insurance Carriers) → SIC 63
- Finance, Insurance, And Real Estate (Insurance Agents, Brokers, And Service) → SIC 64
- Finance, Insurance, And Real Estate (Real Estate) → SIC 65
- Finance, Insurance, And Real Estate (Holding And Other Investment Offices) → SIC 67
- Services (Hotels, Rooming Houses, Camps, And Other Lodging Places) → SIC 70
- Services (Personal Services) → SIC 72
- Services (Business Services) → SIC 73
- Services (Automotive Repair, Services, And Parking) → SIC 75
- Services (Miscellaneous Repair Services) → SIC 76
- Services (Motion Pictures) → SIC 78
- Services (Amusement And Recreation Services) → SIC 79
- Services (Health Services) → SIC 80
- Services (Legal Services) → SIC 81
- Services (Educational Services) → SIC 82
- Services (Social Services) → SIC 83
- Services (Museums, Art Galleries, And Botanical And Zoological Gardens) → SIC 84
- Services (Membership Organizations) → SIC 86
- Services (Engineering, Accounting, Research, Management, And Related Services) → SIC 87
- Services (Private Households) → SIC 88
- Services (Miscellaneous Services) → SIC 89
- Public Administration (Executive, Legislative, And General Government, Except Finance) → SIC 91
- Public Administration (Justice, Public Order, And Safety) → SIC 92
- Public Administration (Public Finance, Taxation, And Monetary Policy) → SIC 93
- Public Administration (Administration Of Human Resource Programs) → SIC 94
- Public Administration (Administration Of Environmental Quality And Housing Programs) → SIC 95
- Public Administration (Administration Of General Economic Programs) → SIC 96
- Public Administration (National Security And International Affairs) → SIC 97
- Nonclassifiable Establishments (Nonclassifiable Establishments) → SIC 99

If the most suitable sector is not in the table above, use the closest matching major group and set `sector_confidence` to "low". You MUST NOT make up an ID.

- `sector_name`: Must exactly match the "Division (Major Group)" string from the table.
- `sector_id`: Must exactly match the "SIC XX" code from the same table row.
- `sector_confidence`: "high", "medium", or "low".

---

### Missing-Value Rules
- If no data is identified for a required string field, write: "None identified"
- All values (except arrays and nested objects) must be strings.

---

### Critical Self-Correction & Verification Step
Before generating the final JSON object for each paper, you must perform a silent, internal compliance check to ensure strict alignment with the coding rules. Verify the following:
1. **Evidence Check:** Did I extract a hypothesis, future goal, or unverified viewpoint as a confirmed factual 
result? If yes, remove it or lower the confidence to 'low'.
2. **Q1 Format Validation:** Is the `tacit_knowledge` just a generic tacit knowledge term (e.g., "knowledge 
acquisition", "tacit knowledge", etc), rewrite it to specific tacit knowledge strictly aligning with the statement in the study.
3. **Q1 Taxonomy Match:** Is `tacit_knowledge_normalized` an exact string match for one of the 5 allowed 
macro-categories? (Ensure the macro label prefix like "Somatic tacit knowledge" is perfectly preserved).
4. **Q2 Taxonomy Match:** Is `digital_technology_normalized` an exact string match for one of the 9 allowed ACM classes?
5. **Q3 SIC Selection:** Did I choose the `sector_name` and `sector_id` strictly from the provided Reference SIC 
Table? If no exact match is possible, did I pick the closest and set confidence to "low"?
6. **Q3 Consistency Validation:** Are `sector_name` and `sector_id` taken from the same row in the Reference SIC Table? If not, correct them to be a matched pair before output.

If any check fails during your internal processing, correct it instantly before writing the output.

---

### Fixed Output Schema
Return exactly one coded JSON object per input object, maintaining the original order. The output must strictly follow this JSON schema structure:
[
  {{
    "uuid": "string",
    "Title": "string",
    "tacit_knowledge_array": [
      {{
        "tacit_knowledge": "string",
        "tacit_knowledge_normalized": "string",
        "tacit_knowledge_confidence": "string"
      }}
    ],
    "digital_technology_array": [
      {{
        "digital_technology": "string",
        "digital_technology_normalized": "string"
      }}
    ],
    "sector": {{
      "sector_name": "string",
      "sector_id": "string",
      "sector_confidence": "string"
    }}
  }}
]

IMPORTANT: Output only the raw JSON array. Do NOT include any markdown formatting, code fences, or explanations.
"""
    }

    def get_prompt(self, cmd):
        return self.prompt_template[cmd]

if __name__ == '__main__':
    body = [
  {
    "uuid": "5446e584-5403-4f37-83f1-e7867e994fbc",
    "Title": "Responsible Ai In Knowledge Creation: An Exploration Of Generative Ai'S Opportunities And Risks",
    "Abstract": "This study explores the transformative potential and inherent challenges of Generative AI in the domain of knowledge creation and management, using the Socialization, Externalization, Combination, and Internalization (SECI) model as an analytical framework. Our qualitative research, based on content analysis from expert opinions, reveals that the integration of Generative AI in knowledge processes is inevitable and offers substantial productivity enhancements. These include providing diverse expression channels, simulating personalized interactions, and facilitating cross-disciplinary communication. However, significant risks accompany these benefits, such as threats to data security, personal privacy, and intellectual property, as well as issues of misinformation, data bias, and reduced human cognitive engagement. The findings extend the SECI model by highlighting specific challenges posed by AI technologies at each knowledge creation stage: socialization, externalization, combination, and internalization. The study underscores the necessity of a balanced approach, integrating technological, ethical, and socio-cultural perspectives to evaluate AI's impact comprehensively. Our research contributes to the theoretical understanding of AI's role in knowledge management and offers actionable strategies for its ethical and effective implementation, emphasizing the importance of interdisciplinary approaches and continuous regulatory adaptation. © 2026 Elsevier Inc."
  },
  {
    "uuid": "10e101b7-3037-487a-8ae0-44336dc20be0",
    "Title": "Effects Of Information Technology Platforms And Governance On Relational Value Creation In Digital Supply Chains",
    "Abstract": "With firms increasingly collaborating to maximize value creation opportunities in digital supply chains, a clear understanding of the foundations for value creation activities must be acquired. The relational view proposes a set of value creation determinants that can enhance interfirm competitive advantages. This research identifies sources of relational value based on relational view theory, namely platform alignment, process synchronization, knowledge sharing, and governance; we also develop an explanatory model for the relationships among these factors. Survey data collected from 230 high-tech manufacturing companies in China and Taiwan reveal several findings: (a) Platform alignment and governance affect collaboration activities directly: process synchronization and knowledge sharing. Moreover, platform alignment partially mediates the relationship between governance and these two collaborative activities. (b) Process synchronization and knowledge sharing mediate the relationship between platform alignment and relational value. (c) Governance has a direct effect on platform alignment. These findings support the relational view, indicating that the four determinants of value creation contribute to relational value. They also recognize that governance and platform alignment are two determinants of creating relational value through interfirm collaborations. By understanding the relationships, firms can effectively leverage information technology platforms and governance mechanisms to improve interfirm collaborations and ultimately create relational value in digital supply chains. © 2025"
  },
  {
    "uuid": "b54177cf-c204-4220-b961-d02977472a26",
    "Title": "Disruptive Technologies For Knowledge Management: Bibliometric Review And Patent Analysis",
    "Abstract": "Purpose – Technological fastembed for knowledge management (KM) actively support and enhance knowledge acquisition and sharing in organizations. However, technology for KM has been understudied, especially in terms of disruptive technologies (DTs). There is a need to identify how DTs, which are becoming increasingly important in industry and society, are applied to KM and their impact. This paper aims to examine the current state of technology and DT adoption in KM. Design/methodology/approach – The analysis involves four steps. First, we examine the current status of DT in academia through a keyword co-occurrence network of literature. Second, we analyze the technological convergence (TC) of KM technology through the cooperative patent classification code co-classification analysis of patents. Third, we explore the main topics of KM technologies using BERTopic, and finally, we explore the introduction of DT into KM technologies and suggest potential TC combinations for the future. Findings – KM technologies can be categorized into four main topics (knowledge acquisition, sharing, searching, and transfer), and DT is most often applied to knowledge transfer and acquisition. The DTs that are attracting attention from academia and industry are artificial intelligence, augmented and virtual reality, and blockchain, which have applications in healthcare, supply chain management, and human resource management. Originality/value – The findings provide useful insights for organizations to build a technology roadmap for KM. They can also improve the rigid mindset of organization employees toward DT adoption and innovation. By adopting a KM system that leverages DT, organizations will be able to manage and operate efficiently and systematically. © 2024 Emerald Publishing Limited"
  }
]
    obj = LiteratureReviewPrompt(body=body)
    print(obj.get_prompt('Cmd_Screen_by_Abstract'))