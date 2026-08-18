#cds C:/Users/pakys/Desktop/autotrader/
# source ./.venv/Scripts/Activate
#https://github.com/pisquiii/NEURALBYTEDEMO

from telethon import TelegramClient, events
import MetaTrader5 as mt5
from enum import IntEnum
import asyncio
import re



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
signals = []

class MARKET_STATES(IntEnum):
    CONSOLIDATION_AFTER_BULLISH = 1
    CONSOLIDATION_AFTER_BEARISH = 2
    BULLISH = 3
    BEARISH = 4
    RETRACEMENT = 5
    BREAKOUT = 6
    REVERSAL = 7

class signal_state(IntEnum):
    pending = 1 #in attesa di richiedere l'ordine
    in_progress = 2 #in attesa di effettuare l'ordine
    executed = 3 #l'ordine è eseguito, il buy / sell è stato lanciato e l'operazione è partita
    delated = 4 #l'ordine è stato eliminato
    closed = 5 #l'ordine è stato chiuso (con profit / stop loss oppure forzatamente (con il BE))
    change_SL= 6 #viene effettuata una richiesta di change dello stop loss
    change_tP = 7 #viene effettuata una richiesta di change del take profit
    be_closing = 8 #si costringe a chiusura
    forcing_operation = 9 #si costringe ad apertura

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

    POS_BUY = mt5.POSITION_TYPE_BUY
    POS_SELL = mt5.POSITION_TYPE_SELL

#region  ------------------------------------------ FUNCTIONS ----------------------------------------
#-----------------------------------------------------------------------------------------------------
#-------------------------------------------- Parser function

def AUTO_change_creator(event): 
    mess = event.text.lower()
    risp_mess = event.message.reply_to_msg_id
    print(mess)
    print(risp_mess)
    print(signals)
    if signals == []: return 

    for signal in signals:

        if signal["mess_id"] == risp_mess:
            if "active" == mess:
                if signal["STATE"] == signal_state.pending:
                    signal["STATE"] = signal_state.forcing_operation


            if "if" not in mess:
                if "be" in mess: 
                    if "hit" in mess or ("out" in mess and "at" in mess) or ("out" in mess and "to" in mess):
                        signal["STATE"] = signal_state.be_closing

            if "sl" in mess: 
                if "set" in mess and "to" in mess: pass
                    #signal["SLs"][0] = (float(re.search(r"\d+(?:\.\d+)?", mess).group()))
                    #signal["STATE"] = signal_state.change_SL

    return 
    
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
        "real_signal" : False,
        "STATE": signal_state.pending,
        "magic": magic,
        "mess_id" : event.message.id
    }

    print(signal["mess_id"])
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
        if "XAUUSD" in text: signal["symbol"] = text+"pm"

        # BUY / SELL
        if "BUY" in text or "SELL" in text: signal["type"] = text

        # Limit and/or Stop
        if "Limit" in text or "LIMIT" in text or "limit" in text: signal["limit"] = True
        if "Stop" in text or "STOP" in text or "stop" in text: signal["stop"] = True

        # ENTER ZONE
        Enter_Zone = [float(EZ_val) for EZ_val in re.findall(r"\d+(?:\.\d+)?", text)]

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
    signals.append(signal)  
    return signal

#---------------------------------- Request creation function

def make_close_request(position, price, deviation, lot = 0.01):
    print(position[0], price, deviation)
    req = {
        "action": ORDER.ACT_INSTANT,
        "position": position[0].ticket,
        "symbol": position[0].symbol,
        "volume": lot,
        "type": position[0].type,
        "price": price,
        "deviation": deviation
    }

    print(req)
    print("dkdkl")

    if position[0].type == ORDER.POS_BUY: req["type"] = ORDER.SELL
    if position[0].type == ORDER.POS_SELL: req["type"] = ORDER.BUY
    print(req)
    return req

