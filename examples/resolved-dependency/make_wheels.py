from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).parent
WHEELHOUSE = ROOT / "wheelhouse"


def build_wheel(version: str) -> None:
    distribution = "mlrm_demo_dep"
    dist_info = f"{distribution}-{version}.dist-info"
    filename = f"{distribution}-{version}-py3-none-any.whl"
    output = WHEELHOUSE / filename

    files = {
        f"{distribution}/__init__.py": (
            f'__version__ = "{version}"\n'
        ),
        f"{dist_info}/METADATA": (
            "Metadata-Version: 2.1\n"
            "Name: mlrm-demo-dep\n"
            f"Version: {version}\n"
        ),
        f"{dist_info}/WHEEL": (
            "Wheel-Version: 1.0\n"
            "Generator: MLReproMutate fixture\n"
            "Root-Is-Purelib: true\n"
            "Tag: py3-none-any\n"
        ),
    }

    record_paths = list(files)
    record_paths.append(f"{dist_info}/RECORD")

    record = "".join(
        f"{path},,\n"
        for path in record_paths
    )

    with ZipFile(output, "w", ZIP_DEFLATED) as wheel:
        for path, content in files.items():
            wheel.writestr(path, content)

        wheel.writestr(
            f"{dist_info}/RECORD",
            record,
        )


def main() -> None:
    WHEELHOUSE.mkdir(exist_ok=True)

    build_wheel("1.0.0")
    build_wheel("1.1.0")

    print(f"Created wheels in {WHEELHOUSE}")


if __name__ == "__main__":
    main()
