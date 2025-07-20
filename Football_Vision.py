import cv2
import numpy as np
import serial
import threading
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QSizePolicy, QMessageBox
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt, QTimer
import sys
import subprocess
import time

read_data = None

init_write_data = f"s000,000p"
write_data = init_write_data



#啟動
start = False

class DetectCircle:
    def __init__(self):
        super().__init__()
        self.origin_x = 642
        self.origin_y = 320
        #值計長度
        self.real_length_x = 290
        self.real_length_y = 295
        
        #像素、實際距離比例
        self.proportion_x = 1
        self.proportion_y = 1
        
        #球的座標
        self.ball_x = 0
        self.ball_y = 0
        

    def circle_detect(self, frame):  
        gray_gauss_canny_frame = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
        gray_gauss_canny_frame = cv2.GaussianBlur(gray_gauss_canny_frame,(11,11),0)

        circles = cv2.HoughCircles(
            gray_gauss_canny_frame,    # 影像（灰階即可）
            cv2.HOUGH_GRADIENT,        # 方法：固定使用 HOUGH_GRADIENT
            dp=1.2,                    # 累加器解析度與影像解析度的反比，例如=1 代表相同解析度
            minDist=50,                # 圓心間最小距離（太小會重複偵測同一個圓）
            param1=150,                # Canny 邊緣檢測的高門檻（低門檻會自動 = param1 * 0.5）
            param2=25,                 # 霍夫累加器的閾值（越小找的圓越多，但可能雜訊）
            minRadius=9,               # 圓半徑最小值（設 0 表示不限制）
            maxRadius=20               # 圓半徑最大值（設 0 表示不限制）
        )
    
        return circles

    def set_origin(self, circles):
        if circles is not None:
            # 圓看誰在左上角
            self.origin_x = int(min(circles[0, :, 0]))
            self.origin_y = int(min(circles[0, :, 1]))
        # return frame
    
    def find_ball(self, circles):
        global write_data
        if circles is not None:
            for i in circles[0, :]:
                #靠球的半徑判斷哪個是球
                if i[2] > 11 and i[2] < 14:
                    self.ball_x = int(i[0] - self.origin_x)
                    self.ball_y = int(i[1] - self.origin_y)
                    #實際球的座標
                    real_ball_x = int(self.ball_x * self.proportion_x)
                    real_ball_y = int(self.ball_y * self.proportion_y)
                    
                    write_data = f's{real_ball_x:03d},{real_ball_y:03d}p'
                    print(write_data)
    
    def draw_circle(self, frame, circles):
        if circles is not None:
            circles = np.uint16(np.around(circles))
            for i in circles[0, :]:
                # 繪製圓的外框
                cv2.circle(frame, (i[0], i[1]), i[2], (0, 255, 0), 2)  # 綠色圓框
                # 繪製圓心
                cv2.circle(frame, (i[0], i[1]), 2, (0, 0, 255), 3)  # 紅色圓心
                # 顯示圓心座標
                cv2.putText(frame, f"({i[0]-self.origin_x}, {i[1]-self.origin_y})", (i[0] + 15, i[1]+10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
        # 顯示原點
        cv2.circle(frame, (self.origin_x, self.origin_y), 5, (255, 0, 255), -1)  
        # 顯示原點座標
        cv2.putText(frame, f"({0}, {0})", (self.origin_x + 15, self.origin_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
    
    # 機算長度像比例
    def calculateScaleRatio(self):
        self.proportion_x = self.real_length_x / self.ball_x
        self.proportion_y = self.real_length_y / self.ball_y
        #像素x比例=實際長度

class VideoWidget(QWidget):
    def __init__(self):
        super().__init__()        
        self.setWindowTitle("Circle Detection")
        self.setGeometry(0, 0, 1080, 600)
        
        # 建立布局
        main_layout = QVBoxLayout()

        # 建立標籤來顯示影像
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(640, 330)
        self.image_label.setStyleSheet("background-color: black;" 
                                       "color: white;"
                                       "font-size: 24px;"           # 设置字体大小，可选
                                       "font-weight: bold;")
        self.image_label.setText("未開始")
        main_layout.addWidget(self.image_label, 2)
        
        #按鈕
        layout = QGridLayout()
        self.start_button = QPushButton("開始")
        self.start_button.setStyleSheet("font-size: 40px")
        self.start_button.clicked.connect(self.start_process)
        
        self.stop_button = QPushButton("停止")
        self.stop_button.setStyleSheet("font-size: 40px")
        self.stop_button.clicked.connect(self.stop_process)
        
        #關機
        self.poweroff_button = QPushButton("關機")
        self.poweroff_button.setStyleSheet("font-size: 40px")
        self.poweroff_button.clicked.connect(self.poweroff)
        
        layout.addWidget(self.start_button, 0, 0)
        layout.addWidget(self.stop_button, 0, 1)
        layout.addWidget(self.poweroff_button, 1, 0)
        
        #比分
        score_lauout = QHBoxLayout()
        self.computer_label = QLabel("電腦\n0")
        self._label = QLabel("比分\n  :  ")
        self.player_label = QLabel("我方\n0")
        
        for lbl in [self.computer_label, self._label, self.player_label]:
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("font-size: 36px; font-weight: bold;")
        
        score_lauout.addWidget(self.computer_label)
        score_lauout.addWidget(self._label)
        score_lauout.addWidget(self.player_label)
        
        layout.addLayout(score_lauout, 1, 1)
        
        #啟動排版
        main_layout.addLayout(layout, 2)
        # main_layout.addLayout(score_layout)
        self.setLayout(main_layout)
        
        # 初始化攝影機
        # self.cap = cv2.VideoCapture(0)
        self.cap = None
        self.detect = DetectCircle()
        self.origin_set = False
        
        # 建立計時器來更新影像
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(15)  # 30ms 更新一次
        
        #啟動變數
          
        self.countdown_seconds = 3
        
        
        #串口輸入輸出
        self.send_stm32_data = Stm32_serial()
        
    #主程式：偵測圓和設定原點    
    def update_frame(self):
        global start
        if start == True:
            ret, frame = self.cap.read()
            if not ret:
                return

            # 裁剪影像
            frame = frame[0:380, 0:640]

            # 檢測圓形
            circles = self.detect.circle_detect(frame)

            # 如果還沒設定原點，嘗試設定
            if not self.origin_set:
                if circles is not None and circles.shape[1] == 2:
                    self.detect.set_origin(circles)
                    self.origin_set = True
            else:
                self.detect.find_ball(circles)
            # 繪製圓形
            self.detect.draw_circle(frame, circles)

            # 轉換為 QImage 並顯示
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # rgb_image = frame
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            # qt_image = QImage(rgb_image.data, w, h, QImage.Format_RGB888)

            pixmap = QPixmap.fromImage(qt_image)
            self.image_label.setPixmap(pixmap)
        
        elif start == False:
            # self.image_label.setText("未開始")
            pass
    
    def closeEvent(self, event):
        self.cap.release()
        event.accept()
    
    def start_process(self):
        global write_data
        self.image_label.setText("初始化中，請稍等...")

        # 傳送初始化命令
        write_data = "init,init"
        self.send_stm32_data.write_serial()

        # 啟動輪詢等待 STM32 回傳 'read'
        QTimer.singleShot(100, self.check_init_response)


    def check_init_response(self):
        global read_data
        self.send_stm32_data.read_serial()

        if read_data == "read":
            self.countdown_seconds = 3
            self.start_countdown()
        else:
            QTimer.singleShot(100, self.check_init_response)  # 每 100ms 檢查一次


    def start_countdown(self):
        if self.countdown_seconds > 0:
            self.image_label.setText(f"倒數 {self.countdown_seconds} 秒開始")
            self.countdown_seconds -= 1
            QTimer.singleShot(1000, self.start_countdown)
        else:
            self.start_main_process()


    def start_main_process(self):
        global write_data, start

        self.image_label.setText("開始！")

        self.cap = cv2.VideoCapture(0)

        write_data = "starttart"
        self.send_stm32_data.write_serial()

        self.send_stm32_data.serial_timer.start(20)

        start = True
       
        
        
    def stop_process(self):
        global start
        global write_data
        global read_data
        global init_write_data
        #停止傳輸
        self.send_stm32_data.serial_timer.stop()
        start = False
        write_data = init_write_data
        read_data = None
        self.origin_set = False
        self.origin_x = 642
        self.origin_y = 320
        self.image_label.setStyleSheet("background-color: black;" 
                                       "color: white;"
                                       "font-size: 24px;"           # 设置字体大小，可选
                                       "font-weight: bold;")
        self.image_label.setText("未開始")
        self.countdown_seconds = 3
        self.cap.release() 
        write_data = "stopstops"
        self.send_stm32_data.write_serial()
        
        self.send_stm32_data.ser.reset_input_buffer()
        
    def poweroff(self):
        message = QMessageBox()
        # message.setMinimumSize(1080, 600)
        # message.showMaximized()
        message.setWindowTitle("poweroff")
        message.setInformativeText("你確定要關機了嘛？")
        message.setIcon(QMessageBox.Icon.Critical)
        message.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        message.setStyleSheet("""
        QLabel {
            font-size: 36px;
        }
        QPushButton {
            font-size: 28px;
            min-width: 120px;
            min-height: 60px;
        }
    """)
            
        ret = message.exec()
        
        
        if ret == QMessageBox.StandardButton.Ok:
            subprocess.run(['poweroff'],check=True,capture_output=True,text=True)
            
        
 
class Stm32_serial():
    def __init__(self):
        super().__init__()
        self.ser =  serial.Serial('/dev/ttyUSB0', baudrate=115200, timeout=1)
        self.serial_timer = QTimer()
        self.serial_timer.timeout.connect(self.write_serial)
    
    def read_serial(self):
        global read_data
        
        if self.ser.in_waiting:
            data = self.ser.readline().decode('ascii', errors='ignore').strip()
            if data:
                read_data = data
        
    def write_serial(self):
        self.ser.write(write_data.encode())

#-------------------------main----------------------------
def main():
    app = QApplication(sys.argv)
    
    # 建立並顯示視窗
    window = VideoWidget()
    window.show()
    
    # 執行應用程式
    sys.exit(app.exec())

def serials():    
    global start
    s = Stm32_serial()
    while True:
        if start == True:
            s.write_serial()
        time.sleep(0.1)
    
if __name__ == "__main__":
    main()