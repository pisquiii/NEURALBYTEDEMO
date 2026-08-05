from telethon import TelegramClient, events
import MetaTrader5 as mt5
from enum import IntEnum
import asyncio
from re import split

#region  ------------------------------------------ ESSENTIAL VAL ------------------------------------
#-----------------------------------------------------------------------------------------------------
#------------------------------------- telegram keys
api_id = 37691251
api_hash = "6f2dd4a88506aaed23609b40851eb782"
#------------------------------------- group ids
trading_room = -1003920687696 
my_group = -5500391350

#------------------------------------- vars
magic_index = 0
receipts = []
tasks = []
open_positions = []
#AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA

class signal_state(IntEnum):
    pending = 1
    in_progress = 2
    executed = 2
    delated = 3
    closed = 4

class ORDER(IntEnum): #ACTIONS
    ACT_INSTANT = mt5.TRADE_ACTION_DEAL #ordine immediato a mercato
    ACT_PENDING = mt5.TRADE_ACTION_PENDING #ordine in pending (usato per buy limit per esempio)
    ACT_SLTP = mt5.TRADE_ACTION_SLTP #modifica stop loss e take profit
    ACT_MODIFY = mt5.TRADE_ACTION_MODIFY #modifica un ordine pendente (buy limit con limit a 100 lo sposti a 200)
    ACT_REMOVE = mt5.TRADE_ACTION_REMOVE #cancella un ordine pendente prima che si inizializzi
    ACT_CLOSE_BY = mt5.TRADE_ACTION_CLOSE_BY #chiude una posizione usando una posizione opposta
                      #TYPES
    BUY = mt5.ORDER_TYPE_BUY		#Acquisto a mercato
    SELL = mt5.ORDER_TYPE_SELL		#Vendita a mercato
    BUY_LIMIT = mt5.ORDER_TYPE_BUY_LIMIT	#Ordine limite BUY
    SELL_LIMIT = mt5.ORDER_TYPE_SELL_LIMIT		#Ordine limite SELL
    BUY_STOP = mt5.ORDER_TYPE_BUY_STOP		#Ordine stop BUY
    SELL_STOP = mt5.ORDER_TYPE_SELL_STOP		#Ordine stop SELL
    BUY_STOP_LIMIT = mt5.ORDER_TYPE_BUY_STOP_LIMIT		#Stop che genera un BUY LIMIT
    SELL_STOP_LIMIT = mt5.ORDER_TYPE_SELL_STOP_LIMIT		#Stop che genera un SELL LIMIT
                      #TIMES
    TIME_TILL_CANCELLED = mt5.ORDER_TIME_GTC #	Good Till Cancelled. L'ordine resta attivo finché non viene eseguito o cancellato manualmente. È il più usato.
    TIME_END_DAY = mt5.ORDER_TIME_DAY	#Valido solo fino alla fine della giornata di trading. Se non viene eseguito, viene eliminato automaticamente.
    TIME_SPECIFIED = mt5.ORDER_TIME_SPECIFIED	#Valido fino a una data e ora specifica. Devi compilare anche il campo expiration.
    TIME__END_DAY_SPECIFIED = mt5.ORDER_TIME_SPECIFIED_DAY	#Valido fino alla fine del giorno specificato in expiration.

    FILL_OR_KILL = mt5.ORDER_FILLING_FOK	#Fill or Kill: l'ordine deve essere eseguito interamente subito, altrimenti viene annullato.
    IMMEDIATE_OR_CANCEL = mt5.ORDER_FILLING_IOC	#Immediate or Cancel: esegue la parte disponibile immediatamente e annulla il resto.
    FILLING_RETURN = mt5.ORDER_FILLING_RETURN #	Return: se non può essere eseguito completamente, la parte rimanente resta attiva (quando supportato dal broker).




#region  ------------------------------------------ FUNCTIONS ----------------------------------------
#-----------------------------------------------------------------------------------------------------
#-------------------------------------------- Parser function

