
from fastapi import FastAPI, Request, Depends
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from .routers import  mobiles, minecraft, fio, crm
from .services.database import get_db_connection
app = FastAPI(
    debug=True,
    title="Palantir",
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
app.include_router(minecraft.router)
app.include_router(fio.router)
app.include_router(crm.router)


origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Nebo "*" pro povolení všech zdrojů (ale pozor na bezpečnost!)
    allow_credentials=True,
    allow_methods=["*"],  # Metody HTTP, které chceš povolit
    allow_headers=["*"],  # Hlavičky, které chceš povolit
)

@app.get("/")
def read_root():
    return RedirectResponse(url='/docs', status_code=302)

@app.get("/url-list")
def get_all_urls():
    url_list = [{"path": route.path, "name": route.name} for route in app.routes]
    return url_list


# Using Request instance
@app.get("/url-list-from-request")
def get_all_urls_from_request(request: Request):
    url_list = [
        {"path": route.path, "name": route.name} for route in request.app.routes
    ]
    return url_list