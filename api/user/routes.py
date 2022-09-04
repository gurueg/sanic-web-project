from sanic import Blueprint
from sanic.response import text, json

from sqlalchemy.ext.asyncio import create_async_engine

from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_
from sqlalchemy.exc import IntegrityError

from ..encryptyng import get_activation_token, need_authentification,\
    check_token, check_activation_token, get_transaction_signasture,\
    get_encripdted_password
from ..models import User, Product, Account, Transaction


bp = Blueprint("user_api")


@bp.get('/')
async def main_page(request):
    if check_token(request):
        session = request.ctx.session
        async with session.begin():
            stmt = select(User).where(User.token == request.token)
            result = await session.execute(stmt)
            user = result.scalar()
        if user:
            return text(str(user.to_dict()))
        else:
            return text('User not found')
    else:
        return text('Need Auth.')


@bp.route('/register', methods=['get', 'post'])
async def register(request):
    if request.method == 'GET':
        return text('Register Form.')

    elif request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')
        if login is None or password is None:
            return text('invalid login or password')

        session = request.ctx.session
        async with session.begin():
            person = User(login, password)
            session.add_all([person])

        activation_token = get_activation_token(person)

        return text('http://127.0.0.1:8000/activate/' + activation_token)


@bp.exception(IntegrityError)
async def integrity_hanling(request, exception):
    return json({'message': 'User with that login already exists'}, 400)


@bp.route('/login', methods=['get', 'post'])
async def login(request):
    if request.method == 'GET':
        return text('Login Form.')

    elif request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')
        if login is None or password is None:
            return text('invalid username or password')

        session = request.ctx.session
        async with session.begin():
            encrypted_password = get_encripdted_password(password)
            stmt = select(User).where(
                and_(User.login == login, User.password == encrypted_password))
            result = await session.execute(stmt)
            person = result.scalar()
            if person is None:
                return json({'message': 'Wrong login or password'}, 400)

        return json(person.to_dict(), 200)


@bp.get('/activate/<activate_token>')
async def activate(request, activate_token):
    user_id = check_activation_token(activate_token)
    if user_id is None:
        return text('Invalid Activation Token')

    session = request.ctx.session
    async with session.begin():
        stmt = (select(User).where(User.id == user_id))
        result = await session.execute(stmt)
        person = result.scalar()
        person.is_activated = True
        return text(str(person.to_dict()))


@bp.get('/test/create')
async def create_products(request):
    session = request.ctx.session
    async with session.begin():
        lst = [
            {'name': 'name1', 'description': 'desc1', 'price': 1},
            {'name': 'name2', 'description': 'desc2', 'price': 2},
            {'name': 'name3', 'description': 'desc3', 'price': 3},
            {'name': 'name4', 'description': 'desc4', 'price': 3},
            {'name': 'name5', 'description': 'desc5', 'price': 100},
            {'name': 'name6', 'description': 'desc6', 'price': 2}
        ]
        adding = []
        for p in lst:
            adding.append(Product(p['name'], p['description'], p['price']))
        session.add_all(adding)
    return text('added')


@bp.get('/products')
@need_authentification
async def get_produts(request):
    session = request.ctx.session
    async with session.begin():
        stmt = select(Product).where(Product.in_stock)
        result = await session.execute(stmt)
        product_list = result.scalars()
        result = [i.to_dict() for i in product_list]

    return json(result)


@bp.get('/accounts')
@need_authentification
async def accounts(request):
    session = request.ctx.session
    async with session.begin():
        stmt = select(User).where(User.token == request.token)
        query_result = await session.execute(stmt)
        user = query_result.scalar()

        if user is None:
            return text('Invalid Token', 400)

        stmt = select(Account).where(Account.owner_id == user.id).\
            options(selectinload(Account.transactions))
        query_result = await session.execute(stmt)
        accounts = query_result.scalars().all()

        result = []
        for acc in accounts:
            transactions = [t.to_dict() for t in acc.transactions]
            acc_dict = acc.to_dict()
            acc_dict['transactions'] = transactions
            result.append(acc_dict)

    return json(result)


@bp.post('/products/buy')
@need_authentification
async def buy_product(request):
    product_id = request.json["product_id"]
    account_id = request.json["account_id"]

    if not product_id:
        return text("Need product id", 400)

    if not account_id:
        return text("Need account id", 400)

    session = request.ctx.session
    async with session.begin():
        stmt = select(User).where(User.token == request.token)
        result = await session.execute(stmt)
        user = result.scalar()

        stmt = select(Account).where(Account.id == account_id)
        result = await session.execute(stmt)
        account = result.scalar()

        stmt = select(Product).where(Product.id == product_id)
        result = await session.execute(stmt)
        product = result.scalar()

        if account is None or user is None or product is None:
            return text("Not found", 400)

        if user.id != account.owner_id:
            return text("It's not your account", 400)

        if account.balance < product.price:
            return text("Not Enough Money", 400)

        account.balance -= product.price

    return text('text')


@bp.post('/payment/webhook')
async def increase_balance(request):
    account_id = request.json["account_id"]
    user_id = request.json["user_id"]
    amount = request.json["amount"]

    if not account_id or not amount or not user_id:
        return text("Bad request body", 400)

    session = request.ctx.session
    async with session.begin():
        stmt = select(Account).where(Account.id == account_id)
        result = await session.execute(stmt)
        account = result.scalar()

        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar()

        if user is None:
            return text("User Not Found", 400)

        if account is None:
            account = Account(account_id)
            account.owner = user
            session.add_all([account])

        transaction = Transaction(account_id, amount)
        session.add_all([transaction])

        print(account)
        account.balance += amount

    signature = get_transaction_signasture(
        transaction.id,
        user_id,
        account_id,
        amount
    )

    response_data = {
        'signature': signature,
        'transaction_id': transaction.id,
        'user_id': user_id,
        'bill_id': account_id,
        'amount': amount
    }
    return json(response_data)
