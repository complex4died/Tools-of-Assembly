from pathlib import Path
import subprocess

def seqkit_stats(input_file, output_file, threads = 16):
    """
    Run SeqKit stats using Docker.
    """

    docker_image_seqkit = "staphb/seqkit:2.13.0"

    input_file = Path(input_file).resolve()
    output_file = Path(output_file).resolve()

    # 1. Check input
    if not input_file.is_file():
        raise FileNotFoundError(
            f"Input file not found: {input_file}"
        )

    if input_file.stat().st_size == 0:
        raise ValueError(
            f"Input file is empty: {input_file}"
        )

    # 2. Create output directory
    output_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # 3. Docker command
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{input_file}:/input.fasta.gz:ro",
        "-v", f"{output_file.parent}:/output",
        docker_image_seqkit,
        "seqkit", "stats",
        "/input.fasta.gz",
        "-aT",
        "-j", str(threads),
        "-o", f"/output/{output_file.name}"
    ]

    # 4. Run Docker
    subprocess.run(cmd, check=True)

    # 5. Check output
    if not output_file.is_file():
        raise FileNotFoundError(
            f"Output file not generated: {output_file}"
        )

    if output_file.stat().st_size == 0:
        raise ValueError(
            f"Output file is empty: {output_file}"
        )

    return output_file