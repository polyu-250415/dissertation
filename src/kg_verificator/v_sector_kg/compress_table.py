import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from matplotlib.table import Table

# 1. 定义数据（直接复制你提供的文本，使用制表符分割）
data = """node_id	Primiary Category	Retention mechanism	Tacit Knowledge Retained	Conditions and Constraints.	Evidence Chain
s001M01TP01	Digital Codification	It adopts digital technologies like BIM/3D information systems with immersive human-computer interfaces to convert spatial arrangements, schedules, hazards and energy-use interactions into persistent, revisable models. Simulation is an experiential secondary feature, but removing the model would remove the preserved representation on which rehearsal and comparison depend.	Trained Sensory and Perceptual Recognition. The target is expert perceptual recognition: noticing hazardous configurations, reading spatial relationships and anticipating consequences. Such judgement is normally situated and difficult to articulate. BIM/4D cases preserve selected cues and sequences so novices can revisit them and designers can inspect hazards earlier. However, a model captures only encoded cues, not the whole embodied judgement of experienced workers.	Modelling requires investment, specialist time and maintenance; model quality, update routines and user trust condition whether representations become organizational memory. A sharing culture is therefore complementary to technical availability. The evidence supports improved visibility and continuity, but provides limited longitudinal proof that recognition persists in live work.	TE04;TE02 → TP01 → TK06 TP01→ LI07; LI08; LI10;OD06
s001M01TP03	Experience Amplification	It uses immersive XR environments for safe, repeatable situated rehearsal in which learners navigate, identify hazards, manipulate conditions and receive feedback. Digital models support the setting, but retention depends primarily on perception and action within it.	Trained Sensory and Perceptual Recognition; Shared Professional Norms and Standards of Judgment; Practised Motor and Tool-Operation Skill; Embodied Posture, Balance and Spatial Control; Immediate Embodied Response. XR exposes dangerous, rare or inaccessible cues for repeated discrimination and response, but does not fully replace instructor-led coaching, codified materials or manual documentation.	Fidelity, comfort, accessibility, instructional sequencing, validation and transfer to real sites are weakest-link conditions. Memory decay, usability and safety risks, cognitive load, technical and infrastructure barriers, staffing/time, institutional change and validation limits can interrupt retention.	"TE02; TE05→ TP03 → TK06; TK10; TK05; TK07; TK08
TP03 → LI01; LI02; LI03; LI04; LI05; LI06; LI08; LI12; LI13; ED01; ED05; ED08; OD01; OD03; OD04; OD05; OD08"
s001M01TP06	Digital Codification	It uses wearable sensors, cameras and tracking devices to convert fleeting movement, gaze, posture and workload into durable signals and recordings. Feedback and training are secondary; the defining retention function is preserving action traces beyond the original performance.	Trained Sensory and Perceptual Recognition; Embodied Posture, Balance and Spatial Control. Multi-modal capture makes selected bodily and perceptual components inspectable, comparable and potentially teachable, while omitting intention and contextual meaning unless experts interpret the traces.	Consent, occupational governance, device fit, calibration, synchronized video, site access and representative samples condition validity. Physiological variability, measurement flaws and small or artificial samples constrain transfer; evidence for longitudinal internalization is limited.	"TE05; TE02 → TP06 → TK06; TK07 
TP06 → LI03; LI13; LI14; ED01; ED08; OD08"
s001M01TP07	Digital Codification	It applies AI and intelligent computation to extract recurring features, categories, rankings and forecasts from dispersed observations and text, preserving algorithmic representations for later retrieval and comparison.	Trained Sensory and Perceptual Recognition; Shared Professional Norms and Standards of Judgment. Models can encode recurrent cues and decision boundaries, but correlations flatten context and do not reproduce the full situated judgement they approximate.	Representative data, stable taxonomies, interoperability, infrastructure, validation, privacy, model monitoring, leadership, user trust and generalizability form a weakest-link chain. Automation redistributes expert work toward labeling, review and exception handling and cannot fully replace manual documentation.	"TE01 → TP07 → TK06; TK10 
TP07 → LI05; LI06; LI09; LI10; LI11; LI13; LI14; ED04; OD02; OD03; OD06; THR15"
s001M01TP08	Digital Codification	It combines AI with data and knowledge systems to retrieve and recombine stored organizational examples, requirements and embeddings into new, context-specific artifacts. The durable repository and representations provide the retention base; conversational generation is secondary.	Organizational Culture and Unwritten Working Practices. Historical examples can carry recurrent bid logic and organizational ways of framing work into new drafts, but generated prose lacks situated judgement, making human expert review constitutive rather than optional.	Confidentiality, provenance, access control, data interoperability, staffing time, adoption culture, prompt/model quality, reliable retrieval, governance and accountable review condition retention. Biased archives and hallucinations can turn apparent memory into error.	"TE01; TE04; TE02 → TP08 → TK12 
TP08 → LI05; LI08; LI09; LI10; LI14; ED06; OD01; OD02; OD03; OD06; OD08; THR15; THR16"
s001M01TP09	Digital Codification	It uses metadata, knowledge graphs, embeddings and semantic search to convert recorded processes, narratives and examples into persistent structures and indexes. Its dominant contribution is preservation and discoverability rather than situated rehearsal.	Practised Motor and Tool-Operation Skill. Semantic structures preserve process traces, demonstrations and access pathways to relevant precedents, but retrieval alone does not produce competent embodied performance; observation, coaching and practice remain necessary.	Vocabulary quality, metadata consistency, embedding relevance, interoperability and repository completeness determine usefulness. Similarity may retrieve superficially close items, and the narrow evidence set provides limited support for claims about sustained adoption and governance.	TE01; TE04 → TP09 → TK05 → LI05
s001M01TP10	Digital Codification	It records, structures, tags and stores stories, sequences, lessons and hazard decisions as retrievable assets that persist beyond original knowledge holders and project closure. Later discussion is secondary to the durable representation.	Examples and Demonstrations; Unarticulated Know-how; Practised Motor and Tool-Operation Skill; Shared Professional Norms and Standards of Judgment; Informal Coordination, Communication and Escalation Know-how; Organizational Culture and Unwritten Working Practices. Archives preserve contextual traces and rationales, but cannot reproduce embodied experience in full.	Contribution time, psychological safety, incentives, taxonomy, access controls, maintenance and retrieval practices jointly condition value. Capital, workload/expertise and culture/adoption constraints can produce empty or decontextualized repositories despite available infrastructure.	"TE04; TE02; TE05; TE08 → TP10 → TK02; TK04; TK05; TK10; TK11; TK12 
TP10 → LI07; LI08; LI09; LI10; ED01; ED02; OD01; OD02; OD03; OD04; OD06; OD07"
s001M01TP12	Experience Amplification	It combines multimedia demonstrations, interaction and blended sequencing to give learners repeated opportunities to observe and apply contextual examples. Recordings provide codified support, while internalization through guided participation and practice is dominant.	Practised Motor and Tool-Operation Skill; Informal Coordination, Communication and Escalation Know-how. Demonstrations expose timing, sequencing and coordination cues that prose misses, though engagement and immediate understanding are not equivalent to durable competent performance.	Scheduling, learner access, cognitive load, facilitation, participation and cultural relevance condition effectiveness. Staffing/time and adoption barriers, uneven group contribution or passive viewing can interrupt internalization; evidence for long-term workplace transfer is limited.	"TE02; TE04; TE07 → TP12 → TK05; TK11 
TP12 → LI03; LI04; LI08; LI09; ED03; OD02; OD04; OD05; OD08; THR11"
s001M01TP13	Digital Codification	It translates observations, survey responses and performance decisions into durable scores, rankings and longitudinal comparisons. Evaluation can guide experiential learning, but its dominant contribution is an explicit evaluative representation.	Shared Professional Norms and Standards of Judgment. Hazard identification, evaluation and response reveal observable proxies for professional judgement, but scores do not capture its entire tacit basis and evaluation alone does not demonstrate capture or transfer.	Valid criteria, comparable scenarios, representative participants, reliable instruments and regulatory alignment determine interpretability. Physiological, cognitive or demographic differences and weak research designs can confound apparent gains.	"TE02; TE04 → TP13 → TK10 
TP13 → LI03; LI13; ED01"
"""

