from flask import Flask, render_template_string
from collections import defaultdict

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>CSV Category Navigation Manager</title>
    <style>
        * {box-sizing: border-box; margin:0; padding:0; font-family:Arial, sans-serif;}
        .top-bar {padding:12px 15px; border-bottom:1px solid #e4e7ed;}
        /* 改为一行三栏布局 */
        .top-main-row {
            display:flex;
            align-items:center;
            gap:24px;
            flex-wrap:wrap;
        }
        .top-col {
            display:flex;
            align-items:center;
            gap:8px;
            flex:1;
            min-width:260px;
        }
        #file-input, #save-path {padding:6px; min-width:220px;}
        .oper-btn {padding:6px 12px; border:none; border-radius:4px; cursor:pointer; white-space:nowrap;}
        .btn-upload {background:#409eff; color:#fff;}
        .btn-choose-dir {background:#409eff; color:#fff;}
        .btn-save-path {background:#722ed1; color:#fff;}
        .btn-reset {background:#f53f3f; color:#fff;}
        .stat-text {color:#333; font-size:14px;}
        .container {display: flex; height: calc(100vh - 130px);}
        .sidebar {width: 280px; background:#f5f7fa; border-right:1px solid #e4e7ed; overflow-y:auto; padding:10px;}
        .category-title {padding:8px 10px; font-weight:bold; font-size:14px; cursor:pointer; display:flex; justify-content:space-between; align-items:center; background:#e9ecef; border-radius:4px; margin:4px 0;}
        .sub-category-item {padding:6px 12px; cursor:pointer; margin:2px 0; border-radius:4px; font-size:13px;}
        .sub-category-item:hover {background:#dde2ff;}
        .sub-category-item.active {background:#409eff; color:#fff;}
        .sub-category-wrap {padding-left:14px; display:block;}
        .content {flex:1; padding:15px; overflow-y:auto;}
        table {width:100%; border-collapse: collapse; margin-top:10px;}
        th,td {border:1px solid #dcdfe6; padding:8px 10px; text-align:left; font-size:13px;}
        th {background:#fafafa;}
        input {width:100%; padding:6px; border:1px solid #ccc; border-radius:3px;}
        input.modified {background:#fff9cc;}
        .empty-hint {margin-top:30px; font-size:16px; color:#999;}
        .tip {font-size:13px; color:#666; margin-bottom:8px;}
    </style>
</head>
<body>
<div class="top-bar">
    <!-- 一行，三列区域：左：上传；中：导出；右：统计+重置 -->
    <div class="top-main-row">
        <!-- 区域1：CSV上传加载 -->
        <div class="top-col">
            <input type="file" id="file-input" accept=".csv" />
            <button class="oper-btn btn-upload" onclick="uploadCsv()">Load CSV File</button>
        </div>

        <!-- 区域2：缓存文件导出 -->
        <div class="top-col">
            <input id="save-path" readonly placeholder="Selected local folder path">
            <button class="oper-btn btn-choose-dir" onclick="pickLocalFolder()">Choose Directory</button>
            <button class="oper-btn btn-save-path" onclick="saveToLocalFolder()">Save To Local Folder</button>
        </div>

        <!-- 区域3：文件信息统计和重置 -->
        <div class="top-col" style="justify-content:flex-end; gap:12px;">
            <div class="stat-text">
                Total Records: <span id="total-count">0</span> &nbsp;|&nbsp; Modified Records: <span id="modified-count">0</span>
            </div>
            <button class="oper-btn btn-reset" onclick="resetAllEdit()">Reset All Edits</button>
        </div>
    </div>
</div>

<div class="container">
    <div class="sidebar" id="sidebar"></div>
    <div class="content">
        <div class="tip">Click sub-category on the left to switch data. Yellow input box means modified, edits are cached without loss</div>
        <div class="empty-hint" id="empty-tip">Please upload CSV file first to view data</div>
        <table id="data-table" style="display:none;">
            <thead>
                <tr>
                    <th>sub_category_id</th>
                    <th>sub_category</th>
                    <th>node_id</th>
                    <th>node_name</th>
                    <th>evidence_statement</th>
                    <th>adjust_sub_category_id</th>
                    <th>adjust_sub_category</th>
                </tr>
            </thead>
            <tbody id="table-body"></tbody>
        </table>
    </div>
</div>

<script>
let allNodeList = [];
let currentSelectSubId = null;
let baseFileName = "data";
let editCache = new Map();
let selectedDirectoryHandle = null;
let originalHeaders = [];

function updateStats(){
    document.getElementById("total-count").textContent = allNodeList.length;
    document.getElementById("modified-count").textContent = editCache.size;
}

async function pickLocalFolder(){
    try {
        selectedDirectoryHandle = await window.showDirectoryPicker();
        document.getElementById("save-path").value = selectedDirectoryHandle.name;
    } catch (err) {
        if (err.name !== 'AbortError') {
            alert("Your browser does not support local folder selection (Chrome/Edge only)");
        }
    }
}

function buildExportRows(){
    return allNodeList.map(node=>{
        const cache = editCache.get(node.node_id);
        return {
            sub_category_id: node.sub_category_id,
            sub_category: node.sub_category,
            node_id: node.node_id,
            node_name: node.node_name,
            evidence_statement: node.evidence_statement,
            adjust_sub_category_id: cache ? cache.adjId : node.sub_category_id,
            adjust_sub_category: cache ? cache.adjName : node.sub_category
        };
    });
}

function buildCsvText(rows){
    const headers = ["sub_category_id","sub_category","node_id","node_name","evidence_statement",
    "adjust_sub_category_id","adjust_sub_category"];
    const escape = v => `"${String(v ?? "").replace(/"/g,'""')}"`;
    let csvText = headers.join(",") + "\\n";
    rows.forEach(row=>{
        csvText += headers.map(h=>escape(row[h])).join(",") + "\\n";
    });
    return csvText;
}

async function saveToLocalFolder(){
    if (!selectedDirectoryHandle) {
        alert("Please click Choose Directory to select local folder first!");
        return;
    }
    if(allNodeList.length === 0) {
        alert("Please upload CSV data first!");
        return;
    }

    try{
        const targetFileName = baseFileName + "_expand.csv";
        const csvText = buildCsvText(buildExportRows());
        const fileBlob = new Blob([String.fromCharCode(0xFEFF), csvText], {type:"text/csv;charset=utf-8"});

        const fileHandle = await selectedDirectoryHandle.getFileHandle(targetFileName, {create:true});
        const fileStream = await fileHandle.createWritable();
        await fileStream.write(fileBlob);
        await fileStream.close();

        alert(`Successfully saved: ${targetFileName} into folder ${selectedDirectoryHandle.name}`);
    }catch(err){
        console.error("save error:", err);
        alert("Save failed: " + err.message);
    }
}


async function uploadCsv(){
    const fileDom = document.getElementById('file-input');
    const file = fileDom.files[0];
    if(!file){alert("Please select a CSV file first!");return;}
    let fullName = file.name;
    baseFileName = fullName.replace(/\\.csv$/i, "");
    const reader = new FileReader();
    reader.onload = function(e){
        const text = e.target.result;
        parseUploadCsv(text);
    };
    reader.readAsText(file, "utf-8");
}

function parseCsvRow(str) {
    const result = [];
    let current = '';
    let inQuote = false;
    for(let i = 0; i < str.length; i++){
        const c = str[i];
        if(c === '"'){
            if(inQuote && str[i+1] === '"'){
                current += '"';
                i++;
            }else{
                inQuote = !inQuote;
            }
        }else if(c === ',' && !inQuote){
            result.push(current);
            current = '';
        }else{
            current += c;
        }
    }
    result.push(current);
    return result;
}

function parseUploadCsv(text){
    if(text.charCodeAt(0) === 0xFEFF) text = text.slice(1);
    const lines = text.split(/\\r?\\n/);
    if(lines.length === 0) return;

    const headerCells = parseCsvRow(lines[0]).map(h=>h.trim());
    originalHeaders = headerCells;

    const colIndex = {};
    headerCells.forEach((h, idx)=>{
        const key = h.toLowerCase().replace(/\\s+/g,'_');
        colIndex[key] = idx;
    });

    const idxSubId   = colIndex['sub_category_id'];
    const idxSubName = colIndex['sub_category'];
    const idxNodeId  = colIndex['node_id'];
    const idxNodeName= colIndex['node_name'];
    const idxEvidenceStatement= colIndex['evidence_statement'];

    if(idxSubId === undefined || idxSubName === undefined || idxNodeId === undefined || idxNodeName === undefined || idxEvidenceStatement === undefined){
        alert("CSV must contain columns: sub_category_id, sub_category, node_id, node_name");
        return;
    }

    const list = [];
    for(let i=1; i<lines.length; i++){
        const line = lines[i];
        if(!line || !line.trim()) continue;
        const cells = parseCsvRow(line);
        const node = {
            sub_category_id:   (cells[idxSubId]   ?? "").trim(),
            sub_category:      (cells[idxSubName] ?? "").trim(),
            node_id:           (cells[idxNodeId]  ?? "").trim(),
            node_name:         (cells[idxNodeName]?? "").trim(),
            evidence_statement:         (cells[idxEvidenceStatement]?? "").trim()
        };
        list.push(node);
    }

    allNodeList = list;
    editCache.clear();
    selectedDirectoryHandle = null;
    document.getElementById("save-path").value = "";
    updateStats();
    document.getElementById("empty-tip").style.display = "none";
    document.getElementById("data-table").style.display = "table";
    renderSidebar();
}

function renderSidebar() {
    const sidebar = document.getElementById('sidebar');
    const groupMap = {};
    allNodeList.forEach(node=>{
        const key = node.sub_category_id;
        if(!groupMap[key]){
            groupMap[key] = {
                sub_category_id: node.sub_category_id,
                sub_category: node.sub_category,
                count: 0
            };
        }
        groupMap[key].count++;
    });

    const groups = Object.values(groupMap).sort((a,b)=>{
        return a.sub_category.localeCompare(b.sub_category, 'zh');
    });

    let html = `<div class="category-title"><span>All Sub‑Categories (${groups.length})</span><span class="expand-icon">▼</span></div>`;
    html += `<div class="sub-category-wrap">`;
    groups.forEach(g=>{
        html += `<div class="sub-category-item" data-sub-id="${g.sub_category_id}">${g.sub_category} <span style="color:#999;font-size:12px;">(${g.count})</span></div>`;
    });
    html += `</div>`;
    sidebar.innerHTML = html;

    document.querySelector('.category-title').onclick = function(){
        const wrap = document.querySelector('.sub-category-wrap');
        wrap.style.display = wrap.style.display === 'block' ? 'none' : 'block';
        this.querySelector('.expand-icon').textContent = wrap.style.display === 'block' ? '▼' : '▶';
    };

    document.querySelectorAll('.sub-category-item').forEach(item => {
        item.onclick = function(){
            document.querySelectorAll('.sub-category-item').forEach(i=>i.classList.remove('active'));
            this.classList.add('active');
            currentSelectSubId = this.dataset.subId;
            renderTable(currentSelectSubId);
        };
    });

    const firstSubItem = document.querySelector('.sub-category-item');
    if(firstSubItem) firstSubItem.click();
}

function renderTable(subId) {
    const tbody = document.getElementById('table-body');
    const filterNodes = allNodeList.filter(item => item.sub_category_id === subId);
    let tableHtml = '';
    filterNodes.forEach(node => {
        const cache = editCache.get(node.node_id);
        const adjIdVal = cache ? cache.adjId : node.sub_category_id;
        const adjNameVal = cache ? cache.adjName : node.sub_category;
        const isModified = cache && (cache.adjId !== node.sub_category_id || cache.adjName !== node.sub_category);

        tableHtml += `
        <tr data-node-id="${node.node_id}">
            <td>${node.sub_category_id}</td>
            <td>${node.sub_category}</td>
            <td>${node.node_id}</td>
            <td>${node.node_name}</td>
            <td>${node.evidence_statement}</td>
            <td>
                <input type="text" class="adj-id-input ${isModified?'modified':''}"
                    data-nodeid="${node.node_id}"
                    value="${adjIdVal}"
                    data-orig="${node.sub_category_id}">
            </td>
            <td>
                <input type="text" class="adj-name-input ${isModified?'modified':''}"
                    data-nodeid="${node.node_id}"
                    value="${adjNameVal}"
                    data-orig="${node.sub_category}">
            </td>
        </tr>`;
    });
    tbody.innerHTML = tableHtml;

    document.querySelectorAll('.adj-id-input, .adj-name-input').forEach(input => {
        input.oninput = function(){
            const nodeId = this.dataset.nodeid;
            const row = this.closest('tr');
            const idInput = row.querySelector('.adj-id-input');
            const nameInput = row.querySelector('.adj-name-input');
            const origId = idInput.dataset.orig;
            const origName = nameInput.dataset.orig;
            const currId = idInput.value.trim();
            const currName = nameInput.value.trim();
            editCache.set(nodeId, {adjId: currId, adjName: currName});
            const changed = currId !== origId || currName !== origName;
            idInput.classList.toggle('modified', changed);
            nameInput.classList.toggle('modified', changed);
            updateStats();
        };
    });
}

function resetAllEdit(){
    if(!confirm("Are you sure to clear all edits and restore original data?")) return;
    editCache.clear();
    updateStats();
    if(currentSelectSubId) renderTable(currentSelectSubId);
}
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    LISTEN_PORT = 8086
    LISTEN_HOST = "0.0.0.0"
    print("=== CSV Category Navigation Manager Started ===")
    print(f"Local Access URL: http://127.0.0.1:{LISTEN_PORT}")
    print(f"LAN Access URL: http://[Your Local IP]:{LISTEN_PORT}")
    app.run(host=LISTEN_HOST, port=LISTEN_PORT, debug=False)
