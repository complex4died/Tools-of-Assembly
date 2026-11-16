# import subprocess
# from pathlib import Path


# def meryl_count(input_file, output_dir, k=17,
#                 threads=128, memory="256g"):

#     input_file = Path(input_file).resolve()
#     output_dir = Path(output_dir).resolve()

#     output_dir.mkdir(parents=True, exist_ok=True)

#     if not input_file.is_file() or input_file.stat().st_size == 0:
#         raise FileNotFoundError(
#             f"Input FASTQ missing or empty: {input_file}"
#         )

#     docker_image = "danylmb/merqury:1.4.1-build2"

#     cmd = [
#         "docker", "run", "--rm",
#         "--memory", memory,
#         "--cpus", str(threads),
#         "-v", f"{input_file}:/input.fastq.gz:ro",
#         "-v", f"{output_dir}:/output",
#         "-e", f"OMP_NUM_THREADS={threads}",
#         docker_image,
#         "meryl",
#         "count",
#         "k=" + str(k),
#         "output", "/output/read.meryl",
#         "/input.fastq.gz"
#     ]

#     subprocess.run(cmd, check=True)

#     read_meryl_db = output_dir / "read.meryl"

#     if not read_meryl_db.is_file() or read_meryl_db.stat().st_size == 0:
#         raise FileNotFoundError(
#             f"Read Meryl database missing or empty: {read_meryl_db}"
#         )

#     return str(read_meryl_db)


# def merqury_stats(input_file, meryl_db, output_dir,
#                   threads=128, memory="256g"):

#     input_file = Path(input_file).resolve()
#     meryl_db = Path(meryl_db).resolve()
#     output_dir = Path(output_dir).resolve()

#     output_dir.mkdir(parents=True, exist_ok=True)

#     if not input_file.is_file() or input_file.stat().st_size == 0:
#         raise FileNotFoundError(
#             f"Assembly FASTA missing or empty: {input_file}"
#         )

#     if not meryl_db.is_dir():
#         raise FileNotFoundError(
#             f"Meryl database not found: {meryl_db}"
#         )

#     docker_image = "danylmb/merqury:1.4.1-build2"

#     cmd = [
#         "docker", "run", "--rm",
#         "--memory", memory,
#         "--cpus", str(threads),
#         "-v", f"{meryl_db}:/input_meryl/read.meryl:ro",
#         "-v", f"{input_file}:/input.fasta:ro",
#         "-v", f"{output_dir}:/output",
#         "-w", "/output",
#         "-e", f"OMP_NUM_THREADS={threads}",
#         docker_image,
#         "merqury.sh",
#         "/input_meryl/read.meryl",
#         "/input.fasta",
#         "merqury_res"
#     ]

#     subprocess.run(cmd, check=True)

#     qv_file = output_dir / "merqury_res.qv"
#     completeness_file = output_dir / "merqury_res.completeness.stats"

#     if not qv_file.is_file() or qv_file.stat().st_size == 0:
#         raise FileNotFoundError(
#             f"Merqury QV result missing or empty: {qv_file}"
#         )

#     if not completeness_file.is_file():
#         raise FileNotFoundError(
#             f"Merqury completeness result not found: {completeness_file}"
#         )

#     return str(output_dir)


import subprocess
from collections import deque
from pathlib import Path


