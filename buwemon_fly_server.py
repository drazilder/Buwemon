#!/usr/bin/env python3
"""
Buwemon Fly.io Server - HTTP + WebSocket auf einem Port
"""
import asyncio
import json
import os
import sys
from pathlib import Path

try:
    from aiohttp import web, WSMsgType
except ImportError:
    os.system(f"{sys.executable} -m pip install aiohttp")
    from aiohttp import web, WSMsgType

PORT = int(os.environ.get('PORT', 8080))
BASE_DIR = Path(__file__).parent
rooms = {}

async def ws_handler(request):
    ws = web.WebSocketResponse(heartbeat=30)
    await ws.prepare(request)
    print("WS CONNECTED", flush=True)
    room_code = None
    async for msg in ws:
        if msg.type == WSMsgType.TEXT:
            try: data = json.loads(msg.data)
            except: continue
            t = data.get('t')
            print(f"MSG: {t}", flush=True)
            if t == 'create':
                room_code = data['code']
                rooms[room_code] = [ws]
                print(f"ROOM CREATED: {room_code}", flush=True)
            elif t == 'join':
                room_code = data['code']
                if room_code in rooms and len(rooms[room_code]) < 2:
                    rooms[room_code].append(ws)
                    await rooms[room_code][0].send_str(json.dumps({'t':'joined'}))
                    await ws.send_str(json.dumps({'t':'joined'}))
                    print(f"JOINED: {room_code}", flush=True)
                else:
                    await ws.send_str(json.dumps({'t':'error','msg':'not found'}))
            else:
                if room_code and room_code in rooms:
                    for c in rooms[room_code]:
                        if c != ws:
                            try: await c.send_str(msg.data)
                            except: pass
    if room_code and room_code in rooms:
        rooms[room_code] = [c for c in rooms[room_code] if c != ws]
        if not rooms[room_code]: del rooms[room_code]
    print("WS DISCONNECTED", flush=True)
    return ws

async def ping_handler(request):
    return web.Response(text='ok')

async def main():
    app = web.Application(client_max_size=100*1024*1024)
    app.router.add_get('/ws', ws_handler)
    app.router.add_get('/ping', ping_handler)
    app.router.add_static('/', str(BASE_DIR), show_index=True)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', PORT).start()
    print(f"READY ON PORT {PORT}", flush=True)
    await asyncio.Future()

asyncio.run(main())
