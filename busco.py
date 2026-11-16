import subprocess
from pathlib import Path

def busco_db_list():
    docker_image = "staphb/busco:6.1.0"
    
    cmd = [
        "docker", "run", "--rm", 
        docker_image, 
        "busco", 
        "--list-datasets"
    ]
    
    result = subprocess.run(
        cmd,
        check=True,
        capture_output=True,
        text=True
    )
    return result.stdout


def busco_download(database_dir, lineage):

    database_dir = Path(database_dir).resolve()
    database_dir.mkdir(parents=True, exist_ok=True)

    docker_image = "staphb/busco:6.1.0"
    # docker_image = "ezlabgva/busco:v6.1.0_cv3"
    
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{database_dir}:/busco_db",
        docker_image,
        "busco",
        "--download_path", "/busco_db",
        "--download", lineage
    ]

    subprocess.run(cmd, check=True)

    return str(database_dir)


def busco_stats(input_file, database_dir, output_dir,
                lineage, threads=128, mode="genome"):

    valid_modes = {"genome", "transcriptome", "proteins"}
    if mode not in valid_modes:
        raise ValueError(
            f"Invalid BUSCO mode: {mode}. "
            f"Choose from: genome, transcriptome, proteins"
        )

    input_file = Path(input_file).resolve()
    database_dir = Path(database_dir).resolve()
    output_dir = Path(output_dir).resolve()

    if not input_file.is_file() or input_file.stat().st_size == 0:
        raise FileNotFoundError(
            f"Input FASTA missing or empty: {input_file}"
        )

    # lineage_dir = database_dir / "lineages" / lineage
    lineage_dir = database_dir / lineage

    if not lineage_dir.is_dir():
        raise FileNotFoundError(
            f"BUSCO database not found: {lineage_dir}"
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    docker_image = "staphb/busco:6.1.0"

    cmd = [
        "docker", "run", "--rm",
        "-v", f"{input_file}:/input.fasta:ro",
        "-v", f"{output_dir}:/output",
        "-v", f"{database_dir}:/busco_db:ro",
        docker_image,
        "busco",
        "-i", "/input.fasta",
        "-o", "busco_result",
        "--out_path", "/output",
        "-l", f"/busco_db/{lineage}",
        "-m", mode,
        "--cpu", str(threads),
        "--offline", 
        "-f"
    ]

    subprocess.run(cmd, check=True)

    return str(output_dir / "busco_result")


def busco_plot(busco_result_dir, percentages=True):

    busco_result_dir = Path(busco_result_dir).resolve()

    if not busco_result_dir.is_dir():
        raise FileNotFoundError(
            f"BUSCO result not found: {busco_result_dir}"
        )

    docker_image = "staphb/busco:6.1.0"
    # docker_image = "ezlabgva/busco:v6.1.0_cv3"

    cmd = [
        "docker", "run", "--rm",
        "-v", f"{busco_result_dir.parent}:/output",
        docker_image,
        "busco",
        "--plot", f"/output/{busco_result_dir.name}"
    ]

    if percentages:
        cmd.append("--plot_percentages")

    subprocess.run(cmd, check=True)

    return str(busco_result_dir)