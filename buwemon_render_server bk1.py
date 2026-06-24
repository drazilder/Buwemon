#!/usr/bin/env python3
"""
Buwemon Render.com Server
HTTP + WebSocket auf Port $PORT (von Render gesetzt)
"""
import asyncio
import json
import os
import sys
import threading
import webbrowser
from pathlib import Path

try:
    from aiohttp import web
except ImportError:
    os.system(f"{sys.executable} -m pip install aiohttp")
    from aiohttp import web

PORT = int(os.environ.get('PORT', 8765))
BASE_DIR = Path(__file__).parent

rooms = {}

async def ws_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    room_code = None
    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                except:
                    continue
                t = data.get('t')
                if t == 'create':
                    room_code = data['code']
                    rooms[room_code] = [ws]
                    print(f"Room created: {room_code}")
                elif t == 'join':
                    room_code = data['code']
                    if room_code in rooms and len(rooms[room_code]) < 2:
                        rooms[room_code].append(ws)
                        print(f"Joined: {room_code}")
                        await rooms[room_code][0].send_str(json.dumps({'t':'joined'}))
                        await ws.send_str(json.dumps({'t':'joined'}))
                    else:
                        await ws.send_str(json.dumps({'t':'error','msg':'Room not found'}))
                else:
                    if room_code and room_code in rooms:
                        for c in rooms[room_code]:
                            if c != ws:
                                try: await c.send_str(msg.data)
                                except: pass
    except:
        pass
    finally:
        if room_code and room_code in rooms:
            rooms[room_code] = [c for c in rooms[room_code] if c != ws]
            if not rooms[room_code]:
                del rooms[room_code]
    return ws

async def main():
    app = web.Application(client_max_size=100*1024*1024)
    app.router.add_get('/ws', ws_handler)
    app.router.add_static('/', str(BASE_DIR), show_index=True)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    print(f"Server läuft auf Port {PORT}")
    await asyncio.Future()

asyncio.run(main())
