"""Round-trip check for the FLEET-335 Phase 2 server patch (message kind 5, a text note).

Connects to a running PersonaPlex server, streams silence as Opus at real time, sends one
note after --note-at seconds, and prints what the server sent back. The server log should
show "note queued" and then "fed a N-token note in M frames". No microphone needed.

    python fleet/phase2/note_client.py --url https://127.0.0.1:8998 --note "Reminder. The page is called News Factory."
"""

from __future__ import annotations

import argparse
import asyncio
import ssl
import time
import urllib.parse

import aiohttp
import numpy as np
import sphn

SAMPLE_RATE = 24000
FRAME = 1920  # 80 ms at 24 kHz


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="https://127.0.0.1:8998")
    parser.add_argument("--prompt", default="Your name is Ruby. You work for Limited Edition Jonathan.")
    parser.add_argument("--voice", default="NATF2.pt")
    parser.add_argument("--note", required=True)
    parser.add_argument("--note-at", type=float, default=5.0, help="seconds after the handshake")
    parser.add_argument("--seconds", type=float, default=40.0, help="how long to stream silence after the handshake")
    args = parser.parse_args()

    query = urllib.parse.urlencode({"text_prompt": args.prompt, "voice_prompt": args.voice, "seed": 101})
    ws_url = args.url.replace("https://", "wss://").replace("http://", "ws://") + "/api/chat?" + query
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    writer = sphn.OpusStreamWriter(SAMPLE_RATE)
    heard = []
    audio_bytes = 0
    handshake_at = None

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(ws_url, ssl=ctx) as ws:

            async def reader() -> None:
                nonlocal audio_bytes, handshake_at
                async for msg in ws:
                    if msg.type != aiohttp.WSMsgType.BINARY or not msg.data:
                        continue
                    kind = msg.data[0]
                    if kind == 0 and handshake_at is None:
                        handshake_at = time.time()
                        print("handshake", flush=True)
                    elif kind == 1:
                        audio_bytes += len(msg.data) - 1
                    elif kind == 2:
                        heard.append((round(time.time() - (handshake_at or time.time()), 1), msg.data[1:].decode("utf8", "replace")))

            task = asyncio.create_task(reader())
            deadline = time.time() + 60
            while handshake_at is None:
                if time.time() > deadline:
                    raise SystemExit("no handshake within 60 s")
                await asyncio.sleep(0.1)
            silence = np.zeros(FRAME, dtype=np.float32)
            start = time.time()
            sent_note = False
            frames = 0
            while time.time() - start < args.seconds:
                if not sent_note and time.time() - start >= args.note_at:
                    await ws.send_bytes(b"\x05" + args.note.encode("utf8"))
                    sent_note = True
                    print(f"note sent at {time.time() - start:.1f}s", flush=True)
                writer.append_pcm(silence)
                data = writer.read_bytes()
                if data:
                    await ws.send_bytes(b"\x01" + data)
                frames += 1
                await asyncio.sleep(max(0.0, start + frames * 0.08 - time.time()))
            await ws.close()
            task.cancel()
    print("audio bytes back:", audio_bytes)
    print("text back:", "".join(t for _, t in heard))


if __name__ == "__main__":
    asyncio.run(main())