def AUTO_signal_creator(event, magic):
    #--------------------------------------- vars
    message = event.text.splitlines()
    #-------------- message sections
    mess_header = []
    TPs = []
    SLs = []

    #-------------- dict. to send to mt5
    signal = {
            #signal data
        "symbol": "", 
        "type": "", 
        "limit" : False,
        "stop" : False,
        "EZ_min_val": 0, 
        "EZ_max_val": 0, 
        "TPs" : [],
        "SLs" : [],
            #meta data
        "id_signal" : event.message.id,
        "real_signal" : False,
        "STATE": signal_state.pending,
        "magic": magic,
        "index_operation": 0,
        "price" : 0
    }

    #-------------- message sectioning
    for line in message:
        mess_header = line.split(" ") if "XAUUSD" in line and mess_header == [] else mess_header
        TPs.append(line.replace("TP", "")) if "TP" in line else None
        SLs.append(line.replace("SL", "")) if "SL" in line else None
    
    #-------------- fulling parsed_mess (dict.)
    for text in mess_header:
        # purge text
        text = text.replace("\xa0", "")

        # SYMBOL
        if "XAUUSD" in text: signal["symbol"] = text

        # BUY / SELL
        if "BUY" in text or "SELL" in text: signal["type"] = text

        # Limit and/or Stop
        if "Limit" in text or "LIMIT" in text or "limit" in text: signal["limit"] = True
        if "Stop" in text or "STOP" in text or "stop" in text: signal["stop"] = True

        # ENTER ZONE
        Enter_Zone = [float(EZ_val) for EZ_val in split(r"[_-]", text) if EZ_val.isdigit()]

    if signal["symbol"] == "" or signal["type"] == "": return None
    if not Enter_Zone: return None
    signal["EZ_min_val"] = min(Enter_Zone[0], Enter_Zone[1])
    signal["EZ_max_val"] = max(Enter_Zone[0], Enter_Zone[1])

    #-------------- VALIDATION OF OPERATION IN TEXT FORMAT
    if signal["EZ_min_val"] == 0 : return None

    # TAKE PROFIT and 
    #-------------- VALIDATION OF OPERATION TP 
    for tp in TPs: 
        signal["TPs"].append(float(tp)) 

    # STOP LOSS and
    #-------------- VALIDATION OF OPERATION SL 
    for sl in SLs:  signal["SLs"].append(float(sl))

    # test or real check
    signal["real_signal"] = True if event.chat_id == trading_room else False  
    return signal

#---------------------------------- Request creation function

def make_request(signal, price, sl, tp, magic,
                 deviation = 100,
                 lot = 0.01,
                 comment = "", 
                 type_time = ORDER.TIME_TILL_CANCELLED, 
                 type_filling = ORDER.FILL_OR_KILL ):

    req = {
        "action": 0,
        "symbol": signal["symbol"],
        "volume": lot,
        "type": 0,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": deviation,
        "magic": magic,
        "comment": comment,
        "type_time": type_time,
        "type_filling": type_filling
    }
    #check enterzone min_max
    if signal["limit"] and signal["stop"] and signal["type"] == "BUY": 
        req["action"] = ORDER.ACT_PENDING
        req["type"] = ORDER.BUY_STOP_LIMIT
        return req
            
    if signal["limit"] and signal["stop"] and signal["type"] == "SELL": 
        req["action"] = ORDER.ACT_PENDING
        req["type"] = ORDER.SELL_STOP_LIMIT
        return req
                    

    if signal["limit"] and signal["type"] == "BUY": 
        req["action"] = ORDER.ACT_PENDING
        req["type"] = ORDER.BUY_LIMIT
        return req
                    
            
    if signal["stop"] and signal["type"] == "BUY": 
        req["action"] = ORDER.ACT_PENDING
        req["type"] = ORDER.BUY_STOP
        return req
                    
            
    if signal["limit"] and signal["type"] == "SELL": 
        req["action"] = ORDER.ACT_PENDING
        req["type"] = ORDER.SELL_LIMIT
        return req
                    

    if signal["stop"] and signal["type"] == "SELL": 
        req["action"] = ORDER.ACT_PENDING
        req["type"] = ORDER.SELL_STOP
        return req
                    

    if signal["type"] == "BUY":
        req["action"] = ORDER.ACT_INSTANT
        req["type"] = ORDER.BUY
        return req
                    
    
    if signal["type"] == "SELL":
        req["action"] = ORDER.ACT_INSTANT
        req["type"] = ORDER.SELL
        return req
                    
def chage_tp(tp): pass
def chage_sl(sl): pass 

def auto_be(signal): pass


