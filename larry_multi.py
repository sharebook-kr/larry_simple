import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
import datetime
import pykorbit

# remove XRP
COINS = ["BTC", "BCH", "ETC", "ETH", "LTC"]

class CurPriceWorker(QThread):
    finished = pyqtSignal(str, float)

    def run(self):
        now = datetime.datetime.now()
        sec = 3600 * now.hour + 60 * now.minute + now.second

        coin_idx = sec % len(COINS)
        coin_name = COINS[coin_idx]

        _price = pykorbit.get_current_price(coin_name)
        print(coin_name, coin_price)


form_class = uic.loadUiType("window2.ui")[0]
class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.create_timers()

        self.email = None
        self.password = None
        self.key = None
        self.secret = None
        self.korbit = None

        self.price_worker = CurPriceWorker()

    def create_korbit(self):
        self.read_secret()
        self.korbit = pykorbit.Korbit(self.email, self.password, self.key, self.secret)


    def create_timers(self):
        self.timer = QTimer(self)
        self.timer.start(1000)
        self.timer.timeout.connect(self.timer_1sec)

    def timer_1sec(self):
        self.price_worker.start()
        now = datetime.datetime.now()
        str_time = now.strftime("%Y-%m-%d %H:%M:%S")
        self.statusBar().showMessage(str_time)

    def read_secret(self):
        try:
            f = open("secret.conf")
            lines = f.readlines()
            self.emal, self.password, self.key, self.secret = (x.strip() for x in lines)
            f.close()
        except:
            print("secret file open failed")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mywindow = MyWindow()
    mywindow.show()
    app.exec_()
