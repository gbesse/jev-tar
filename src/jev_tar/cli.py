# Purpose: Command-line access to review classification, validation and export artifacts.
from __future__ import annotations
import argparse, csv, json, sys
from pathlib import Path
from .client import JevClient, FakeJev
from .core import *

def _read_jsonl(path): return [json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]
def _write_jsonl(path, rows): Path(path).write_text("".join(json.dumps(x)+"\n" for x in rows))

def main(argv=None):
    parser=argparse.ArgumentParser(prog="jev-tar"); sub=parser.add_subparsers(dest="command",required=True)
    p=sub.add_parser("classify");p.add_argument("input");p.add_argument("--protocol",required=True);p.add_argument("--out",required=True);p.add_argument("--fake",action="store_true")
    p=sub.add_parser("rank");p.add_argument("input");p.add_argument("--out",required=True)
    p=sub.add_parser("plan");p.add_argument("--population",type=int,required=True);p.add_argument("--margin",type=float,required=True);p.add_argument("--confidence",type=float,required=True)
    p=sub.add_parser("sample");p.add_argument("input");p.add_argument("--n",type=int,required=True);p.add_argument("--seed",type=int,default=7);p.add_argument("--cutoff",type=float,default=.5);p.add_argument("--out",required=True)
    p=sub.add_parser("elusion");p.add_argument("input");p.add_argument("--population-below",type=int,required=True);p.add_argument("--reviewed-found",type=int,default=0)
    p=sub.add_parser("log");p.add_argument("input");p.add_argument("--out",required=True);p.add_argument("--privileged",action="store_true")
    p=sub.add_parser("export");p.add_argument("input");p.add_argument("--format",choices=["csv","dat"],default="csv");p.add_argument("--out",required=True)
    args=parser.parse_args(argv)
    try:
        if args.command=="classify":
            rows=load_collection(args.input); protocol=json.loads(Path(args.protocol).read_text()); existing=_read_jsonl(args.out) if Path(args.out).exists() else []
            _write_jsonl(args.out,classify(rows,protocol,FakeJev() if args.fake else JevClient(),audit_path=Path(args.out).with_name("audit.jsonl"),existing=existing))
        elif args.command=="rank":
            rows=rank_rows(_read_jsonl(args.input)); fields=sorted({k for r in rows for k in r});
            with Path(args.out).open("w",newline="") as h: w=csv.DictWriter(h,fieldnames=fields);w.writeheader();w.writerows(rows)
        elif args.command=="plan": print(json.dumps(plan_sample(args.population,args.margin,args.confidence),indent=2))
        elif args.command=="sample":
            rows=sample_elusion(_read_jsonl(args.input),args.cutoff,args.n,args.seed);fields=sorted({k for r in rows for k in r})
            with Path(args.out).open("w",newline="") as h:w=csv.DictWriter(h,fieldnames=fields);w.writeheader();w.writerows(rows)
        elif args.command=="elusion":
            with Path(args.input).open(newline="") as h: print(json.dumps(elusion_estimate(list(csv.DictReader(h)),args.population_below,args.reviewed_found),indent=2))
        elif args.command=="log":
            rows=privilege_log(_read_jsonl(args.input));
            with Path(args.out).open("w",newline="") as h:w=csv.DictWriter(h,fieldnames=list(rows[0]) if rows else ["document_id","status"]);w.writeheader();w.writerows(rows)
        elif args.command=="export": print(json.dumps(export_production(_read_jsonl(args.input),args.out),indent=2))
    except Exception as error:
        print(f"jev-tar: {error}",file=sys.stderr); raise SystemExit(1)
