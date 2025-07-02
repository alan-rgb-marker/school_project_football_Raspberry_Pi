import cv2
import numpy as np
import serial
import threading

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



#-------------------------main----------------------------
cap = cv2.VideoCapture(0)
# 設定原點或更新原點

while True: 
    ret, origin_frame = cap.read()
    if not ret:
        print("無法讀取影像幀，退出。")
        exit()
    origin_frame = origin_frame[0:330, 0:640]

    origin_detect = DetectCircle()
    origin_circles = origin_detect.circle_detect(origin_frame)
    if origin_circles is not None and origin_circles.shape[1] == 1:# and origin_circles[0, 0, 2] > 16:# 15指的是圓的半徑，原點的半徑要超過像素15
        origin_detect.set_origin(origin_circles)
        break
    else:
        print("超過兩個圓")
        origin_detect.draw_circle(origin_frame, origin_circles)
    cv2.imshow("football", origin_frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

#偵測圓和座標系統
while True:
    ret, frame = cap.read()
    if not ret:
        print("無法讀取影像幀，退出。")
        break
    frame = frame[0:330, 0:640]
    detect = DetectCircle()
    circles = detect.circle_detect(frame)
    
    # detect.set_origin(circles) 
    detect.draw_circle(frame, circles)
    cv2.imshow("football",frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break 