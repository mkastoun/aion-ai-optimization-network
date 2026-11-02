"""Regenerate checked-in expectations using independent Python implementations.

Run from an installed checkout: python tools/generate_expectations.py
"""

import json
from pathlib import Path

from aion.reference import expected

SIZES = {
    "array": (1_000_000, 16), "sorting": (100_000, 10),
    "hashmap": (100_000, 10), "matrix": (128, 12), "strings": (1_000_000, 16),
    "records": (40_000, 3), "graph": (4_000, 3), "logs": (60_000, 3),
    "image": (256, 3), "kv": (30_000, 3),
}


def generate():
    manifest = {"schema_version": 1, "workloads": {}}
    for name, (size, rounds) in SIZES.items():
        cases = []
        for label, n, seed, count in (("empty", 0, 1, 1), ("small", 7, 123, 3),
                                       ("alternate", 17, 4294967295, 2),
                                       ("performance", size, 42, rounds),
                                       ("training", size, 271828, 2),
                                       ("confirmation", size, 314159, rounds)):
            cases.append({"name": label, "args": [str(n), str(seed), str(count)],
                          "expected": expected(name, n, seed, count)})
        if name in {"records", "graph", "logs", "image", "kv"}:
            files = {"records": ["main", "parser", "aggregate", "format"],
                     "graph": ["main", "graph", "routing", "report"],
                     "logs": ["main", "parser", "aggregate", "format"],
                     "image": ["main", "filter", "edges", "format"],
                     "kv": ["main", "store", "process", "format"]}[name]
            manifest["workloads"][name] = {"sources": [f"{name}/{file}.cpp" for file in files],
                "headers": ["common.hpp", "application.hpp", f"{name}/{name}.hpp"], "category": "applications", "cases": cases}
        else:
            manifest["workloads"][name] = {"source": f"{name}.cpp", "cases": cases}
        print(f"Generated {name}", flush=True)
    path = Path(__file__).resolve().parents[1] / "src/aion/workloads/manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    # Additional correctness coverage does not change historical timing cases
    # or fingerprints of the eight existing workloads.
    validation={"schema_version":1,"workloads":{}}
    for name,(size,_) in SIZES.items():
        items=[("singleton",1,0,1),("two-elements-wrap",2,4294967294,3),
               ("large",2*size,1234567,1),("fresh-seed",min(size,257),8675309,2)]
        if name in {"image","kv"}:
            items += [("flat-or-hotspot",32 if name=="image" else 1024,0,2),
                      ("checkerboard-or-sequential",32 if name=="image" else 1024,4294967295,2)]
        validation["workloads"][name]=[{"name":label,"args":[str(n),str(seed),str(count)],
            "expected":expected(name,n,seed,count)} for label,n,seed,count in items]
        print(f"Generated extended validation {name}",flush=True)
    path.with_name("validation.json").write_text(json.dumps(validation,indent=2)+"\n",encoding="utf-8")


if __name__ == "__main__":
    generate()
