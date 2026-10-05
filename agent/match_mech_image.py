"""Match a screenshot/crop against exported mech portraits without network models."""
import argparse
import json
import hashlib
import math
import os
import sys
import time
from pathlib import Path

try:
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
except ModuleNotFoundError:
    print('Use the bundled Python described in UPDATE_GUIDE.md (Pillow + NumPy required).',file=sys.stderr)
    raise

ROOT=Path(__file__).resolve().parent
CACHE_VERSION=3

def foreground(image,transparent=False):
    rgba=np.asarray(image.convert('RGBA'),dtype=np.float32)
    rgb=rgba[:,:,:3]
    if transparent and np.any(rgba[:,:,3]<250):
        mask=rgba[:,:,3]>12
    else:
        h,w=rgb.shape[:2]
        border=np.concatenate([rgb[:max(2,h//20)].reshape(-1,3),rgb[-max(2,h//20):].reshape(-1,3),
                               rgb[:,:max(2,w//20)].reshape(-1,3),rgb[:,-max(2,w//20):].reshape(-1,3)])
        bg=np.median(border,axis=0)
        distance=np.sqrt(((rgb-bg)**2).sum(axis=2))
        # Grid lines are weak deviations; saturated/dark mech pixels remain foreground.
        spread=np.median(np.sqrt(((border-bg)**2).sum(axis=1)))
        threshold=max(24.0,spread*3.0)
        mask=distance>threshold
        # Remove isolated grid/noise using a 3x3 neighbour count, no OpenCV required.
        padded=np.pad(mask,1)
        neighbours=sum(padded[y:y+h,x:x+w] for y in range(3) for x in range(3))
        mask=neighbours>=4
    ys,xs=np.where(mask)
    if len(xs)<100:return rgb,np.ones(rgb.shape[:2],bool)
    return rgb[ys.min():ys.max()+1,xs.min():xs.max()+1],mask[ys.min():ys.max()+1,xs.min():xs.max()+1]

def normalized(image,transparent=False,size=192):
    rgb,mask=foreground(image,transparent)
    h,w=mask.shape;scale=min((size-12)/max(w,1),(size-12)/max(h,1))
    nw,nh=max(1,round(w*scale)),max(1,round(h*scale))
    rgb_im=Image.fromarray(np.uint8(np.clip(rgb,0,255))).resize((nw,nh),Image.Resampling.LANCZOS)
    mask_im=Image.fromarray(np.uint8(mask)*255).resize((nw,nh),Image.Resampling.NEAREST)
    canvas=np.zeros((size,size,3),np.float32);alpha=np.zeros((size,size),bool)
    x=(size-nw)//2;y=(size-nh)//2
    canvas[y:y+nh,x:x+nw]=np.asarray(rgb_im,dtype=np.float32)/255
    alpha[y:y+nh,x:x+nw]=np.asarray(mask_im)>127
    return canvas,alpha

def features(image,transparent=False):
    rgb,mask=normalized(image,transparent)
    gray=rgb@np.array([.299,.587,.114],np.float32)
    # Center/scale brightness over foreground so lighting differences matter less.
    values=gray[mask];mean=float(values.mean());std=float(values.std())+1e-5
    norm=np.zeros_like(gray);norm[mask]=np.clip((gray[mask]-mean)/(2.5*std),-1,1)
    gx=np.zeros_like(gray);gy=np.zeros_like(gray)
    gx[:,1:]=np.abs(norm[:,1:]-norm[:,:-1]);gy[1:]=np.abs(norm[1:]-norm[:-1])
    edge=np.sqrt(gx*gx+gy*gy)
    # Downsample normalized luminance, edges and silhouette for structure comparison.
    def small(a,n=32):return np.asarray(Image.fromarray(np.float32(a),mode='F').resize((n,n),Image.Resampling.BILINEAR))
    structure=np.concatenate([small(norm).ravel(),small(edge).ravel(),small(mask.astype(np.float32)).ravel()])
    structure/=np.linalg.norm(structure)+1e-8
    hist=[]
    for c in range(3):
        h,_=np.histogram(rgb[:,:,c][mask],bins=16,range=(0,1),density=True);hist.extend(h)
    hist=np.asarray(hist,np.float32);hist/=np.linalg.norm(hist)+1e-8
    return structure,hist,rgb,mask

def cosine(a,b):return float(np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b)+1e-8))

def source_signature(library,paths):
    """Return a stable cache key for the exact portrait set being searched."""
    library=library.resolve()
    digest=hashlib.sha256()
    # 按图片内容生成缓存键，避免不同机器检出后的修改时间让预置缓存失效。
    digest.update(f"feature-cache-v{CACHE_VERSION}\n".encode('utf-8'))
    for rel in sorted(paths):
        candidate=(library/rel).resolve()
        if not candidate.is_relative_to(library):
            raise ValueError(f'portrait path escapes library: {rel}')
        digest.update(f"{rel.replace(chr(92),'/')}\0".encode('utf-8'))
        with candidate.open('rb') as source:
            for chunk in iter(lambda: source.read(1024*1024), b''):
                digest.update(chunk)
    return digest.hexdigest()

def load_feature_cache(cache,signature,expected_paths):
    """Load and validate a feature cache; return None for stale/corrupt data."""
    try:
        with np.load(cache,allow_pickle=False) as loaded:
            version=int(np.asarray(loaded['cache_version']).item())
            cached_signature=str(np.asarray(loaded['source_signature']).item())
            paths=[str(value) for value in np.asarray(loaded['paths']).tolist()]
            structures=np.asarray(loaded['structures'],dtype=np.float32).copy()
            histograms=np.asarray(loaded['histograms'],dtype=np.float32).copy()
        if version!=CACHE_VERSION:
            return None,'cache version changed'
        if cached_signature!=signature:
            return None,'source signature changed'
        if len(paths)!=len(set(paths)):
            return None,'duplicate cached portrait path'
        if not set(paths).issubset(set(expected_paths)):
            return None,'cached path is absent from current library'
        if structures.ndim!=2 or histograms.ndim!=2 or len(paths)!=len(structures) or len(paths)!=len(histograms):
            return None,'cached feature shapes are invalid'
        return {rel:(structures[i],histograms[i]) for i,rel in enumerate(paths)},None
    except Exception as exc:
        return None,f'{type(exc).__name__}: {exc}'

def write_feature_cache(cache,signature,paths,structures,histograms):
    """Write a complete cache atomically so an interrupted build is harmless."""
    cache.parent.mkdir(parents=True,exist_ok=True)
    temporary=cache.with_name(f'.{cache.name}.{os.getpid()}.{time.time_ns()}.tmp')
    try:
        with temporary.open('wb') as handle:
            np.savez_compressed(handle,
                cache_version=np.asarray(CACHE_VERSION,dtype=np.int32),
                source_signature=np.asarray(signature),
                paths=np.asarray(paths,dtype=str),
                structures=np.asarray(structures,dtype=np.float32),
                histograms=np.asarray(histograms,dtype=np.float32))
        temporary.replace(cache)
    finally:
        if temporary.exists():
            temporary.unlink()

def build_feature_cache(library,by_path,cache,signature):
    paths=[];structures=[];histograms=[];failed=0
    for rel in sorted(by_path):
        try:
            with Image.open(library/rel) as image:
                candidate=features(image,True)
        except Exception:
            failed+=1
            continue
        paths.append(rel);structures.append(candidate[0]);histograms.append(candidate[1])
    if not paths:
        raise RuntimeError('no readable portrait features were produced')
    write_feature_cache(cache,signature,paths,structures,histograms)
    return {rel:(structures[i],histograms[i]) for i,rel in enumerate(paths)},failed

def main():
    p=argparse.ArgumentParser(description='Match one image against extracted portraits')
    p.add_argument('image',type=Path);p.add_argument('--top',type=int,default=20);p.add_argument('--output',type=Path)
    p.add_argument('--no-sheet',action='store_true',help='Skip contact sheet for fastest lookup')
    p.add_argument('--library',type=Path,help='mech_assets output directory; defaults to latest successful update')
    p.add_argument('--cache-dir',type=Path,help='feature cache directory; defaults to .resource_cache/image_match')
    args=p.parse_args()
    if not args.image.is_file():p.error('input image not found')
    if args.library:library=args.library.resolve()
    else:
        latest=json.loads((ROOT/'outputs/latest_mech_assets.json').read_text(encoding='utf-8'))
        library=Path(latest['directory'])
    mapping=json.loads((library/'idmap.json').read_text(encoding='utf-8'))
    by_path={}
    for row in mapping['rows']:
        for rel in row['portrait']['paths']:by_path.setdefault(rel,[]).append(row)
    signature=source_signature(library,by_path)
    cache_root=(args.cache_dir or ROOT/'.resource_cache/image_match').resolve()
    cache_root.mkdir(parents=True,exist_ok=True)
    cache=cache_root/(signature+'.npz')
    cache_started=time.perf_counter()
    cache_hit=False;cache_invalid_reason=None;failed=0
    if cache.exists():
        cached,cache_invalid_reason=load_feature_cache(cache,signature,by_path)
        cache_hit=cached is not None
        if not cache_hit:
            print(f'CACHE_INVALID {cache_invalid_reason}')
    else:
        cached=None
    cache_load_seconds=time.perf_counter()-cache_started
    if cached is None:
        cached,failed=build_feature_cache(library,by_path,cache,signature)
        cache_build_seconds=time.perf_counter()-cache_started
    else:
        cache_build_seconds=0.0
    query_started=time.perf_counter()
    with Image.open(args.image) as image:
        query=features(image,False)
    results=[]
    for rel,rows in by_path.items():
        candidate=cached.get(rel)
        if candidate is None:continue
        structural=max(cosine(query[0],candidate[0]),0)
        color=max(cosine(query[1],candidate[1]),0)
        score=.78*structural+.22*color
        results.append(dict(score=round(score,6),structure=round(structural,6),color=round(color,6),
                            portrait_id=Path(rel).stem,path=rel,units=[dict(id=r['master_unit_id'],name=r['name'],model=r['model_number']) for r in rows]))
    results.sort(key=lambda r:r['score'],reverse=True);results=results[:max(1,args.top)]
    query_seconds=time.perf_counter()-query_started
    cache_hit_query_seconds=(time.perf_counter()-cache_started) if cache_hit else None
    output=args.output or ROOT/'outputs/image_match'
    output.mkdir(parents=True,exist_ok=True)
    report=dict(query=str(args.image.resolve()),library=str(library),cache=str(cache),
                cache_version=CACHE_VERSION,source_signature=signature,cache_hit=cache_hit,
                cache_entries=len(cached),cache_load_seconds=round(cache_load_seconds,6),
                cache_build_seconds=round(cache_build_seconds,6),cache_build_failed=failed,
                query_seconds=round(query_seconds,6),
                cache_hit_query_seconds=None if cache_hit_query_seconds is None else round(cache_hit_query_seconds,6),
                algorithm='foreground + normalized luminance/edge/silhouette cosine + RGB histogram',results=results)
    (output/'matches.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    if not args.no_sheet:
        thumb_w,thumb_h=220,220;label_h=74;cols=5;rows_count=math.ceil(len(results)/cols)
        sheet=Image.new('RGB',(cols*thumb_w,rows_count*(thumb_h+label_h)),(244,247,250));draw=ImageDraw.Draw(sheet)
        font=ImageFont.load_default()
        for i,result in enumerate(results):
            x=(i%cols)*thumb_w;y=(i//cols)*(thumb_h+label_h)
            im=Image.open(library/result['path']).convert('RGBA');im.thumbnail((thumb_w-16,thumb_h-16),Image.Resampling.LANCZOS)
            tile=Image.new('RGBA',(thumb_w,thumb_h),(238,242,247,255));tile.alpha_composite(im,((thumb_w-im.width)//2,(thumb_h-im.height)//2));sheet.paste(tile.convert('RGB'),(x,y))
            unit=result['units'][0];text=f"#{i+1} {result['portrait_id']}\nscore {result['score']:.3f}\n{unit['id']} {unit['name'] or ''}"
            draw.multiline_text((x+6,y+thumb_h+5),text,fill=(25,43,60),font=font,spacing=3)
        sheet.save(output/'contact_sheet.png')
    print(json.dumps(results[:10],ensure_ascii=False,indent=2))
    print(f"CACHE_{'HIT' if cache_hit else 'BUILD'} entries={len(cached)} path={cache}")
    if cache_hit:print(f'CACHE_HIT_QUERY_SECONDS {cache_hit_query_seconds:.6f}')
    else:print(f'CACHE_BUILD_SECONDS {cache_build_seconds:.6f}')
    print(f'QUERY_SECONDS {query_seconds:.6f}')
    print('RESULT',output/'matches.json')
    if not args.no_sheet:print('SHEET',output/'contact_sheet.png')

if __name__=='__main__':main()
