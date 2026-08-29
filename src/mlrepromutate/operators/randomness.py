import ast
from pathlib import Path

from mlrepromutate.models import MutationCandidate
from mlrepromutate.operators.base import MutationOperator

_SUPPORTED_CALLS = {
    "random.seed": "random",
    "np.random.seed": "numpy",
    "numpy.random.seed": "numpy",
    "torch.manual_seed": "torch",
}

_IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "build",
    "dist",
}


class ChangePythonRandomSeedOperator(MutationOperator):
    """Change supported literal Python random seeds from ``N`` to ``N + 1``.

    Args:
        python_file: Optional project-relative Python file to inspect. When
            omitted, the operator searches Python files under the project.

    Attributes:
        python_file: Optional project-relative file restriction.
    """

    def __init__(
        self,
        python_file: Path | None = None,
    ) -> None:
        self.python_file = python_file

    @property
    def name(self) -> str:
        """Return the unique operator name."""
        return "change_python_random_seed"

    @property
    def category(self) -> str:
        """Return the ``randomness`` threat category."""
        return "randomness"

    def detect(
        self,
        project_root: Path,
    ) -> list[MutationCandidate]:
        """Detect supported literal seed calls.

        Args:
            project_root: Root directory of the project to inspect.

        Returns:
            Candidates ordered by target path and source line.

        Raises:
            ValueError: ``python_file`` is absolute or outside the project.
            FileNotFoundError: The requested ``python_file`` does not exist.
        """

        project_root = project_root.resolve()
        candidates: list[MutationCandidate] = []

        for python_file in self._get_python_files(project_root):
            source = python_file.read_text(encoding="utf-8")

            try:
                tree = ast.parse(
                    source,
                    filename=str(python_file),
                )
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue

                call_name = _qualified_name(node.func)

                if call_name not in _SUPPORTED_CALLS:
                    continue

                if not node.args:
                    continue

                seed_node = node.args[0]

                if not _is_integer_literal(seed_node):
                    continue

                original_seed = seed_node.value

                candidate = MutationCandidate(
                    operator=self.name,
                    category=self.category,
                    target=python_file.relative_to(project_root),
                    description=(
                        f"Change random seed for {call_name} "
                        f"from {original_seed} to {original_seed + 1}."
                    ),
                    metadata={
                        "library": _SUPPORTED_CALLS[call_name],
                        "call": call_name,
                        "original_seed": original_seed,
                        "mutated_seed": original_seed + 1,
                        "line_number": node.lineno,
                        "seed_line_number": seed_node.lineno,
                        "seed_col_offset": seed_node.col_offset,
                        "seed_end_line_number": seed_node.end_lineno,
                        "seed_end_col_offset": seed_node.end_col_offset,
                    },
                )

                candidates.append(candidate)

        return sorted(
            candidates,
            key=lambda candidate: (
                str(candidate.target),
                int(candidate.metadata["line_number"]),
            ),
        )

    def apply(
        self,
        project_root: Path,
        candidate: MutationCandidate,
    ) -> None:
        """Apply a detected seed mutation.

        Args:
            project_root: Root directory of the workspace to modify.
            candidate: Candidate previously detected by this operator.

        Raises:
            ValueError: The candidate is incompatible or no longer matches.
            TypeError: Required candidate metadata has an invalid type.
            FileNotFoundError: The candidate target is not a file.
        """

        if candidate.operator != self.name:
            raise ValueError(
                f"Candidate belongs to operator {candidate.operator!r}, "
                f"not {self.name!r}."
            )

        project_root = project_root.resolve()
        target = (project_root / candidate.target).resolve()

        try:
            target.relative_to(project_root)
        except ValueError as exc:
            raise ValueError(
                "Candidate target must be inside the project root."
            ) from exc

        if not target.is_file():
            raise FileNotFoundError(
                f"Candidate target does not exist: {candidate.target}"
            )

        original_seed = candidate.metadata.get("original_seed")
        mutated_seed = candidate.metadata.get("mutated_seed")
        call_name = candidate.metadata.get("call")
        seed_line_number = candidate.metadata.get("seed_line_number")
        seed_col_offset = candidate.metadata.get("seed_col_offset")
        seed_end_line_number = candidate.metadata.get(
            "seed_end_line_number"
        )
        seed_end_col_offset = candidate.metadata.get(
            "seed_end_col_offset"
        )

        if (
            not isinstance(original_seed, int)
            or isinstance(original_seed, bool)
            or not isinstance(mutated_seed, int)
            or isinstance(mutated_seed, bool)
        ):
            raise TypeError(
                "Seed metadata must contain integer seed values."
            )

        if not isinstance(call_name, str):
            raise TypeError(
                "Seed metadata must contain a call name."
            )

        positions = (
            seed_line_number,
            seed_col_offset,
            seed_end_line_number,
            seed_end_col_offset,
        )

        if not all(isinstance(value, int) for value in positions):
            raise TypeError(
                "Seed metadata must contain integer source positions."
            )

        source = target.read_text(encoding="utf-8")

        try:
            tree = ast.parse(
                source,
                filename=str(target),
            )
        except SyntaxError as exc:
            raise ValueError(
                "Candidate target is no longer valid Python."
            ) from exc

        matching_seed_node: ast.Constant | None = None

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            if _qualified_name(node.func) != call_name:
                continue

            if not node.args:
                continue

            seed_node = node.args[0]

            if not _is_integer_literal(seed_node):
                continue

            if (
                seed_node.lineno == seed_line_number
                and seed_node.col_offset == seed_col_offset
                and seed_node.end_lineno == seed_end_line_number
                and seed_node.end_col_offset == seed_end_col_offset
                and seed_node.value == original_seed
            ):
                matching_seed_node = seed_node
                break

        if matching_seed_node is None:
            raise ValueError(
                "Seed candidate no longer matches the target source."
            )

        mutated_source = _replace_integer_literal(
            source,
            matching_seed_node,
            mutated_seed,
        )

        target.write_text(
            mutated_source,
            encoding="utf-8",
        )

    def _get_python_files(
        self,
        project_root: Path,
    ) -> list[Path]:
        if self.python_file is not None:
            if self.python_file.is_absolute():
                raise ValueError(
                    "Python file must be relative to the project root."
                )

            target = (project_root / self.python_file).resolve()

            try:
                target.relative_to(project_root)
            except ValueError as exc:
                raise ValueError(
                    "Python file must be inside the project root."
                ) from exc

            if not target.exists():
                raise FileNotFoundError(
                    f"Python file does not exist: {self.python_file}"
                )

            if not target.is_file():
                raise ValueError(
                    f"Python path is not a file: {self.python_file}"
                )

            if target.suffix != ".py":
                raise ValueError(
                    f"Python target must end in .py: {self.python_file}"
                )

            return [target]

        return sorted(
            path
            for path in project_root.rglob("*.py")
            if path.is_file()
            and not any(
                part in _IGNORED_DIRECTORIES
                for part in path.relative_to(project_root).parts
            )
        )


