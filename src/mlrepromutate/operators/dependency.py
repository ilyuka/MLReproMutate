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
    """Relax exact requirements pins from ``==`` to ``>=``.

    Args:
        requirements_file: Optional project-relative requirements file. When
            omitted, matching top-level ``requirements*.txt`` files are used.

    Attributes:
        requirements_file: Optional project-relative file restriction.
    """

    def __init__(
        self,
        requirements_file: Path | None = None,
    ) -> None:
        self.requirements_file = requirements_file

    @property
    def name(self) -> str:
        """Return the unique operator name."""
        return "relax_requirements_pin"

    @property
    def category(self) -> str:
        """Return the ``dependency`` threat category."""
        return "dependency"

    def detect(self, project_root: Path) -> list[MutationCandidate]:
        """Detect exact pins in supported requirements files.

        Args:
            project_root: Root directory of the project to inspect.

        Returns:
            Candidates in requirements-file and line order.

        Raises:
            ValueError: ``requirements_file`` is invalid or outside the
                project.
            FileNotFoundError: The requested requirements file does not exist.
        """
        project_root = project_root.resolve()
        candidates: list[MutationCandidate] = []

        requirements_files = self._get_requirements_files(project_root)

        for requirements_file in requirements_files:
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

    def _get_requirements_files(
        self,
        project_root: Path,
    ) -> list[Path]:
        if self.requirements_file is None:
            return sorted(
                path
                for path in project_root.glob("requirements*.txt")
                if path.is_file()
            )

        if self.requirements_file.is_absolute():
            raise ValueError(
                "Requirements file must be relative to the project root."
            )

        target = (project_root / self.requirements_file).resolve()

        try:
            target.relative_to(project_root)
        except ValueError as exc:
            raise ValueError(
                "Requirements file must be inside the project root."
            ) from exc

        if not target.exists():
            raise FileNotFoundError(
                f"Requirements file does not exist: {self.requirements_file}"
            )

        if not target.is_file():
            raise ValueError(
                f"Requirements path is not a file: {self.requirements_file}"
            )

        return [target]

    def apply(
        self,
        project_root: Path,
        candidate: MutationCandidate,
    ) -> None:
        """Relax the exact pin represented by a detected candidate.

        Args:
            project_root: Root directory of the workspace to modify.
            candidate: Candidate previously detected by this operator.

        Raises:
            ValueError: The candidate is incompatible or no longer matches.
            TypeError: Required candidate metadata has an invalid type.
            FileNotFoundError: The candidate target does not exist.
        """
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
