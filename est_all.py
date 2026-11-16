import os
import subprocess


def jellyfish_genomescope(input_data, output_dir, threads=4, ploidy=2):
    """
    使用 Jellyfish 和 GenomeScope 分析 k-mer 分布。

    Parameters
    ----------
    input_data : str
        已解压的 FASTQ 文件路径。
    output_dir : str
        输出根目录。
    threads : int
        Jellyfish 使用的线程数。

    Returns
    -------
    dict
        k-mer 数据库、直方图和 GenomeScope 结果目录。
    """

    input_data = os.path.abspath(os.fspath(input_data))
    output_dir = os.path.abspath(os.fspath(output_dir))

    if not os.path.isfile(input_data):
        raise FileNotFoundError(f"输入文件不存在：{input_data}")

    if not isinstance(threads, int) or isinstance(threads, bool) or threads < 1:
        raise ValueError("threads 必须是正整数")

    jellyfish_dir = os.path.join(output_dir, "jellyfish")
    genomescope_dir = os.path.join(output_dir, "genomescope")

    os.makedirs(jellyfish_dir, exist_ok=True)
    os.makedirs(genomescope_dir, exist_ok=True)

    docker_image_jellyfish = "openeuler/jellyfish:2.3.1-oe2403sp4"
    docker_image_genomescope = "abner12/genomescope:2.0"

    kmer_size = 21

    reads_jf = os.path.join(jellyfish_dir, "reads.jf")
    hist_file = os.path.join(jellyfish_dir, "reads.histo")

    # 1. Jellyfish：统计 k-mer
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{input_data}:/input.fastq:ro",
        "-v", f"{jellyfish_dir}:/output",
        docker_image_jellyfish,
        "jellyfish", "count",
        "-C",
        "-m", str(kmer_size),
        "-s", "1000000000",
        "-t", str(threads),
        "/input.fastq",
        "-o", "/output/reads.jf"
    ]

    subprocess.run(cmd, check=True)

    # 2. Jellyfish：生成 k-mer 频数直方图
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{reads_jf}:/input.jf:ro",
        "-v", f"{jellyfish_dir}:/output",
        docker_image_jellyfish,
        "jellyfish", "histo",
        "-t", str(threads),
        "/input.jf",
        "-o", "/output/reads.histo"
    ]

    subprocess.run(cmd, check=True)

    # 3. GenomeScope：拟合 k-mer 分布
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{hist_file}:/input.histo:ro",
        "-v", f"{genomescope_dir}:/output",
        docker_image_genomescope,
        "genomescope.R",
        "-i", "/input.histo",
        "-o", "/output",
        "-k", str(kmer_size), 
        "-p", str(ploidy)
    ]

    subprocess.run(cmd, check=True)
    
        # 4. 读取 GenomeScope 预估的基因组大小
    summary_file = os.path.join(genomescope_dir, "summary.txt")

    est_size_min = None
    est_size_max = None

    with open(summary_file, encoding="utf-8") as f:
        for line in f:
            if line.strip().startswith("Genome Haploid Length"):
                fields = line.split()

                est_size_min = int(fields[3].replace(",", ""))
                est_size_max = int(fields[5].replace(",", ""))
                break

    if est_size_min is None or est_size_max is None:
        raise ValueError(
            f"未能从 {summary_file} 中读取 Genome Haploid Length"
        )

    # 取上下限中点，单位 bp
    est_size = (est_size_min + est_size_max) // 2

    # 保存为文本，方便其他步骤单独读取
    est_size_file = os.path.join(genomescope_dir, "est_size.txt")

    with open(est_size_file, "w", encoding="utf-8") as f:
        f.write(f"{est_size}\n")

    return {
        "reads_jf": reads_jf,
        "hist_file": hist_file,
        "genomescope_dir": genomescope_dir,
        "est_size": est_size,
        "est_size_min": est_size_min,
        "est_size_max": est_size_max,
        "est_size_file": est_size_file
    }