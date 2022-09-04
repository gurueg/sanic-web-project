from encryptyng import get_activation_token, need_authentification,\
    check_token, check_activation_token, get_transaction_signasture,\
    get_encripdted_password

from sanic import Blueprint
from sanic.response import json
from models import User, Product, Account,\
    get_user_by_token, get_user_by_id

from sqlalchemy import select
from sqlalchemy.orm import selectinload

bp = Blueprint('admin')


@bp.get('/products')
@need_authentification
async def watch_products(request):
    session = request.ctx.session
    async with session.begin():
        user = await get_user_by_token(session, request.token)

        if not user.is_admin:
            return json({'message': 'Page Not Found'}, 404)

        stmt = select(Product)
        result = await session.execute(stmt)
        products = result.scalars().all()

    return json([p.to_dict() for p in products])


@bp.get('/users')
@need_authentification
async def watch_users(request):
    session = request.ctx.session
    async with session.begin():
        user = await get_user_by_token(session, request.token)

        if not user.is_admin:
            return json({'message': 'Page Not Found'}, 404)

        stmt = select(User).options(selectinload(User.accounts))
        query_result = await session.execute(stmt)
        users = query_result.scalars().all()

        result = []
        for person in users:
            accounts = [acc.to_dict() for acc in person.accounts]
            acc_dict = person.to_dict()
            acc_dict['accounts'] = accounts
            result.append(acc_dict)

    return json(result)


@bp.post('/ban_user')
@need_authentification
async def change_user_ban_status(request):
    session = request.ctx.session
    async with session.begin():
        admin = await get_user_by_token(session, request.token)

        if not admin.is_admin:
            return json({'message': 'Page Not Found'}, 404)

        user_id = request.json.user_id
        ban_status = request.json.status

        if user_id is None or ban_status is None:
            return json({'message': 'Bad request body'}, 400)

        user = await get_user_by_id(session, user_id)
        user.is_banned = ban_status

    return json({'message': f'User {user_id} change status to {ban_status}'})
