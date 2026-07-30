# 神经记忆场模拟器

<small>V5.4 · 弹性空间版</small>

一个用于探索 AI 记忆检索机制的交互式模拟器。

> 🌐 **Non-Chinese Users**: The simulator UI is in Chinese. If you need an English version, you can paste the HTML file into any AI tool (ChatGPT, Claude, Gemini, etc.) and ask it to translate all Chinese text to English.

---

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

## 实验结论 | Findings

通过本模拟器，我们发现 | Key findings from this simulator:

- 固定空间下，节点超过 800 后性能急剧下降 | With fixed space, performance drops sharply beyond 800 nodes
- 弹性空间使 2000 节点成功率从 13.3% 提升到 66.7% | Elastic space improves 2000-node success rate from 13.3% to 66.7%
- 节点密度恒定比节点数量更重要 | Constant node density matters more than node count

## 许可证 | License

MIT License
