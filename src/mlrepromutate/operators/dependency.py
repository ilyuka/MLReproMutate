import re
from pathlib import Path

from mlrepromutate.models import MutationCandidate
from mlrepromutate.operators.base import MutationOperator

_EXACT_PIN_PATTERN = re.compile(
    r"^(?P<prefix>\s*)"
    r"(?P<package>[A-Za-z0-9_.-]+)"
    r"=="
    r"(?P<version>[^\s;#]+)"
    r"(?P<suffix>.*)$"
)


class RelaxRequirementsPinOperator(MutationOperator):
    """Relax exact dependency pins in requirements files."""

    @property
    def name(self) -> str:
        return "relax_requirements_pin"

    @property
    def category(self) -> str:
        return "dependency"

    def detect(self, project_root: Path) -> list[MutationCandidate]:
        candidates: list[MutationCandidate] = []

        for requirements_file in sorted(project_root.glob("requirements*.txt")):
            if not requirements_file.is_file():
                continue

            lines = requirements_file.read_text(encoding="utf-8").splitlines()

            for line_number, line in enumerate(lines, start=1):
                match = _EXACT_PIN_PATTERN.match(line)

                if match is None:
                    continue

                package = match.group("package")
                version = match.group("version")

                candidates.append(
                    MutationCandidate(
                        operator=self.name,
                        category=self.category,
                        target=requirements_file.relative_to(project_root),
                        description=(
                            f"Relax exact dependency pin for {package} "
                            f"from =={version} to >={version}."
                        ),
                        metadata={
                            "package": package,
                            "version": version,
                            "line_number": line_number,
                        },
                    )
                )

        return candidates

    def apply(
        self,
        project_root: Path,
        candidate: MutationCandidate,
    ) -> None:
        if candidate.operator != self.name:
            raise ValueError(
                f"Candidate belongs to operator {candidate.operator!r}, "
                f"not {self.name!r}."
            )

        target = project_root / candidate.target

        if not target.exists():
            raise FileNotFoundError(f"Mutation target does not exist: {target}")

        line_number = candidate.metadata.get("line_number")

        if not isinstance(line_number, int):
            raise TypeError("Candidate line number must be an integer.")

        package = candidate.metadata.get("package")
        version = candidate.metadata.get("version")

        if not isinstance(package, str) or not isinstance(version, str):
            raise TypeError("Candidate dependency metadata is invalid.")

        lines = target.read_text(encoding="utf-8").splitlines(keepends=True)

        index = line_number - 1

        if index < 0 or index >= len(lines):
            raise ValueError("Candidate line number is outside the target file.")

        original_line = lines[index]

        expected = f"{package}=={version}"

        if expected not in original_line:
            raise ValueError(
                "Mutation target no longer matches the detected dependency pin."
            )

        lines[index] = original_line.replace(
            expected,
            f"{package}>={version}",
            1,
        )

        target.write_text("".join(lines), encoding="utf-8")