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
git clone https://github.com/complex4died/Tools-of-Assembly.git
cd Tools-of-Assembly
python3 --version
docker --version
```

如果仓库地址或所有者发生变化，请以 GitHub 仓库页面提供的 Clone URL 为准。首次运行会按需拉取对应 Docker 镜像。

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

### 4. 基因组大小估计：LRGE（`lrge.py`）

`lrge_estimate(input_file, output_dir, threads=32, platform="ont", target=10000, query=5000, seed=42, force=False)` 使用长读数据估算基因组大小。

```python
from lrge import lrge_estimate

lrge_file = lrge_estimate(
    input_file="/path/to/clean_reads.fastq.gz",
    output_dir="/path/to/results/lrge",
    threads=32,
    platform="ont",     # "ont" 或 "pb"
    target=10000,
    query=5000,
    seed=42,
    force=False,
)
print(lrge_file)  # /path/to/results/lrge/est_size.txt (Path)
```

- **输入**：FASTQ/FASTA/未比对 BAM（由 LRGE 处理；请确认对应格式与镜像兼容）；`platform` 为 `ont` 或 `pb`。
- **输出**：`est_size.txt`，函数返回该文件的 `Path`；同时使用 `output_dir/tmp/` 存放临时文件。
- **复用行为**：已有非空 `est_size.txt` 时默认跳过，`force=True` 可重新运行。
- **注意**：估计值并非真实基因组大小的保证，复杂重复、高杂合或测序覆盖不足的数据尤其需要与其他证据交叉验证。

### 5. k-mer 基因组特征预测：Jellyfish + GenomeScope（`est_all.py`）

`jellyfish_genomescope(input_data, output_dir, threads=4, ploidy=2)` 使用 Jellyfish 构建 k-mer 频谱，再调用 GenomeScope 2 拟合模型。

```python
from est_all import jellyfish_genomescope

result = jellyfish_genomescope(
    input_data="/path/to/reads.fastq",  # 当前实现要求解压后的 FASTQ
    output_dir="/path/to/results/kmer_estimation",
    threads=8,
    ploidy=2,
)
print(result["est_size"])        # GenomeScope 单倍体长度上下限的中点，单位 bp
print(result["hist_file"])       # Jellyfish k-mer 频数直方图
print(result["genomescope_dir"])
print(result["est_size_file"])   # 单个整数的文本文件
```

- **输入**：未压缩 FASTQ。当前 `kmer_size=21` 在函数内部固定，修改 k 值需要修改源代码；`ploidy` 传递给 GenomeScope 的 `-p`。
- **输出**：`jellyfish/reads.jf`、`jellyfish/reads.histo`、`genomescope/`、`genomescope/est_size.txt`。
- **返回值**：字典，键包括 `reads_jf`、`hist_file`、`genomescope_dir`、`est_size`、`est_size_min`、`est_size_max`、`est_size_file`。
- **注意**：`est_size` 是从 `summary.txt` 中 *Genome Haploid Length* 的范围计算的中点，而不是自动推断出的完整倍体基因组总量；模型结果需要结合频谱是否合理来判断。

### 6. 倍性探索：FastK + Smudgeplot（`polyploid_pre.py`）

`run_smudgeplot(input_data, output_dir, threads=8)` 依次运行 FastK、Smudgeplot `hetmers` 和 `all`。

```python
from polyploid_pre import run_smudgeplot