def _qualified_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.Attribute):
        parent = _qualified_name(node.value)

        if parent is None:
            return None

        return f"{parent}.{node.attr}"

    return None


def _is_integer_literal(node: ast.expr) -> bool:
    return (
        isinstance(node, ast.Constant)
        and isinstance(node.value, int)
        and not isinstance(node.value, bool)
    )


def _replace_integer_literal(
    source: str,
    node: ast.Constant,
    replacement: int,
) -> str:
    if node.end_lineno is None or node.end_col_offset is None:
        raise ValueError(
            "Python AST does not contain seed source positions."
        )

    if node.lineno != node.end_lineno:
        raise ValueError(
            "Multiline integer seed literals are not supported."
        )

    lines = source.splitlines(keepends=True)
    line_index = node.lineno - 1

    if line_index >= len(lines):
        raise ValueError(
            "Seed source position is outside the target file."
        )

    line = lines[line_index]

    start = _byte_offset_to_character_offset(
        line,
        node.col_offset,
    )
    end = _byte_offset_to_character_offset(
        line,
        node.end_col_offset,
    )

    lines[line_index] = (
        line[:start]
        + str(replacement)
        + line[end:]
    )

    return "".join(lines)


def _byte_offset_to_character_offset(
    line: str,
    byte_offset: int,
) -> int:
    encoded = line.encode("utf-8")
    prefix = encoded[:byte_offset]

    return len(prefix.decode("utf-8"))
