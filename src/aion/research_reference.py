"""Independent Python oracle for fixed research-only log distributions."""
import json
from .application_reference import output_hash, MASK64
from .reference import _values


def logs_expected(n, seed, rounds):
    def one(seed):
        family = (seed >> 24) & 15 if seed >> 28 == 13 else 0
        values = iter(_values(n*6, seed))
        services, invalid, selected = {}, 0, 0
        for i in range(n):
            stamp = 1700000000+i*3+next(values)%60
            level = (next(values)>>24)%3
            service = (next(values)>>16)%32
            status = (200,404,500)[(next(values)>>16)%3]
            size, latency = next(values)%8192, next(values)%50000
            # Independently aggregate semantic records, rather than C++ parsing.
            if family == 1:
                level, status = 2, 500
            elif family == 2:
                level, status = 0, 200
            if i % (3 if family == 3 else 97) == 0:
                invalid += 1
                continue
            if level != 2 and status < 400:
                continue
            selected += 1
            stats = services.setdefault(service, [0,0,0,0,[0]*60])
            stats[0] += 1; stats[1] += size; stats[2] += latency; stats[3] += status >= 500
            stats[4][(stamp//60)%60] += 1
        return output_hash(json.dumps({"lines":n,"invalid":invalid,"selected":selected,
            "services":[[key,*services[key]] for key in sorted(services)]},separators=(",",":")))
    return str(sum(one((seed+r)&0xffffffff) for r in range(rounds)) & MASK64)
