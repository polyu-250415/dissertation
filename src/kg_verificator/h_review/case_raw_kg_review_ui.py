import tkinter as tk
from tkinter import ttk
import sys
from io import StringIO

from src.kg_verificator.v_case_kg.s0_evaluate_raw_kg import measure_kg_by_indicator
from src.utils.graph_tools.create_paper_graph_by_id import create_kg_by_case


class PrintCapture:
    """捕获函数print输出"""
    def __enter__(self):
        self._stdout = sys.stdout
        self._buffer = StringIO()
        sys.stdout = self._buffer
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self._stdout
        self.output = self._buffer.getvalue()


def run_logic(case_id: str, step: int, model: str):
    print(f"===== 开始执行 case_id={case_id}, step={step}, model={model} =====")
    if step == 1:
        measure_kg_by_indicator(case_id, model=model)

    elif step == 2:
        path_dir = "../../data/graph/case_study/case_1_raw_kg_m/"
        # 执行生成图谱
        create_kg_by_case(case_id, path_dir=path_dir, mid_seg=f"_{model}")
        print(f"[step2] 知识图谱已生成，准备打开图谱页面")

    elif step == 3:
        path_dir = "../../data/graph/case_study/case_6_v_ds/"
        create_kg_by_case(case_id,path_dir=path_dir)
    else:
        print(f"错误：不支持的step={step}，仅支持1/2/3")


def on_submit():
    case_id = entry_case.get().strip()
    step_str = entry_step.get().strip()
    model_name = combo_model.get().strip()

    text_output.delete(1.0, tk.END)

    if not all([case_id, step_str, model_name]):
        text_output.insert(tk.END, "错误：case id / step / model 不能为空！\n")
        return
    try:
        step_val = int(step_str)
    except ValueError:
        text_output.insert(tk.END, "错误：step必须是数字(1/2/3)\n")
        return

    try:
        with PrintCapture() as cap:
            run_logic(case_id, step_val, model_name)
        captured_text = cap.output
    except Exception as e:
        captured_text = f"执行异常：{str(e)}\n"

    print("\n====捕获函数print输出====")
    print(captured_text)
    print("==========================\n")
    text_output.insert(tk.END, captured_text)


def copy_output():
    content = text_output.get(1.0, tk.END).strip()
    if not content:
        return
    root.clipboard_clear()
    root.clipboard_append(content)


def start_gui():
    global root, entry_case, entry_step, combo_model, text_output
    root = tk.Tk()
    root.title("Evaluating Case-Level Knowledge Graphs")

    # 全屏，ESC退出全屏
    root.attributes("-fullscreen", True)
    root.bind("<Escape>", lambda e: root.attributes("-fullscreen", False))
    # 想要窗口最大化（带标题栏）注释上面，打开下面
    # root.state("zoomed")

    root.grid_rowconfigure(5, weight=1)
    root.grid_columnconfigure(1, weight=1)

    row_idx = 0
    ttk.Label(root, text="case id:").grid(row=row_idx, column=0, sticky="w", padx=20, pady=8)
    entry_case = ttk.Entry(root)
    entry_case.grid(row=row_idx, column=1, sticky="ew", padx=20, pady=8)
    row_idx += 1

    ttk.Label(root, text="task:").grid(row=row_idx, column=0, sticky="w", padx=20, pady=8)
    entry_step = ttk.Entry(root)
    entry_step.grid(row=row_idx, column=1, sticky="ew", padx=20, pady=8)
    row_idx += 1

    ttk.Label(root, text="model name:").grid(row=row_idx, column=0, sticky="w", padx=20, pady=8)
    combo_model = ttk.Combobox(root, values=["deepseek", "chatgpt"], state="readonly")
    combo_model.current(0)
    combo_model.grid(row=row_idx, column=1, sticky="ew", padx=20, pady=8)
    row_idx += 1

    btn_frame = ttk.Frame(root)
    btn_frame.grid(row=row_idx, column=0, columnspan=2, pady=10)
    submit_btn = ttk.Button(btn_frame, text="Execute", command=on_submit)
    submit_btn.pack(side="left", padx=15)
    copy_btn = ttk.Button(btn_frame, text="Copy", command=copy_output)
    copy_btn.pack(side="left", padx=15)
    row_idx += 1

    ttk.Label(root, text="Output：").grid(row=row_idx, column=0, columnspan=2, sticky="w", padx=20)
    row_idx += 1

    text_output = tk.Text(root)
    text_output.grid(row=row_idx, column=0, columnspan=2, sticky="nsew", padx=20, pady=10)

    root.mainloop()


if __name__ == "__main__":
    start_gui()
