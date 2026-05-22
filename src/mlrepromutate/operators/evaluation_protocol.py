import ast
from pathlib import Path

from mlrepromutate.models import MutationCandidate
from mlrepromutate.operators.base import MutationOperator

_SUPPORTED_SPLITTERS = {
    "KFold",
    "StratifiedKFold",
    "RepeatedKFold",
    "RepeatedStratifiedKFold",
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


class ChangeCrossValidationFoldCountOperator(MutationOperator):
    """Increase an explicit cross-validation fold count by one."""

    def __init__(
        self,
        python_file: Path | None = None,
    ) -> None:
        self.python_file = python_file

    @property
    def name(self) -> str:
        return "change_cross_validation_fold_count"

    @property
    def category(self) -> str:
        return "evaluation_protocol"

    def detect(
        self,
        project_root: Path,
    ) -> list[MutationCandidate]:
        """Detect supported CV splitters with literal n_splits values."""

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

            bindings = _find_cross_validation_bindings(tree)

            if not bindings:
                continue

            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue

                call_name = _qualified_name(node.func)

                if call_name not in bindings:
                    continue

                keyword = _find_n_splits_keyword(node)

                if keyword is None:
                    continue

                value_node = keyword.value

                if not _is_valid_fold_count_literal(value_node):
                    continue

                original_n_splits = value_node.value
                mutated_n_splits = original_n_splits + 1
                splitter = bindings[call_name]

                candidates.append(
                    MutationCandidate(
                        operator=self.name,
                        category=self.category,
                        target=python_file.relative_to(project_root),
                        description=(
                            f"Change {splitter} cross-validation folds "
                            f"from {original_n_splits} "
                            f"to {mutated_n_splits}."
                        ),
                        metadata={
                            "library": "scikit-learn",
                            "splitter": splitter,
                            "call": call_name,
                            "original_n_splits": original_n_splits,
                            "mutated_n_splits": mutated_n_splits,
                            "line_number": node.lineno,
                            "n_splits_line_number": value_node.lineno,
                            "n_splits_col_offset": value_node.col_offset,
                            "n_splits_end_line_number": (
                                value_node.end_lineno
                            ),
                            "n_splits_end_col_offset": (
                                value_node.end_col_offset
                            ),
                        },
                    )
                )

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
        """Apply a detected cross-validation fold-count mutation."""

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

        call_name = candidate.metadata.get("call")
        splitter = candidate.metadata.get("splitter")
        original_n_splits = candidate.metadata.get(
            "original_n_splits"
        )
        mutated_n_splits = candidate.metadata.get(
            "mutated_n_splits"
        )

        positions = (
            candidate.metadata.get("n_splits_line_number"),
            candidate.metadata.get("n_splits_col_offset"),
            candidate.metadata.get("n_splits_end_line_number"),
            candidate.metadata.get("n_splits_end_col_offset"),
        )

        if not isinstance(call_name, str):
            raise TypeError(
                "Evaluation metadata must contain a call name."
            )

        if not isinstance(splitter, str):
            raise TypeError(
                "Evaluation metadata must contain a splitter name."
            )

        if not _is_integer_fold_count(original_n_splits):
            raise TypeError(
                "Evaluation metadata must contain a valid original "
                "fold count."
            )

        if not _is_integer_fold_count(mutated_n_splits):
            raise TypeError(
                "Evaluation metadata must contain a valid mutated "
                "fold count."
            )

        if mutated_n_splits != original_n_splits + 1:
            raise ValueError(
                "Mutated fold count must be exactly one greater "
                "than the original."
            )

        if not all(isinstance(value, int) for value in positions):
            raise TypeError(
                "Evaluation metadata must contain integer "
                "source positions."
            )

        (
            line_number,
            col_offset,
            end_line_number,
            end_col_offset,
        ) = positions

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

        bindings = _find_cross_validation_bindings(tree)
        matching_node: ast.Constant | None = None

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            current_call = _qualified_name(node.func)

            if current_call != call_name:
                continue

            if bindings.get(current_call) != splitter:
                continue

            keyword = _find_n_splits_keyword(node)

            if keyword is None:
                continue

            value_node = keyword.value

            if not _is_valid_fold_count_literal(value_node):
                continue

            if (
                value_node.lineno == line_number
                and value_node.col_offset == col_offset
                and value_node.end_lineno == end_line_number
                and value_node.end_col_offset == end_col_offset
                and value_node.value == original_n_splits
            ):
                matching_node = value_node
                break

        if matching_node is None:
            raise ValueError(
                "Cross-validation candidate no longer matches "
                "the target source."
            )

        mutated_source = _replace_integer_literal(
            source,
            matching_node,
            mutated_n_splits,
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


def _find_cross_validation_bindings(
    tree: ast.AST,
) -> dict[str, str]:
    bindings: dict[str, str] = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name != "sklearn.model_selection":
                    continue

                if alias.asname is not None:
                    module_name = alias.asname
                else:
                    module_name = "sklearn.model_selection"

                for splitter in _SUPPORTED_SPLITTERS:
                    bindings[f"{module_name}.{splitter}"] = splitter

        elif isinstance(node, ast.ImportFrom):
            if node.module == "sklearn.model_selection":
                for alias in node.names:
                    if alias.name not in _SUPPORTED_SPLITTERS:
                        continue

                    bindings[
                        alias.asname or alias.name
                    ] = alias.name

            elif node.module == "sklearn":
                for alias in node.names:
                    if alias.name != "model_selection":
                        continue

                    module_name = alias.asname or alias.name

                    for splitter in _SUPPORTED_SPLITTERS:
                        bindings[
                            f"{module_name}.{splitter}"
                        ] = splitter

    return bindings


def _find_n_splits_keyword(
    node: ast.Call,
) -> ast.keyword | None:
    for keyword in node.keywords:
        if keyword.arg == "n_splits":
            return keyword

    return None


def _qualified_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.Attribute):
        parent = _qualified_name(node.value)

        if parent is None:
            return None

        return f"{parent}.{node.attr}"

    return None


def _is_valid_fold_count_literal(
    node: ast.expr,
) -> bool:
    return (
        isinstance(node, ast.Constant)
        and _is_integer_fold_count(node.value)
    )


def _is_integer_fold_count(value: object) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and value >= 2
    )


def _replace_integer_literal(
    source: str,
    node: ast.Constant,
    replacement: int,
) -> str:
    if node.end_lineno is None or node.end_col_offset is None:
        raise ValueError(
            "Python AST does not contain fold-count source positions."
        )

    if node.lineno != node.end_lineno:
        raise ValueError(
            "Multiline integer fold-count literals are not supported."
        )

    lines = source.splitlines(keepends=True)
    line_index = node.lineno - 1

    if line_index >= len(lines):
        raise ValueError(
            "Fold-count source position is outside the target file."
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
