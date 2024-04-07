from fastapi import APIRouter, HTTPException
from mcstatus import MinecraftServer

router = APIRouter(prefix='/mobiles', tags=['minecft'])

SERVER_ADDRESS = "localhost:25565"


@router.get("/invoices")
async def read_server_status():
    server = MinecraftServer.lookup(SERVER_ADDRESS)
    status = server.status()
    return {
        "description": status.description,
        "players_online": status.players.online,
        "max_players": status.players.max,
        "version": status.version.name,
        "latency": status.latency,
        "online": True
    }

@router.get("/ping")
async def ping_server():
    server = MinecraftServer.lookup(SERVER_ADDRESS)
    try:
        latency = server.ping()
        return {"latency": latency, "online": True}
    except Exception:
        return {"online": False}