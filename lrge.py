from pathlib import Path
import subprocess


def lrge_estimate(
    input_file,
    output_dir,
    threads=32,
    platform="ont",
    target=10000,
    query=5000,
    seed=42,
    force=False
):
    """
    Estimate genome size using LRGE with Docker.

    Parameters
    ----------
    input_file : str or Path
        Input FASTQ, FASTA, or unaligned BAM file.
    output_dir : str or Path
        Output directory.
    threads : int
        Number of threads.
    platform : str
        Sequencing platform: ont or pb.
    target : int
        Number of target reads.
    query : int
        Number of query reads.
    seed : int
        Random seed.
    force : bool
        Whether to overwrite existing results.

    Returns
    -------
    Path
        Estimated genome size output file.
    """

    docker_image_lrge = "staphb/lrge:1.0.0"

    # 1. Validate input
    input_file = Path(input_file).resolve()
    output_dir = Path(output_dir).resolve()

    if not input_file.is_file():
        raise FileNotFoundError(
            f"Input file not found: {input_file}"
        )

    if input_file.stat().st_size == 0:
        raise ValueError(
            f"Input file is empty: {input_file}"
        )

    if threads < 1:
        raise ValueError("threads must be >= 1")

    if platform not in ("ont", "pb"):
        raise ValueError(
            "platform must be 'ont' or 'pb'"
        )

    if target < 1 or query < 1:
        raise ValueError(
            "target and query must be >= 1"
        )

    # 2. Prepare directories
    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    temp_dir = output_dir / "tmp"
    temp_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = output_dir / "est_size.txt"

    # 3. Skip existing result
    if (
        not force
        and output_file.is_file()
        and output_file.stat().st_size > 0
    ):
        print(
            f"[LRGE] Existing result found: {output_file}"
        )
        return output_file

    # 4. Docker command
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{input_file}:/input.fastq.gz:ro",
        "-v", f"{output_dir}:/output",
        docker_image_lrge,
        "lrge",
        "-P", platform,
        "-t", str(threads),
        "-T", str(target),
        "-Q", str(query),
        "-s", str(seed),
        "-D", "/output/tmp",
        "-o", "/output/est_size.txt",
        "/input.fastq.gz"
    ]

    # 5. Run LRGE
    print("[LRGE] Estimating genome size...")

    subprocess.run(
        cmd,
        check=True
    )

    # 6. Validate output
    if not output_file.is_file():
        raise FileNotFoundError(
            f"LRGE output not generated: {output_file}"
        )

    if output_file.stat().st_size == 0:
        raise ValueError(
            f"LRGE output is empty: {output_file}"
        )

    print(
        f"[LRGE] Completed: {output_file}"
    )

    return output_file