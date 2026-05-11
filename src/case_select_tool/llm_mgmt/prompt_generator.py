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
Doc_type: UUse only one of the following categories;you may customize the items inside the parentheses for the `"Other"` category.
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
    "Abstract": "Purpose – Technological tools for knowledge management (KM) actively support and enhance knowledge acquisition and sharing in organizations. However, technology for KM has been understudied, especially in terms of disruptive technologies (DTs). There is a need to identify how DTs, which are becoming increasingly important in industry and society, are applied to KM and their impact. This paper aims to examine the current state of technology and DT adoption in KM. Design/methodology/approach – The analysis involves four steps. First, we examine the current status of DT in academia through a keyword co-occurrence network of literature. Second, we analyze the technological convergence (TC) of KM technology through the cooperative patent classification code co-classification analysis of patents. Third, we explore the main topics of KM technologies using BERTopic, and finally, we explore the introduction of DT into KM technologies and suggest potential TC combinations for the future. Findings – KM technologies can be categorized into four main topics (knowledge acquisition, sharing, searching, and transfer), and DT is most often applied to knowledge transfer and acquisition. The DTs that are attracting attention from academia and industry are artificial intelligence, augmented and virtual reality, and blockchain, which have applications in healthcare, supply chain management, and human resource management. Originality/value – The findings provide useful insights for organizations to build a technology roadmap for KM. They can also improve the rigid mindset of organization employees toward DT adoption and innovation. By adopting a KM system that leverages DT, organizations will be able to manage and operate efficiently and systematically. © 2024 Emerald Publishing Limited"
  }
]
    obj = LiteratureReviewPrompt(body=body)
    print(obj.get_prompt('Cmd_Screen_by_Abstract'))