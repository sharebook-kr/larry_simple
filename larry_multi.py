import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5 import uic
import datetime
import pykorbit
import time

# remove XRP
COINS = ["XRP", "BTC", "BCH", "ETC", "ETH", "LTC"]

#----------------------------------------------------------------------------------------------------------------------
# 현재가 조회
#----------------------------------------------------------------------------------------------------------------------
class CurPriceWorker(QThread):
    finished = pyqtSignal(int, str, float)

    def __init__(self):
        super().__init__()

    def run(self):
        now = datetime.datetime.now()
        sec = 3600 * now.hour + 60 * now.minute + now.second

        coin_idx = sec % len(COINS)
        coin_name = COINS[coin_idx]

        coin_price = pykorbit.get_current_price(coin_name)
        if coin_price is not None:
            self.finished.emit(coin_idx, coin_name, coin_price)

#----------------------------------------------------------------------------------------------------------------------
# 목표가 설정
#----------------------------------------------------------------------------------------------------------------------
class TargetPriceWorker(QThread):
    finished = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

    def run(self):
        targets = {}
        for coin_idx, coin_name in enumerate(COINS):
            low, high, last, volume = pykorbit.get_market_detail(coin_name)
            target = last + (high - low) * 0.5
            targets[coin_name] = target
            time.sleep(1)
        self.finished.emit(targets)


form_class = uic.loadUiType("window2.ui")[0]
class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.tableWidget.setRowCount(len(COINS))

        self.create_timers()

        self.email = None
        self.password = None
        self.key = None
        self.secret = None
        self.korbit = None

        self.price_worker = CurPriceWorker()
        self.price_worker.finished.connect(self.update_cur_price)

        self.target_price_worker = TargetPriceWorker()
        self.target_price_worker.finished.connect(self.update_target_price)

    def create_korbit(self):
        self.read_secret()
        self.korbit = pykorbit.Korbit(self.email, self.password, self.key, self.secret)

    @pyqtSlot(int, str, float)
    def update_cur_price(self, row, coin, price):
        self.tableWidget.setItem(row, 0, QTableWidgetItem(coin))

        price = int(price)
        price = format(price, ',d')
        self.tableWidget.setItem(row, 1, QTableWidgetItem(price))

    @pyqtSlot(dict)
    def update_target_price(self, targets):
        for coin, target_price in targets.items():
            row = COINS.index(coin)
            target_price = int(target_price)
            target_price = format(target_price, ',d')
            self.tableWidget.setItem(row, 2, QTableWidgetItem(target_price))


    def create_timers(self):
        self.timer = QTimer(self)
        self.timer.start(1000)
        self.timer.timeout.connect(self.timer_1sec)

    def timer_1sec(self):
        start_time = self.timeEdit.time()
        str_start_time = start_time.toString("hh:mm:ss")

        current_time = QTime.currentTime()
        str_current_time = current_time.toString("hh:mm:ss")

        self.statusBar().showMessage(str_current_time)

        if str_start_time == str_current_time:
            self.textEdit.insertPlainText("목표가 설정\n")
            self.target_price_worker.start()
        else:
            self.price_worker.start()

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
