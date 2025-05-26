import argparse
import json
from typing import Iterable


# Simple DSL parser: "key=value" lines


def parse_pricing_dsl(text: str) -> dict:
    result: dict[str, object] = {}
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if "=" not in line:
            raise ValueError(f"invalid line: {raw!r}")
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip()
        try:
            parsed = json.loads(val)
        except json.JSONDecodeError:
            parsed = val
        result[key] = parsed
    return result


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Pricing DSL utilities")
    sub = parser.add_subparsers(dest="cmd", required=True)

    comp_p = sub.add_parser("compile", help="Compile DSL file to JSON")
    comp_p.add_argument("source", help="Path to DSL file")
    comp_p.add_argument("-o", "--output", help="Write JSON to file instead of stdout")

    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.cmd == "compile":
        with open(args.source) as f:
            data = parse_pricing_dsl(f.read())
        json_str = json.dumps(data, indent=2)
        if args.output:
            with open(args.output, "w") as out:
                out.write(json_str)
        else:
            print(json_str)


def cli() -> None:
    main()


if __name__ == "__main__":
    cli()
