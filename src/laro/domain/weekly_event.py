class WeeklyEvent:
    DATA = [
        # WoE oficial do servidor Ragnarok Online LATAM (fonte: ro.gnjoylatam.com —
        # guia de Guerras do Emperium): todo domingo, 20:00-22:00 no horário do
        # servidor (UTC-3 = America/Sao_Paulo). 16 castelos (WoE 1.0).
        # O modo WoE 2.0 ainda não existe no LATAM; eventos GMC e Happy Hour de
        # outros servidores não acontecem aqui.
        {'name': 'WoE', 'type': 'woe', 'weekday': '7', 'begin': '20:00', 'end': '22:00'},
    ]
