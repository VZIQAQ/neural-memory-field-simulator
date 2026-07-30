# 神经记忆场模拟器

<small>V5.4 · 弹性空间版</small>

一个用于探索 AI 记忆检索机制的交互式模拟器。

> 🌐 **Non-Chinese Users**: The simulator UI is in Chinese. If you need an English version, you can paste the HTML file into any AI tool (ChatGPT, Claude, Gemini, etc.) and ask it to translate all Chinese text to English.


---

## 界面预览 | Screenshot

![神经记忆场模拟器界面](v2-7ba83d65557235358c32a0be1c593a7d_720w.png)

## 这是什么 | What is this

这是一个在浏览器中运行的记忆场模拟器。它将对话记忆建模为图结构，通过热核扩散和链路传播来模拟记忆的激活与检索。主要用来研究：

- 记忆节点密度对检索性能的影响
- 「确定」与「追问」状态的切换机制
- 弹性空间如何解决大规模记忆检索的性能问题

A browser-based memory field simulator that models conversational memory as a graph structure, simulating memory activation and retrieval via heat kernel diffusion and link propagation. Main research areas:

- Impact of memory node density on retrieval performance
- Switching mechanism between "certain" and "question" states
- How elastic space solves large-scale memory retrieval performance issues

## 核心机制 | Core Mechanisms

- **热核扩散 | Heat Kernel Diffusion** — 查询作为热源，在记忆图上扩散能量，激活相关记忆。Query acts as a heat source, diffusing energy across the memory graph to activate relevant memories.
- **链路传播 | Link Propagation** — 从主峰出发沿突触连接传播，唤醒关联记忆。Propagates from the main peak along synaptic connections to awaken associated memories.
- **窗口隔离 | Window Isolation** — 当前对话窗口节点不参与检索（已在上下文中）。Current conversation window nodes are excluded from retrieval (already in context).
- **弹性空间 | Elastic Space** — 节点数量增加时，语义空间自动扩展，保持密度恒定。Semantic space automatically expands as node count increases, maintaining constant density.
- **Hebbian 塑形 | Hebbian Plasticity** — 共激活的节点之间边权重自动增强。Edge weights between co-activated nodes are automatically strengthened.

## 如何使用 | How to Use

直接用浏览器打开 `记忆模拟器V5.4-弹性空间.html` 即可运行。

Simply open `记忆模拟器V5.4-弹性空间.html` in a browser.

1. 点击「新建对话」初始化记忆场 | Click "New Dialog" to initialize the memory field
2. 点击「用户输入」模拟一轮对话 | Click "User Input" to simulate a conversation round
3. 观察右侧面板的 T1 值、状态（确定/模糊/追问）、Token 消耗 | Observe T1 value, state (certain/fuzzy/question), and token consumption in the right panel
4. 调节左侧参数观察系统行为变化 | Adjust left-side parameters to observe behavior changes

## 核心参数说明 | Key Parameters

| 参数 | Parameter | 作用 | Description |
|------|-----------|------|-------------|
| 温层节点总数 | Total Nodes | 记忆场中的节点数量 | Number of nodes in the memory field |
| 弹性空间 | Elastic Space | 自动根据节点数扩展空间，保持密度恒定 | Auto-expands space based on node count, maintaining constant density |
| 热核步数 | Diffusion Steps | 信号在图上传播的跳数 | Number of hops the signal propagates across the graph |
| 链路深度 | Link Depth | 从主峰向外传播的步数 | Steps propagated outward from the main peak |
| T1 确定阈值 | T1 Certain Threshold | >0.75 时系统进入「确定」状态 | System enters "certain" state when > 0.75 |

## 自动化实验 | Automated Testing

`experiment_template.py` 是配套的自动化试验脚本，用于批量运行实验并生成数据。

`experiment_template.py` is a companion automation script for batch experiments and data generation.

### 依赖 | Dependencies

```bash
pip install playwright matplotlib numpy
playwright install chromium
```

### 使用 | Usage

1. 复制 `experiment_template.py`，重命名为你的实验名称 | Copy and rename the script for your experiment
2. 修改脚本中「用户修改区域」的配置（实验矩阵、参数、输出路径）| Edit the "User Configuration" section (experiment matrix, parameters, output paths)
3. 运行 | Run:

```bash
python experiment_template.py
```

脚本会自动 | The script will automatically:
- 按配置批量跑实验（支持并发）| Run experiments in batch (concurrent)
- 输出 CSV 原始数据 | Output raw CSV data
- 生成对比图表（成功率、T1 均值）| Generate comparison charts (success rate, T1 average)
- 生成实验报告 | Generate experiment report

## 📊 实验数据 / Experimental Data

本仓库包含 V5.4 弹性空间实验的完整数据，位于 [`experiments/elastic_space_v54/`](experiments/elastic_space_v54/) 目录下：

| 文件 / File | 说明 / Description |
|-------------|-------------------|
| [`exp_elastic_space_v54.py`](exp_elastic_space_v54.py) | 自动化实验脚本 / Automated experiment script |
| [`exp_elastic_space_v54.csv`](experiments/elastic_space_v54/exp_elastic_space_v54.csv) | 原始实验数据（每轮检索的完整记录） / Raw experimental data |
| [`exp_elastic_space_v54_report.txt`](experiments/elastic_space_v54/exp_elastic_space_v54_report.txt) | 实验报告（汇总统计 + 关键发现） / Experiment report |
| [`exp_elastic_space_v54_plot.png`](experiments/elastic_space_v54/exp_elastic_space_v54_plot.png) | 可视化图表 / Visualization plot |

这些数据可以直接复现本文档中的所有实验结论。
All conclusions in this document are reproducible using these data.

---

## 实验结论 / Key Findings

> **弹性空间使 2000 节点成功率从 13.3% 提升到 66.7%。节点密度恒定比节点数量更重要。**

| 节点量级 / Nodes | 固定空间 / Fixed | 弹性空间 / Elastic | 提升 / Improvement |
|-----------------|------------------|-------------------|-------------------|
| 800 | 33.3% | **70.0%** | +36.7% |
| 1200 | 30.0% | **76.7%** | +46.7% |
| 2000 | 13.3% | **66.7%** | +53.3% |

固定空间下，节点超过 800 后性能急剧下降；弹性空间通过同步扩展语义空间使密度保持恒定，从根本上解决了这个问题。

> In fixed space, performance drops sharply beyond 800 nodes. Elastic space maintains constant density by scaling the semantic space, solving the problem at its root.

---

## 下一步计划 / Next Steps

- V6：可调随机种子 + 时序边遗忘机制探索
- 接入真实 LLM 的书童协议系统

## 许可证 | License

MIT License

## 贡献 | Contributing

欢迎贡献！如果你对记忆检索机制感兴趣，欢迎：

- 提交 Issue 反馈问题或建议
- Fork 项目提交 Pull Request
- 分享你的实验结果

Contributions are welcome! If you're interested in memory retrieval mechanisms:

- Open an Issue to report bugs or suggest features
- Fork the repo and submit a Pull Request
- Share your experiment results
