import cv2
import numpy as np

def circle_dectect(frame):
    #cv2.imshow("frame", frame)
    gray_gauss_canny_frame = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
    gray_gauss_canny_frame = cv2.GaussianBlur(gray_gauss_canny_frame,(7,7),0)
    circles = cv2.HoughCircles(
        gray_gauss_canny_frame,                      # 影像（灰階即可）
        cv2.HOUGH_GRADIENT,        # 方法：固定使用 HOUGH_GRADIENT
        dp=1.2,                    # 累加器解析度與影像解析度的反比，例如=1 代表相同解析度
        minDist=20,                # 圓心間最小距離（太小會重複偵測同一個圓）
        param1=150,                 # Canny 邊緣檢測的高門檻（低門檻會自動 = param1 * 0.5）
        param2=30,                 # 霍夫累加器的閾值（越小找的圓越多，但可能雜訊）
        minRadius=20,              # 圓半徑最小值（設 0 表示不限制）
        maxRadius=50               # 圓半徑最大值（設 0 表示不限制）
    )
    return circles

def draw_circle(frame, circles):
    circle_frame = frame.copy()
    if circles is not None:
        circles = np.uint16(np.around(circles))
        for i in circles[0, :]:
            # 繪製圓的外框
            cv2.circle(circle_frame, (i[0], i[1]), i[2], (0, 255, 0), 2)  # 綠色圓框
            # 繪製圓心
            cv2.circle(circle_frame, (i[0], i[1]), 2, (0, 0, 255), 3)  # 紅色圓心
    return circle_frame


#------------------main----------------------------
cap = cv2.VideoCapture(0)
while True:
    ret, frame = cap.read()
    if not ret:
        print("無法讀取影像幀，退出。")
        break
    cv2.namedWindow("football", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("football", 642, 320) 
    
    circles = circle_dectect(frame)
    
    circle_frame = draw_circle(frame, circles)
            
    cv2.imshow("football",circle_frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break 