"""Independent Python image and key/value specifications; no compiler output."""
import json
from .application_reference import output_hash

MASK32=(1<<32)-1
MASK64=(1<<64)-1


def image_pixels(n,seed,pattern_seed=None):
    pattern_seed=seed if pattern_seed is None else pattern_seed
    state=seed
    pixels=[]
    for y in range(n):
        row=[]
        for x in range(n):
            state=(1664525*state+1013904223)&MASK32
            row.append(32768 if pattern_seed==0 else 65535*((x+y)%2) if pattern_seed==MASK32 else state>>16)
        pixels.append(row)
    return pixels


def image_output(n,seed,*,pattern_seed=None):
    pixels=image_pixels(n,seed,pattern_seed)
    if n:
        weights=(1,4,6,4,1)
        clamp=lambda i:max(0,min(n-1,i))
        horizontal=[[sum(weights[k+2]*row[clamp(x+k)] for k in range(-2,3))//16 for x in range(n)] for row in pixels]
        filtered=[[sum(weights[k+2]*horizontal[clamp(y+k)][x] for k in range(-2,3))//16 for x in range(n)] for y in range(n)]
        pixels=[]
        sx=((-1,0,1),(-2,0,2),(-1,0,1));sy=((-1,-2,-1),(0,0,0),(1,2,1))
        for y in range(n):
            row=[]
            for x in range(n):
                dx=sum(sx[j][i]*filtered[clamp(y+j-1)][clamp(x+i-1)] for j in range(3) for i in range(3))
                dy=sum(sy[j][i]*filtered[clamp(y+j-1)][clamp(x+i-1)] for j in range(3) for i in range(3))
                row.append(min(65535,abs(dx)+abs(dy)))
            pixels.append(row)
    histogram=[0]*16
    total=weighted=0
    rows=[]
    for y,row in enumerate(pixels):
        digest=14695981039346656037
        for x,value in enumerate(row):
            total+=value;weighted+=value*((y*n+x)%251+1);histogram[value>>12]+=1
            for byte in value.to_bytes(2,'little'):digest=((digest^byte)*1099511628211)&MASK64
        rows.append(digest)
    return json.dumps({"width":n,"sum":total,"weighted":weighted&MASK64,"histogram":histogram,"rows":rows},separators=(',',':'))


def kv_output(n,seed,*,pattern_seed=None):
    pattern_seed=seed if pattern_seed is None else pattern_seed
    state=seed
    def rand():
        nonlocal state
        state=(1664525*state+1013904223)&MASK32
        return state
    table={};queries=hits=updates=deletes=checksum=0
    actions=('insert','insert','lookup','lookup','update','lookup','delete','insert')
    for i in range(n):
        random_key=rand();length=8+(rand()>>16)%89
        key=(i//8)%64 if pattern_seed==0 else i%(n//4+1) if pattern_seed==MASK32 else random_key%(64 if i%5==0 else n//4+1)
        value=''.join(chr(97+(rand()>>24)%26) for _ in range(length))
        action=actions[i%8]
        if action=='insert':table[key]=value
        elif action=='lookup':
            queries+=1
            if key in table:hits+=1;checksum=(checksum+(output_hash(table[key])^key))&MASK64
        elif action=='update':
            if key in table:updates+=1;table[key]=value
        elif key in table:deletes+=1;del table[key]
    return json.dumps({"queries":queries,"hits":hits,"updates":updates,"deletes":deletes,
                       "query_checksum":checksum,"entries":[[k,table[k]] for k in sorted(table)]},separators=(',',':'))


EXPANDED_REFERENCES={"image":image_output,"kv":kv_output}


def expected_expanded(name,n,seed,rounds):
    # Distribution is selected by the original input seed, not by a wrapped
    # round seed. The C++ generators apply that same explicit contract.
    return str(sum(output_hash(EXPANDED_REFERENCES[name](n,(seed+r)&MASK32,pattern_seed=seed)) for r in range(rounds))&MASK64)
