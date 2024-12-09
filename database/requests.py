from asyncio import Lock
import asyncio
import datetime
from database.models import Accounts, CountryCode, Transaction, User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import joinedload

from sqlalchemy.exc import IntegrityError

class UserReq:
    def __init__(self, db_session_maker: async_sessionmaker) -> None:
        self.db_session_maker = db_session_maker
        self.lock = Lock()

    async def add_user(self, uid: int, uname: str):
        async with self.lock:
            async with self.db_session_maker() as session:
                try:
                    new_user = User(uid=uid, uname=uname)
                    session.add(new_user)
                    await session.commit()
                    return True
                except IntegrityError:
                    await session.rollback()
                    return False
                
    async def add_transaction(self, user_id: int, value: float, valuta: str, date: datetime):
        async with self.lock:
            async with self.db_session_maker() as session:
                transaction = Transaction(
                    user=user_id,
                    value=value,
                    valuta=valuta,
                    date=date,
                )
                session.add(transaction)
                return True

    async def get_user_language(self, uid: int) -> str:
        async with self.lock:
            async with self.db_session_maker() as session:
                result = await session.execute(
                    select(User.language).filter(User.uid == uid)
                )
                user_language = result.scalar()
                return user_language or "en"
            
    async def get_user(self, uid: int) -> str:
        async with self.lock:
            async with self.db_session_maker() as session:
                result = await session.execute(
                    select(User.uid).filter(User.uid == uid)
                )
                user_language = result.scalar()
                return user_language or "en"
            
    async def get_user_transactions(self, uid: int):
        async with self.lock:
            async with self.db_session_maker() as session:
                result = await session.execute(
                    select(Transaction).filter(Transaction.user == uid)
                )
                transactions = result.scalars().all()
                return transactions

            
    async def get_balance_user(self, uid: str) -> int:
        async with self.lock:
            async with self.db_session_maker() as session:
                result = await session.execute(
                    select(User.balance).filter(User.uid == uid)
                )
                user_balance = result.scalar()
                return user_balance or 0
    
    async def set_user_language(self, uid: int, new_language: str) -> bool:
        async with self.lock:
            async with self.db_session_maker() as session:
                try:
                    user = await session.execute(select(User).filter(User.uid == uid))
                    user = user.scalar()

                    if user:
                        user.language = new_language
                        await session.commit()
                        return True
                    else:
                        return False
                except IntegrityError as e:
                    await session.rollback()
                    return False
                

    async def add_balance(self, uid: int, balance: int) -> bool:
        async with self.lock:
            async with self.db_session_maker() as session:
                try:
                    user = await session.execute(select(User).filter(User.uid == uid))
                    user = user.scalar()
                    if user:
                        user.balance += balance
                        await session.commit()
                        return True
                    else:
                        return False
                except IntegrityError as e:
                    await session.rollback()
                    return False
                
                
    async def decrement_balance(self, uid: int, balance: int) -> bool:
        async with self.lock:
            async with self.db_session_maker() as session:
                try:
                    user = await session.execute(select(User).filter(User.uid == uid))
                    user = user.scalar()
                    if user:
                        user.balance -= balance
                        await session.commit()
                        return True
                    else:
                        return False
                except IntegrityError as e:
                    await session.rollback()
                    return False


class AccountReq:
    def __init__(self, db_session_maker: async_sessionmaker) -> None:
        self.db_session_maker = db_session_maker
        self.lock = Lock()
        
    async def add_acc(self, account_name: str, country_code_id: int):
        async with self.lock:
            async with self.db_session_maker() as session:
                try:
                    new_account = Accounts(name=account_name, country_code_id=country_code_id)
                    session.add(new_account)
                    await session.commit()
                    return True
                except IntegrityError:
                    await session.rollback()
                    return False

    async def get_account_by_name(self, account_name: str):
        async with self.lock:
            async with self.db_session_maker() as session:
                result = await session.execute(
                    select(Accounts).where(Accounts.name == account_name)
                )
                return result.scalars().one_or_none()

    async def get_account_price(self, account_name: str):
        async with self.lock:
            async with self.db_session_maker() as session:
                result = await session.execute(
                    select(Accounts)
                    .options(joinedload(Accounts.country_code))
                    .where(Accounts.name == account_name)
                )
                account = result.scalars().one_or_none()
                if account and account.country_code:
                    return account.country_code.price
                return None
    
    async def get_country_code(self, code: str):
        async with self.db_session_maker() as session:
            result = await session.execute(
                select(CountryCode).filter(CountryCode.code == code)
            )
            return result.scalar()

    async def add_country_code(self, code: str, price: float):
        async with self.db_session_maker() as session:
            new_code = CountryCode(code=code, price=price)
            session.add(new_code)
            await session.commit()
            return new_code.id

    async def update_country_code_price(self, country_code_id: int, price: float):
        async with self.db_session_maker() as session:
            result = await session.execute(
                select(CountryCode).filter(CountryCode.id == country_code_id)
            )
            country_code = result.scalar()
            if country_code:
                country_code.price = price
                await session.commit()

    async def delete_account(self, account_name: str) -> bool:
        lock = asyncio.Lock() 
        async with lock:
            async with self.db_session_maker() as session:
                try:
                    account = await self.get_account_by_name(account_name)
                    if account:
                        await session.delete(account)
                        await session.commit()
                        return True
                    return False
                except IntegrityError:
                    await session.rollback()
                    return False

                