import sys
from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtCore import *
import datetime
import pykorbit
import logging
import time


# ---------------------------------------------------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------------------------------------------------
logger = logging.getLogger()
#logger.setLevel(logging.DEBUG)
logger.setLevel(logging.CRITICAL)

file_handler = logging.FileHandler("log.txt", encoding="utf-8")
stream_handler = logging.StreamHandler()
logger.addHandler(file_handler)
logger.addHandler(stream_handler)


form_class = uic.loadUiType("window.ui")[0]


# ---------------------------------------------------------------------------------------------------------------------
# Korbit으로 부터 현재가를 조회하는 스레드
# ---------------------------------------------------------------------------------------------------------------------
class InquiryWorker(QThread):
    # 사용자 정의 시그널 (float 값을 하나 전달)
    finished = pyqtSignal(float)

    # run 이라는 이름 변경할 수 없음
    def run(self):
        btc_price = pykorbit.get_current_price("btc_krw")              # 비트코인 현재가 조회

        if isinstance(btc_price, float):                                # 금액 조회가 정상적인 경우에만
            self.finished.emit(btc_price)                               # 일이 끝났음을 알려줌


# ---------------------------------------------------------------------------------------------------------------------
# Main Window
# ---------------------------------------------------------------------------------------------------------------------
class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.init()
        self.create_korbit()
        self.create_threads()
        self.create_timers()
        self.set_signal_slots()

    def init(self):
        self.tableWidget.setRowCount(1)
        self.range = None
        self.open = None
        self.target = None
        self.activate = False
        self.email = None
        self.password = None
        self.key = None
        self.secret = None

    def create_korbit(self):
        self.read_secret()
        self.korbit = pykorbit.Korbit(self.email, self.password, self.key, self.secret)

    def create_threads(self):
        self.inquiry_worker = InquiryWorker()
        self.inquiry_worker.finished.connect(self.display_cur_price)

    def create_timers(self):
        # 시간 출력 타이머
        self.time_timer = QTimer(self)
        self.time_timer.start(1000)
        self.time_timer.timeout.connect(self.display_cur_time)

        # refresh token 갱신 타이머
        self.refresh_timer = QTimer(self)
        self.refresh_timer.start(1000 * 60 * 30)
        self.refresh_timer.timeout.connect(self.refresh_token)

        # 매매를 위한 타이머
        self.trading_timer = QTimer(self)
        self.trading_timer.start(1000)
        self.trading_timer.timeout.connect(self.trading)

    def set_signal_slots(self):
        # 버튼 이벤트 추가하기
        self.btn_start.clicked.connect(self.start)
        self.btn_stop.clicked.connect(self.stop)

    def start(self):
        self.textEdit.insertPlainText("자동 매매 활성화\n")
        self.activate = True

    def stop(self):
        self.textEdit.insertPlainText("자동 매매 비활성화\n")
        self.activate = False

    def trading(self):
        now = datetime.datetime.now()
        str_now = now.strftime("%H:%M:%S")                  # 현재 시간
        str_target = self.timeEdit.time().toString()          # 타겟 시간
        sell_target = self.timeEdit_2.time().toString()       # 매도 타겟 시간

        logging.info("trading 함수 active: {0}".format(self.activate))
        if self.activate is True:
            if str_now == str_target:
                logging.info("trading 함수 set open range")
                self.set_open_range()
            elif str_now == sell_target:
                logging.info("trading 함수 try sell")
                self.try_sell()
            else:
                logging.info("trading 함수 try buy")
                self.try_buy()

    def try_buy(self):
        logging.info("try_buy {}".format(self.target))
        if self.target is not None and self.get_btc_balance() == 0:
            btc_cur_price = pykorbit.get_current_price("btc_krw")
            if btc_cur_price is not None and btc_cur_price > self.target:
                self.buy()

    def try_sell(self):
        logging.info("try_sell")
        if self.get_btc_balance() != 0:
            self.sell()

    def buy(self):
        logging.info("buy")
        # 원화 잔고 조회
        self.textEdit.insertPlainText("비트코인 시장가 매수\n")
        balances = self.korbit.get_balances()
        krw = int(balances['krw']['available'])
        logger.info(krw)
        self.korbit.buy_market_order("btc_krw", krw)

    def sell(self):
        logging.info("sell")
        # 비트코인 잔고 조회
        self.textEdit.insertPlainText("비트코인 시장가 매도\n")
        btc = self.get_btc_balance()
        self.korbit.sell_market_order("btc_krw", btc)

    def get_btc_balance(self):
        logging.info("get_btc_balance-1")
        balances = self.korbit.get_balances()
        logging.info("get_btc_balance-2")
        if balances is None:
            return 0
        else:
            btc = float(balances['btc']['available'])
            return btc

    def set_open_range(self):
        logging.info("set_open_range")
        cur_time = QTime.currentTime().toString()
        self.textEdit.insertPlainText("시가/변동성 갱신 " + cur_time + "\n")

        low, high, last, vol = pykorbit.get_market_detail("btc_krw")
        self.range = (high - low) * 0.5

        time.sleep(1)           # ticker interval
        self.open = pykorbit.get_current_price("btc_krw")
        self.target = self.open + self.range

    def refresh_token(self):
        logging.info("refresh_token")
        self.korbit.renew_access_token()

    def display_cur_time(self):
        logging.info("display_cur_time")
        now = datetime.datetime.now()
        str_time = now.strftime("%Y-%m-%d %H:%M:%S")

        if self.activate:
            state = " (자동 매매 활성화)"
        else:
            state = " (자동 매매 비활성화)"
        self.statusBar().showMessage(str_time + state)

        # 1초마다 가격 조회 시키기
        self.inquiry_worker.start()

    @pyqtSlot(float)
    def display_cur_price(self, btc_price):
        name = QTableWidgetItem(str("BTC"))
        price = QTableWidgetItem(str(btc_price))
        self.tableWidget.setItem(0, 0, name)
        self.tableWidget.setItem(0, 1, price)

        # 시가 출력
        if self.open is not None:
            open = QTableWidgetItem(str(self.open))
            self.tableWidget.setItem(0, 2, open)

        # 목표가 출력
        if self.open is not None:
            target = QTableWidgetItem(str(self.target))
            self.tableWidget.setItem(0, 3, target)

        # 보유 여부 출력
        if self.get_btc_balance() != 0:
            state = QTableWidgetItem("보유 중")
        else:
            state = QTableWidgetItem("미보유 중")

        self.tableWidget.setItem(0, 4, state)

    def read_secret(self):
        logging.info("read secret 시작")
        f = open("secret.conf")
        lines = f.readlines()
        self.email = lines[0].rstrip()
        self.password = lines[1].rstrip()
        self.key = lines[2].rstrip()
        self.secret = lines[3].rstrip()
        f.close()
        logging.info("read secret 종료")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MyWindow()
    win.show()
    app.exec_()