import os
import csv

# 获取当前脚本所在的文件夹路径
folder_path = os.getcwd()

# 遍历文件夹里所有文件
for filename in os.listdir(folder_path):
    # 只处理 .txt 文件（不区分大小写）
    if filename.lower().endswith(".txt"):
        txt_path = os.path.join(folder_path, filename)

        # 生成对应的csv文件名（替换后缀）
        csv_filename = os.path.splitext(filename)[0] + ".csv"
        csv_path = os.path.join(folder_path, csv_filename)

        print(f"正在转换：{filename} → {csv_filename}")

        # 核心：自动处理引号内的逗号，不会错位
        with open(txt_path, "r", encoding="utf-8") as txt_file, \
                open(csv_path, "w", encoding="utf-8", newline="") as csv_file:

            reader = csv.reader(txt_file, delimiter=',')  # 智能解析
            writer = csv.writer(csv_file)

            for row in reader:
                writer.writerow(row)

print("✅ 所有文件转换完成！")