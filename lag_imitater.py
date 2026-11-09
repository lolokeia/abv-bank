import asyncio
from faulty.core import FaultyProxy
import faulty.middlewares as faul

async def main():
    # Прокси слушает 9999 и перенаправляет на ваш "банк"
    proxy = FaultyProxy(
        listen_host="127.0.0.1",
        listen_port=9998,
        target_host="localhost", # или IP вашего банка
        target_port=9999
    )
    # Добавляем задержку 100 мс на входящий трафик
    proxy.add_egress_rule(faul.LatencyMiddleware(min_ms=1000, max_ms=1000))
    proxy.add_ingress_rule(faul.LatencyMiddleware(min_ms=1000, max_ms=1000))
    # Дропаем 5% исходящих пакетов
    proxy.add_ingress_rule(faul.DropMiddleware(drop_rate=0.05))

    proxy.add_egress_rule(faul.ThrottleMiddleware(bytes_per_sec=1000))
    
    await proxy.start()

asyncio.run(main())