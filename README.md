# Tools-of-Assembly

[简体中文](README.md) | [English](README_EN.md)

**Tools-of-Assembly** 是一个面向基因组 *de novo* 组装及组装质量评估的 Python 工具集。项目将常用生物信息学软件封装成可复用函数，通过 Docker（部分模块结合本地工具）调用，便于在 Python 脚本或 Notebook 中组织分析。

> **项目状态：持续开发中（Work in progress）**  
> 当前仓库以独立功能模块为主，**尚不是一键运行的完整 Pipeline**。接口、依赖和输出结构可能随开发调整。欢迎根据实际需求组合模块。

## 功能概览

| 阶段 | 文件 | 已实现的函数 | 用途 |
| --- | --- | --- | --- |
| 测序数据统计 | `seqkit.py` | `seqkit_stats` | FASTA/FASTQ 统计 |
| 长读质控 | `fastplong.py` | `fastplong_filter` | ONT FASTQ 过滤及 HTML/JSON 报告 |
| 基因组大小估计 | `lrge.py` | `lrge_estimate` | 基于长读的基因组大小估计 |
| k-mer 分析 | `est_all.py` | `jellyfish_genomescope` | Jellyfish 计数及 GenomeScope 估计 |
| 倍性探索 | `polyploid_pre.py` | `run_smudgeplot` | FastK + Smudgeplot 分析 |
| 基因组组装 | `genome_assembly.py` | `assembly_flye`, `assembly_hifiasm` | ONT 数据的 Flye/Hifiasm 组装 |
| 连续性评估 | `quast.py` | `quast_stats` | QUAST 组装统计 |
| 基因内容完整性 | `busco.py` | `busco_db_list`, `busco_download`, `busco_stats`, `busco_plot` | BUSCO 数据库管理、评估和绘图 |
| k-mer 质量评估 | `merqury.py` | `meryl_count`, `merqury_stats` | Merqury QV 和 k-mer 完整性 |
| Reads 回贴评估 | `minimap.py` | `mapping_minimap2` | minimap2 比对、BAM 和覆盖度统计 |
| 重复序列注释 | `edta.py` | `edta_annotation` | EDTA 转座元件注释 |

## 仓库结构

```text
Tools-of-Assembly/
├── README.md                # 中文说明（本文件）
├── README_EN.md             # English documentation
├── seqkit.py
├── fastplong.py
├── lrge.py
├── est_all.py
├── polyploid_pre.py
├── genome_assembly.py
├── quast.py
├── busco.py
├── merqury.py
├── minimap.py
└── edta.py
```

> 上方为当前已上传脚本的平铺结构；后续新增模块时可继续追加文件或按功能分类调整目录。

## 运行环境

- **Python 3**：用于导入函数及执行 `subprocess`；当前模块主要使用 Python 标准库。
- **Docker**：需可在终端执行 `docker run`，并能拉取相应镜像。
- **Linux 环境推荐**：脚本通过绝对路径挂载输入文件与输出目录，适合 Linux 工作站/服务器；其他系统需自行验证 Docker 文件共享与路径兼容性。
- **额外依赖**：`polyploid_pre.py` 中的 FastK 通过本地 Conda 环境运行；`minimap.py` 在构建 BAM 索引、统计 flagstat/coverage 时需要宿主机的 `samtools`。
- **资源需求**：线程数、可用内存及磁盘空间应结合物种基因组大小和测序深度调整。部分函数默认线程数为 `128`，**不是最低要求**。

### 获取仓库

```bash
git clone https://github.com/<YOUR_USERNAME>/Tools-of-Assembly.git
cd Tools-of-Assembly
python3 --version
docker --version
```

将 `<YOUR_USERNAME>` 替换为实际 GitHub 用户名，或直接使用 GitHub 页面上的 Clone URL。首次运行会按需拉取对应 Docker 镜像。

## 快速开始

以下示例假设 Python 从仓库根目录运行，示例路径请替换为自己的数据路径；各模块可独立执行。

### 1. 测序数据统计和过滤

```python
from seqkit import seqkit_stats
from fastplong import fastplong_filter

reads = "/path/to/ont_reads.fastq.gz"
seqkit_stats(reads, "/path/to/results/seqkit_stats.txt", threads=16)
clean_reads = fastplong_filter(
    reads,
    "/path/to/results/fastplong",
    threads=16,
    min_length=1000,
)
```

`fastplong_filter` 返回过滤后的 FASTQ 路径；同时产生 `fastplong.html` 和 `fastplong.json`。

### 2. 组装 ONT Reads

```python
from genome_assembly import assembly_flye, assembly_hifiasm

assembly = assembly_flye(
    input_file="/path/to/clean_reads.fastq.gz",
    output_dir="/path/to/results/flye",
    threads=32,
)

# 可选：使用另一种组装器独立运行
# alternative = assembly_hifiasm(
#     "/path/to/clean_reads.fastq.gz", "/path/to/results/hifiasm", threads=32
# )
```

