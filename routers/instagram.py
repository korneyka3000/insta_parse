import asyncio
import concurrent.futures
from functools import partial
from typing import Annotated

from fastapi import APIRouter, Query

from dependencies import SeleniumWorker, UrlsResponse, get_settings

router = APIRouter()


@router.get("/getPhotos")
async def get_photos(
        username: Annotated[str, Query(description='instagram username', max_length=100)],
        max_count: Annotated[int, Query(description='max amount of photo urls to get', ge=1)]
) -> UrlsResponse:
    loop = asyncio.get_running_loop()

    with concurrent.futures.ThreadPoolExecutor() as pool:
        result: list = await loop.run_in_executor(
            pool, partial(
                SeleniumWorker(**get_settings().model_dump()).get_url,
                username, max_count
            ))

    return UrlsResponse(urls=result)
