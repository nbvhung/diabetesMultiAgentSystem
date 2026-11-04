"""Versioned, auditable paragraph corpus from exact allowlisted diabetes pages.

Only explicit preparation may fetch. Runtime reads and verifies cached provenance.
"""
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse
import hashlib, json, re
import httpx
from bs4 import BeautifulSoup
from .config import ROOT, research_settings

SOURCE_CONFIG=ROOT/'experiments/configs/diabetes_sources.json'
BASE='https://www.niddk.nih.gov/health-information/diabetes/overview/'


def sha_bytes(value):return hashlib.sha256(value).hexdigest()
def normalize(value):return re.sub(r'\s+',' ',value).strip()
def source_config():return json.loads(SOURCE_CONFIG.read_text(encoding='utf-8'))
def allowed_urls():return {BASE+s['path'] for s in source_config()['sources']}


def validate_source_url(url):
    value=str(url);parts=urlparse(value)
    if parts.scheme!='https' or parts.hostname!='www.niddk.nih.gov' or parts.username or parts.password or parts.port or parts.query or parts.fragment or value not in allowed_urls():
        raise ValueError('SOURCE_NOT_REGISTERED')
    return value


def safe_document_text(text):
    # Documents are data; instructions and personalized drug dosing are never admitted.
    return not re.search(r'ignore.{0,40}(instruction|rules)|system prompt|system:|developer:|<script|\b\d+(?:\.\d+)?\s*(?:mg|mcg|units)\b|adjust.{0,30}(?:dose|insulin)|change.{0,30}(?:dose|insulin)',text,re.I)


def parse_page(raw,source,retrieved_at):
    soup=BeautifulSoup(raw,'html.parser');article=soup.select_one('article.dk-content')
    if article is None or article.h1 is None:raise ValueError('SOURCE_LAYOUT_REVIEW_REQUIRED')
    title=normalize(article.h1.get_text(' ',strip=True));section=title;parent_section=title;out=[];seen=set()
    reviewed=next((normalize(node.get_text(' ',strip=True)) for node in article.find_all(['div','p','span']) if re.fullmatch(r'Last Reviewed [A-Za-z]+ \d{4}',normalize(node.get_text(' ',strip=True)))),None)
    for node in article.find_all(['h2','h3','p','ul','ol']):
        if node.find_parent(['nav','aside','figure','table']) or node.find_parent(class_=re.compile('share|reference|related|author|sidebar|toc|citation',re.I)):continue
        if node.find_parent(['ul','ol']):continue
        if node.name in ('h2','h3'):
            section=normalize(node.get_text(' ',strip=True))
            if node.name=='h2':parent_section=section
            if re.match(r'^(references?|additional links|clinical trials|what (?:clinical trials|are clinical trials|have we learned)|related conditions)',section.lower()):break
            continue
        text=normalize(node.get_text(' ',strip=True))
        if node.name in ('ul','ol'):
            # Keep symptom/risk lists together; filtering short individual bullets
            # would discard core facts and leave only long complication passages.
            previous=node.find_previous_sibling('p')
            if previous is not None and len(normalize(previous.get_text(' ',strip=True)))<500:
                text=normalize(previous.get_text(' ',strip=True))+' '+text
        if len(text)<45 or text in seen or text.startswith(('Last Reviewed','Share this page','This content is provided','NIDDK would like')):continue
        if not safe_document_text(text):continue
        if node.find_parent(class_=re.compile('dk-toc',re.I)):continue
        # Preserve sentence/paragraph context, bounded to the encoder's 128-token window.
        sentences=re.split(r'(?<=[.!?])\s+',text)
        groups=[];current=''
        for sentence in sentences:
            if len(sentence)>900:continue
            if current and len(current)+len(sentence)>550:groups.append(current);current=''
            current=(current+' '+sentence).strip()
        if current:groups.append(current)
        for paragraph in groups:
            if len(paragraph)<45 or paragraph in seen:continue
            seen.add(paragraph)
            identity=sha_bytes((source['url']+'|'+section+'|'+paragraph).encode())
            context=parent_section+' / '+section if parent_section!=section else section
            out.append({'id':identity,'source_id':source['id'],'text':paragraph,'section':section,'section_context':context,'title':title,'url':source['url'],'publisher':'NIDDK','retrieved_at':retrieved_at,'last_reviewed':reviewed,'source_sha256':sha_bytes(raw),'topics':source['topics']})
    if not out:raise ValueError('EMPTY_SOURCE_REVIEW_REQUIRED')
    return out


