import os
import re
import subprocess


def run_smudgeplot(input_data, output_dir, threads=8):
    """
    FastK → hetmers → Smudgeplot。

    返回：
        status: completed 或 undetermined
        smu: k-mer 对统计文件
        log: Smudgeplot all 运行日志
    """
    input_data = os.path.abspath(os.fspath(input_data))
    output_dir = os.path.abspath(os.fspath(output_dir))

    if not os.path.isfile(input_data):
        raise FileNotFoundError(input_data)

    if not isinstance(threads, int) or threads < 1:
        raise ValueError("threads 必须是正整数")

    # 输出目录
    fastk_dir = os.path.join(output_dir, "fastk")
    smudgeplot_dir = os.path.join(output_dir, "smudgeplot")

    os.makedirs(fastk_dir, exist_ok=True)
    os.makedirs(smudgeplot_dir, exist_ok=True)

    docker_image = "changshengw6/smudgeplot:0.5.3"

    # 1. FastK
    output_prefix = os.path.join(fastk_dir, "reads")

    cmd = [
        "/home/led/miniforge3/bin/conda",
        "run",
        "--no-capture-output",
        "-p", "/home/led/miniforge3/envs/fastk",
        "FastK",
        "-v",
        "-t4",
        "-k40",
        "-M128",
        f"-T{threads}",
        input_data,
        f"-N{output_prefix}",
    ]

    subprocess.run(cmd, check=True)

    # 2. 提取候选 k-mer 对
    # 挂载整个目录，保留 FastK 数据库的配套文件。
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{fastk_dir}:/input_dir:ro",
        "-v", f"{smudgeplot_dir}:/output_dir",
        docker_image,
        "smudgeplot", "hetmers",
        "-L", "12",
        "-t", str(threads),
        "-o", "/output_dir/reads",
        "--verbose",
        "/input_dir/reads.ktab",
    ]

    subprocess.run(cmd, check=True)

    # 3. 倍性推断与绘图
    smu_file = os.path.join(smudgeplot_dir, "reads.smu")
    log_file = os.path.join(smudgeplot_dir, "smudgeplot.log")

    cmd = [
        "docker", "run", "--rm",
        "-v", f"{smu_file}:/reads.smu:ro",
        "-v", f"{smudgeplot_dir}:/output_dir",
        docker_image,
        "smudgeplot", "all",
        "-o", "/output_dir/reads",
        "/reads.smu",
    ]

    with open(log_file, "w", encoding="utf-8") as log:
        result = subprocess.run(
            cmd,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=False,
        )

    with open(log_file, encoding="utf-8", errors="replace") as log:
        log_text = log.read()

    no_smudges = bool(
        re.search(r"Genomic kmers in smudges:\s*0\b", log_text)
    )

    known_empty_result_error = (
        no_smudges
        and "AttributeError" in log_text
        and "Can only use .str accessor" in log_text
    )

    # 仅允许已知的空聚类报告异常，不忽略其他错误。
    if result.returncode != 0 and not known_empty_result_error:
        print(log_text)
        result.check_returncode()

    status = "undetermined" if no_smudges else "completed"

    if status == "undetermined":
        print("Smudgeplot：未检测到有效 smudge，倍性未确定。")
    else:
        print("Smudgeplot：运行完成，请结合图形检查推断结果。")

    print(f"日志：{log_file}")

    return {
        "status": status,
        "smu": smu_file,
        "log": log_file,
    }