from sanic import Sanic
from api.admin import admin_api
from api.main import user_api

from sqlalchemy.ext.asyncio import create_async_engine
from contextvars import ContextVar
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
import asyncio
import settings

from api.models import Base

app = Sanic(__name__)
app.blueprint([admin_api, user_api])


def setup_database():
    _bind = create_async_engine(settings.DB_URL)
    _base_ctx = ContextVar('session')

    @app.middleware('request')
    async def inject_session(request):
        print('inject_session')
        request.ctx.session = sessionmaker(
            _bind,
            AsyncSession,
            expire_on_commit=False)()
        request.ctx.session_ctx_token = _base_ctx.set(request.ctx.session)

    @app.middleware('response')
    async def close_session(request, response):
        print('close_session')
        if hasattr(request.ctx, 'session_ctx_token'):
            _base_ctx.reset(request.ctx.session_ctx_token)
            await request.ctx.session.close()

    _metadata = Base.metadata

    async def init_models():
        async with _bind.begin() as conn:
            # await conn.run_sync(_metadata.drop_all)
            await conn.run_sync(_metadata.create_all)

    asyncio.run(init_models())


def run():
    setup_database()
    app.run(
        host=settings.HOST,
        port=settings.PORT,
        debug=settings.DEBUG,
        auto_reload=settings.DEBUG
    )


if __name__ == '__main__':
    run()