def prepare_corpus(folder=None,*,fetch=False):
    folder=Path(folder or research_settings.diabetes_corpus_dir);folder.mkdir(parents=True,exist_ok=True)
    config=source_config();snapshots=[];chunks=[]
    # Validate the cached publisher policy before admitting any page.
    policy_path=folder/'copyright.html'
    with httpx.Client(timeout=40,follow_redirects=False,headers={'User-Agent':'DiabetesMASResearch/2.0 (educational source audit)'}) as client:
        if fetch:
            response=client.get(config['usage_policy']);response.raise_for_status();policy_path.write_bytes(response.content)
        policy=BeautifulSoup(policy_path.read_bytes(),'html.parser').get_text(' ',strip=True).lower()
        if 'copyright free' not in policy or 'majority' not in policy:raise ValueError('SOURCE_USAGE_POLICY_REVIEW_REQUIRED')
        for item in config['sources']:
            source=dict(item,url=BASE+item['path']);validate_source_url(source['url'])
            path=folder/(source['id']+'.html');meta_path=folder/(source['id']+'.metadata.json')
            if fetch:
                response=client.get(source['url']);response.raise_for_status()
                if len(response.content)>3_000_000:raise ValueError('SOURCE_TOO_LARGE')
                path.write_bytes(response.content)
                meta={'id':source['id'],'url':source['url'],'retrieved_at':datetime.now(timezone.utc).isoformat(),'sha256':sha_bytes(response.content)}
                meta_path.write_text(json.dumps(meta,indent=2),encoding='utf-8')
            raw=path.read_bytes();meta=json.loads(meta_path.read_text(encoding='utf-8'))
            if meta['url']!=source['url'] or sha_bytes(raw)!=meta['sha256']:raise ValueError('SOURCE_SNAPSHOT_MODIFIED')
            parsed=parse_page(raw,source,meta['retrieved_at']);chunks.extend(parsed)
            immutable=folder/'snapshots'/(meta['sha256']+'.html');immutable.parent.mkdir(exist_ok=True)
            if not immutable.exists():immutable.write_bytes(raw)
            snapshots.append(dict(meta,chunk_count=len(parsed),file='snapshots/'+immutable.name))
    chunks.sort(key=lambda c:c['id'])
    data=json.dumps(chunks,ensure_ascii=False,indent=2).encode('utf-8');(folder/'chunks.json').write_bytes(data)
    version=sha_bytes(data);(folder/('chunks-'+version+'.json')).write_bytes(data)
    manifest={'dataset_version':config['version'],'timestamp':datetime.now(timezone.utc).isoformat(),'sources':snapshots,'source_config_sha256':sha_bytes(SOURCE_CONFIG.read_bytes()),'usage_policy_sha256':sha_bytes(policy_path.read_bytes()),'chunks_sha256':version,'chunks_file':'chunks-'+version+'.json','chunk_count':len(chunks),'source_count':len(snapshots),'scope':config['scope']}
    (folder/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    releases=folder/'releases';releases.mkdir(exist_ok=True)
    (releases/(version+'.json')).write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    return manifest


class Corpus:
    def __init__(self,path=None):self.path=Path(path or research_settings.diabetes_corpus_dir);self._loaded=False
    def load(self):
        if self._loaded:return
        manifest=json.loads((self.path/'manifest.json').read_text(encoding='utf-8'))
        if manifest['chunks_file']!='chunks-'+manifest['chunks_sha256']+'.json':raise ValueError('CORPUS_FILE_MISMATCH')
        raw=(self.path/manifest['chunks_file']).read_bytes()
        if sha_bytes(raw)!=manifest['chunks_sha256'] or sha_bytes(SOURCE_CONFIG.read_bytes())!=manifest['source_config_sha256']:raise ValueError('CORPUS_CHECKSUM_MISMATCH')
        if sha_bytes((self.path/'copyright.html').read_bytes())!=manifest['usage_policy_sha256']:raise ValueError('USAGE_POLICY_CHECKSUM_MISMATCH')
        for source in manifest['sources']:
            validate_source_url(source['url'])
            if source['file']!='snapshots/'+source['sha256']+'.html' or sha_bytes((self.path/source['file']).read_bytes())!=source['sha256']:raise ValueError('SOURCE_CHECKSUM_MISMATCH')
        self.chunks=json.loads(raw);self.by_id={c['id']:c for c in self.chunks};self.manifest=manifest
        if len(self.by_id)!=manifest['chunk_count']:raise ValueError('CORPUS_ID_MISMATCH')
        for c in self.chunks:
            validate_source_url(c['url'])
            if c['id']!=sha_bytes((c['url']+'|'+c['section']+'|'+c['text']).encode()) or not safe_document_text(c['text']):raise ValueError('CORPUS_CONTENT_MISMATCH')
        self._loaded=True
    def admits(self,evidence):
        self.load();source=self.by_id.get(evidence.evidence_id)
        return source is not None and all(str(getattr(evidence,k))==str(source[v]) for k,v in [('excerpt','text'),('source_url','url'),('source_title','title'),('publisher','publisher'),('section','section'),('section_context','section_context'),('last_reviewed','last_reviewed'),('source_version','source_sha256'),('source_id','source_id')]) and evidence.retrieved_at==datetime.fromisoformat(source['retrieved_at'])
