import MetaTrader5 as mt5
from enum import IntEnum
import asyncio
from re import split


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



#region  ------------------------------------- META TRADER CONNECTION ----------------------------------
#-----------------------------------------------------------------------------------------------------
if not mt5.initialize():
    print("initialize() failed")
    mt5.shutdown()

