from pathlib import Path
import subprocess

def fastplong_filter(input_file, output_dir, threads=16, min_length=500):
    """
    Run fastplong using Docker.

    Parameters
    ----------
    input_file : str or Path
        Input FASTQ file.
    output_dir : str or Path
        Output directory.
    threads : int, optional
        Number of threads to use (default is 16).
    Returns
    -------
    Path
        Filtered FASTQ file path.
    """

    #docker_image_fastplong = "staphb/fastplong:0.7.0"
    docker_image_fastplong = "staphb/fastplong:0.7.1"

    # 1. Input validation
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

    # 2. Create output directory
    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    # 3. Output files
    filtered_file = output_dir / "filtered.fastq.gz"
    html_file = output_dir / "fastplong.html"
    json_file = output_dir / "fastplong.json"

    # 4. Docker command
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{input_file}:/input.fastq.gz:ro",
        "-v", f"{output_dir}:/output_dir",
        docker_image_fastplong,
        "fastplong",
        "-i", "/input.fastq.gz",
        "-w", str(threads),
        "-l", str(min_length),
        "-o", "/output_dir/filtered.fastq.gz",
        "-h", "/output_dir/fastplong.html",
        "-j", "/output_dir/fastplong.json"
    ]

    # 5. Run Docker
    subprocess.run(cmd, check=True)

    # 6. Output validation
    for file in [filtered_file, html_file, json_file]:
        if not file.is_file():
            raise FileNotFoundError(
                f"Output file not generated: {file}"
            )

        if file.stat().st_size == 0:
            raise ValueError(
                f"Output file is empty: {file}"
            )

    return filtered_file