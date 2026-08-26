import os
import json
import io
import pandas as pd
from pathlib import Path
from flask import Flask, render_template_string, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "audit_secret_key_2026"

in_memory_cache = dict()

# 主页面模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>Annotation Review Tool</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        html,body {
            font-size: 13px; /* 全局缩小基础字体 */
        }
        h3 {
            font-size:16px;
            margin-bottom:0.5rem;
        }
        h5 {
            font-size:14px;
            margin-bottom:0.4rem;
        }
        .sidebar{height:92vh;overflow:auto;border-right:1px solid #ddd;}
        .main-content{height:92vh;overflow:auto;}
        textarea.human-review-input{width:100%;border:1px solid #ccc;min-height:40px;font-size:12px;padding:4px;}
        textarea.interpret-input{width:100%;border:1px solid #ccc;min-height:40px;font-size:12px;padding:4px;}
        .nav-item-btn {
            width:100%;
            text-align:left !important;
            border:none !important;
            border-radius:0;
            white-space:nowrap;
            overflow:hidden;
            text-overflow:ellipsis;
            font-size:12px;
            padding:4px 8px !important;
        }
        .nav-item-btn.active-bg {
            background:#ced4da;
        }
        .nav-item-btn:hover {
            background:#e9ecef;
        }
        /* 二级导航样式 */
        .nav-group {
            border-bottom:1px solid #eee;
        }
        .nav-group summary {
            cursor:pointer;
            padding:6px 10px;
            font-weight:600;
            font-size:12.5px;
            background:#f8f9fa;
            list-style:none;
            user-select:none;
        }
        .nav-group summary::-webkit-details-marker { display:none; }
        .nav-group summary::before {
            content:"▶ ";
            font-size:8px;
            color:#6c757d;
        }
        .nav-group[open] summary::before {
            content:"▼ ";
        }
        .nav-group summary:hover {
            background:#e9ecef;
        }
        .nav-group .item-list {
            padding-left:0;
        }
        .nav-group .item-list .nav-item-btn {
            padding-left:22px !important;
        }
        .loading-mask{
            position:absolute;top:0;left:0;right:0;bottom:0;background:rgba(255,255,255,0.7);
            display:flex;align-items:center;justify-content:center;font-weight:bold;font-size:13px;
        }
        /* 全局压缩间距 */
        .mt-2 {margin-top:0.4rem !important;}
        .mb-3 {margin-bottom:0.6rem !important;}
        .p-0 {padding:0 !important;}
        .p-2 {padding:0.4rem !important;}
        .p-2 > h5 {padding:0.3rem 0.5rem !important;}
        /* 表单控件缩小 */
        .form-control, .form-select {
            font-size:12px;
            padding:0.25rem 0.4rem;
            height:auto;
        }
        .btn {
            font-size:12px;
            padding:0.25rem 0.5rem;
        }
        label {
            font-size:12px;
            margin-bottom:0.2rem;
        }
        /* 表格进一步压缩行高 */
        .table-sm th,
        .table-sm td {
            padding:0.3rem 0.4rem !important;
            font-size:12px;
        }
    </style>
</head>
<body>
<div class="container-fluid mt-2">
    <h3>Annotation Review Tool</h3>
    {% with messages = get_flashed_messages() %}
        {% if messages %}
            {% for msg in messages %}
                <div class="alert alert-success py-2 px-3">{{msg}}</div>
            {% endfor %}
        {% endif %}
    {% endwith %}
    {% if error %}
        <div class="alert alert-danger py-2 px-3">{{error}}</div>
    {% endif %}

    <form method="post" id="mainForm">
        <div class="row mb-3">
            <div class="col-auto">
                <label>data_dir</label>
                <input class="form-control" name="data_dir" id="inputDataDir" value="{{data_dir}}">
            </div>
            <div class="col-auto">
                <label>case_id</label>
                <input class="form-control" name="case_id" id="inputCaseId" value="{{case_id}}">
            </div>
            <div class="col-auto">
                <label>Validation Mode</label>
                <select class="form-select" name="check_mode" id="checkModeSelect">
                    <option value="node" {% if check_mode=="node" %}selected{% endif %}>node</option>
                    <option value="relation" {% if check_mode=="relation" %}selected{% endif %}>relation</option>
                </select>
            </div>
            <div class="col-auto align-self-end">
                <button class="btn btn-primary" type="submit">Load</button>
                <button class="btn btn-success" onclick="doExport()">📥Export CSV</button>
                <button class="btn btn-danger" onclick="doReset()">🔄Reset Cache</button>
            </div>
        </div>

        <input type="hidden" name="action" id="actionInput">
        <input type="hidden" name="selected_nav" id="selNavInput" value="{{selected_nav}}">
        <input type="hidden" name="target_nav" id="targetNavInput" value="">
        <input type="hidden" name="row_payload" id="rowPayload">
    </form>

        <div class="row">
            <div class="col-3 sidebar p-0">
                <h5 class="p-2">Navigation List</h5>

                {% if check_mode=="node" %}
                    {% for cat in nav_tree %}
                        <details class="nav-group" {% if cat.has_selected %}open{% endif %}>
                            <summary>{{cat.category}} <span class="text-muted fw-normal">({{cat.nodes|length}})</span></summary>
                            <div class="item-list">
                                {% for nav_item in cat.nodes %}
                                    <button type="button" class="nav-item-btn btn {% if nav_item.id==selected_nav %}active-bg{% endif %}"
                                            onclick="ajaxSwitchNav('{{nav_item.id}}', event)">
                                        {{nav_item.name}}
                                    </button>
                                {% endfor %}
                            </div>
                        </details>
                    {% endfor %}
                {% else %}
                    {# relation模式：一级relation_type，二级边 #}
                    {% for rt in rel_tree %}
                        <details class="nav-group" {% if rt.has_selected %}open{% endif %}>
                            <summary>{{rt.rel_type}} <span class="text-muted fw-normal">({{rt.edges|length}})</span></summary>
                            <div class="item-list">
                                {% for nav_item in rt.edges %}
                                    <button type="button" class="nav-item-btn btn {% if nav_item.id==selected_nav %}active-bg{% endif %}"
                                            onclick="ajaxSwitchNav('{{nav_item.id}}', event)">
                                        {{nav_item.name}}
                                    </button>
                                {% endfor %}
                            </div>
                        </details>
                    {% endfor %}
                {% endif %}
            </div>

            <div class="col-9 main-content p-2" id="mainContentWrap" style="position:relative;">
                {{main_content_html|safe}}
            </div>
        </div>

<script>
// 优先从表单读取真实参数，不再只依赖url searchParams
function getFormParams(){
    return {
        data_dir: document.getElementById("inputDataDir").value.trim(),
        case_id: document.getElementById("inputCaseId").value.trim(),
        check_mode: document.getElementById("checkModeSelect").value,
    }
}

document.getElementById("checkModeSelect").addEventListener("change", function(){
    const params = new URLSearchParams();
    const fp = getFormParams();
    params.set("data_dir", fp.data_dir);
    params.set("case_id", fp.case_id);
    params.set("check_mode", this.value);
    window.location.href = "?" + params.toString();
});

// 局部切换导航，只刷新右侧表格
async function ajaxSwitchNav(targetNav, event){
    if(event) event.preventDefault();
    const wrap = document.getElementById("mainContentWrap");
    wrap.insertAdjacentHTML("beforeend",`<div class="loading-mask" id="loadingMask">loading...</div>`);
    const fp = getFormParams();

    try{
        const formData = new FormData();
        formData.append("data_dir", fp.data_dir);
        formData.append("case_id", fp.case_id);
        formData.append("check_mode", fp.check_mode);
        formData.append("selected_nav", targetNav);
        formData.append("action", "partial_content");

        const resp = await fetch("/", {method:"POST", body:formData});
        const html = await resp.text();
        wrap.innerHTML = html;

        // 更新浏览器url历史
        const params = new URLSearchParams(window.location.search);
        params.set("data_dir", fp.data_dir);
        params.set("case_id", fp.case_id);
        params.set("check_mode", fp.check_mode);
        params.set("selected_nav", targetNav);
        const newUrl = window.location.pathname + "?" + params.toString();
        history.replaceState(null, "", newUrl);

        // 更新左侧按钮active状态
        document.querySelectorAll(".nav-item-btn").forEach(btn=>{
            const onclickText = btn.getAttribute("onclick");
            const m = onclickText.match(/'([^']+)'/);
            const tid = m ? m[1] : "";
            if(tid === targetNav){
                btn.classList.add("active-bg");
            }else{
                btn.classList.remove("active-bg");
            }
        })
    }catch(err){
        console.error(err);
        alert("load content failed:"+err);
    }finally{
        const mask = document.getElementById("loadingMask");
        if(mask) mask.remove();
    }
}

function collectPayload(){
    const rows = document.querySelectorAll("#tableBody .data-row");
    const payload = [];
    rows.forEach(tr=>{
        let item = {};
        {% if check_mode=="relation" %}
        item.src_node_id = tr.querySelector(".col-src").innerText.trim();
        item.dst_node_id = tr.querySelector(".col-dst").innerText.trim();
        {% else %}
        item.node_id = tr.querySelector(".col-nodeid").innerText.trim();
        {% endif %}
        item.sample_type = tr.querySelector(".col-sample").innerText.trim();
        item.question = tr.querySelector(".col-question").innerText.trim();
        item.rag_rate = tr.querySelector(".col-rate").innerText.trim();
        item.evaluation_label = tr.querySelector(".col-eval").innerText.trim();
        item.human_review = tr.querySelector(".human-review-input").value;
        item.interpretation = tr.querySelector(".interpret-input").value;
        payload.push(item);
    })
    return payload;
}

let autoSaveLock = false;
async function autoSavePage(){
    if(autoSaveLock) return;
    const payload = collectPayload();
    const fp = getFormParams();
    autoSaveLock = true;
    try{
        const formData = new FormData();
        formData.append("data_dir", fp.data_dir);
        formData.append("case_id", fp.case_id);
        formData.append("check_mode", fp.check_mode);
        formData.append("action", "cache");
        formData.append("row_payload", JSON.stringify(payload));
        formData.append("selected_nav", document.getElementById("selNavInput").value);

        await fetch("/", {method:"POST", body: formData});
    }catch(err){
        console.error("auto save failed", err);
        alert("自动保存失败："+err);
    }finally{
        autoSaveLock = false;
    }
}

function doReset(){
    document.getElementById("actionInput").value="reset";
    document.getElementById("mainForm").submit();
}

function doExport(){
    document.getElementById("actionInput").value="export";
    document.getElementById("mainForm").submit();
}

function safeSwitchNav(targetNav, event){
    if(event) event.preventDefault();
    const fp = getFormParams();
    const params = new URLSearchParams();
    params.set("data_dir", fp.data_dir);
    params.set("case_id", fp.case_id);
    params.set("check_mode", fp.check_mode);
    params.set("selected_nav", targetNav);
    window.location.href = "?" + params.toString();
}
</script>

</body>
</html>
"""

# 局部内容片段模板（仅右侧表格区域，ajax返回）
PARTIAL_CONTENT_TPL = """
<h5>Current key：{{selected_nav}} — {{selected_name}}</h5>
<table class="table table-bordered table-sm">
    <thead>
    <tr>
        {% if check_mode=="relation" %}
        <th>src_node_id</th>
        <th>dst_node_id</th>
        {% endif %}
        {% if check_mode=="node" %}
        <th>node_id</th>
        {% endif %}
        <th>sample_type</th>
        <th>question</th>
        <th>rag_rate</th>
        <th>evaluation_label</th>
        <th>human_review</th>
        <th>interpretation</th>
    </tr>
    </thead>
    <tbody id="tableBody">
    {% for r in rows %}
    <tr class="data-row">
        {% if check_mode=="relation" %}
        <td class="col-src">{{r.src_node_id}}</td>
        <td class="col-dst">{{r.dst_node_id}}</td>
        {% endif %}
        {% if check_mode=="node" %}
        <td class="col-nodeid">{{r.node_id}}</td>
        {% endif %}
        <td class="col-sample">{{r.sample_type}}</td>
        <td class="col-question">{{r.question}}</td>
        <td class="col-rate">{{r.rag_rate}}</td>
        <td class="col-eval">{{r.evaluation_label}}</td>
        <td>
            <textarea class="human-review-input" rows="1" onblur="autoSavePage()">{{ (r.human_review or "") }}</textarea>
        </td>
        <td>
            <textarea class="interpret-input" rows="1" onblur="autoSavePage()">{{ (r.interpretation or "") }}</textarea>
        </td>
    </tr>
    {% endfor %}
    </tbody>
</table>
"""


def load_node_info(data_dir: str, case_id: str):
    """读取 nodes.csv，返回 node_map(id->name) 和 node_category(id->category)"""
    node_file = Path(data_dir) / f"{case_id}_nodes.csv"
    if not node_file.exists():
        return None, None, f"File not found {node_file}"
    df = pd.read_csv(node_file)
    node_map = dict(zip(df["node_id"], df["node_name"]))
    if "category" in df.columns:
        node_category = dict(zip(df["node_id"], df["category"].fillna("default")))
    else:
        node_category = {nid: "default" for nid in df["node_id"]}
    return node_map, node_category, "ok"


def get_cache_key(data_dir, case_id, mode):
    return f"{data_dir}||{case_id}||{mode}"


def build_nav_tree(df, node_map, node_category, check_mode):
    nav_tree = []
    rel_tree = []
    valid_ids = []
    if check_mode == "node":
        node_ids = sorted(df["node_id"].unique().tolist())
        cat_map = {}
        for nid in node_ids:
            cat = node_category.get(nid, "default")
            name = node_map.get(nid, str(nid))
            if cat not in cat_map:
                cat_map[cat] = []
            cat_map[cat].append({"id": str(nid), "name": name})
        for cat in sorted(cat_map.keys()):
            nodes = cat_map[cat]
            nav_tree.append({
                "category": cat,
                "nodes": nodes,
                "has_selected": False
            })
        valid_ids = [n["id"] for cat in nav_tree for n in cat["nodes"]]
    else:
        df_edge_unique = df[["src_node_id","dst_node_id","relation_type"]].drop_duplicates(subset=["src_node_id","dst_node_id"]).copy()
        reltype_map = {}
        for _, row in df_edge_unique.iterrows():
            sid = row["src_node_id"]
            did = row["dst_node_id"]
            key = f"{sid}||{did}"
            s_name = node_map.get(sid, str(sid))
            d_name = node_map.get(did, str(did))
            disp_name = f"{s_name} --> {d_name}"
            if "relation_type" in df_edge_unique.columns:
                rt = row.get("relation_type", "default")
                if pd.isna(rt):
                    rt = "default"
            else:
                rt = "default"
            item = {"id": key, "name": disp_name}
            if rt not in reltype_map:
                reltype_map[rt] = []
            reltype_map[rt].append(item)
        for rt in sorted(reltype_map.keys()):
            edges = reltype_map[rt]
            rel_tree.append({
                "rel_type": rt,
                "edges": edges,
                "has_selected": False
            })
        valid_ids = [e["id"] for rt in rel_tree for e in rt["edges"]]
    return nav_tree, rel_tree, valid_ids


@app.route("/", methods=["GET", "POST"])
def index():
    q_data_dir = request.args.get("data_dir")
    q_case_id = request.args.get("case_id")
    q_check_mode = request.args.get("check_mode")
    get_selected_nav = request.args.get("selected_nav", "")

    f_data_dir = request.form.get("data_dir", "../../data/graph/case_study/case_4_v_kg/")
    f_case_id = request.form.get("case_id", "c001")
    f_check_mode = request.form.get("check_mode", "node")
    action = request.form.get("action", "")
    payload_json = request.form.get("row_payload", "")
    post_selected_nav = request.form.get("selected_nav", "")

    # ==========【修复BUG】POST表单提交时，form优先级高于url query ==========
    if request.method == "POST":
        # POST：以表单输入为准，忽略url上旧query参数
        data_dir = f_data_dir
        case_id = f_case_id
        check_mode = f_check_mode
        if action == "partial_content":
            get_selected_nav = post_selected_nav
    else:
        # GET请求才使用url query参数
        data_dir = q_data_dir if q_data_dir else f_data_dir
        case_id = q_case_id if q_case_id else f_case_id
        check_mode = q_check_mode if q_check_mode else f_check_mode

    ckey = get_cache_key(data_dir, case_id, check_mode)

    # reset缓存
    if action == "reset":
        if ckey in in_memory_cache:
            del in_memory_cache[ckey]
        flash("✅Cache reset, reload original file")
        # reset之后跳转不带selected_nav，新case从头开始
        return redirect(url_for("index", data_dir=data_dir, case_id=case_id, check_mode=check_mode))

    # 导出：写入本地data_dir目录
    if action == "export":
        if ckey not in in_memory_cache:
            flash("❌No cached data, please load data first")
            return redirect(url_for("index", data_dir=data_dir, case_id=case_id, check_mode=check_mode))
        df = in_memory_cache[ckey]
        out_path = Path(data_dir) / f"{case_id}_{check_mode}_hr.csv"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_path, index=False, encoding="utf-8-sig")
        flash(f"✅Export success, saved to: {out_path.resolve()}")
        return redirect(url_for("index", data_dir=data_dir, case_id=case_id, check_mode=check_mode))

    # cache保存：ajax自动保存，直接返回ok，禁止redirect，避免整页刷新
    if action == "cache" and payload_json and ckey in in_memory_cache:
        df = in_memory_cache[ckey]
        payload = json.loads(payload_json)
        for item in payload:
            if check_mode == "node":
                cond = (df["node_id"] == item["node_id"]) & (df["sample_type"] == item["sample_type"]) & (df["question"] == item["question"])
            else:
                cond = (df["src_node_id"] == item["src_node_id"]) & (df["dst_node_id"] == item["dst_node_id"]) & (df["sample_type"] == item["sample_type"]) & (df["question"] == item["question"])
            df.loc[cond, "human_review"] = item["human_review"]
            df.loc[cond, "interpretation"] = item["interpretation"]
        in_memory_cache[ckey] = df.copy()
        return "ok"

    node_map, node_category, msg = load_node_info(data_dir, case_id)
    if node_map is None:
        if action == "partial_content":
            return "<div class='alert alert-danger'>"+msg+"</div>"
        return render_template_string(
            HTML_TEMPLATE,
            error=msg,
            data_dir=data_dir,
            case_id=case_id,
            check_mode=check_mode,
            nav_tree=[],
            rel_tree=[],
            selected_nav="",
            selected_name="",
            main_content_html=""
        )

    file_path = None
    if check_mode == "node":
        file_path = Path(data_dir) / f"{case_id}_nodes_vq_evaluation.csv"
    elif check_mode == "relation":
        file_path = Path(data_dir) / f"{case_id}_edges_vq_evaluation.csv"

    if not file_path.exists():
        err_msg = f"File not found {file_path}"
        if action == "partial_content":
            return "<div class='alert alert-danger'>"+err_msg+"</div>"
        return render_template_string(
            HTML_TEMPLATE,
            error=err_msg,
            data_dir=data_dir,
            case_id=case_id,
            check_mode=check_mode,
            nav_tree=[],
            rel_tree=[],
            selected_nav="",
            selected_name="",
            main_content_html=""
        )

    if ckey not in in_memory_cache:
        df_raw = pd.read_csv(file_path)
        if "human_review" not in df_raw.columns:
            df_raw["human_review"] = ""
        df_raw["human_review"] = df_raw["human_review"].fillna("")
        if "interpretation" not in df_raw.columns:
            df_raw["interpretation"] = ""
        df_raw["interpretation"] = df_raw["interpretation"].fillna("")
        in_memory_cache[ckey] = df_raw.copy()

    df = in_memory_cache[ckey]

    nav_tree, rel_tree, valid_ids = build_nav_tree(df, node_map, node_category, check_mode)

    # 校验selected_nav
    if get_selected_nav and get_selected_nav in valid_ids:
        selected_nav = get_selected_nav
    else:
        selected_nav = ""

    if not selected_nav:
        if check_mode == "node" and nav_tree:
            selected_nav = nav_tree[0]["nodes"][0]["id"]
        elif rel_tree:
            selected_nav = rel_tree[0]["edges"][0]["id"]

    # selected_name
    selected_name = ""
    if selected_nav:
        if check_mode == "node":
            for cat in nav_tree:
                for n in cat["nodes"]:
                    if n["id"] == selected_nav:
                        selected_name = n["name"]
                        break
        else:
            for rt in rel_tree:
                for e in rt["edges"]:
                    if e["id"] == selected_nav:
                        selected_name = e["name"]
                        break

    # 筛选表格数据
    df_show = pd.DataFrame()
    if selected_nav:
        if check_mode == "node":
            df_show = df[df["node_id"] == selected_nav].copy()
        else:
            src_sel, dst_sel = selected_nav.split("||")
            df_show = df[(df["src_node_id"] == src_sel) & (df["dst_node_id"] == dst_sel)].copy()
    rows = df_show.to_dict("records")

    # 局部ajax请求，只返回表格片段
    if action == "partial_content":
        return render_template_string(PARTIAL_CONTENT_TPL,
            check_mode=check_mode,
            selected_nav=selected_nav,
            selected_name=selected_name,
            rows=rows
        )

    # 主页面渲染，标记当前选中项用于渲染active按钮
    for cat in nav_tree:
        cat["has_selected"] = any(n["id"] == selected_nav for n in cat["nodes"])
    for rt in rel_tree:
        rt["has_selected"] = any(e["id"] == selected_nav for e in rt["edges"])

    main_content_html = render_template_string(PARTIAL_CONTENT_TPL,
        check_mode=check_mode,
        selected_nav=selected_nav,
        selected_name=selected_name,
        rows=rows
    )

    return render_template_string(
        HTML_TEMPLATE,
        error=None,
        data_dir=data_dir,
        case_id=case_id,
        check_mode=check_mode,
        nav_tree=nav_tree,
        rel_tree=rel_tree,
        selected_nav=selected_nav,
        selected_name=selected_name,
        main_content_html=main_content_html
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5003)
