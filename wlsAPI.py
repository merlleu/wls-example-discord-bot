import aiohttp
import asyncio
import json

class wlsAPI:
    host="https://system.warlegend.net"
    cookies={}
    def __init__(self, token):
        self.token=token
        self.jconf=json.dumps({
        "token": self.token
        })
    async def start(self):
        self.session = aiohttp.ClientSession()
        await self.connect()
        r=await self.get("/api/player/displayName/get/")
        print(f"Logged-in to WLS as {r['name']} ({r['id']})")
        await self.refresh_loop()

    async def refresh_loop(self):
        await asyncio.sleep(30*24*60*60)
        await self.connect()

    async def connect(self):
        r=await self.post("/api/oauth/wlsInternal/token/", data=self.jconf, cookies={}, parse_json=False)

    async def get(self, url, *args, parse_json=True, **kwargs):
        # print("GET", "".join((self.host, url)))
        async with self.session.get("".join((self.host, url)), *args, **kwargs) as r:
            if parse_json:
                return await r.json()
            else:
                return r
    async def post(self,url, *args, parse_json=True, **kwargs):
        # print("POST","".join((self.host, url)))
        async with self.session.post("".join((self.host, url)), *args, **kwargs) as r:
            if parse_json:
                return await r.json()
            else:
                return r


    async def get_tournament(self, tid):
        r=await self.get(f"/api/data/tournament/standings/{tid}/")
        return r

    async def get_participants(self, tid):
        r=await self.get(f"/api/data/tournament/dashboard/{tid}/")
        return r

    async def is_organizer(self, tid):
        r=await self.get(f"/api/tournament/organize/isOrga/{tid}/")
        return not r.get("error")

    async def get_player(self, pid):
        r=await self.get("/api/player/epicid/get/{}/".format(pid))
        return r

    async def invite_player(self, tid, pid):
        r=await self.post("/api/tournament/organize/players/invite/", json={
        "tid":tid, "id": pid
        })
        return r

    async def kick_player(self, tid, playerid):
        r=await self.post("/api/tournament/organize/kick/", json={
        "tid": tid, "id": playerid
        })
        return r

class YuniteAPI:
    host="https://yunite.xyz"
    def __init__(self, token):
        self.hdrs={
        "Y-Api-Key": token
        }
        self.session=aiohttp.ClientSession()
    async def get_player(self,gid, id):
        r= await self.get("/api/v2/servers/{}/regsys/single/byDiscordID/{}".format(gid, id))
        return r
    async def get(self, url, *args, parse_json=True, **kwargs):
        # print("GET", "".join((self.host, url)))
        async with self.session.get("".join((self.host, url)), *args, headers=self.hdrs, **kwargs) as r:
            if parse_json:
                return await r.json()
            else:
                return r
