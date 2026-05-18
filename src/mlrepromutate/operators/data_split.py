import ast
from pathlib import Path

from mlrepromutate.models import MutationCandidate
from mlrepromutate.operators.base import MutationOperator

_CANONICAL_CALL = "sklearn.model_selection.train_test_split"

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


class RemoveTrainTestSplitStratificationOperator(MutationOperator):
    """Disable explicit stratification in sklearn train_test_split calls."""

    def __init__(
        self,
        python_file: Path | None = None,
    ) -> None:
        self.python_file = python_file

    @property
    def name(self) -> str:
        return "remove_train_test_split_stratification"

    @property
    def category(self) -> str:
        return "data_splitting"

    def detect(
        self,
        project_root: Path,
    ) -> list[MutationCandidate]:
        """Detect sklearn train_test_split calls with stratify enabled."""

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

            supported_calls = _find_train_test_split_bindings(tree)

            if not supported_calls:
                continue

            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue

                call_name = _qualified_name(node.func)

                if call_name not in supported_calls:
                    continue

                stratify_keyword = _find_stratify_keyword(node)

                if stratify_keyword is None:
                    continue

                stratify_node = stratify_keyword.value

                if _is_none_literal(stratify_node):
                    continue

                original_stratify = ast.get_source_segment(
                    source,
                    stratify_node,
                )

                if original_stratify is None:
                    continue

                candidates.append(
                    MutationCandidate(
                        operator=self.name,
                        category=self.category,
                        target=python_file.relative_to(project_root),
                        description=(
                            "Disable train/test split stratification "
                            f"for {call_name}."
                        ),
                        metadata={
                            "library": "scikit-learn",
                            "call": call_name,
                            "canonical_call": _CANONICAL_CALL,
                            "original_stratify": original_stratify,
                            "mutated_stratify": "None",
                            "original_stratify_ast": ast.dump(
                                stratify_node,
                                include_attributes=False,
                            ),
                            "line_number": node.lineno,
                            "stratify_line_number": stratify_node.lineno,
                            "stratify_col_offset": (
                                stratify_node.col_offset
                            ),
                            "stratify_end_line_number": (
                                stratify_node.end_lineno
                            ),
                            "stratify_end_col_offset": (
                                stratify_node.end_col_offset
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
        """Replace the detected stratify expression with None."""

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
        original_stratify = candidate.metadata.get(
            "original_stratify"
        )
        mutated_stratify = candidate.metadata.get(
            "mutated_stratify"
        )
        original_stratify_ast = candidate.metadata.get(
            "original_stratify_ast"
        )

        positions = (
            candidate.metadata.get("stratify_line_number"),
            candidate.metadata.get("stratify_col_offset"),
            candidate.metadata.get("stratify_end_line_number"),
            candidate.metadata.get("stratify_end_col_offset"),
        )

        if not isinstance(call_name, str):
            raise TypeError(
                "Data-split metadata must contain a call name."
            )

        if not isinstance(original_stratify, str):
            raise TypeError(
                "Data-split metadata must contain the original expression."
            )

        if mutated_stratify != "None":
            raise ValueError(
                "Data-split mutation must replace stratify with None."
            )

        if not isinstance(original_stratify_ast, str):
            raise TypeError(
                "Data-split metadata must contain the original AST."
            )

        if not all(isinstance(value, int) for value in positions):
            raise TypeError(
                "Data-split metadata must contain integer source positions."
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

        supported_calls = _find_train_test_split_bindings(tree)
        matching_node: ast.expr | None = None

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            if _qualified_name(node.func) != call_name:
                continue

            if call_name not in supported_calls:
                continue

            keyword = _find_stratify_keyword(node)

            if keyword is None:
                continue

            value = keyword.value

            if (
                value.lineno != line_number
                or value.col_offset != col_offset
                or value.end_lineno != end_line_number
                or value.end_col_offset != end_col_offset
            ):
                continue

            current_source = ast.get_source_segment(source, value)

            if current_source != original_stratify:
                continue

            if (
                ast.dump(value, include_attributes=False)
                != original_stratify_ast
            ):
                continue

            matching_node = value
            break

        if matching_node is None:
            raise ValueError(
                "Data-split candidate no longer matches the target source."
            )

        mutated_source = _replace_expression(
            source,
            matching_node,
            "None",
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


def _find_train_test_split_bindings(
    tree: ast.AST,
) -> set[str]:
    bindings: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name != "sklearn.model_selection":
                    continue

                if alias.asname is not None:
                    bindings.add(
                        f"{alias.asname}.train_test_split"
                    )
                else:
                    bindings.add(_CANONICAL_CALL)

        elif isinstance(node, ast.ImportFrom):
            if node.module == "sklearn.model_selection":
                for alias in node.names:
                    if alias.name != "train_test_split":
                        continue

                    bindings.add(
                        alias.asname or "train_test_split"
                    )

            elif node.module == "sklearn":
                for alias in node.names:
                    if alias.name != "model_selection":
                        continue

                    module_name = alias.asname or "model_selection"
                    bindings.add(
                        f"{module_name}.train_test_split"
                    )

    return bindings


def _find_stratify_keyword(
    node: ast.Call,
) -> ast.keyword | None:
    for keyword in node.keywords:
        if keyword.arg == "stratify":
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


def _is_none_literal(node: ast.expr) -> bool:
    return (
        isinstance(node, ast.Constant)
        and node.value is None
    )


def _replace_expression(
    source: str,
    node: ast.expr,
    replacement: str,
) -> str:
    if node.end_lineno is None or node.end_col_offset is None:
        raise ValueError(
            "Python AST does not contain expression source positions."
        )

    lines = source.splitlines(keepends=True)

    start_index = node.lineno - 1
    end_index = node.end_lineno - 1

    if start_index >= len(lines) or end_index >= len(lines):
        raise ValueError(
            "Expression source position is outside the target file."
        )

    start_line = lines[start_index]
    end_line = lines[end_index]

    start_offset = _byte_offset_to_character_offset(
        start_line,
        node.col_offset,
    )
    end_offset = _byte_offset_to_character_offset(
        end_line,
        node.end_col_offset,
    )

    replacement_line = (
        start_line[:start_offset]
        + replacement
        + end_line[end_offset:]
    )

    lines[start_index:end_index + 1] = [replacement_line]

    return "".join(lines)


def _byte_offset_to_character_offset(
    line: str,
    byte_offset: int,
) -> int:
    encoded = line.encode("utf-8")
    prefix = encoded[:byte_offset]

    return len(prefix.decode("utf-8"))