Flye 支持可选的 `lrge_result`（包含基因组大小的文本文件）；未提供时不传入 `--genome-size`。Flye 默认会复用已有的非空 `assembly.fasta`，可通过 `force=True` 控制重新运行。

### 3. 组装质量评估

```python
from quast import quast_stats
from busco import busco_stats
from minimap import mapping_minimap2

assembly = "/path/to/results/flye/assembly.fasta"

quast_report = quast_stats(assembly, "/path/to/results/quast", threads=32)

# 请先下载与目标物种匹配的 BUSCO lineage 数据集
busco_result = busco_stats(
    input_file=assembly,
    database_dir="/path/to/busco_db",
    output_dir="/path/to/results/busco",
    lineage="<LINEAGE_NAME>",
    threads=32,
    mode="genome",
)

bam = mapping_minimap2(
    input_file="/path/to/clean_reads.fastq.gz",
    reference_file=assembly,
    output_dir="/path/to/results/minimap2",
    threads=32,
)
```

BUSCO 的 `<LINEAGE_NAME>` 必须替换为实际已下载的数据集名。`mapping_minimap2` 还会生成 `flagstat.txt` 与 `coverage.txt`。

### 4. 可选分析

- `lrge_estimate`：从长读估计基因组大小；对复杂、重复丰富或覆盖不足的基因组，应谨慎解释结果。
- `jellyfish_genomescope`：目前输入要求为**已解压的 FASTQ**；代码中 k-mer 长度固定为 `21`，可通过 `ploidy` 选择模型倍性。
- `run_smudgeplot`：当前 FastK 使用硬编码的本地 Conda 路径，运行前需修改 `polyploid_pre.py`；没有有效 smudge 时可能返回 `undetermined`。
- `meryl_count` + `merqury_stats`：先建立 reads 的 Meryl 数据库，再评估组装；两个函数都要求目标输出目录为空。
- `edta_annotation`：对组装 FASTA 运行 EDTA，支持参数匹配时复用已有完整结果。

## 注意事项与已知限制

1. **不是自动化总控流程**：目前没有统一入口或工作流调度器，需要自己按分析目标调用对应函数。
2. **Docker 不覆盖全部依赖**：FastK 依赖本地 Conda（见 `polyploid_pre.py`）；`minimap.py` 的 BAM 索引及统计环节依赖宿主机 `samtools`。
3. **部分参数是代码默认值**：例如 `est_all.py` 固定 `k=21`，`polyploid_pre.py` 的 FastK 固定 `-k40`；使用前建议检查输入格式及参数。
4. **结果不能只看单一指标**：QUAST、BUSCO、Merqury 与 reads 回贴覆盖度分别反映不同质量维度；高完整性不等同于高连续性。
5. **复用与覆盖行为并不统一**：例如 Flye 可以跳过已有组装，Merqury 则拒绝非空输出目录。重新运行前应检查相应函数逻辑。
6. **镜像版本以脚本为准**：各模块固定了 Docker 镜像及版本，个别镜像使用 `latest` 标签。公开运行的可复现性取决于镜像的可用性和版本一致性。

## 后续扩展计划

以下内容为预留的可编辑空间，**不代表已经实现**：

- [ ] 统一参数配置（例如 YAML/JSON）
- [ ] 统一日志、失败重试与输出目录约定
- [ ] 移除本地硬编码路径，增强跨环境兼容性
- [ ] 为模块增加最小测试数据与测试案例
- [ ] 新组装工具 / 质量评估模块（待定）
- [ ] 工作流整合（例如 Snakemake/Nextflow，待定）

### 新增模块登记模板

每新增一个脚本，可复制下面这一节并填写；同时更新上方**功能概览**和**仓库结构**。

````markdown
### <模块名称>（<script_name.py>）

- **功能**：<一句话说明>
- **核心函数**：`<function_name>`
- **输入**：<文件格式、必要参数>
- **输出**：<返回值、主要文件>
- **依赖**：<Docker 镜像/本地命令/数据库>
- **运行示例**：

```python
from <script_name> import <function_name>
# <调用示例>
```

- **注意事项**：<适用条件、限制或已知问题>
````

## 贡献、引用与许可

欢迎通过 Issue 提交问题和功能建议，或通过 Pull Request 贡献改进。引用分析结果时，请同时引用实际使用的 Flye、Hifiasm、BUSCO 等上游软件及其对应论文。

**许可证**：暂未指定。公开仓库不代表自动授予他人复制、修改或分发代码的许可；如需开源复用，请另行添加 `LICENSE` 并在此更新许可证信息。

<!-- 维护备注：新增脚本时，更新「功能概览」「仓库结构」「后续扩展计划」，并同步维护 README_EN.md。 -->

