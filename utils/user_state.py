from aiogram.fsm.state import State, StatesGroup


class FSMChangeLanguage(StatesGroup):
    language = State()
    
class FSMSetRegion(StatesGroup):
    region = State()
    quantity = State()

class FSMAddBalance(StatesGroup):
    balance = State()
    
class FSMAddBalanceAdm(StatesGroup):
    uid = State()
    balance = State()
    
class FSMAddAcc(StatesGroup):
    typeacc = State()
    amount = State()
    document = State()
    