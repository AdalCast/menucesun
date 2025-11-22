from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from api.v1.routers import productos, categorias, menu

app = FastAPI(
    title="Cafetería API",
    version="1.0.0",
    description="API REST para gestión de menú de cafetería con FastAPI."
)

# ----------------------------
# CORS (permite conexión desde el frontend)
# ----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],         
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Rutas de la API
# ----------------------------
API_PREFIX = "/api/v1"

app.include_router(menu.router, prefix=API_PREFIX)
app.include_router(categorias.router, prefix=API_PREFIX)
app.include_router(productos.router, prefix=API_PREFIX)


# Servir interfaz gráfica 
app.mount(
    "/ui",
    StaticFiles(directory="frontend", html=True),
    name="frontend",
)


# Redirigir la raíz a la interfaz principal
@app.get("/")
def root():
    return RedirectResponse(url="/ui/")
