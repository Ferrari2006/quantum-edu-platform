from __future__ import annotations

import ast
from typing import Any


QUANTUM_GATE_METHODS = {
    "h",
    "x",
    "y",
    "z",
    "s",
    "sdg",
    "t",
    "tdg",
    "rx",
    "ry",
    "rz",
    "cx",
    "cz",
    "swap",
    "measure",
}


def analyze_qiskit_code(code: str) -> dict[str, Any]:
    """Perform safe static checks without importing or executing user code."""

    diagnostics: list[dict[str, Any]] = []
    normalized = (code or "").strip()
    if not normalized:
        return {"analyzed": False, "diagnostics": []}

    try:
        tree = ast.parse(normalized)
    except SyntaxError as exc:
        return {
            "analyzed": True,
            "diagnostics": [
                {
                    "severity": "error",
                    "code": "python_syntax_error",
                    "line": exc.lineno,
                    "message": exc.msg,
                }
            ],
        }

    imports_qiskit = any(
        (
            isinstance(node, ast.Import)
            and any(alias.name == "qiskit" or alias.name.startswith("qiskit.") for alias in node.names)
        )
        or (
            isinstance(node, ast.ImportFrom)
            and bool(node.module)
            and (node.module == "qiskit" or node.module.startswith("qiskit."))
        )
        for node in ast.walk(tree)
    )
    if not imports_qiskit:
        diagnostics.append(
            {
                "severity": "warning",
                "code": "qiskit_import_not_found",
                "line": None,
                "message": "未检测到 Qiskit 导入，请确认代码片段包含完整上下文。",
            }
        )

    circuit_sizes: dict[str, int] = {}
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        value = node.value
        target = node.targets[0] if isinstance(node, ast.Assign) and node.targets else node.target
        if (
            isinstance(target, ast.Name)
            and isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id == "QuantumCircuit"
            and value.args
            and isinstance(value.args[0], ast.Constant)
            and isinstance(value.args[0].value, int)
        ):
            circuit_sizes[target.id] = value.args[0].value

    gate_call_count = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in QUANTUM_GATE_METHODS:
            continue
        gate_call_count += 1
        owner = node.func.value
        if not isinstance(owner, ast.Name) or owner.id not in circuit_sizes:
            continue
        qubit_count = circuit_sizes[owner.id]
        for argument in node.args:
            if (
                isinstance(argument, ast.Constant)
                and isinstance(argument.value, int)
                and (argument.value < 0 or argument.value >= qubit_count)
            ):
                diagnostics.append(
                    {
                        "severity": "error",
                        "code": "qubit_index_out_of_range",
                        "line": getattr(node, "lineno", None),
                        "message": (
                            f"量子比特索引 {argument.value} 超出线路 {owner.id} "
                            f"的范围 0..{qubit_count - 1}。"
                        ),
                    }
                )

    if circuit_sizes and gate_call_count == 0:
        diagnostics.append(
            {
                "severity": "info",
                "code": "empty_circuit",
                "line": None,
                "message": "检测到 QuantumCircuit，但未识别到常用量子门调用。",
            }
        )

    return {
        "analyzed": True,
        "execution_performed": False,
        "circuit_sizes": circuit_sizes,
        "gate_call_count": gate_call_count,
        "diagnostics": diagnostics,
    }
