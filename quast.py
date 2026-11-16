import subprocess
from pathlib import Path


def quast_stats(input_file, output_dir, threads=128):

    input_file = Path(input_file).resolve()
    output_dir = Path(output_dir).resolve()

    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_file.is_file():
        raise FileNotFoundError(f"Input FASTA not found: {input_file}")

    docker_image = "staphb/quast:5.3.0"

    cmd = [
        "docker", "run", "--rm",
        "-v", f"{input_file}:/input.fasta:ro",
        "-v", f"{output_dir}:/output",
        docker_image,
        "quast.py",
        "/input.fasta",
        "-o", "/output",
        "-t", str(threads)
    ]

    subprocess.run(cmd, check=True)

    report_file = output_dir / "report.tsv"

    if not report_file.is_file():
        raise FileNotFoundError(
            f"QUAST report not found: {report_file}"
        )

    return str(report_file)