from fastapi import FastAPI

# from dependencies import lifespan
from routers.instagram import router

app = FastAPI(title='InstaParser')

app.include_router(router)