def meryl_count(
    input_file,
    output_dir,
    k=17,
    threads=128,
    memory="256g"
):
    """从 reads 建立 meryl 数据库，返回数据库目录路径。"""

    input_file = Path(input_file).resolve()
    output_dir = Path(output_dir).resolve()

    docker_image = "danylmb/merqury:1.4.1-build2"

    # 检查输入文件
    if not input_file.is_file() or input_file.stat().st_size == 0:
        raise FileNotFoundError(
            f"Input FASTQ missing or empty: {input_file}"
        )

    # 禁止复用非空输出目录，避免混入旧数据库
    if output_dir.exists():
        if not output_dir.is_dir():
            raise NotADirectoryError(
                f"Not a directory: {output_dir}"
            )

        if any(output_dir.iterdir()):
            raise FileExistsError(
                f"Output directory is not empty: {output_dir}\n"
                "Please use a new output directory."
            )

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Reads: {input_file}", flush=True)
    print(f"Meryl output: {output_dir}", flush=True)
    print(f"k-mer size: {k}", flush=True)

    cmd = [
        "docker", "run", "--rm",
        "--memory", memory,
        "--cpus", str(threads),
        "-v", f"{input_file}:/input.fastq.gz:ro",
        "-v", f"{output_dir}:/output",
        "-w", "/output",
        "-e", f"OMP_NUM_THREADS={threads}",
        docker_image,
        "meryl",
        "count",
        f"k={k}",
        "output", "/output/read.meryl",
        "/input.fastq.gz"
    ]

    subprocess.run(cmd, check=True)

    read_meryl_db = output_dir / "read.meryl"

    # meryl 数据库是目录，不是普通文件
    if (
        not read_meryl_db.is_dir()
        or not any(read_meryl_db.iterdir())
    ):
        raise FileNotFoundError(
            f"Read Meryl database missing or empty: {read_meryl_db}"
        )

    print(f"Read Meryl database: {read_meryl_db}", flush=True)

    return str(read_meryl_db)


def merqury_stats(
    input_file,
    meryl_db,
    output_dir,
    threads=128,
    memory="256g"
):
    """运行 Merqury，检查结果并返回输出目录路径。"""

    input_file = Path(input_file).resolve()
    meryl_db = Path(meryl_db).resolve()
    output_dir = Path(output_dir).resolve()

    docker_image = "danylmb/merqury:1.4.1-build2"

    # 检查组装文件
    if not input_file.is_file() or input_file.stat().st_size == 0:
        raise FileNotFoundError(
            f"Assembly FASTA missing or empty: {input_file}"
        )

    # 检查 reads 数据库目录
    if not meryl_db.is_dir() or not any(meryl_db.iterdir()):
        raise FileNotFoundError(
            f"Read Meryl database missing or empty: {meryl_db}"
        )

    # 禁止复用非空输出目录，避免沿用旧的 input.meryl 等文件
    if output_dir.exists():
        if not output_dir.is_dir():
            raise NotADirectoryError(
                f"Not a directory: {output_dir}"
            )

        if any(output_dir.iterdir()):
            raise FileExistsError(
                f"Output directory is not empty: {output_dir}\n"
                "Please use a new output directory."
            )

    output_dir.mkdir(parents=True, exist_ok=True)

    log_file = (
        output_dir
        / "logs"
        / "merqury_res.spectra-cn.log"
    )

    print(f"Assembly: {input_file}", flush=True)
    print(f"Reads database: {meryl_db}", flush=True)
    print(f"Output directory: {output_dir}", flush=True)
    print(f"Internal log: {log_file}", flush=True)

    cmd = [
        "docker", "run", "--rm",
        "--memory", memory,
        "--cpus", str(threads),
        "-v", f"{meryl_db}:/input_meryl/read.meryl:ro",
        "-v", f"{input_file}:/input.fasta:ro",
        "-v", f"{output_dir}:/output",
        "-w", "/output",
        "-e", f"OMP_NUM_THREADS={threads}",
        docker_image,
        "merqury.sh",
        "/input_meryl/read.meryl",
        "/input.fasta",
        "merqury_res"
    ]

    # 手动检查退出码，以便失败时同时显示内部日志
    result = subprocess.run(cmd, check=False)

    qv_file = output_dir / "merqury_res.qv"
    completeness_file = (
        output_dir / "merqury_res.completeness.stats"
    )

    expected_files = [
        qv_file,
        completeness_file,
    ]

    # 即使退出码为 0，也必须检查结果是否存在且非空
    missing_files = [
        p.name
        for p in expected_files
        if not p.is_file() or p.stat().st_size == 0
    ]

    if result.returncode != 0 or missing_files:
        log_tail = "Internal log was not generated."

        if log_file.is_file():
            with log_file.open(errors="replace") as f:
                log_tail = "".join(deque(f, maxlen=80))

        raise RuntimeError(
            "Merqury failed or produced incomplete results.\n"
            f"Exit code: {result.returncode}\n"
            f"Missing/empty files: {missing_files}\n"
            f"Log: {log_file}\n\n"
            f"Last 80 log lines:\n{log_tail}"
        )

    print(f"QV result: {qv_file}", flush=True)
    print(f"Completeness result: {completeness_file}", flush=True)

    return str(output_dir)