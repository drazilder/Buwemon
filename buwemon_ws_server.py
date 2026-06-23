#!/usr/bin/env python3
"""
Buwemon kombinierter HTTP + WebSocket Server auf Port 8765
WebSocket läuft über /ws Pfad auf demselben Port
"""
import asyncio
import json
import threading
import webbrowser
import os
import sys

try:
    import websockets
except ImportError:
    os.system(f"{sys.executable} -m pip install websockets")
    import websockets

try:
    from aiohttp import web
except ImportError:
    os.system(f"{sys.executable} -m pip install aiohttp")
    from aiohttp import web

PORT = 8765
os.chdir(os.path.dirname(os.path.abspath(__file__)))

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
                        host = rooms[room_code][0]
                        await host.send_str(json.dumps({'t': 'joined'}))
                        await ws.send_str(json.dumps({'t': 'joined'}))
                    else:
                        await ws.send_str(json.dumps({'t': 'error', 'msg': 'Room not found'}))
                else:
                    if room_code and room_code in rooms:
                        others = [c for c in rooms[room_code] if c != ws]
                        for other in others:
                            try:
                                await other.send_str(msg.data)
                            except:
                                pass
    except:
        pass
    finally:
        if room_code and room_code in rooms:
            rooms[room_code] = [c for c in rooms[room_code] if c != ws]
            if not rooms[room_code]:
                del rooms[room_code]
    return ws

async def main():
    app = web.Application()
    app.router.add_get('/ws', ws_handler)
    app.router.add_static('/', './')
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    
    print(f"Server läuft auf http://localhost:{PORT}")
    print(f"WebSocket: ws://localhost:{PORT}/ws")
    
    def open_browser():
        import time; time.sleep(0.8)
        webbrowser.open(f'http://localhost:{PORT}/buwemon.html')
    threading.Thread(target=open_browser, daemon=True).start()
    
    await asyncio.Future()

asyncio.run(main())
