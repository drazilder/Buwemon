#!/usr/bin/env python3
"""
Buwemon WebSocket + HTTP Server
Doppelklick oder: python3 buwemon_ws_server.py
"""
import asyncio, json, http.server, threading, webbrowser, os, sys

try:
    import websockets
except ImportError:
    os.system(f"{sys.executable} -m pip install websockets")
    import websockets

PORT_HTTP = 8765
PORT_WS = 8766
os.chdir(os.path.dirname(os.path.abspath(__file__)))

rooms = {}  # code -> [ws1, ws2]

async def handler(websocket):
    room_code = None
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
            except:
                continue
            
            if data.get('t') == 'create':
                room_code = data['code']
                rooms[room_code] = [websocket]
                print(f"Room created: {room_code}")
                
            elif data.get('t') == 'join':
                room_code = data['code']
                if room_code in rooms and len(rooms[room_code]) < 2:
                    rooms[room_code].append(websocket)
                    print(f"Joined room: {room_code}")
                    # Notify host that someone joined
                    host = rooms[room_code][0]
                    await host.send(json.dumps({'t': 'joined'}))
                    # Notify guest they're connected
                    await websocket.send(json.dumps({'t': 'joined'}))
                else:
                    await websocket.send(json.dumps({'t': 'error', 'msg': 'Room not found'}))
                    
            else:
                # Relay to other client in same room
                if room_code and room_code in rooms:
                    others = [c for c in rooms[room_code] if c != websocket]
                    for other in others:
                        try:
                            await other.send(message)
                        except:
                            pass
    except:
        pass
    finally:
        if room_code and room_code in rooms:
            rooms[room_code] = [c for c in rooms[room_code] if c != websocket]
            if not rooms[room_code]:
                del rooms[room_code]
        print(f"Client disconnected, rooms: {list(rooms.keys())}")

async def main():
    async with websockets.serve(handler, "0.0.0.0", PORT_WS):
        print(f"WebSocket: ws://localhost:{PORT_WS}")
        print(f"HTTP:      http://localhost:{PORT_HTTP}")
        await asyncio.Future()

def run_http():
    class H(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    http.server.HTTPServer(('', PORT_HTTP), H).serve_forever()

threading.Thread(target=run_http, daemon=True).start()

def open_browser():
    import time; time.sleep(0.5)
    webbrowser.open(f'http://localhost:{PORT_HTTP}/buwemon_ws.html')
threading.Thread(target=open_browser, daemon=True).start()

print("Starte Server...")
asyncio.run(main())
