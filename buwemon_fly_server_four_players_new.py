#!/usr/bin/env python3
"""
Buwemon Fly.io Server - 4-Spieler Version
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

PORT = int(os.environ.get('PORT', 8081))
BASE_DIR = Path(__file__).parent
rooms = {}  # code -> list of ws connections (max 4)

async def ws_handler(request):
    ws = web.WebSocketResponse(heartbeat=30)
    await ws.prepare(request)
    print("WS CONNECTED", flush=True)
    room_code = None
    player_num = None

    async for msg in ws:
        if msg.type == WSMsgType.TEXT:
            try: data = json.loads(msg.data)
            except: continue
            t = data.get('t')
            print(f"MSG: {t}", flush=True)

            if t == 'create':
                room_code = data['code']
                rooms[room_code] = [ws]
                player_num = 1
                await ws.send_str(json.dumps({'t': 'created', 'playerNum': 1}))
                print(f"ROOM CREATED: {room_code}", flush=True)

            elif t == 'join':
                room_code = data['code']
                if room_code in rooms and len(rooms[room_code]) < 4:
                    rooms[room_code].append(ws)
                    player_num = len(rooms[room_code])
                    # Tell all players current player count and new player's number
                    total = len(rooms[room_code])
                    for i, c in enumerate(rooms[room_code]):
                        await c.send_str(json.dumps({
                            't': 'joined',
                            'playerNum': i + 1,
                            'total': total
                        }))
                    print(f"JOINED: {room_code} ({total}/4)", flush=True)
                else:
                    await ws.send_str(json.dumps({'t': 'error', 'msg': 'not found or full'}))

            else:
                # Broadcast to all others in room
                if room_code and room_code in rooms:
                    for c in rooms[room_code]:
                        if c != ws:
                            try: await c.send_str(msg.data)
                            except: pass

    # Cleanup on disconnect
    if room_code and room_code in rooms:
        rooms[room_code] = [c for c in rooms[room_code] if c != ws]
        if not rooms[room_code]:
            del rooms[room_code]
        else:
            # Notify remaining players
            total = len(rooms[room_code])
            for i, c in enumerate(rooms[room_code]):
                try:
                    await c.send_str(json.dumps({
                        't': 'player_left',
                        'playerNum': i + 1,
                        'total': total
                    }))
                except: pass
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
