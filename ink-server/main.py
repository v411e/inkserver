import logging
import os
import re

from aiohttp import web, ClientSession
from image_provider import ImageProviderInterface, XKCDImageProvider, LocalImageProvider

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


async def handle_root_post(request: web.Request) -> web.Response:
    """Handler for route: /

    Args:
        request (web.Request): Request

    Returns:
        web.Response: Response
    """
    log.info("Post-Request to /")
    json: dict = await request.json()
    log.info(f"Raw json: {json}")
    return web.Response(text="Success!")


def isAuthenticated(request: web.Request) -> bool:
    """Raise error if request is unauthenticated.

    Args:
        params (dict): Params of the request. Must include 'secret' key.

    Raises:
        Exception: When AUTH_SECRET ist not configured
        web.HTTPUnauthorized: When request is not allowed

    Returns:
        bool: True if request is authenticated
    """

    secret = ""
    try:
        with open("/run/secrets/auth_secret", "r") as secret_file:
            secret = secret_file.read().rstrip("\n")
    except FileNotFoundError as e:
        log.warning(
            "'auth_secret' not at /run/secrets/auth_secret. Fallback to environment variable AUTH_SECRET."
        )
        if not os.getenv("AUTH_SECRET"):
            raise Exception("AUTH_SECRET not configured.")
        else:
            secret = os.getenv("AUTH_SECRET")

    if (
        not request.rel_url.query.get("secret")
        or request.rel_url.query.get("secret", "") != secret
    ):
        log.info("Unauthorized request to /random")
        raise web.HTTPUnauthorized

    return True


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

    # check if request is authenticated
    isAuthenticated(request)

    # I want only XKCD for now.
    # image_provider: ImageProviderInterface = ImageProviderInterface.random_provider()
    # image_provider: ImageProviderInterface = XKCDImageProvider()
    image_provider: ImageProviderInterface = LocalImageProvider()
    image_path = await image_provider.get_random_image()
    if image_path:
        return web.FileResponse(path=image_path)
    else:
        raise web.HTTPInternalServerError(reason="Error fetching image.")


async def handle_upload_form(request: web.Request) -> web.Response:
    """Provide html form for file upload

    Args:
        request (web.Request): Request

    Returns:
        web.Response: Response with html form
    """
    # check if request is authenticated
    isAuthenticated(request)

    return web.Response(
        text=f"""
    <form action="/upload?secret={request.rel_url.query.get("secret")}" method="post" accept-charset="utf-8"
      enctype="multipart/form-data">

    <label for="file">Image file</label>
    <input id="file" name="file" type="file" value="" accept="image/*"/>

    <input type="submit" value="submit"/>
    </form>
    """,
        content_type="text/html",
    )


async def handle_upload(request: web.Request) -> web.Response:
    """Handle image file upload via post request

    Args:
        request (web.Request): Request

    Raises:
        web.HTTPServerError: If not an image file

    Returns:
        web.Response: Success message
    """
    # check if request is authenticated
    isAuthenticated(request)

    reader = await request.multipart()

    field = await reader.next()
    assert field.name == "file"
    filename = field.filename

    if not filename.endswith(
        (
            ".jpeg",
            ".JPEG",
            ".jpg",
            ".JPG",
            ".png",
            ".PNG",
            ".gif",
            ".GIF",
            ".webp",
            ".WEBP",
        )
    ):
        raise web.HTTPServerError(text="This is not a image.")

    # You cannot rely on Content-Length if transfer is chunked.
    size = 0
    with open(os.path.join("data", filename), "wb") as f:
        while True:
            chunk = await field.read_chunk()  # 8192 bytes by default.
            if not chunk:
                break
            size += len(chunk)
            f.write(chunk)

    return web.Response(
        text="{} sized of {} successfully stored" "".format(filename, size)
    )


async def handle_fetch_url(request: web.Request) -> web.Response:
    """Fetch an image file from a given url.

    Args:
        request (web.Request): Post request with json data

    Returns:
        web.Response: Success message
    """
    # check if request is authenticated
    isAuthenticated(request)
    json: dict = await request.json()
    log.info(f"Raw json: {json}")
    img_url = json.get("url", "")
    img_url = re.match(r'^(.*\.(jpeg|jpg|png|gif|svg|webp))', img_url, re.IGNORECASE).group()
    filename = img_url.split("/")[-1]

    async with ClientSession() as session:
        logging.getLogger("ink").info(f"Fetching image from {img_url}")
        async with session.get(img_url) as resp:
            img = await resp.read()
            with open(os.path.join("data", filename), "wb") as f:
                f.write(img)
    return web.Response(text="Success")


app = web.Application()
app.add_routes(
    [
        web.get("/", handle_root),
        web.post("/", handle_root_post),
        web.get("/random", handle_random),
        web.get("/upload", handle_upload_form),
        web.post("/upload", handle_upload),
        web.post("/fetch-url", handle_fetch_url),
    ]
)

if __name__ == "__main__":
    log.info("Ink server is running.")
    web.run_app(app)
