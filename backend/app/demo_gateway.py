"""Small authenticated demo gateway for built React + an existing local API.

No model, database credentials or Groq key are loaded by this process. Expose this
gateway through the temporary tunnel, never a development server or database.
"""
from collections import deque
from contextlib import asynccontextmanager
from pathlib import Path
import base64
import binascii
import os
import secrets
import time
from fastapi import FastAPI,Request
from fastapi.responses import FileResponse,JSONResponse,Response
import httpx

ROOT=Path(__file__).resolve().parents[2]
PUBLIC_GET_PREFIXES=('/api/v2/mas/runs/','/api/v1/experiments/')
PUBLIC_GET_PATHS={'/api/v2/system/readiness','/api/v2/knowledge/sources','/api/v2/knowledge/graph','/api/v2/mas/agents','/api/v1/experiments','/health'}

def create_gateway(*,password=None,upstream=None,dist=None,transport=None):
    password=password if password is not None else os.getenv('DEMO_ACCESS_PASSWORD','')
    if len(password)<16:raise ValueError('DEMO_ACCESS_PASSWORD must contain at least 16 characters')
    upstream=upstream or os.getenv('DEMO_UPSTREAM','http://127.0.0.1:8000')
    parsed=httpx.URL(upstream)
    if parsed.scheme!='http' or parsed.host not in ('127.0.0.1','localhost'):raise ValueError('The temporary gateway must target a loopback HTTP backend')
    dist=Path(dist or ROOT/'frontend/dist').resolve()
    if not (dist/'index.html').is_file():raise ValueError('Build frontend first: cd frontend; npm run build')
    @asynccontextmanager
    async def lifespan(app):
        async with httpx.AsyncClient(base_url=upstream,timeout=125,transport=transport,trust_env=False,follow_redirects=False) as client:
            app.state.client=client
            yield
    app=FastAPI(title='GlucoLab temporary demo gateway',docs_url=None,redoc_url=None,openapi_url=None,lifespan=lifespan)
    attempts=deque()
    @app.middleware('http')
    async def gate(request,call_next):
        try:
            scheme,credential=request.headers.get('authorization','').split(' ',1)
            user,provided=base64.b64decode(credential,validate=True).decode().split(':',1)
            valid=scheme.lower()=='basic' and secrets.compare_digest(user,'demo') and secrets.compare_digest(provided,password)
        except (ValueError,UnicodeError,binascii.Error,TypeError):valid=False
        if not valid:return Response(status_code=401,headers={'WWW-Authenticate':'Basic realm="GlucoLab demo", charset="UTF-8"','Cache-Control':'no-store'})
        try:length=int(request.headers.get('content-length','0'))
        except ValueError:return JSONResponse({'detail':'DEMO_INVALID_CONTENT_LENGTH'},400)
        if length<0:return JSONResponse({'detail':'DEMO_INVALID_CONTENT_LENGTH'},400)
        if length>16384:return JSONResponse({'detail':'DEMO_REQUEST_TOO_LARGE'},413)
        response=await call_next(request)
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Referrer-Policy']='strict-origin-when-cross-origin'
        response.headers['Cache-Control']='no-store' if request.url.path.startswith('/api/') else 'no-cache'
        response.headers['Content-Security-Policy']="default-src 'self'; img-src 'self' data:; font-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; script-src 'self'; frame-ancestors 'none'"
        return response
    @app.api_route('/{path:path}',methods=['GET','POST'])
    async def proxy(path:str,request:Request):
        route='/'+path
        if route.startswith('/api/') or route=='/health':
            allowed=(request.method=='POST' and route=='/api/v2/mas/runs') or (request.method=='GET' and (route in PUBLIC_GET_PATHS or any(route.startswith(prefix) for prefix in PUBLIC_GET_PREFIXES)))
            if not allowed:return JSONResponse({'detail':'DEMO_ROUTE_NOT_AVAILABLE'},404)
            content=await request.body()
            if len(content)>16384:return JSONResponse({'detail':'DEMO_REQUEST_TOO_LARGE'},413)
            if request.method=='POST':
                now=time.monotonic()
                while attempts and now-attempts[0]>=60:attempts.popleft()
                if len(attempts)>=6:return JSONResponse({'detail':'DEMO_RATE_LIMIT'},429,headers={'Retry-After':'60'})
                attempts.append(now)
            try:
                response=await app.state.client.request(request.method,route,params=request.query_params,content=content,headers={'Content-Type':request.headers.get('content-type','application/json')})
                return Response(response.content,response.status_code,media_type=response.headers.get('content-type','application/json'))
            except httpx.HTTPError:return JSONResponse({'detail':'DEMO_BACKEND_UNAVAILABLE'},503)
        if request.method!='GET':return Response(status_code=405)
        target=(dist/path).resolve()
        if not target.is_relative_to(dist):return Response(status_code=404)
        if target.is_file():return FileResponse(target)
        if '.' in Path(path).name:return Response(status_code=404)
        return FileResponse(dist/'index.html')
    return app
