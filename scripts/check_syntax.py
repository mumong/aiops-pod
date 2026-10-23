"""Check maintained Python source without imports or bytecode writes."""

from pathlib import Path


def main() -> None:
    """Compile maintained source to memory; never invoke tools or network."""
    root = Path(__file__).resolve().parents[1]
    paths = []
    for folder in ("app", "a2a_adapter", "aiops_edge", "scripts", "tests"):
        paths.extend(sorted((root / folder).rglob("*.py")))
    for path in paths:
        compile(path.read_bytes(), str(path), "exec")
    print(f"Syntax checked {len(paths)} Python files")


if __name__ == "__main__":
    main()
