from fastapi import APIRouter,HTTPException
from mcstatus import JavaServer
import os
router = APIRouter(prefix='/mc')
from dotenv import load_dotenv
load_dotenv()
SERVER_ADDRESS = os.getenv("MC_URL")


@router.get("/status", tags=['minecraft'])
async def read_server_status():
    try:
        server = JavaServer.lookup(SERVER_ADDRESS)
        status = server.status()
        return {
            "description": status.description,
            "players_online": status.players.online,
            "max_players": status.players.max,
            "version": status.version.name,
            "latency": status.latency,
            "online": True
        }
    except ConnectionRefusedError:  # Pokud je server nedostupný
        raise HTTPException(status_code=503, detail="Minecraft server is offline or not reachable")
    except:
        raise HTTPException(status_code=500, detail="MC server probably offline")
       

@router.get("/ping", tags=['minecraft'])
async def ping_server():
    server = JavaServer.lookup(SERVER_ADDRESS)
    try:
        latency = server.ping()
        return {"latency": latency, "online": True}
    except ConnectionRefusedError:  # Pokud je server nedostupný
        return {"latency": 'N/A', "online": False}
    except Exception as e:  # Pro všechny ostatní chyby
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    
@router.get("/query", tags=['minecraft'])
async def read_server_query():
    server = JavaServer.lookup(SERVER_ADDRESS)
    try:
        query = server.query()  # Zkoušíme provést Query
        return {
            "version": query.software.version,
            "motd": query.motd,
            "map": query.map,
            "players_online": query.players.online,
            "max_players": query.players.max,
            "players_names": query.players.names,  # Seznam jmen online hráčů
            "plugins": query.software.plugins,
            "online": True
        }
    except ConnectionRefusedError:  # Pokud je server nedostupný
        raise HTTPException(status_code=503, detail="Minecraft server is offline or not reachable")
    except Exception as e:  # Pro všechny ostatní chyby
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

import aiomcrcon
import asyncio

@router.get("/rcon", tags=['minecraft'])
async def send_rcon_command(command: str):

    RCON_HOST = "localhost"  # Adresa serveru
    RCON_PORT = 25575        # RCON port
    RCON_PASSWORD = "password1234"  # RCON heslo
    try:
        client = aiomcrcon.Client(RCON_HOST, RCON_PORT, RCON_PASSWORD)
        await client.connect()
    except aiomcrcon.errors.RCONConnectionError as e:
        return { "error": e }

   
    response = await client.send_cmd(command)
    await client.close()
    return response
    # try:
    # except aiomcrcon.RCONConnectionError as e:
    #     raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    # except aiomcrcon.IncorrectPasswordError:
    #     raise HTTPException(status_code=500, detail="The provided password was incorrect...")
    # except e:
    #     raise HTTPException(status_code=500, detail=e)

    # try:
      
    # except aiomcrcon.ClientNotConnectedError as e:
    #     raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    # except:
    #     return {'hello': 'world'}

    







import subprocess

@router.post("/start-minecraft-server", tags=['minecraft'])
async def start_minecraft_server():
    try:
        # Předpokládá, že 'minecraft_server.jar' je ve stejném adresáři jako tento skript
        # a že Java je nainstalovaná a správně nastavená
        process = subprocess.Popen(["java", "-Xmx1024M", "-Xms1024M", "-jar", "/home/thanos/minecraft_server.jar", "nogui"],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return {"message": "Minecraft server is starting."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")