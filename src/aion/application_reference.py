"""Independent application oracles: parse text and produce canonical JSON.

Small graph cases use Bellman-Ford, separate from the C++ Dijkstra algorithm.
Full cases use heapq. No compiler output is used to generate expectations.
"""

import csv
import heapq
import io
import json

MASK64 = (1<<64)-1


def output_hash(text: str) -> int:
    value = 14695981039346656037
    for byte in text.encode(): value = ((value ^ byte)*1099511628211) & MASK64
    return value


def _json(value) -> str:
    return json.dumps(value, separators=(",", ":"))


def records_output(n: int, seed: int) -> str:
    from .reference import _values
    values = iter(_values(n*4, seed))
    text = "".join(f"{i},{(next(values)>>8)%512},{(next(values)>>16)%8},{next(values)%100000},{(next(values)>>24)%3}\n"
                   for i in range(n))
    groups, accepted, ids = {}, 0, 0
    for row in csv.reader(io.StringIO(text)):
        ident, user, region, amount, status = map(int, row)
        if status != 1: continue
        accepted += 1
        ids += ident
        key = user*8 + region
        count, cents = groups.get(key, (0,0))
        groups[key] = (count+1,cents+amount)
    return _json({"records": n, "accepted": accepted, "ids": ids,
                  "groups": [[key,*groups[key]] for key in sorted(groups)]})


def graph_edges(n: int, seed: int):
    from .reference import _values
    values = iter(_values(n*8, seed))
    edges = []
    for vertex in range(n):
        edges.extend([(vertex,(vertex+1)%n,1), (vertex,(vertex+n-1)%n,2)])
        for _ in range(4): edges.append((vertex,(next(values)>>8)%n,(next(values)>>16)%97+1))
    return edges


def graph_distances(n: int, edges, source: int, *, bellman_ford: bool):
    distance = [None]*n
    distance[source] = 0
    if bellman_ford:
        for _ in range(n-1):
            changed = False
            for origin,target,weight in edges:
                if distance[origin] is not None and (distance[target] is None or distance[origin]+weight < distance[target]):
                    distance[target] = distance[origin]+weight
                    changed = True
            if not changed: break
    else:
        adjacency = [[] for _ in range(n)]
        for origin,target,weight in edges: adjacency[origin].append((target,weight))
        pending = [(0,source)]
        while pending:
            cost,origin = heapq.heappop(pending)
            if distance[origin] != cost: continue
            for target,weight in adjacency[origin]:
                candidate = cost+weight
                if distance[target] is None or candidate < distance[target]:
                    distance[target] = candidate
                    heapq.heappush(pending,(candidate,target))
    return distance


def graph_output(n: int, seed: int) -> str:
    edges, queries = graph_edges(n, seed), []
    for query in range(4 if n else 0):
        source = (seed+query*97)%n
        distance = graph_distances(n,edges,source,bellman_ford=n<=32)
        finite = [(i,value) for i,value in enumerate(distance) if value is not None]
        queries.append({"source": source, "sum": sum(value*(i%19+1) for i,value in finite)&MASK64,
                        "max": max(value for _,value in finite), "reachable": len(finite)})
    return _json({"vertices": n, "queries": queries})


def logs_output(n: int, seed: int) -> str:
    from .reference import _values
    values = iter(_values(n*6, seed))
    lines = []
    for i in range(n):
        stamp = 1700000000+i*3+next(values)%60
        level = ("INFO","WARN","ERROR")[(next(values)>>24)%3]
        service = (next(values)>>16)%32
        status = (200,404,500)[(next(values)>>16)%3]
        size,latency = next(values)%8192,next(values)%50000
        lines.append("malformed line" if i%97==0 else f"{stamp}|{level}|svc{service}|{status}|{size}|{latency}")
    services, invalid, selected = {}, 0, 0
    for line in lines:
        fields = line.split("|")
        if len(fields)!=6:
            invalid+=1
            continue
        stamp,level,service,status,size,latency = fields
        stamp,status,size,latency = map(int,(stamp,status,size,latency))
        if level!="ERROR" and status<400: continue
        selected+=1
        ident=int(service[3:])
        stats=services.setdefault(ident,[0,0,0,0,[0]*60])
        stats[0]+=1; stats[1]+=size; stats[2]+=latency; stats[3]+=status>=500
        stats[4][(stamp//60)%60]+=1
    return _json({"lines":n,"invalid":invalid,"selected":selected,
                  "services":[[key,*services[key]] for key in sorted(services)]})


APPLICATION_REFERENCES = {"records": records_output, "graph": graph_output, "logs": logs_output}


def expected_application(name: str, n: int, seed: int, rounds: int) -> str:
    return str(sum(output_hash(APPLICATION_REFERENCES[name](n,(seed+r)&((1<<32)-1))) for r in range(rounds)) & MASK64)
