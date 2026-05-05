from __future__ import annotations

from pathlib import Path
import shutil
import sys
from urllib.request import urlretrieve
import zipfile

from research.io.text import write_text
from research.util.jlog import jline
from research.util.logger import Logger
from research.util.progress import make_progress
from research.util.run import Run, make_run, run_err, run_ok, task_name


def clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)

    path.mkdir(parents=True, exist_ok=False)


def fetch_zip(url: str, path: Path, logger: Logger) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(jline("profile", "user", "fetch", {"url": url, "path": str(path)}))
    urlretrieve(url, path)
    return path


def unzip_file(path: Path, target: Path, logger: Logger) -> Path:
    logger.info(
        jline("profile", "user", "unzip", {"path": str(path), "target": str(target)})
    )

    with zipfile.ZipFile(path, "r") as file:
        file.extractall(target)

    data = [item for item in target.iterdir() if item.is_dir()]

    if len(data) != 1:
        raise RuntimeError("archive root mismatch")

    return data[0]


def skip_path(path: Path) -> bool:
    for part in path.parts:
        if part.startswith("."):
            return True

    return False


def md_list(source: Path) -> list[Path]:
    data: list[Path] = []

    for path in sorted(source.rglob("*.md")):
        rel = path.relative_to(source)

        if skip_path(rel):
            continue

        data.append(path)

    return data


def copy_md(source: Path, target: Path, logger: Logger) -> list[Path]:
    data = md_list(source)
    output: list[Path] = []
    progress = make_progress(logger, "profile", len(data))

    progress.start()

    for path in data:
        rel = path.relative_to(source)
        out = target / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, out)
        output.append(out)
        logger.info(
            jline(
                "profile",
                "user",
                "copy",
                {
                    "source": str(path),
                    "target": str(out),
                },
            )
        )
        progress.step(1)

    progress.finish()
    return output


def manifest_text(url: str, source: Path, target: Path, output: list[Path]) -> str:
    body: list[str] = []

    body.append("# User Profile Manifest\n")
    body.append("## Source\n")
    body.append(f"- url: {url}")
    body.append(f"- source: {source}")
    body.append(f"- target: {target}")
    body.append(f"- count: {len(output)}")
    body.append("\n## File\n")

    for path in output:
        rel = path.relative_to(target)
        body.append(f"- [{rel}](./{rel})")

    body.append("")
    return "\n".join(body)


def write_manifest(url: str, source: Path, target: Path, output: list[Path]) -> Path:
    path = target / "_manifest.md"

    if path.exists():
        raise FileExistsError(str(path))

    text = manifest_text(url, source, target, output)
    return write_text(path, text)


def write_user(
    root: Path, url: str, temp: Path, target: Path, logger: Logger
) -> list[Path]:
    clean_dir(temp)
    clean_dir(target)

    archive = temp / "source.zip"
    source = fetch_zip(url, archive, logger)
    folder = unzip_file(source, temp / "extract", logger)

    output = copy_md(folder, target, logger)
    output.append(write_manifest(url, folder, target, output))

    return output


def fail(run: Run, comp: str, error: BaseException) -> None:
    run.logger.error(
        jline(
            "script",
            comp,
            "error",
            {
                "type": type(error).__name__,
                "message": str(error),
                "run": run.run_dir,
            },
        )
    )
    run_err(run, error, {"comp": comp})
    raise error


def main(argv: list[str]) -> None:
    if len(argv) != 5:
        raise ValueError("usage: write.py ROOT URL TEMP TARGET")

    root = Path(argv[1]).resolve()
    url = argv[2]
    temp = Path(argv[3])
    target = Path(argv[4])
    script = Path(__file__).resolve()
    task = task_name(root, script)

    run = make_run(
        root=root,
        name=task,
        params={
            "task": task,
            "url": url,
            "temp": str(temp),
            "target": str(target),
        },
        script=script,
        src=root / "src",
        config=None,
    )

    try:
        run.logger.info(
            jline(
                "script",
                "profile",
                "start",
                {
                    "root": str(root),
                    "url": url,
                    "temp": str(temp),
                    "target": str(target),
                    "script": str(script),
                    "run": run.run_dir,
                },
            )
        )

        output = write_user(root, url, temp, target, run.logger)

        run.logger.info(
            jline(
                "script",
                "profile",
                "ok",
                {
                    "output": len(output),
                    "target": str(target),
                    "run": run.run_dir,
                },
            )
        )

        run_ok(
            run,
            {
                "task": task,
                "url": url,
                "temp": str(temp),
                "target": str(target),
                "output": len(output),
            },
        )

    except (
        ValueError,
        KeyError,
        FileNotFoundError,
        NotADirectoryError,
        RuntimeError,
        TypeError,
        zipfile.BadZipFile,
    ) as error:
        fail(run, "profile", error)


if __name__ == "__main__":
    main(sys.argv)
