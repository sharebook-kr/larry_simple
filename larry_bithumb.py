import sys
from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtCore import *
import requests
import datetime
import time

def get_currenc_price():
    try:
        r = requests.get("https://api.bithumb.com/public/ticker/ALL")
        contents = r.json()
        return contents.get('data')
    except:
        return None


class Worker(QThread):
    finished = pyqtSignal(dict)

    def __init__(self, api=None):
        super().__init__()
        self.api = api

    def run(self):
        while True:
            data = get_currenc_price()
            if data is not None:
                self.finished.emit(data)
            self.msleep(100)


form_class = uic.loadUiType("window3.ui")[0]
class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # 코인 개수
        data = get_currenc_price()
        self.tableWidget.setRowCount(len(data)-1)

        self.worker = Worker()
        self.worker.finished.connect(self.update_price)
        time.sleep(1)
        self.worker.start()

        self.timer = QTimer(self)
        self.timer.start(1000)
        self.timer.timeout.connect(self.timeout)


    @pyqtSlot(dict)
    def update_price(self, data):
        keys = data.keys()
        tickers = [x for x in keys if x != 'date']

        row = 0
        for ticker in tickers:
            price_data = data[ticker]
            print(price_data)
            price = format(int(price_data['closing_price']), ',d') + ' 원'
            rate24 = price_data['24H_fluctate_rate'] + ' %'

            ticker = QTableWidgetItem(ticker)
            price = QTableWidgetItem(price)
            rate24 = QTableWidgetItem(rate24)

            price.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            rate24.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)

            self.tableWidget.setItem(row, 0, ticker)
            self.tableWidget.setItem(row, 1, price)
            self.tableWidget.setItem(row, 2, rate24)
            row += 1


    def timeout(self):
        now = datetime.datetime.now()
        str_now = now.strftime("%Y-%m-%d %H:%M:%S")
        self.statusBar().showMessage(str_now)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MyWindow()
    win.show()
    app.exec_()