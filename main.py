from fastapi import FastAPI

from routers.instagram import router

app = FastAPI(title='InstaParser')

app.include_router(router)
