"""Local film preview with byte ranges and fresh delivery metadata."""
from pathlib import Path
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parents[1]


class FreshMetadataFiles(StaticFiles):
    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        if path in {'', '.', '/'} or Path(path).suffix in {'.html', '.json', '.vtt', '.srt', '.md'}:
            response.headers['Cache-Control'] = 'no-store'
        return response


app = Starlette(routes=[Mount('/', app=FreshMetadataFiles(directory=ROOT, html=True))])
