
from sqlalchemy import Column, Integer, String,\
    Boolean, ForeignKey, CheckConstraint
from sqlalchemy.orm import declarative_base, relationship
import jwt

from encryptyng import get_encripdted_password, get_user_auth_token

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    login = Column(String(40), unique=True)
    password = Column(String(33))
    token = Column(String())
    is_admin = Column(Boolean, nullable=False, default=False)
    is_activated = Column(Boolean, nullable=False, default=False)
    is_banned = Column(Boolean, nullable=False, default=False)
    accounts = relationship('Account', back_populates='owner')

    def __init__(self, login, password, is_admin=False):
        self.login = login
        self.password = get_encripdted_password(password)
        self.is_admin = is_admin
        self.token = get_user_auth_token(login)

    def to_dict(self):
        return {
            'id': self.id,
            'token': self.token,
            'login': self.login
        }


class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    title = Column(String(40))
    description = Column(String())
    price = Column(Integer)
    in_stock = Column(Boolean, default=True)

    def __init__(self, title, description, price):
        self.title = title
        self.description = description
        self.price = price

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'price': self.price
        }


class Account(Base):
    __tablename__ = 'accounts'
    __table_args__ = (
        CheckConstraint('balance > 0', name='positive_balance_cons'),
    )

    id = Column(Integer, primary_key=True)
    balance = Column(Integer)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship('User', back_populates='accounts')
    transactions = relationship('Transaction', back_populates='account')

    def __init__(self, id=None):
        if id is not None:
            self.id = id
            self.balance = 0

    def to_dict(self):
        return {
            'id': self.id,
            'balance': self.balance
        }


class Transaction(Base):
    __tablename__ = 'transactions'
    __table_args__ = (
        CheckConstraint('amount > 0', name='positive_amount_cons'),
    )

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    amount = Column(Integer)
    account = relationship('Account', back_populates='transactions')

    def __init__(self, account_id, amount):
        self.account_id = account_id
        self.amount = amount

    def to_dict(self):
        return {
            'id': self.id,
            'account_id': self.account_id,
            'amount': self.amount
        }
