from __future__ import annotations

import asyncio
import random
import string
from base64 import b64decode

import aiohttp
import aiofiles # type: ignore
import aiofiles.os # type: ignore
from aiohttp import web

def gen_id() -> str:
  pool: str = string.ascii_letters + string.digits
  return "".join(random.choices(pool,k=32))

def build_sanjuuni(src: str, out: str, *, 
                   binary: bool = False, 
                   cc_pal: bool = False, 
                   dithering: str = "none", 
                   width: int = None, # type: ignore
                   height: int = None, # type: ignore
                   output: str = "blit") -> str:
    if dithering not in ["threshold","ordered","lab-color","octree","kmeans","none"]:
      raise ValueError("dithering not in threshold, ordered, lab-color, octree, kmeans, none")
    if output not in ["bimg","nfp"]:
      raise ValueError("dithering not in bimg, nfp")
    
    builder = "sanjuuni {fmt} {dither} {pal} {h} {w} {b} -i {src} -o {out}"
    dither = ({
      "threshold": "-t",
      "ordered": "-O",
      "lab-color": "-L",
      "octree": "-8",
      "kmeans": "-k",
      "none": ""
    })[dithering]
    fmt = ({
      "bimg": "-b",
      "nfp": "-n"
    })[output]
    pal = "-p" if cc_pal else ""
    b = "-B" if binary else ""
    w = f"-W {width}" if width else ""
    h = f"-H {height}" if height else ""
    return builder.format(fmt=fmt,dither=dither,pal=pal,b=b,w=w,h=h, src=src, out=out)

routes = web.RouteTableDef()

@routes.post("/convert")
async def post_convert(request: web.Request) -> web.Response:
  body = await request.json()
  if "url" in body and "data" in body:
     return web.Response(status=400,body="url and data passed in json")
  dithering = body.get("dithering","none")
  pal = body.get("cc-palette",False)
  binary = body.get("binary",False)
  width = body.get("width",None)
  height = body.get("height",None)
  fmt = body.get("format","blit")

  job_id = gen_id()
  src = f"/tmp/sanjuuni_in{job_id}"
  out: str = f"/tmp/sanjuuni_out{job_id}.blit"

  try:
    cmd = build_sanjuuni(src,out,output=fmt,dithering=dithering,cc_pal=pal,binary=binary,width=width,height=height)
    print(cmd)
  except ValueError as e:
    return web.Response(status=400,body=str(e))
  
  data: bytes

  try:
    if "url" in body:
      async with aiohttp.ClientSession() as sess:
        async with sess.get(body["url"]) as resp:
          data = await resp.read()
    elif "data" in body:
      data = b64decode(body["data"])
  except:
    return web.Response(status=400,body="failed parsing data/url")
  
  async with aiofiles.open(f"/tmp/sanjuuni_in{job_id}","wb") as f:
    await f.write(data) #type: ignore
  
  # run sanjuuni with asyncio subprocess
  process = await asyncio.subprocess.create_subprocess_shell(cmd)
  code = await process.wait()
  if code == 0:
    async with aiofiles.open(f"/tmp/sanjuuni_out{job_id}.blit") as f:
      lua = await f.read()
    await aiofiles.os.remove(f"/tmp/sanjuuni_in{job_id}")
    await aiofiles.os.remove(f"/tmp/sanjuuni_out{job_id}.blit")
    return web.Response(body=lua,content_type="text/x-lua")
  else:
    return web.Response(body=f"sanjuuni exited with code {code}",status=500)
  
app = web.Application()
app.add_routes(routes)

web.run_app(app) # type: ignore