import ast
import operator
import re
from typing import Any, List, Optional


class CalculationAgent:
    """Agent for performing numeric calculations."""

    _binary_ops = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.FloorDiv: operator.floordiv,
    }

    _unary_ops = {
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,
    }

    def _eval_node(self, node: ast.AST):
        """Recursively evaluate a restricted AST node."""
        if isinstance(node, ast.BinOp):
            op = self._binary_ops.get(type(node.op))
            if op is None:
                raise ValueError("Unsupported operator")
            return op(self._eval_node(node.left), self._eval_node(node.right))
        if isinstance(node, ast.UnaryOp):
            op = self._unary_ops.get(type(node.op))
            if op is None:
                raise ValueError("Unsupported unary operator")
            return op(self._eval_node(node.operand))
        if isinstance(node, ast.Num):
            return node.n
        if isinstance(node, ast.Constant):  # for Python 3.8+
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Unsupported constant")
        raise ValueError("Unsupported expression")

    def compute(
        self,
        expression: Optional[str] = None,
        *,
        question: Optional[str] = None,
        table: Optional[List[List[Any]]] = None,
        operator_chain: Optional[List[dict]] = None,
        base_value: Optional[float] = None,
    ):
        """Return the evaluated result of an expression or derive a value from question/table/operator chain."""

        expression = (expression or "").strip()
        if expression:
            try:
                tree = ast.parse(expression, mode="eval")
                return self._eval_node(tree.body)
            except Exception:
                pass

        chain_result = self._derive_from_operator_chain(base_value, operator_chain)
        if chain_result is not None:
            return chain_result

        derived = self._derive_from_table(question, table)
        return derived

    def _derive_from_operator_chain(
        self,
        base_value: Optional[float],
        operator_chain: Optional[List[dict]],
    ) -> Optional[float]:
        """Execute deterministic synthetic operator chains (5–8 steps)."""

        if base_value is None or not operator_chain:
            return None

        result = float(base_value)
        for step in operator_chain:
            if not isinstance(step, dict):
                continue
            op = step.get("op")
            try:
                val = float(step.get("value"))
            except (TypeError, ValueError):
                continue

            if op == "add":
                result += val
            elif op == "subtract":
                result -= val
            elif op == "multiply":
                result *= val
            elif op == "divide":
                if val != 0:
                    result /= val
            # ignore unknown ops silently

        return result

    def _derive_from_table(self, question: Optional[str], table: Optional[List[List[Any]]]):
        """Heuristically answer lookup-style questions from a simple table."""

        if not question or not table or not isinstance(table, list):
            return None

        if not table:
            return None

        headers = None
        rows = table
        first_row = table[0]
        if isinstance(first_row, list) and all(isinstance(item, (str, int, float)) for item in first_row):
            headers = [str(x) for x in first_row]
            rows = table[1:]

        if not rows:
            return None

        q_lower = question.lower()
        numbers = re.findall(r"\d{3,4}", q_lower)
        tokens = {tok for tok in re.findall(r"[a-zA-Z]+", q_lower) if len(tok) > 2}

        question_lower = question.lower()
        derived = self._aggregate_table(question_lower, headers, rows)
        if derived:
            return derived

        target_row = None
        for row in rows:
            if not row:
                continue
            row_label = str(row[0]).lower()
            if numbers and any(num in row_label for num in numbers):
                target_row = row
                break
            if tokens and any(tok in row_label for tok in tokens):
                target_row = row
                break

        if target_row is None:
            target_row = rows[0]

        col_index = self._determine_column(headers, target_row, tokens)
        if col_index is None or col_index >= len(target_row):
            return None

        value = target_row[col_index]
        header = headers[col_index] if headers and col_index < len(headers) else f"column {col_index}"
        row_label = target_row[0]
        return f"{header} for {row_label} = {value}"

    def _determine_column(self, headers: Optional[List[str]], row: List[Any], tokens: set) -> Optional[int]:
        """Pick the column that overlaps with question tokens or contains numeric data."""

        if headers:
            for idx, header in enumerate(headers[1:], start=1):
                header_tokens = set(re.findall(r"[a-zA-Z]+", header.lower()))
                if tokens and header_tokens & tokens:
                    return idx

        for idx, cell in enumerate(row[1:], start=1):
            if isinstance(cell, (int, float)):
                return idx
            try:
                float(str(cell).replace(",", ""))
                return idx
            except ValueError:
                continue
        return None

    def _aggregate_table(self, question: str, headers: Optional[List[str]], rows: List[List[Any]]):
        """Handle sum/difference/average questions over a column."""

        if not headers or len(headers) < 2:
            return None

        target_col = None
        for idx, header in enumerate(headers[1:], start=1):
            if header and header.strip():
                if header.lower() in question or any(tok in header.lower() for tok in re.findall(r"[a-zA-Z]+", question)):
                    target_col = idx
                    break
        if target_col is None:
            target_col = 1

        numeric_values = []
        labels = []
        for row in rows:
            if len(row) <= target_col:
                continue
            try:
                numeric_values.append(float(str(row[target_col]).replace(",", "")))
                labels.append(str(row[0]))
            except ValueError:
                continue

        if not numeric_values:
            return None

        if "average" in question or "mean" in question:
            avg = sum(numeric_values) / len(numeric_values)
            return f"Average {headers[target_col]} = {avg:.2f}"
        if "sum" in question or "total" in question:
            total = sum(numeric_values)
            return f"Total {headers[target_col]} = {total}"
        if "difference" in question or "decrease" in question or "increase" in question:
            if len(numeric_values) >= 2:
                diff = numeric_values[-1] - numeric_values[0]
                return f"Difference in {headers[target_col]} from {labels[0]} to {labels[-1]} = {diff}"
        if "max" in question or "highest" in question:
            max_val = max(numeric_values)
            label = labels[numeric_values.index(max_val)]
            return f"Highest {headers[target_col]} is {max_val} for {label}"
        if "min" in question or "lowest" in question:
            min_val = min(numeric_values)
            label = labels[numeric_values.index(min_val)]
            return f"Lowest {headers[target_col]} is {min_val} for {label}"
        return None