#region  ------------------------------------- META TRADER CONNECTION ----------------------------------
#-----------------------------------------------------------------------------------------------------
if not mt5.initialize():
    print("initialize() failed")
    mt5.shutdown()




def set_sl_tp(sl, tp, pos_ticket, pos_symbol):
    print("MODIFICA SL")
    request = {
        "action": mt5.TRADE_ACTION_SLTP,
        "position": pos_ticket,
        "symbol": pos_symbol,
        "sl": sl,
        "tp": tp
    }

    result = mt5.order_send(request)

    return result

async def metatrader_connection(signal):
    current_price = None
    position = None
    sl_modified = False
    while signal["STATE"] == signal_state.pending: 
        print("aaa")
        await asyncio.sleep(0.5)
        tick = mt5.symbol_info_tick(signal["symbol"])
        ask = tick.ask
        bid = tick.bid

        if signal["limit"] or signal["stop"]:
            req = make_request(signal, signal["EZ_min_val"], signal["SLs"][0], signal["TPs"][0], signal["magic"])
           
        elif signal["type"] == "BUY":
            if ask < float(signal["EZ_min_val"]) or ask > float(signal["EZ_max_val"]):
                continue

            req = make_request(signal, ask, signal["SLs"][0], signal["TPs"][0], signal["magic"])    

        elif signal["type"] == "SELL":
            if bid < signal["EZ_min_val"] or bid > signal["EZ_max_val"]:
                continue

            req = make_request(signal, bid, signal["SLs"][0], signal["TPs"][0], signal["magic"])


        receipt = mt5.order_send(req)
        if receipt == None: 
            continue
        if receipt.retcode == mt5.TRADE_RETCODE_DONE:
            print(receipt)
            signal["STATE"] = signal_state.in_progres
        else: print(receipt.retcode)
        receipts.append(receipt)

    while signal["STATE"] == signal_state.in_progress:
        await asyncio.sleep(1)
        position = mt5.positions_get(magic=signal["magic"])
        print("POS", position)
        if position == None: continue 

        signal["STATE"] = signal_state.executed
        break

    while signal["STATE"] == signal_state.executed:
        await asyncio.sleep(0.8)
        if sl_modified == False:
            current_price = mt5.positions_get(magic=signal["magic"])[0].price_current
            print(current_price)


            if signal["type"] == "BUY":
                print((signal["TPs"][0] - position[0].price_open)/2)
                print(current_price - position[0].price_open)
                
                if (current_price - position[0].price_open)> (signal["TPs"][0] - position[0].price_open)/2:
                    res = set_sl_tp(position[0].price_open + float(2), signal["TPs"][0],position[0].ticket, position[0].symbol)
                    if res:
                        print(res)
                        sl_modified = True
                    else: mt5.last_error()

            
            if signal["type"] == "SELL":
                print((signal["TPs"][0] - position[0].price_open)/2)
                print(current_price - position[0].price_open)
                
                if (position[0].price_open - current_price) > (position[0].price_open - signal["TPs"][0])/2:
                    res = set_sl_tp(position[0].price_open - float(2), signal["TPs"][0], position[0].ticket, position[0].symbol)
                    if res:
                        print(res)
                        sl_modified = True
                    else: mt5.last_error()
            

#region  -------------------------------------- TELEGRAM CONNECTION ----------------------------------
#-----------------------------------------------------------------------------------------------------
client = TelegramClient("session", api_id, api_hash) # connetion


Magic = 0
@client.on(events.NewMessage) # waiting for messages
async def handler(event):
    global Magic
    print(event.text) # check message

    # "command" to close the connection from telegram
    if event.chat_id == my_group and event.text == ".": 
        await client.disconnect()

    if event.chat_id == my_group and event.text == "..": 
            for task in tasks: task.cancel()
            print(tasks)
            

    signal = AUTO_signal_creator(event, Magic)
    
    print(signal)
    if signal:
        tasks.append(asyncio.create_task(metatrader_connection(signal)))
        Magic = Magic +1
        print(tasks)




async def main():
    print("main avviato")

    try:
        await client.start("+393467223351") #login
        await client.run_until_disconnected()

    finally: 
        if tasks: 
            for task in tasks: task.cancel()


if __name__ == "__main__":
    asyncio.run(main())