import subprocess
import sys
import os
import json
import csv

# 手动配置需要运行的版本（修改为新文件夹名称）
RUN_VERSIONS = ["server", "server_optimized"]  # 确保包含两个版本
OUTPUT_CSV = "performance_comparison.csv"  # 输出的CSV文件名

# 定义负载梯度的顺序
LOAD_GRADIENT_ORDER = ["轻度负载", "中度负载", "重度负载"]


def extract_performance_data(output, version):
    """从测试输出中提取性能数据，增加版本参数用于错误提示"""
    start_marker = "===== PERFORMANCE_DATA_START ====="
    end_marker = "===== PERFORMANCE_DATA_END ====="

    start_idx = output.find(start_marker)
    end_idx = output.find(end_marker)

    if start_idx == -1:
        print(f"错误：{version} 版本输出中未找到开始标记 '{start_marker}'")
        return None
    if end_idx == -1:
        print(f"错误：{version} 版本输出中未找到结束标记 '{end_marker}'")
        return None
    if start_idx >= end_idx:
        print(f"错误：{version} 版本中开始标记在结束标记之后")
        return None

    data_str = output[start_idx + len(start_marker):end_idx].strip()
    try:
        return json.loads(data_str)
    except json.JSONDecodeError as e:
        print(f"错误：{version} 版本性能数据解析失败 - {str(e)}")
        print(f"待解析数据: {data_str}")  # 输出原始数据便于调试
        return None


def run_test(version):
    """调用指定版本文件夹下的test.py，实时显示输出并返回性能数据"""
    valid_versions = ["server", "server_optimized"]
    if version not in valid_versions:
        print(f"错误：无效版本 '{version}'，请检查配置")
        return None

    # 构造test.py的路径并验证
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_script_path = os.path.join(current_dir, "..", version, "test.py")
    test_script_path = os.path.normpath(test_script_path)

    # 提前检查文件是否存在
    if not os.path.exists(test_script_path):
        print(f"错误：{version} 版本的测试脚本不存在 - {test_script_path}")
        return None

    try:
        print(f"\n===== 开始运行 {version} 版本的测试 =====")
        # 启动进程，实时捕获并打印输出（同时记录完整输出用于解析）
        process = subprocess.Popen(
            [sys.executable, test_script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            bufsize=1  # 行缓冲，确保实时输出
        )

        # 实时读取并打印stdout，同时累积完整输出
        full_stdout = []
        print(f"\n{version} 版本实时输出：")
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break  # 进程结束且无更多输出
            if line:
                print(line, end="")  # 实时打印当前行（end=""避免重复换行）
                full_stdout.append(line)  # 累积输出用于后续解析

        # 检查进程是否正常结束
        return_code = process.wait()
        if return_code != 0:
            # 读取并打印错误信息
            stderr = process.stderr.read()
            print(f"\n{version} 版本测试执行失败，返回码：{return_code}")
            print(f"错误输出：{stderr}")
            return None

        # 拼接完整输出字符串
        full_stdout_str = ''.join(full_stdout)
        print(f"\n===== {version} 版本测试完成 =====")

        # 提取并返回性能数据
        return extract_performance_data(full_stdout_str, version)

    except Exception as e:
        print(f"\n{version} 版本测试发生未知错误：{str(e)}")
        return None


def save_comparison_to_csv(performance_data):
    """将性能对比数据保存到CSV文件（保留中文）"""
    # 获取所有梯度名称并按指定顺序排序
    gradient_names = []
    all_gradients = set()
    for data in performance_data.values():
        all_gradients.update(data.keys())

    # 按预设的负载顺序添加梯度，确保顺序正确
    for gradient in LOAD_GRADIENT_ORDER:
        if gradient in all_gradients:
            gradient_names.append(gradient)
            all_gradients.remove(gradient)

    # 添加任何剩余的梯度（如果有的话）
    gradient_names.extend(sorted(all_gradients))

    # 准备CSV头部（保留中文）
    headers = ["梯度名称", "版本"]
    metrics = ["座位利用率(%)", "所有请求平均响应时间(ms)", "所有请求最长响应时间(ms)",
               "成功请求平均响应时间(ms)", "成功请求最长响应时间(ms)",
               "总测试时间(ms)", "吞吐量(请求/秒)"]
    headers.extend(metrics)

    # 写入CSV文件
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)

        # 写入每个梯度的各版本数据，不添加空行避免重复
        for grad_name in gradient_names:
            for version, data in performance_data.items():
                if grad_name not in data:
                    print(f"警告：{version} 版本中未找到梯度 '{grad_name}' 的数据，跳过")
                    continue
                row = [
                    grad_name,
                    version,
                    f"{data[grad_name]['seat_utilization']:.2f}",
                    f"{data[grad_name]['all_requests_avg']:.2f}",
                    f"{data[grad_name]['all_requests_max']:.2f}",
                    f"{data[grad_name]['success_requests_avg']:.2f}",
                    f"{data[grad_name]['success_requests_max']:.2f}",
                    f"{data[grad_name]['total_test_time']:.2f}",
                    f"{data[grad_name]['throughput']:.2f}"
                ]
                writer.writerow(row)

    print(f"\n性能对比结果已保存到 {OUTPUT_CSV}")


if __name__ == "__main__":
    all_performance_data = {}

    # 顺序运行每个版本（一个完成后再运行下一个）
    for version in RUN_VERSIONS:
        print(f"准备运行 {version} 版本测试...")
        data = run_test(version)
        if data:
            all_performance_data[version] = data
        else:
            print(f"{version} 版本未产生有效性能数据，将不纳入对比")

    if all_performance_data:
        save_comparison_to_csv(all_performance_data)
    else:
        print("\n警告：未收集到任何有效性能数据，不生成CSV文件")

    print("\n===== 所有指定版本测试结束 =====")