# 2. 使用StringIO读取数据，并指定分隔符为制表符
from io import StringIO
df = pd.read_csv(StringIO(data), sep='\t', engine='python', quotechar='"')

# 3. 设置绘图参数 - 由于表格列数多且文本长，需要设置极大的画布
fig, ax = plt.subplots(figsize=(36, 20))  # 宽度36英寸，高度20英寸
ax.axis('off')  # 隐藏坐标轴

# 4. 创建表格
# 将DataFrame转换为列表格式，同时保留列名
cell_text = df.values.tolist()
columns = df.columns.tolist()

# 使用matplotlib的table函数
table = ax.table(cellText=cell_text,
                 colLabels=columns,
                 cellLoc='left',  # 左对齐，便于阅读长文本
                 loc='center',
                 colWidths=[0.08, 0.08, 0.18, 0.20, 0.22, 0.24])  # 为每一列分配宽度比例

# 5. 美化表格样式
table.auto_set_font_size(False)
table.set_fontsize(8)  # 字体调小以适应长文本

# 设置表头样式（加粗、背景色）
for (i, j), cell in table.get_celld().items():
    if i == 0:  # 表头行
        cell.set_text_props(fontweight='bold', color='white')
        cell.set_facecolor('#40466e')
        cell.set_edgecolor('black')
    else:  # 数据行
        cell.set_facecolor('#f5f5f5' if i % 2 == 0 else 'white')
        cell.set_edgecolor('grey')
        cell.set_text_props(wrap=True)  # 启用自动换行

# 6. 调整行高，使其能容纳多行文本
# 由于文本长度不一，采用自动调整
table.scale(1, 2.5)  # 垂直方向放大2.5倍，水平不变

# 7. 保存为SVG文件
plt.savefig('table_output.svg', format='svg', dpi=300, bbox_inches='tight', pad_inches=0.5)
print("SVG文件已成功生成：table_output.svg")