import json, collections, itertools
rows = json.load(open("/tmp/claude-1000/-home-jb-DSAT-REDUX-MD/636cbe72-4606-428d-8f8d-631620aa6c65/scratchpad/cb_rows.json"))
def nrm(s): return s.replace("Cross-text","Cross-Text")

by_pdf = collections.defaultdict(set)
for r in rows: by_pdf[r["pdf"]].add(r["qid"])
pdfs = list(by_pdf)
print("=== unique IDs per PDF ===")
for p in pdfs: print(f"{len(by_pdf[p]):5d} unique / {sum(1 for r in rows if r['pdf']==p):5d} rows  {p}")

print("\n=== containment matrix (A subset of B) ===")
for a,b in itertools.permutations(pdfs,2):
    if by_pdf[a] and by_pdf[a] <= by_pdf[b]:
        print(f"  {a}  ⊆  {b}")

allids = set(r["qid"] for r in rows)
print(f"\n=== TOTAL unique question IDs across every PDF: {len(allids)} ===")

# difficulty-split union
diffs = ["09_2026/MyPractice - Question Bank - Results - easy.pdf",
         "09_2026/MyPractice - Question Bank - Results medium.pdf",
         "09_2026/MyPractice - Question Bank - Results - Verbal Hard.pdf"]
u = set().union(*(by_pdf[d] for d in diffs))
print(f"EASY∪MED∪HARD unique = {len(u)}  (sum={sum(len(by_pdf[d]) for d in diffs)}) -> overlap {sum(len(by_pdf[d]) for d in diffs)-len(u)}")
for a,b in itertools.combinations(diffs,2):
    print(f"   {a.split('- ')[-1]} ∩ {b.split('- ')[-1]} = {len(by_pdf[a]&by_pdf[b])}")

bank = by_pdf["09_2026/09_2026_New_Verbal_Bank.pdf"]
print(f"\nBank(752) ⊆ difficulty-union? {bank <= u}  | bank∩union={len(bank&u)}")
print(f"IDs outside difficulty-union: {len(allids-u)}")
for p in pdfs:
    out = by_pdf[p]-u
    if out: print(f"   {len(out)} from {p}")

# consistency of domain/skill/difficulty per qid
dom = collections.defaultdict(set); sk = collections.defaultdict(set); df = collections.defaultdict(set); ca=collections.defaultdict(set)
for r in rows:
    dom[r["qid"]].add(r["domain"]); sk[r["qid"]].add(nrm(r["skill"]))
    if r["difficulty"]: df[r["qid"]].add(r["difficulty"])
    if r["correct"]: ca[r["qid"]].add(r["correct"])
print("\n=== cross-PDF consistency ===")
print("qids with conflicting DOMAIN:", sum(1 for v in dom.values() if len(v)>1))
print("qids with conflicting SKILL (case-normalized):", sum(1 for v in sk.values() if len(v)>1))
bad = [k for k,v in df.items() if len(v)>1]
print("qids with conflicting DIFFICULTY:", len(bad), bad[:10])
print("qids with conflicting CORRECT ANSWER:", sum(1 for v in ca.values() if len(v)>1))
print("qids with NO difficulty anywhere:", sum(1 for q in allids if not df.get(q)))
print("qids with NO correct answer anywhere:", sum(1 for q in allids if not ca.get(q)))

print("\n=== canonical domain x skill over ALL unique ids ===")
c = collections.Counter((next(iter(dom[q])), next(iter(sk[q]))) for q in allids)
for k,v in sorted(c.items()): print(f"  {v:5d}  {k[0]} | {k[1]}")
print(f"  combos={len(c)} total={sum(c.values())}")

print("\n=== difficulty distribution over unique ids ===")
print(collections.Counter(next(iter(df[q])) if df.get(q) else "NONE" for q in allids))
