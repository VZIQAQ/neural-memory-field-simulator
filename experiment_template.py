#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
通用试验模板 · 神经记忆场模拟器

【使用说明】
1. 复制这个文件，重命名为你的实验名称
2. 修改「===== 用户修改区域 =====」下面的配置
3. 运行脚本，自动生成 CSV + 图表 + 报告

【模板版本】
V1.0 - 2026-07-30
"""

import asyncio
import csv
import os
import re
from pathlib import Path
from collections import defaultdict

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np

from playwright.async_api import async_playwright

# ================================================================
# 设置中文字体（绘图用）
# ================================================================

# Windows 系统字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# Mac 系统字体（如使用 Mac，取消下面两行注释，注释掉上面两行）
# plt.rcParams['font.sans-serif'] = ['PingFang SC', 'Heiti SC', 'STHeiti']
# plt.rcParams['axes.unicode_minus'] = False

# ================================================================
# ===== 用户修改区域 =====
# ================================================================

# -------- 1. 文件路径 --------
HTML_PATH = r"C:\Users\84426\Desktop\模拟器\记忆模拟器V5.4-弹性空间.html"
OUTPUT_DIR = r"C:\Users\84426\Desktop\模拟器\LAB"
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "exp_my_results.csv")
OUTPUT_PLOT = os.path.join(OUTPUT_DIR, "exp_my_plot.png")
OUTPUT_REPORT = os.path.join(OUTPUT_DIR, "exp_my_report.txt")

# -------- 2. 实验规模 --------
TOTAL_ROUNDS = 10          # 每个配置跑多少轮
COMPACT_INTERVAL = 5       # 每多少轮新增一个节点（模拟整理）
REPEATS = 3                # 每个配置重复次数
MAX_CONCURRENT = 4         # 并发数（根据电脑性能调 2-8）

# -------- 3. 实验矩阵 --------
# 格式：(节点量级, 实验名称, 额外参数)
# 额外参数会覆盖基线配置
EXPERIMENTS = [
    # 例子：测试不同节点量级
    (500, "baseline_500", {}),
    (800, "baseline_800", {}),
    (1200, "baseline_1200", {}),
    (2000, "baseline_2000", {}),
    
    # 例子：测试不同参数
    # (500, "sigma_0.40", {"#param-sigma": "0.40"}),
    # (500, "sigma_0.60", {"#param-sigma": "0.60"}),
]

# -------- 4. 基线参数 --------
# 所有实验共用的默认参数
BASELINE_CONFIG = {
    "#param-topic-radius": "0.15",
    "#param-steps": "5",
    "#param-alpha": "0.15",
    "#param-depth": "12",
    "#param-decay": "0.75",
    "#param-t1-question": "0.60",
    "#param-t1-certain": "0.75",
    "#param-spr": "0.50",
    "#param-cluster-prob": "0.70",
    "#param-hebbian-eta": "0.010",
    "#param-hebbian-min": "0.15",
    "#param-temporal-weight": "0.40",
    "#param-bridge": "2",
    "#param-same-window": "3",
    "#param-sigma": "0.25",
    "#param-thresh": "0.15",
    "#param-cluster-count": "10",
    "#param-cluster-skew": "5",
    "#param-base-nodes": "500",
    "#param-auto-scale": "on",      # 弹性空间默认开启
}

# ================================================================
# ===== 固定框架（以下内容一般不需要修改） =====
# ================================================================

def classify_result(state: str, recall_tokens: int) -> str:
    """将状态和回忆Token分类为测试结果"""
    if state == "确定" and recall_tokens > 0:
        return "success"
    elif state == "确定" and recall_tokens == 0:
        return "success_no_recall"
    elif state == "追问":
        return "question"
    elif state == "模糊" and recall_tokens > 0:
        return "weak_recall"
    elif state == "模糊" and recall_tokens == 0:
        return "miss"
    else:
        return "unknown"

async def apply_config(page, baseline: dict, extra_params: dict):
    """应用参数配置：先基线，再覆盖实验参数"""
    merged = {**baseline, **extra_params}
    
    for pid, val in merged.items():
        if pid == "#param-nodes":
            continue
        try:
            await page.evaluate(
                """(args) => {
                    const el = document.querySelector(args.selector);
                    if (el) {
                        if (el.type === 'checkbox') {
                            el.checked = args.value === 'on' || args.value === true;
                            el.dispatchEvent(new Event('change', { bubbles: true }));
                        } else {
                            el.value = args.value;
                            el.dispatchEvent(new Event('input', { bubbles: true }));
                            el.dispatchEvent(new Event('change', { bubbles: true }));
                        }
                    }
                }""",
                {"selector": pid, "value": str(val)}
            )
            await page.wait_for_timeout(50)
        except Exception as e:
            print(f"  ⚠️ 设置 {pid}={val} 失败: {e}")

async def run_single_experiment(
    browser,
    total_nodes: int,
    exp_name: str,
    extra_params: dict,
    repeat: int,
    all_results: list,
    lock: asyncio.Lock,
    semaphore: asyncio.Semaphore
):
    """在一个独立页面中跑完一个完整实验"""
    async with semaphore:
        print(f"▶ 启动: {exp_name} | {total_nodes}节点 | 重复{repeat}")

        page = await browser.new_page(viewport={"width": 1400, "height": 900})

        try:
            html_path = Path(HTML_PATH).absolute().as_uri()
            await page.goto(html_path)
            await page.wait_for_selector("#btn-new", timeout=5000)

            # 重置
            await page.click("#btn-reset")
            await page.wait_for_timeout(80)

            # 应用参数
            await apply_config(page, BASELINE_CONFIG, extra_params)
            await page.wait_for_timeout(80)

            # 设置节点数
            await page.evaluate(
                """(args) => {
                    const el = document.querySelector('#param-nodes');
                    if (el) {
                        el.value = args.value;
                        el.dispatchEvent(new Event('input', { bubbles: true }));
                        el.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                }""",
                {"value": str(total_nodes)}
            )
            await page.wait_for_timeout(80)

            # 生成簇分布
            await page.click("#btn-gen-clusters")
            await page.wait_for_timeout(200)

            # 新建对话
            await page.click("#btn-new")
            await page.wait_for_timeout(150)

            for round_num in range(1, TOTAL_ROUNDS + 1):
                if round_num % COMPACT_INTERVAL == 0:
                    await page.click("#btn-add-node")
                    await page.wait_for_timeout(80)

                await page.click("#btn-user")
                await page.wait_for_timeout(120)

                # 读取指标
                t1 = await page.text_content("#m-t1")
                spr = await page.text_content("#m-spr")
                peaks = await page.text_content("#m-peaks")
                state = await page.text_content("#m-state")
                awake = await page.text_content("#m-awake")
                window_tokens = await page.text_content("#m-window")
                recall_tokens = await page.text_content("#m-tokens")
                total_tokens = await page.text_content("#m-total")
                layer_info = await page.text_content("#layer-info")
                scale_display = await page.text_content("#m-scale")

                try:
                    window_part = layer_info.split("|")[1].strip()
                    current_window = int(window_part.split(":")[1].strip())
                except:
                    current_window = 0

                recall_val = int(recall_tokens.replace(",", "")) if recall_tokens != "—" else 0
                state_val = state.strip() if state else "—"
                test_result = classify_result(state_val, recall_val)
                scale_val = float(scale_display) if scale_display != "—" else 1.0

                record = {
                    "exp_name": exp_name,
                    "total_nodes": total_nodes,
                    "repeat": repeat,
                    "round": round_num,
                    "t1": float(t1) if t1 != "—" else None,
                    "spr": float(spr) if spr != "—" else None,
                    "peaks": int(peaks) if peaks != "—" else None,
                    "state": state_val,
                    "awake_nodes": int(awake) if awake != "—" else None,
                    "windowTokens": int(window_tokens.replace(",", "")) if window_tokens != "—" else 0,
                    "recallTokens": recall_val,
                    "totalTokens": int(total_tokens.replace(",", "")) if total_tokens != "—" else 0,
                    "current_window": current_window,
                    "scale": scale_val,
                    "test_result": test_result
                }

                async with lock:
                    all_results.append(record)
                    print(f"  [{exp_name}/R{repeat}] 轮次{round_num:2d}: {state_val:4} | T1={t1:>5} | 回忆={recall_val:>6}")

        except Exception as e:
            async with lock:
                print(f"❌ 实验失败: {exp_name} | 错误: {e}")
        finally:
            await page.close()
            async with lock:
                print(f"✅ 完成: {exp_name}")

# ================================================================
# 主程序
# ================================================================

async def run_experiment():
    all_results = []
    lock = asyncio.Lock()
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        tasks = []
        for total_nodes, exp_name, extra_params in EXPERIMENTS:
            for repeat in range(1, REPEATS + 1):
                tasks.append(
                    run_single_experiment(
                        browser, total_nodes, exp_name, extra_params, repeat,
                        all_results, lock, semaphore
                    )
                )

        total_tasks = len(tasks)
        print("\n" + "=" * 70)
        print(f"📊 实验配置: {len(EXPERIMENTS)} 组 × {REPEATS} 次重复 × {TOTAL_ROUNDS} 轮 = {total_tasks} 个任务")
        print("=" * 70 + "\n")

        await asyncio.gather(*tasks)
        await browser.close()

    # 保存 CSV
    fieldnames = [
        'exp_name', 'total_nodes', 'repeat', 'round',
        't1', 'spr', 'peaks', 'state', 'awake_nodes',
        'windowTokens', 'recallTokens', 'totalTokens',
        'current_window', 'scale', 'test_result'
    ]

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_results)

    print(f"\n✅ 原始数据已保存至 {OUTPUT_CSV}")

    # ================================================================
    # 数据分析
    # ================================================================

    # 按实验聚合
    summary = {}
    for exp_name in set(r['exp_name'] for r in all_results):
        sub = [r for r in all_results if r['exp_name'] == exp_name]
        total = len(sub)
        success = len([r for r in sub if r['test_result'] == 'success'])
        question = len([r for r in sub if r['test_result'] == 'question'])
        weak = len([r for r in sub if r['test_result'] == 'weak_recall'])
        miss = len([r for r in sub if r['test_result'] == 'miss'])

        valid_t1 = [r['t1'] for r in sub if r['t1'] is not None]
        avg_t1 = sum(valid_t1) / len(valid_t1) if valid_t1 else 0
        avg_recall = sum(r['recallTokens'] for r in sub) / total

        summary[exp_name] = {
            'total_nodes': sub[0]['total_nodes'],
            'total': total,
            'success_rate': success / total,
            'question_rate': question / total,
            'weak_rate': weak / total,
            'miss_rate': miss / total,
            'avg_t1': avg_t1,
            'avg_recall': avg_recall
        }

    # ---- 打印结果 ----
    print("\n" + "=" * 70)
    print("📊 各实验配置表现")
    print("=" * 70)
    print(f"{'实验名称':<20} {'节点':<6} {'成功率':<10} {'追问率':<10} {'T1均值':<10}")
    print("-" * 70)

    for exp_name in sorted(summary.keys()):
        s = summary[exp_name]
        print(f"{exp_name:<20} {s['total_nodes']:<6} "
              f"{s['success_rate']*100:>6.1f}%     {s['question_rate']*100:>6.1f}%     "
              f"{s['avg_t1']:>8.4f}")

    print("-" * 70)

    # ---- 生成图表 ----
    print("\n📊 生成图表...")

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # 子图1：成功率
    ax1 = axes[0]
    exp_names = [e for e in summary.keys()]
    nodes_list = [summary[e]['total_nodes'] for e in exp_names]
    success_rates = [summary[e]['success_rate'] * 100 for e in exp_names]

    bars1 = ax1.bar(range(len(exp_names)), success_rates, color='#2d7aff', alpha=0.7)
    ax1.set_xticks(range(len(exp_names)))
    ax1.set_xticklabels(exp_names, rotation=45, ha='right', fontsize=9)
    ax1.set_ylabel('成功率 (%)')
    ax1.set_title('各实验配置成功率')
    ax1.grid(True, alpha=0.3)

    # 子图2：T1 均值
    ax2 = axes[1]
    t1_values = [summary[e]['avg_t1'] for e in exp_names]

    bars2 = ax2.bar(range(len(exp_names)), t1_values, color='#f0883e', alpha=0.7)
    ax2.axhline(y=0.75, color='#3fb950', linestyle='--', label='确定阈值')
    ax2.axhline(y=0.60, color='#e5484d', linestyle='--', label='追问阈值')
    ax2.set_xticks(range(len(exp_names)))
    ax2.set_xticklabels(exp_names, rotation=45, ha='right', fontsize=9)
    ax2.set_ylabel('T1 均值')
    ax2.set_title('各实验配置 T1 均值')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(OUTPUT_PLOT, dpi=150, bbox_inches='tight')
    print(f"✅ 图表已保存至 {OUTPUT_PLOT}")

    # ---- 生成报告 ----
    with open(OUTPUT_REPORT, "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("实验报告\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"实验时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("【各配置表现】\n")
        f.write("-" * 40 + "\n")
        f.write(f"{'实验名称':<20} {'成功率':<10} {'追问率':<10} {'T1均值':<10}\n")
        for exp_name in sorted(summary.keys()):
            s = summary[exp_name]
            f.write(f"{exp_name:<20} {s['success_rate']*100:>6.1f}%     {s['question_rate']*100:>6.1f}%     {s['avg_t1']:>8.4f}\n")

        # 找出最佳配置
        best = max(summary.keys(), key=lambda x: summary[x]['success_rate'])
        f.write(f"\n【最佳配置】{best}: 成功率 {summary[best]['success_rate']*100:.1f}%\n")

    print(f"✅ 报告已保存至 {OUTPUT_REPORT}")

    print("\n" + "=" * 70)
    print("✅ 全部完成！")
    print("=" * 70)
    print(f"📁 CSV数据: {OUTPUT_CSV}")
    print(f"📊 图表: {OUTPUT_PLOT}")
    print(f"📄 报告: {OUTPUT_REPORT}")

# ================================================================
# 运行入口
# ================================================================

if __name__ == "__main__":
    asyncio.run(run_experiment())