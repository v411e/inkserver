import logging
import os

from aiohttp import web
from image_provider import ImageProviderInterface, XKCDImageProvider

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.getLevelName("INFO"),
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("ink")


async def handle_root(request: web.Request) -> web.Response:
    """Handler for route: /

    Args:
        request (web.Request): Request

    Returns:
        web.Response: Response
    """
    log.info("Request to /")
    text = f"Use /random to return a random image."
    return web.Response(text=text)


async def handle_random(request: web.Request) -> web.FileResponse:
    """Handler for route: /random

    Args:
        request (web.Request): Request

    Raises:
        Exception: If AUTH_SECRET is not configured
        web.HTTPUnauthorized: If secret is not provided via params
        web.HTTPInternalServerError: If image fetching failed

    Returns:
        web.FileResponse: Response
    """
    log.info("Request to /random")

    # read params
    params = {}
    params["width"] = request.rel_url.query.get("width", "1200")
    params["heigth"] = request.rel_url.query.get("heigth", "800")
    params["format"] = request.rel_url.query.get("format", "png")
    params["secret"] = request.rel_url.query.get("secret")

    # check if request is authenticated
    secret = ""
    try:
        with open('/run/secrets/auth_secret', 'r') as secret_file:
            secret = secret_file.read()
    except FileNotFoundError as e:
        log.warning("'auth_secret' not at /run/secrets/auth_secret. Fallback to environment variable AUTH_SECRET.")
        if not os.getenv("AUTH_SECRET"):
            raise Exception("AUTH_SECRET not configured.")
        else:
            secret = os.getenv("AUTH_SECRET")
    
    if not params["secret"] or params["secret"] != secret:
        log.info("Unauthorized request to /random")
        raise web.HTTPUnauthorized

    # I want only XKCD for now.
    # image_provider: ImageProviderInterface = ImageProviderInterface.random_provider()
    image_provider: ImageProviderInterface = XKCDImageProvider()
    image_path = await image_provider.get_random_image()
    if image_path:
        return web.FileResponse(path=image_path)
    else:
        raise web.HTTPInternalServerError(reason="Error fetching image.")


async def handle_upload(request: web.Request):
    text = "Not yet implemented."
    return web.Response(text=text)


app = web.Application()
app.add_routes(
    [
        web.get("/", handle_root),
        web.get("/random", handle_random),
        web.post("/upload", handle_upload),
    ]
)

if __name__ == "__main__":
    log.info("Ink server is running.")
    web.run_app(app)
