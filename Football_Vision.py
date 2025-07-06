import cv2
import numpy as np
import serial
import threading
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt, QTimer
import sys
import time

origin_x = 642
origin_y = 320

class DetectCircle:
    def __init__(self):
        pass

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
        global origin_x
        global origin_y

        if circles is not None:
            # 圓看誰在左上角
            origin_x = int(min(circles[0, :, 0]))
            origin_y = int(min(circles[0, :, 1]))
        # return frame
    
    def draw_circle(self, frame, circles):
        if circles is not None:
            circles = np.uint16(np.around(circles))
            for i in circles[0, :]:
                # 繪製圓的外框
                cv2.circle(frame, (i[0], i[1]), i[2], (0, 255, 0), 2)  # 綠色圓框
                # 繪製圓心
                cv2.circle(frame, (i[0], i[1]), 2, (0, 0, 255), 3)  # 紅色圓心
                # 顯示圓心座標
                cv2.putText(frame, f"({int(i[0]) - origin_x}, {int(i[1]) - origin_y}, {i[2]})", (i[0] + 15, i[1]+10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
        # 顯示原點
        cv2.circle(frame, (origin_x, origin_y), 5, (255, 0, 255), -1)  
        # 顯示原點座標
        cv2.putText(frame, f"({0}, {0})", (origin_x + 15, origin_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)

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
        main_layout.addWidget(self.image_label)
        
        #按鈕
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("開始")
        self.start_button.clicked.connect(self.start_process)
        self.stop_button = QPushButton("停止")
        self.stop_button.clicked.connect(self.stop_process)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        
        #啟動排版
        main_layout.addLayout(button_layout)
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
        self.start = False    
        self.countdown_seconds = 3
        
    #主程式：偵測圓和設定原點    
    def update_frame(self):
        if self.start == True:
            ret, frame = self.cap.read()
            if not ret:
                return

            # 裁剪影像
            frame = frame[0:330, 0:640]

            # 檢測圓形
            circles = self.detect.circle_detect(frame)

            # 如果還沒設定原點，嘗試設定
            if not self.origin_set:
                if circles is not None and circles.shape[1] == 1:
                    self.detect.set_origin(circles)
                    self.origin_set = True

            # 繪製圓形
            self.detect.draw_circle(frame, circles)

            # 轉換為 QImage 並顯示
            # rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # rgb_image = frame
            h, w, ch = frame.shape
            # bytes_per_line = ch * w
            # qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            qt_image = QImage(frame.data, w, h, QImage.Format_RGB888)

            pixmap = QPixmap.fromImage(qt_image)
            self.image_label.setPixmap(pixmap)
        
        elif self.start == False:
            # self.image_label.setText("未開始")
            pass
    
    def closeEvent(self, event):
        self.cap.release()
        event.accept()
    
    def start_process(self):
        
        if self.countdown_seconds > 0:
            self.image_label.setText(f"倒數 {self.countdown_seconds} 秒開始")
            self.countdown_seconds -= 1
            QTimer.singleShot(1000, self.start_process)  # 每 1 秒呼叫一次自己
        else:
            self.image_label.setText("開始！")
            self.cap = cv2.VideoCapture(0)
            self.start = True  # 倒數完畢才開始執行你的邏輯
        
    def stop_process(self):
        self.start = False
        self.image_label.setStyleSheet("background-color: black;" 
                                       "color: white;"
                                       "font-size: 24px;"           # 设置字体大小，可选
                                       "font-weight: bold;")
        self.image_label.setText("未開始")
        self.countdown_seconds = 3
        self.cap.release() 

#-------------------------main----------------------------
def main():
    app = QApplication(sys.argv)
    
    # 建立並顯示視窗
    window = VideoWidget()
    window.show()
    
    # 執行應用程式
    sys.exit(app.exec())
    
if __name__ == "__main__":
    # main()
    a = threading.Thread(target=main)
    a.start()