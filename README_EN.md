# Tools-of-Assembly

[简体中文](README.md) | [English](README_EN.md)

**Tools-of-Assembly** is a Python toolkit for *de novo* genome assembly and assembly quality assessment. It wraps commonly used bioinformatics programs in reusable Python functions, primarily through Docker, so individual analysis steps can be incorporated into Python scripts or notebooks.

> **Status: Work in progress**  
> The repository currently consists of **independent utility modules**, **not a fully automated, one-command pipeline**. Interfaces, dependencies and output conventions may evolve as new modules are added.

## Features and modules

| Stage | File | Available functions | Purpose |
| --- | --- | --- | --- |
| Read statistics | `seqkit.py` | `seqkit_stats` | FASTA/FASTQ statistics |
| Long-read filtering | `fastplong.py` | `fastplong_filter` | Filter ONT reads and generate HTML/JSON reports |
| Genome size estimation | `lrge.py` | `lrge_estimate` | Long-read-based genome size estimation |
| k-mer analysis | `est_all.py` | `jellyfish_genomescope` | Jellyfish counting and GenomeScope estimation |
| Ploidy exploration | `polyploid_pre.py` | `run_smudgeplot` | FastK and Smudgeplot analysis |
| Genome assembly | `genome_assembly.py` | `assembly_flye`, `assembly_hifiasm` | ONT assembly with Flye or Hifiasm |
| Contiguity metrics | `quast.py` | `quast_stats` | QUAST assembly statistics |
| Gene-content completeness | `busco.py` | `busco_db_list`, `busco_download`, `busco_stats`, `busco_plot` | BUSCO dataset management and assessment |
| k-mer-based quality | `merqury.py` | `meryl_count`, `merqury_stats` | Merqury QV and k-mer completeness |
| Read mapping | `minimap.py` | `mapping_minimap2` | minimap2 mapping, BAM and coverage statistics |
| Repeat annotation | `edta.py` | `edta_annotation` | Transposable-element annotation with EDTA |

## Repository structure

```text
Tools-of-Assembly/
├── README.md                # Chinese documentation
├── README_EN.md             # English documentation (this file)
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

This is the current flat layout. Additional scripts can be appended, or modules can be reorganized into subdirectories later.

## Requirements

- **Python 3** for importing the modules and invoking subprocesses. The current wrappers primarily use the standard library.
- **Docker** installed and accessible through `docker run`, with permission to pull and launch the required images.
- **Linux recommended**. Input and output paths are mounted into containers as absolute paths; verify file sharing and path behavior on other platforms.
- **Additional host-side dependencies**: FastK is invoked from a local Conda environment in `polyploid_pre.py`. The indexing and statistics stages in `minimap.py` require `samtools` installed on the host.
- **Sufficient compute resources**: adjust CPU threads, memory and disk space to the genome and sequencing dataset. Some function defaults are `128` threads; this is **not a minimum requirement**.

### Clone

```bash
git clone https://github.com/complex4died/Tools-of-Assembly.git
cd Tools-of-Assembly
python3 --version
docker --version
```

Replace `<YOUR_USERNAME>` with your actual GitHub username, or use the clone URL provided by GitHub. Docker images are pulled as needed.

## Quick start

The following examples assume Python is launched from the repository root. Replace placeholder paths with your own files and directories. Modules can be run independently.

### 1. Read statistics and filtering

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

`fastplong_filter` returns the filtered FASTQ path and also creates `fastplong.html` and `fastplong.json`.

### 2. Assemble ONT reads

```python
from genome_assembly import assembly_flye, assembly_hifiasm

assembly = assembly_flye(
    input_file="/path/to/clean_reads.fastq.gz",
    output_dir="/path/to/results/flye",
    threads=32,
)

# Optional, independent alternative assembler:
# alternative = assembly_hifiasm(
#     "/path/to/clean_reads.fastq.gz", "/path/to/results/hifiasm", threads=32
# )
```

Flye optionally accepts `lrge_result`, a text file containing the genome size estimate; if omitted, the wrapper does not pass `--genome-size`. By default, Flye reuses an existing non-empty `assembly.fasta`; set `force=True` to rerun it.

### 3. Evaluate an assembly

```python
from quast import quast_stats
from busco import busco_stats
from minimap import mapping_minimap2

assembly = "/path/to/results/flye/assembly.fasta"

quast_report = quast_stats(assembly, "/path/to/results/quast", threads=32)

# Download the appropriate BUSCO lineage dataset before running this step.
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

Replace `<LINEAGE_NAME>` with the name of an installed BUSCO dataset. `mapping_minimap2` also generates `flagstat.txt` and `coverage.txt`.

### 4. Optional analyses

- `lrge_estimate`: estimates genome size from long reads; interpret results cautiously for highly repetitive, complex or under-covered genomes.
- `jellyfish_genomescope`: currently expects an **uncompressed FASTQ** input, uses a hard-coded `k=21`, and exposes the GenomeScope model ploidy via `ploidy`.
- `run_smudgeplot`: requires updating hard-coded local Conda/FastK paths in `polyploid_pre.py`; can return `undetermined` when no informative smudges are detected.
- `meryl_count` + `merqury_stats`: create a Meryl reads database and assess the assembly; both functions require **empty output directories**.
- `edta_annotation`: annotates transposable elements in a genome FASTA and can reuse previously completed results when inputs and parameters match.

## Known limitations

1. **No central workflow orchestrator**: users compose the modules manually according to their analysis goals.
2. **Not all dependencies are containerized**: FastK uses a host Conda environment, while part of `minimap.py` relies on host `samtools`.
3. **Some parameters are fixed in source code**: for example, `est_all.py` uses `k=21`, and FastK in `polyploid_pre.py` uses `-k40`. Check input formats and parameters before execution.
4. **Assembly quality is multidimensional**: QUAST, BUSCO, Merqury and read-mapping coverage evaluate different aspects; high completeness does not imply high contiguity.
5. **Existing-output handling differs by module**: Flye may skip a completed assembly, whereas Merqury functions reject non-empty output directories.
6. **Image versions are specified in the scripts**: most wrappers use explicit Docker image tags, while a few use `latest`. Reproducibility depends on image availability and version consistency.

## Roadmap and extension space

The following items are **planned placeholders**, not implemented features:

- [ ] Centralized YAML/JSON configuration
- [ ] Consistent logging, failure handling and output naming
- [ ] Removal of host-specific hard-coded paths
- [ ] Minimal test datasets and automated tests
- [ ] Additional assemblers / assessment modules (TBD)
- [ ] Optional Snakemake/Nextflow integration (TBD)

### Template for new modules

Copy and complete this section when adding another script. Update both the **Features and modules** table and the **Repository structure** above.

````markdown
### <Module name> (`<script_name.py>`)

- **Purpose**: <One-sentence description>
- **Main function**: `<function_name>`
- **Inputs**: <File formats and required parameters>
- **Outputs**: <Return value and main result files>
- **Dependencies**: <Docker image / host binaries / databases>
- **Example**:

```python
from <script_name> import <function_name>
# <Example invocation>
```

- **Notes / limitations**: <Requirements and known caveats>
````

## Contributing, citation and license

Issues and pull requests for bug reports, suggestions and improvements are welcome. When publishing analyses, please cite the underlying tools (such as Flye, Hifiasm and BUSCO) and their original papers, as appropriate.

**License**: Not specified yet. A public repository does not automatically grant others permission to reproduce, modify or redistribute its code. Add a `LICENSE` file and update this section if you intend to release it under an open-source license.

<!-- Maintenance note: when adding scripts, update the module table, repository tree and roadmap; keep README.md in sync. -->

