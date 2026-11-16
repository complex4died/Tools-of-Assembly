from pathlib import Path
import subprocess

# def assembly_flye(input_file, lrge_result, output_dir, threads=128):

#     input_file = Path(input_file).resolve()
#     lrge_result = Path(lrge_result).resolve()
#     output_dir = Path(output_dir).resolve()

#     output_dir.mkdir(parents=True, exist_ok=True)

#     # Read estimated genome size
#     with open(lrge_result) as f:
#         genome_size = f.read().strip()

#     print(f"Estimated genome size: {genome_size}")

#     docker_image = "staphb/flye:2.9.6"

#     cmd = [
#         "docker", "run", "--rm",
#         "-v", f"{input_file}:/input.fastq.gz:ro",
#         "-v", f"{output_dir}:/output",
#         docker_image,
#         "flye",
#         "--nano-hq", "/input.fastq.gz",
#         "--genome-size", genome_size,
#         "--out-dir", "/output",
#         "--threads", str(threads)
#     ]

#     subprocess.run(cmd, check=True)

#     return str(output_dir / "assembly.fasta")


def assembly_flye(
    input_file,
    output_dir,
    threads=128,
    lrge_result=None,
    force=False
):
    """
    Assemble ONT reads using Flye Docker.

    Parameters
    ----------
    input_file : str or Path
        Input ONT FASTQ file (.fastq or .fastq.gz).
    output_dir : str or Path
        Output directory.
    threads : int
        Number of threads.
    lrge_result : str or Path or None
        Optional LRGE genome size estimation file.
    force : bool
        Whether to rerun an existing completed assembly.

    Returns
    -------
    str
        Path to assembly.fasta.
    """

    docker_image = "staphb/flye:2.9.6"

    # 1. Paths
    input_file = Path(input_file).resolve()
    output_dir = Path(output_dir).resolve()

    if not input_file.is_file():
        raise FileNotFoundError(
            f"Input file not found: {input_file}"
        )

    if threads < 1:
        raise ValueError("threads must be >= 1")

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    assembly_file = output_dir / "assembly.fasta"

    # 2. Skip existing assembly
    if assembly_file.is_file() and not force and assembly_file.stat().st_size > 0:
        print(
            f"[Flye] Existing assembly found: {assembly_file}"
        )
        return str(assembly_file)

    # 3. Docker command
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{input_file}:/input.fastq.gz:ro",
        "-v", f"{output_dir}:/output",
        docker_image,
        "flye",
        "--nano-hq", "/input.fastq.gz",
        "--out-dir", "/output",
        "--threads", str(threads)
    ]

    # 4. Optional genome size
    if lrge_result is not None:

        lrge_result = Path(lrge_result).resolve()

        if not lrge_result.is_file():
            raise FileNotFoundError(
                f"LRGE result not found: {lrge_result}"
            )

        genome_size = lrge_result.read_text().strip()

        if not genome_size:
            raise ValueError(
                "LRGE genome size result is empty"
            )

        print(
            f"[Flye] Estimated genome size: {genome_size}"
        )

        cmd.extend([
            "--genome-size", genome_size
        ])

    else:
        print(
            "[Flye] Genome size not provided. "
            "Using Flye automatic estimation."
        )

    # 5. Run Flye
    print("[Flye] Starting assembly...")

    subprocess.run(
        cmd,
        check=True
    )

    # 6. Validate output
    if (
        not assembly_file.is_file()
        or assembly_file.stat().st_size == 0
    ):
        raise RuntimeError(
            f"Flye assembly failed: {assembly_file}"
        )

    print(
        f"[Flye] Assembly completed: {assembly_file}"
    )

    return str(assembly_file)



def assembly_hifiasm(input_file, output_dir, threads=128):

    input_file = Path(input_file).resolve()
    output_dir = Path(output_dir).resolve()

    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_file.is_file():
        raise FileNotFoundError(f"Input FASTQ not found: {input_file}")

    # 1. Hifiasm assembly
    docker_image_hifiasm = "staphb/hifiasm:0.25.0"

    cmd = [
        "docker", "run", "--rm",
        "-v", f"{input_file}:/input.fastq.gz:ro",
        "-v", f"{output_dir}:/output",
        docker_image_hifiasm,
        "hifiasm",
        "--ont",
        "-t", str(threads),
        "-o", "/output/ONT.asm",
        "/input.fastq.gz"
    ]

    subprocess.run(cmd, check=True)

    # 2. GFA to FASTA
    docker_image_gfatools = "dnalinux/gfatools:latest"

    gfa_file = output_dir / "ONT.asm.bp.p_ctg.gfa"
    assembly_file = output_dir / "assembly.fasta"

    if not gfa_file.is_file():
        raise FileNotFoundError(f"GFA file not found: {gfa_file}")

    cmd = [
        "docker", "run", "--rm",
        "-v", f"{gfa_file}:/input.gfa:ro",
        docker_image_gfatools,
        "gfatools-final-gt/gfatools",
        "gfa2fa",
        "/input.gfa"
    ]

    with open(assembly_file, "wb") as output:
        subprocess.run(
            cmd,
            stdout=output,
            check=True
        )

    if not assembly_file.is_file() or assembly_file.stat().st_size == 0:
        raise FileNotFoundError(
            f"Assembly FASTA missing or empty: {assembly_file}"
        )

    return str(assembly_file)