result = run_smudgeplot(
    input_data="/path/to/reads.fastq.gz",
    output_dir="/path/to/results/ploidy",
    threads=8,
)
print(result["status"])  # "completed" 或 "undetermined"
print(result["smu"])
print(result["log"])
```

- **输入**：FastK 可读取的测序 reads 文件；当前脚本将 FastK 的 k 值固定为 `40`（`-k40`），`hetmers` 使用 `-L 12`。
- **依赖**：在 `polyploid_pre.py` 中，FastK 通过硬编码的 `/home/led/miniforge3/bin/conda` 和 `/home/led/miniforge3/envs/fastk` 运行。**其他机器上必须先修改这两个路径**；Smudgeplot 使用 Docker。
- **输出**：`fastk/` 中的 FastK 数据库、`smudgeplot/reads.smu`、`smudgeplot/smudgeplot.log` 及 Smudgeplot 生成的图表（若成功）。
- **结果解读**：`undetermined` 表示日志显示没有有效 smudge，不能解释为已经证明单倍体或二倍体；`completed` 也需要查看图表后才可作出生物学判断。

### 7. k-mer 组装质量评估：Meryl + Merqury（`merqury.py`）

`meryl_count(input_file, output_dir, k=17, threads=128, memory="256g")` 从 reads 建立 Meryl 数据库；`merqury_stats(input_file, meryl_db, output_dir, threads=128, memory="256g")` 使用该数据库对组装结果进行评估。

```python
from merqury import meryl_count, merqury_stats

meryl_db = meryl_count(
    input_file="/path/to/reads.fastq.gz",
    output_dir="/path/to/results/meryl",
    k=17,
    threads=32,
    memory="64g",
)
merqury_dir = merqury_stats(
    input_file="/path/to/results/flye/assembly.fasta",
    meryl_db=meryl_db,
    output_dir="/path/to/results/merqury",
    threads=32,
    memory="64g",
)
print(meryl_db)     # .../meryl/read.meryl（目录）
print(merqury_dir)  # Merqury 结果目录
```

- **输入**：`meryl_count` 接收 FASTQ reads；`merqury_stats` 接收组装 FASTA 和先前生成的 **Meryl 数据库目录**（非单个文件）。
- **关键输出**：`read.meryl/`、`merqury_res.qv`、`merqury_res.completeness.stats`，以及上游 Merqury 生成的其他图表和文件。
- **重要限制**：这两个函数都会拒绝**非空输出目录**。重新执行时请指定新目录或先人工处理旧结果，不要直接覆盖。
- **资源**：`memory` 参数作为 Docker 内存限制传入；需要根据实际机器修改，不意味着必须有 256 GB 内存。
- **方法学提醒**：Merqury 的参考 k-mer 集应尽可能来自合适质量和深度的测序 reads；结果可靠性受 reads 质量和 k 值选择影响，不能仅靠 QV 判断全部结构正确性。

### 8. 重复序列注释：EDTA（`edta.py`）

`edta_annotation` 将组装 FASTA 复制到工作目录，运行 EDTA 并记录执行状态，适合对真核基因组中的转座元件进行结构与同源注释。

```python
from edta import edta_annotation

result = edta_annotation(
    assembly_fasta="/path/to/assembly.fasta",
    output_dir="/path/to/results/edta",
    threads=32,
    species="others",  # "Rice" / "Maize" / "others"
    step="all",        # "all" / "filter" / "final" / "anno"
    sensitive=0,
    anno=1,
    overwrite=0,
    reuse=True,
)
print(result["status"])       # "completed" 或 "skipped"
print(result["output_dir"])
print(result["status_file"])  # edta_status.json
```

- **输入**：已组装的基因组 FASTA；`species`、`step` 的允许值如示例所示。
- **输出**：输出目录中的 `genome.fasta`、`genome.fasta.mod.EDTA*` 结果及 `edta_status.json`。
- **返回值**：字典。正常完成时包含 `status`、`input_fasta`、`output_dir`、`output_files`、`status_file`；跳过时不包含 `output_files`。
- **缓存策略**：`reuse=True` 会根据输入路径、文件大小、修改时间和参数对应的状态记录决定是否跳过；它**不是**严格的内容哈希校验。`overwrite` 是传给 EDTA 的参数，与 `reuse` 含义不同。
- **注意**：EDTA 计算量较大；对极度碎片化的组装，完整转座元件识别效果可能受限。

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


