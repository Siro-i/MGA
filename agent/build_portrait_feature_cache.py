"""Build or validate the portrait feature cache without requiring a query image."""
import argparse
import json
import time
from pathlib import Path
from match_mech_image import ROOT, source_signature, load_feature_cache, build_feature_cache

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--library',type=Path,help='mech_assets directory; defaults to latest successful update')
    p.add_argument('--cache-dir',type=Path,default=ROOT.parent/'assets/resource/units_info/cache')
    p.add_argument('--force',action='store_true',help='Recompute even when the current cache is valid')
    args=p.parse_args()
    if args.library:library=args.library.resolve()
    else:
        library=(ROOT.parent/'assets/resource/units_info').resolve()
    mapping=json.loads((library/'idmap.json').read_text(encoding='utf-8'))
    paths={rel:True for row in mapping['rows'] for rel in row['portrait']['paths']}
    if not paths:raise RuntimeError('No portrait paths in idmap.json')
    signature=source_signature(library,paths);cache=args.cache_dir.resolve()/(signature+'.npz')
    started=time.perf_counter();cached=None;reason=None
    existed=cache.exists()
    if existed and not args.force:cached,reason=load_feature_cache(cache,signature,paths)
    if cached is None:
        cached,failed=build_feature_cache(library,paths,cache,signature)
        action='rebuilt' if existed else 'built'
    else:failed=0;action='reused'
    elapsed=time.perf_counter()-started
    result=dict(action=action,entries=len(cached),failed=failed,seconds=round(elapsed,3),cache=str(cache),signature=signature,invalid_reason=reason)
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
