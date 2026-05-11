Retrieve papers from ProQuest

Keywords for filter:
Field Code	Full Name / Description
AB	Abstract – searches within the abstract only
AU	Author – searches author names
TI	Title – searches words in the document title
SU	Subject – searches subject terms (often controlled vocabulary or author keywords)
KW	Keywords – author-provided keywords (if available)
FT	Full Text – searches the entire full-text content (when available)
SO	Publication Title / Source – journal, conference, or publication name
IS	ISSN / ISBN – searches by ISSN (journals) or ISBN (books/dissertations)
PU	Publisher
PB	Publication Body (sometimes used for publisher or sponsoring organization)
LA	Language
DT	Document Type (e.g., article, dissertation, report, book review)
PT	Publication Type
CF	Conference Information (e.g., conference name, proceedings)
DE	Descriptors / Thesaurus Terms (subject headings from ProQuest’s indexing thesaurus)
ID	Identifier (e.g., DOI, accession number)
RN	Report Number
CO	Corporate Author / Organization
GE	Geographic Term
PE	Person/Name as Subject
TX	All Text (similar to full text but may include metadata; behavior varies)

Use Boolean Operators for Multiple Conditions
AND: All terms must appear (narrows results).
OR: Any of the terms may appear (broadens results).
NOT: Excludes terms.

Commands_1
(TI("knowledge retention") OR TI("knowledge loss") OR TI("loss of knowledge") 
OR KW("knowledge retention") OR KW("knowledge loss") OR KW("loss of knowledge")
OR AB("knowledge retention") OR AB("knowledge loss") OR AB("loss of knowledge"))
AND (STYPE("Scholarly Journals") OR STYPE("Conference Papers & Proceedings")
OR STYPE("Government & Official Publications") OR STYPE("Dissertations & Theses")
OR STYPE("Books") OR STYPE("Newspapers")) AND pd(20160101-20260115)

Commands_2
(AB("knowledge retention") OR AB("knowledge loss") OR AB("loss of knowledge"))
AND (AB("technology") OR AB("technologies"))
AND pd(20220101-20260127)

Web of Service
(knowledge retention(Abstract) OR knowledge loss(Abstract) or loss of knowledge(abstract)) and 
technolog*(Abstract)

Commands
(TI("older worker") OR TI("retiring worker") OR TI("aging workforce")
OR KW("older worker") OR KW("retiring worker") OR KW("aging workforce")
OR AB("older worker") OR AB("retiring worker") OR AB("aging workforce"))
AND (TI("knowledge retention") OR TI("knowledge loss") OR TI("loss of knowledge") 
OR KW("knowledge retention") OR KW("knowledge loss") OR KW("loss of knowledge")
OR AB("knowledge retention") OR AB("knowledge loss") OR AB("loss of knowledge"))
AND (STYPE("Scholarly Journals") OR STYPE("Conference Papers & Proceedings")
OR STYPE("Government & Official Publications") OR STYPE("Dissertations & Theses")
OR STYPE("Books") OR STYPE("Newspapers")) AND pd(20000101-20260115)


AB("knowledge retention strategies") OR AB("knowledge retention approaches")
OR AB("knowledge retention framework") OR AB("knowledge retention model")
OR AB("knowledge retention tools") OR AB("knowledge retention method")


(AB("older worker") OR AB("retiring worker") OR AB("aging workforce") OR AB("generational"))
AND (AB("knowledge retention") OR AB("knowledge loss") OR AB("loss of knowledge"))
AND (AB("case study") OR AB("practice"))

