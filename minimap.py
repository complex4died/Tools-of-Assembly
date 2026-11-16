from pathlib import Path
import subprocess


def mapping_minimap2(
    input_file,
    reference_file,
    output_dir,
    threads=128,
    memory="10G"
):
    """
    Map ONT reads to an assembled reference genome.

    Parameters
    ----------
    input_file : str or Path
        ONT FASTQ / FASTQ.GZ reads.
    reference_file : str or Path
        Assembled reference genome FASTA.
    output_dir : str or Path
        Output directory.
    threads : int
        Number of threads.
    memory : str
        Amount of memory to allocate.

    Returns
    -------
    str
        Path to sorted BAM file.
    """

    docker_image = "staphb/minimap2:2.31"

    # 1. Paths
    input_file = Path(input_file).resolve()
    reference_file = Path(reference_file).resolve()
    output_dir = Path(output_dir).resolve()

    if not input_file.is_file():
        raise FileNotFoundError(input_file)

    if not reference_file.is_file():
        raise FileNotFoundError(reference_file)

    if threads < 1:
        raise ValueError("threads must be >= 1")

    output_dir.mkdir(parents=True, exist_ok=True)

    bam_file = output_dir / "mapped.sorted.bam"
    bai_file = output_dir / "mapped.sorted.bam.bai"

    flagstat_file = output_dir / "flagstat.txt"
    coverage_file = output_dir / "coverage.txt"

    # 2. Skip completed mapping
    if (
        bam_file.is_file()
        and bam_file.stat().st_size > 0
        and bai_file.is_file()
        and bai_file.stat().st_size > 0
    ):
        print(f"[Minimap2] Existing BAM: {bam_file}")

    else:
        # 3. Minimap2 Docker command
        cmd_minimap2 = [
            "docker", "run", "--rm",
            "-v", f"{input_file}:/input.fastq.gz:ro",
            "-v", f"{reference_file}:/reference.fasta:ro",
            docker_image,
            "minimap2",
            "-ax", "map-ont",
            "-t", str(threads),
            "/reference.fasta",
            "/input.fastq.gz"
        ]

        # 4. SAMtools sorting
        docker_image_samtools = "staphb/samtools:1.24"
        
        cmd_sort = [
            "docker", "run", "--rm", "-i",
            "-v", f"{output_dir}:/output",
            docker_image_samtools,
            "samtools", "sort",
            "-@", str(min(threads, 16)),
            "-m", memory,
            "-T", "/output/sort_tmp",
            "-o", "/output/mapped.sorted.bam",
            "-"
        ]

        print("[Minimap2] Mapping ONT reads...")

        with subprocess.Popen(
            cmd_minimap2,
            stdout=subprocess.PIPE
        ) as p1:

            with subprocess.Popen(
                cmd_sort,
                stdin=p1.stdout
            ) as p2:

                # Allow SIGPIPE if downstream exits
                p1.stdout.close()

                sort_status = p2.wait()

            map_status = p1.wait()

        if map_status != 0 or sort_status != 0:
            raise RuntimeError(
                f"Mapping failed: minimap2={map_status}, "
                f"samtools sort={sort_status}"
            )

        # 5. BAM index
        subprocess.run(
            [
                "samtools", "index",
                "-@", str(min(threads, 16)),
                str(bam_file)
            ],
            check=True
        )

    # 6. Mapping statistics
    with open(flagstat_file, "w") as f:
        subprocess.run(
            [
                "samtools", "flagstat",
                "-@", str(min(threads, 16)),
                str(bam_file)
            ],
            stdout=f,
            check=True
        )

    # 7. Per-contig coverage
    with open(coverage_file, "w") as f:
        subprocess.run(
            [
                "samtools", "coverage",
                str(bam_file)
            ],
            stdout=f,
            check=True
        )

    print("[Minimap2] Completed")
    print(f"BAM: {bam_file}")
    print(f"Flagstat: {flagstat_file}")
    print(f"Coverage: {coverage_file}")

    return str(bam_file)