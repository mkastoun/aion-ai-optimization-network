"""Independent, intentionally simple Python correctness oracles.

Only small cases run during ordinary test collection. The fixture generation
script also computes the full-size expected outputs without using a compiler.
"""

MASK32 = (1 << 32) - 1
MASK64 = (1 << 64) - 1


def _values(n: int, seed: int):
    for _ in range(n):
        seed = (1664525 * seed + 1013904223) & MASK32
        yield seed


def expected(name: str, n: int, seed: int, rounds: int) -> str:
    from .expanded_reference import EXPANDED_REFERENCES, expected_expanded
    if name in EXPANDED_REFERENCES:
        return expected_expanded(name,n,seed,rounds)
    from .application_reference import APPLICATION_REFERENCES, expected_application
    if name in APPLICATION_REFERENCES:
        return expected_application(name,n,seed,rounds)
    checksum = 0
    for r in range(rounds):
        values = _values(n, (seed + r) & MASK32)
        if name == "array":
            checksum += sum(((((x * 3 + 7) & MASK32) ^ (x >> 3)) * (i % 17 + 1))
                            for i, x in enumerate(values))
        elif name == "sorting":
            checksum += sum(x * (i % 23 + 1) for i, x in enumerate(sorted(values)))
        elif name == "hashmap":
            entries = {}
            for x in values:
                key = x % (n // 2 + 1)
                entries[key] = (entries.get(key, 0) + x) & MASK64
            checksum += sum(v * (k % 13 + 1) for k, v in entries.items())
            checksum += sum(k % 3 != 0 for k in entries)
        elif name == "matrix":
            values = iter(_values(2 * n * n, (seed + r) & MASK32))
            a = [[0] * n for _ in range(n)]
            b = [[0] * n for _ in range(n)]
            for i in range(n):
                for j in range(n):
                    a[i][j], b[i][j] = next(values) % 17, next(values) % 17
            # Different traversal from C++'s i/k/j accumulation.
            for i in range(n):
                for j in range(n):
                    checksum += sum(a[i][k] * b[k][j] for k in range(n)) * ((i*n+j) % 19 + 1)
        elif name == "strings":
            text = "".join(chr(65 + x % 26) for x in values)
            checksum += sum(ord(c) * (i % 11 + 1) for i, c in enumerate(text))
            checksum += text.count("AB") * 97
        else:
            raise ValueError(f"Unknown reference workload: {name}")
    return str(checksum & MASK64)
