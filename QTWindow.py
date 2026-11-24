from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtWidgets import QTableWidgetItem, QLabel
from PyQt5.QtGui import QKeyEvent, QIcon
from PyQt5.QtCore import QTime, QEventLoop, Qt, QFile, QTextStream, pyqtSignal, QThread
from MainWindow import Ui_Form
from GameHelper import GameHelper, play_sound, read_json, write_json

AllCards = ['D', 'X', '2', 'A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3']

funWorker = None

class MyPyQT_Form(QtWidgets.QWidget, Ui_Form):
    def __init__(self):
        super(MyPyQT_Form, self).__init__()
        self.setupUi(self)
        self.setWindowFlags(QtCore.Qt.WindowMinimizeButtonHint |  # 使能最小化按钮
                            QtCore.Qt.WindowStaysOnTopHint |  # 窗体总在最前端
                            QtCore.Qt.WindowCloseButtonHint)
        self.setWindowIcon(QIcon(':/pics/favicon.ico'))
        self.setWindowTitle("DouZero欢乐斗地主  v5.7")
        play_sound("music/2.wav")
        self.setFixedSize(self.width(), self.height())  # 固定窗体大小
        self.move(20, 20)
        window_pale = QtGui.QPalette()

        self.setPalette(window_pale)
        self.setWindowOpacity(1)
        self.HandButton.clicked.connect(self.hand_game)
        self.AutoButton.clicked.connect(self.auto_game)
        self.StopButton.clicked.connect(self.stop)
        self.ResetButton.clicked.connect(self.init_threshold)
        self.ClassicsButton.setStyleSheet('background-color: rgba(255, 170, 0, 0.5);')

        self.read_threshold()
        self.Players = [self.RPlayedCard, self.PredictedCard, self.LPlayedCard]
        self.thread = funWorker#Worker()
        self.thread.change_mode = False
        self.ClassicsButton.setStyleSheet('background-color: rgba(255, 170, 0, 0.5);')
        self.thread.auto_game.connect(self.auto_game)
        self.thread.hand_game.connect(self.hand_game)
        self.thread.init_interface.connect(self.init_interface)
        self.thread.player_display.connect(self.player_display)
        self.thread.state_display.connect(self.state_display)
        self.thread.three_cards_display.connect(self.three_cards_display)
        self.thread.bid_display.connect(self.bid_display)
        self.thread.pre_display.connect(self.pre_display)
        self.thread.stop.connect(self.stop)
        self.thread.winrate_display.connect(self.winrate_display)
        self.thread.pre_cards_display.connect(self.pre_cards_display)
        self.thread.left_cards_display.connect(self.left_cards_display)
        self.thread.right_cards_display.connect(self.right_cards_display)
        self.thread.recorder_display.connect(self.cards_recorder)
        self.thread.write_threshold.connect(self.write_threshold)

    def hand_game(self, result):
        self.thread.auto_sign = False
        self.thread.start()
        self.AutoButton.setStyleSheet('background-color: none;')
        self.HandButton.setStyleSheet('background-color: rgba(255, 85, 255, 0.5);')

    def auto_game(self, result):
        self.thread.auto_sign = True
        self.thread.start()

        self.AutoButton.setStyleSheet('background-color: rgba(255, 85, 255, 0.5);')
        self.HandButton.setStyleSheet('background-color: none;')

    def stop(self, result):
        print()
        print("停止线程")
        self.thread.terminate()
        self.init_interface(1)
        self.AutoButton.setStyleSheet('background-color: none;')
        self.HandButton.setStyleSheet('background-color: none;')

    def player_display(self, result):
        for player in self.Players:
            player.setStyleSheet('background-color: rgba(0, 255, 0, 0);')
        self.Players[result].setStyleSheet('background-color: rgba(0, 255, 0, 0.5);')

    def init_threshold(self):
        self.bid_lineEdit_1.setText("0.2")
        self.bid_lineEdit_2.setText("0.4")
        self.bid_lineEdit_3.setText("0.5")
        self.jiabei_lineEdit_1.setText("0.5")
        self.jiabei_lineEdit_2.setText("0.4")
        self.jiabei_lineEdit_3.setText("0.6")
        self.jiabei_lineEdit_4.setText("0.5")
        self.jiabei_lineEdit_5.setText("1.3")
        self.jiabei_lineEdit_6.setText("1.1")
        self.jiabei_lineEdit_7.setText("1.2")
        self.jiabei_lineEdit_8.setText("1.0")
        self.mingpai_lineEdit.setText("1.5")

        data = {'bid1': self.bid_lineEdit_1.text(), 'bid2': self.bid_lineEdit_2.text(),
                'bid3': self.bid_lineEdit_3.text(), 'jiabei1': self.jiabei_lineEdit_1.text(),
                'jiabei2': self.jiabei_lineEdit_2.text(), 'jiabei3': self.jiabei_lineEdit_3.text(),
                'jiabei4': self.jiabei_lineEdit_4.text(), 'jiabei5': self.jiabei_lineEdit_5.text(),
                'jiabei6': self.jiabei_lineEdit_6.text(), 'jiabei7': self.jiabei_lineEdit_7.text(),
                'jiabei8': self.jiabei_lineEdit_8.text(), 'mingpai': self.mingpai_lineEdit.text()}
        write_json(data)

    def write_threshold(self, result):
        data = {'bid1': self.bid_lineEdit_1.text(), 'bid2': self.bid_lineEdit_2.text(),
                'bid3': self.bid_lineEdit_3.text(), 'jiabei1': self.jiabei_lineEdit_1.text(),
                'jiabei2': self.jiabei_lineEdit_2.text(), 'jiabei3': self.jiabei_lineEdit_3.text(),
                'jiabei4': self.jiabei_lineEdit_4.text(), 'jiabei5': self.jiabei_lineEdit_5.text(),
                'jiabei6': self.jiabei_lineEdit_6.text(), 'jiabei7': self.jiabei_lineEdit_7.text(),
                'jiabei8': self.jiabei_lineEdit_8.text(), 'mingpai': self.mingpai_lineEdit.text()}
        write_json(data)

    def read_threshold(self):
        data = read_json()
        self.bid_lineEdit_1.setText(data['bid1'])
        self.bid_lineEdit_2.setText(data['bid2'])
        self.bid_lineEdit_3.setText(data['bid3'])
        self.jiabei_lineEdit_1.setText(data['jiabei1'])
        self.jiabei_lineEdit_2.setText(data['jiabei2'])
        self.jiabei_lineEdit_3.setText(data['jiabei3'])
        self.jiabei_lineEdit_4.setText(data['jiabei4'])
        self.jiabei_lineEdit_5.setText(data['jiabei5'])
        self.jiabei_lineEdit_6.setText(data['jiabei6'])
        self.jiabei_lineEdit_7.setText(data['jiabei7'])
        self.jiabei_lineEdit_8.setText(data['jiabei8'])
        self.mingpai_lineEdit.setText(data['mingpai'])

    def init_interface(self, result):
        self.WinRate.setText("评分")
        self.WinRate.setStyleSheet('background-color: none;')
        self.label.setText("游戏状态")
        self.BidWinrate.setText("叫牌得分")
        self.PreWinrate.setText("局前得分")
        self.label.setStyleSheet('background-color: none;')
        self.LPlayedCard.setText("上家出牌区域")
        self.RPlayedCard.setText("下家出牌区域")
        self.PredictedCard.setText("AI出牌区域")
        self.ThreeLandlordCards.setText("底牌")
        self.recorder2zero()
        for player in self.Players:
            player.setStyleSheet('background-color: none;')

    def state_display(self, result):
        self.label.setText(result)
        self.label.setStyleSheet('background-color: rgba(255, 0, 0, 0.5);')

    def three_cards_display(self, result):
        self.ThreeLandlordCards.setText(result)

    def bid_display(self, result):
        self.BidWinrate.setText(result)

    def pre_display(self, result):
        self.PreWinrate.setText(result)

    def pre_cards_display(self, result):
        self.PredictedCard.setText(result)
        self.PredictedCard.setStyleSheet('background-color: rgba(0, 255, 0, 0.5);')
        self.LPlayedCard.setStyleSheet('background-color: rgba(0, 255, 0, 0);')
        self.RPlayedCard.setStyleSheet('background-color: rgba(0, 255, 0, 0);')

    def left_cards_display(self, result):
        self.LPlayedCard.setText(result)
        self.PredictedCard.setStyleSheet('background-color: rgba(0, 255, 0, 0);')
        self.LPlayedCard.setStyleSheet('background-color: rgba(0, 255, 0, 0.5);')
        self.RPlayedCard.setStyleSheet('background-color: rgba(0, 255, 0, 0);')

    def right_cards_display(self, result):
        self.RPlayedCard.setText(result)
        self.PredictedCard.setStyleSheet('background-color: rgba(0, 255, 0, 0);')
        self.LPlayedCard.setStyleSheet('background-color: rgba(0, 255, 0, 0);')
        self.RPlayedCard.setStyleSheet('background-color: rgba(0, 255, 0, 0.5);')

    def winrate_display(self, result):
        self.WinRate.setText(result)
        self.WinRate.setStyleSheet('background-color: rgba(255, 85, 0, 0.4);')

    def cards_recorder(self, result):
        for i in range(15):
            char = AllCards[i]
            num = result.count(char)
            newItem = QTableWidgetItem(str(num))
            newItem.setTextAlignment(Qt.AlignHCenter)
            self.tableWidget.setItem(0, i, newItem)

    def recorder2zero(self):
        for i in range(15):
            newItem = QTableWidgetItem("0")
            newItem.setTextAlignment(Qt.AlignHCenter)
            self.tableWidget.setItem(0, i, newItem)