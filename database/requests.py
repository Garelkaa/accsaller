from asyncio import Lock
import datetime
from database.models import Accounts, Transaction, User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.future import select
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
        
    async def add_acc(self, account_name: str, price: int):
        async with self.lock:
            async with self.db_session_maker() as session:
                try:
                    new_user = Accounts(name=account_name, price=price)
                    session.add(new_user)
                    await session.commit()
                    print("adadadasdasdasdasd")
                    return True
                except IntegrityError:
                    await session.rollback()
                    return False

    async def get_account_by_name(self, account_name: str):
        async with self.lock:
            async with self.db_session_maker() as session:
                result = await session.execute(
                    select(Accounts).filter(Accounts.name == account_name)
                )
                account = result.scalar()
                return account

    async def get_account_price(self, account_name: str) -> float:
        account = await self.get_account_by_name(account_name)
        if account:
            return account.price
        return None

    async def delete_account(self, account_name: str) -> bool:
        async with self.lock:
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
                