def make_request(signal, price, sl, tp, deviation, magic,
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
    sl_modified = False
    position = None
    sl_modified = False
    print("ERROR:", mt5.last_error())
    print(mt5.terminal_info())
    while signal["STATE"] == signal_state.pending: #SI ATTENDE CHE LA RICHIESTA DELL'ORDINE VENGA EFFETTUATA
        await asyncio.sleep(0.5)

        tick = mt5.symbol_info_tick(signal["symbol"])
        ask = tick.ask
        bid = tick.bid

        if signal["limit"] or signal["stop"]:
            req = make_request(signal, signal["EZ_min_val"] + (signal["EZ_max_val"] - signal["EZ_min_val"])/2, signal["SLs"][0], signal["TPs"][1], 20, signal["magic"])
           
        elif signal["type"] == "BUY":
            if ask < float(signal["EZ_min_val"]) or ask > float(signal["EZ_max_val"]):
                continue

            req = make_request(signal, ask, signal["SLs"][0], signal["TPs"][1], 20, signal["magic"])    

        elif signal["type"] == "SELL":
            if bid < signal["EZ_min_val"] or bid > signal["EZ_max_val"]:
                continue

            req = make_request(signal, bid, signal["SLs"][0], signal["TPs"][1], 20, signal["magic"])

        receipt = mt5.order_send(req)
        print(receipt)
        print(mt5.last_error())
        if receipt == None: 
            continue
        if receipt.retcode == mt5.TRADE_RETCODE_DONE:
            print(receipt)
            signal["STATE"] = signal_state.in_progress #LA RICHIESTA DELL'ORDINE E' STATA EFFETTUATA
        receipts.append(receipt)

    while signal["STATE"] == signal_state.forcing_operation:
        if signal["type"] == "BUY":
            req = make_request(signal, ask, signal["SLs"][0], signal["TPs"][1], 20, signal["magic"])    

        elif signal["type"] == "SELL":
            req = make_request(signal, bid, signal["SLs"][0], signal["TPs"][1], 20, signal["magic"])

        receipt = mt5.order_send(req)

        if receipt == None: 
            continue
        if receipt.retcode == mt5.TRADE_RETCODE_DONE:
            print(receipt)
            signal["STATE"] = signal_state.in_progress #LA RICHIESTA DELL'ORDINE E' STATA EFFETTUATA
        receipts.append(receipt)

        
    while signal["STATE"] == signal_state.in_progress: #SI ATTENDE CHE L'ORDINE VENGA EFFETTUATO
        await asyncio.sleep(1)
        position = mt5.positions_get(magic=signal["magic"]) #recuperiamo le info dell'ordine
        if position == None: continue 

        signal["STATE"] = signal_state.executed #L'ORDINE E' STATO EFFETTUATO
        break

    while signal["STATE"] == signal_state.executed: #SI ATTENDE CHE L'ORDINE GIUNGA AL SUO COMPLETAMENTO CON LA CHIUSURA
        await asyncio.sleep(0.8)
        position = mt5.positions_get(magic=signal["magic"])
        if position == None: signal["STATE"] = signal_state.closed

        if sl_modified == True: continue

        current_price = position[0].price_current

        if signal["type"] == "BUY":
            if current_price >= signal["TPs"][0]:
                res = set_sl_tp(position[0].price_open + float(2), signal["TPs"][1],position[0].ticket, position[0].symbol)
                if res:
                    sl_modified = True
                else: mt5.last_error()

        
        if signal["type"] == "SELL":
            if current_price <= signal["TPs"][0]:
                res = set_sl_tp(position[0].price_open - float(2), signal["TPs"][1], position[0].ticket, position[0].symbol)
                if res:
                    sl_modified = True
                else: mt5.last_error()

        

    while signal["STATE"] == signal_state.be_closing:
        print("sono in chiusura")
        tick = mt5.symbol_info_tick(signal["symbol"])
        ask = tick.ask
        bid = tick.bid

        if signal["type"] == "BUY":
            print("è un buy")
            req = make_close_request(position, ask, 20)
            print(req)
        if signal["type"] == "SELL":
            print("è un sell")
            req = make_close_request(position, bid, 20)
            print(req)

        receipt = mt5.order_send(req)
        
        if receipt == None: 
            continue
        
        if receipt.retcode == mt5.TRADE_RETCODE_DONE:
            signal["STATE"] = signal_state.closed



    if signal["STATE"] == signal_state.closed: #SE L'ORDINE E' CHIUSO, CHIUDIAMO IL TASK ASYNC
            print("UIRRUIIUR")
            return    

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
    else:
        AUTO_change_creator(event)



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