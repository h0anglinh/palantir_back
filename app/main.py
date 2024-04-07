from typing import Union

from fastapi import FastAPI

from .routers import  mobiles



app = FastAPI(
    title="ChimichangApp",
    summary="Deadpool's favorite app. Nuff said.",
    version="0.0.1-beta",
    terms_of_service="http://example.com/terms/",
    contact={
        "name": "L!(0)N",
        "url": "https://linhhoang.eu",
        "email": "linh.hoang@hotmail.cz",
    },
    license_info={
        "name": "NGINX",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)

app.include_router(mobiles.router)


@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}
