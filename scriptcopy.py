import MetaTrader5 as mt5
from enum import IntEnum
import asyncio
from re import split

#
#mt5.TIMEFRAME_M1    # 1 minuto
#mt5.TIMEFRAME_M2    # 2 minuti
#mt5.TIMEFRAME_M3    # 3 minuti
#mt5.TIMEFRAME_M4    # 4 minuti
#mt5.TIMEFRAME_M5    # 5 minuti
#mt5.TIMEFRAME_M6    # 6 minuti
#mt5.TIMEFRAME_M10   # 10 minuti
#mt5.TIMEFRAME_M12   # 12 minuti
#mt5.TIMEFRAME_M15   # 15 minuti
#mt5.TIMEFRAME_M20   # 20 minuti
#mt5.TIMEFRAME_M30   # 30 minuti

#mt5.TIMEFRAME_H1    # 1 ora
#mt5.TIMEFRAME_H2    # 2 ore
#mt5.TIMEFRAME_H3    # 3 ore
#mt5.TIMEFRAME_H4    # 4 ore
#mt5.TIMEFRAME_H6    # 6 ore
#mt5.TIMEFRAME_H8    # 8 ore
#mt5.TIMEFRAME_H12   # 12 ore

#mt5.TIMEFRAME_D1    # giorno
#mt5.TIMEFRAME_W1    # settimana
#mt5.TIMEFRAME_MN1   # mese


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

async def main():
    rates = mt5.copy_rates_from_pos(
        "XAUUSD",          # simbolo
        mt5.TIMEFRAME_M5,  # timeframe
        0,                 # da quale candela partire
        100                # numero candele
    )
    #print(rates[-1] ) #candela corrente
    #for candle in rates:
        #time          1785961500  → apertura candela
        #open          4240.01     → prezzo apertura
        #high          4246.52     → massimo raggiunto
        #low           4237.27     → minimo raggiunto
        ##close         4244.90     → chiusura
        #tick_volume   2216        → numero movimenti prezzo
        #spread        9           → spread in punti
        #real_volume   0           → volume reale non disponibile
        # example(1785960900, 4241.87, 4241.87, 4237.92, 4238.64, 1159, 7, 0)



        #print(mt5.symbol_info_tick("XAUUSD"))
        #Tick(time=1785961191, bid=4238.04, ask=4238.31, last=0.0, volume=0, time_msc=1785961191713, flags=1030, volume_real=0.0)








if not mt5.initialize():
    print("initialize() failed")
    mt5.shutdown()

elif __name__ == "__main__":
    asyncio.run(main())