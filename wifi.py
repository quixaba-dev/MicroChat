from config import cfg
import network
import time


class Connector:
    def __init__(self):
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)

        self.wlan.disconnect()
        self.ssid = None

    def connect(self):
        self.wlan.disconnect()
        time.sleep(2)

        redes = sorted(
            self.wlan.scan(),
            key=lambda x: x[3],
            reverse=True
        )

        for rede in redes:
            ssid = rede[0].decode("utf-8")

            print("Tentando:", ssid)

            self.wlan.connect(ssid, cfg.wifi_password)

            # Espera até 10 segundos pela conexão
            for _ in range(20):
                if self.wlan.isconnected():
                    self.ssid = ssid

                    print("Conectado em:", ssid)
                    print("IP:", self.wlan.ifconfig()[0])

                    return True

                time.sleep(0.5)

            # Não conectou; garante que o estado anterior terminou
            print("Falhou:", ssid)
            self.wlan.disconnect()
            time.sleep(1)

        print("Nenhuma rede compatível encontrada.")
        return False