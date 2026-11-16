import os
import json
import shutil
import hashlib
import subprocess
from pathlib import Path


def edta_annotation(
    assembly_fasta,
    output_dir,
    threads=128,
    species="others",
    step="all",
    sensitive=0,
    anno=1,
    overwrite=0,
    docker_image="oushujun/edta:2.0.0",
    reuse=True
):
    """
    Run EDTA transposable element annotation using Docker.

    Parameters
    ----------
    assembly_fasta : str
        Assembled genome FASTA.
    output_dir : str
        EDTA working/output directory.
    threads : int
        Number of CPU threads.
    species : str
        Rice, Maize, or others.
    step : str
        all, filter, final, or anno.
    sensitive : int
        Whether to use RepeatModeler (0/1).
    anno : int
        Whether to perform whole-genome annotation (0/1).
    overwrite : int
        Whether to overwrite existing raw TE results (0/1).
    reuse : bool
        Skip when matching completed results are available.

    Returns
    -------
    dict
        Status and EDTA output paths.
    """

    # 1. 输入检查
    assembly_fasta = Path(assembly_fasta).expanduser().resolve()
    output_dir = Path(output_dir).expanduser().resolve()

    if not assembly_fasta.is_file():
        raise FileNotFoundError(assembly_fasta)

    if int(threads) < 1:
        raise ValueError("threads must be >= 1")

    if species not in ("Rice", "Maize", "others"):
        raise ValueError("Invalid species")

    if step not in ("all", "filter", "final", "anno"):
        raise ValueError("Invalid EDTA step")

    output_dir.mkdir(parents=True, exist_ok=True)

    # 2. 输出文件和完成标记
    edta_input = output_dir / "genome.fasta"
    status_file = output_dir / "edta_status.json"

    source_stat = assembly_fasta.stat()

    parameters = {
        "source": str(assembly_fasta),
        "source_size": source_stat.st_size,
        "source_mtime_ns": source_stat.st_mtime_ns,
        "threads": int(threads),
        "species": species,
        "step": step,
        "sensitive": int(sensitive),
        "anno": int(anno),
        "overwrite": int(overwrite),
        "docker_image": docker_image
    }

    # 3. 跳过已完成步骤
    if reuse and status_file.is_file():
        try:
            old = json.loads(status_file.read_text())

            if (
                old.get("status") == "completed"
                and old.get("parameters") == parameters
                and any(output_dir.glob("genome.fasta.mod.EDTA*"))
            ):
                print("[EDTA] Existing completed results found. Skipping.")

                return {
                    "status": "skipped",
                    "output_dir": str(output_dir),
                    "input_fasta": str(edta_input),
                    "status_file": str(status_file)
                }

        except (OSError, ValueError):
            pass

    # 4. 复制输入 FASTA
    # 源文件改变时刷新工作目录中的副本
    needs_copy = (
        not edta_input.exists()
        or edta_input.stat().st_size != source_stat.st_size
        or edta_input.stat().st_mtime_ns != source_stat.st_mtime_ns
    )

    if needs_copy and assembly_fasta != edta_input:
        print("[EDTA] Copying assembly FASTA...")
        shutil.copy2(assembly_fasta, edta_input)

    # 5. Docker 命令
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{output_dir}:/work",
        "-w", "/work",

        docker_image,
        "perl", "/EDTA/EDTA.pl",

        "--genome", "genome.fasta",
        "--species", species,
        "--step", step,
        "--threads", str(threads),
        "--anno", str(int(anno)),
        "--sensitive", str(int(sensitive)),
        "--overwrite", str(int(overwrite))
    ]

    # 6. 执行 EDTA
    print("[EDTA] Starting TE annotation...")

    status_file.write_text(json.dumps({
        "status": "running",
        "parameters": parameters
    }, indent=4))

    try:
        subprocess.run(
            cmd,
            check=True,
            stdin=subprocess.DEVNULL
        )

        # EDTA 输出检查
        output_files = sorted(
            p for p in output_dir.glob("genome.fasta.mod.EDTA*")
            if p.is_file() and p.stat().st_size > 0
        )

        if not output_files:
            raise RuntimeError(
                "EDTA completed but expected result files were not found."
            )

        status = "completed"

    except Exception as exc:
        status_file.write_text(json.dumps({
            "status": "failed",
            "parameters": parameters,
            "error": str(exc)
        }, indent=4))

        raise

    # 7. 保存完成状态
    status_file.write_text(json.dumps({
        "status": status,
        "parameters": parameters,
        "output_files": [str(p) for p in output_files]
    }, indent=4))

    print("[EDTA] Completed.")

    return {
        "status": status,
        "input_fasta": str(edta_input),
        "output_dir": str(output_dir),
        "output_files": [str(p) for p in output_files],
        "status_file": str(status_file)
    }