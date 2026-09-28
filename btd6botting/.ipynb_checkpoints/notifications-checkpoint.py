import io

import requests

from .config import DISCORD_WEBHOOK


def post_to_discord(message, image=None):
    try:
        data = {"content": message}

        if image is not None:
            with io.BytesIO() as img_bytes:
                image.save(img_bytes, format="PNG")
                img_bytes.seek(0)
                files = {"file": ("screenshot.png", img_bytes, "image/png")}
                response = requests.post(
                    DISCORD_WEBHOOK,
                    data=data,
                    files=files,
                    timeout=5,
                )
                response.close()
        else:
            response = requests.post(
                DISCORD_WEBHOOK,
                json=data,
                timeout=5,
            )
            response.close()

    except Exception:
        pass
