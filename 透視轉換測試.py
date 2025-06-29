# import cv2
# import numpy as np


# def circle_detect(frame):  
#         gray_gauss_canny_frame = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
#         gray_gauss_canny_frame = cv2.GaussianBlur(gray_gauss_canny_frame,(7,7),0)

#         circles = cv2.HoughCircles(
#             gray_gauss_canny_frame,    # 影像（灰階即可）
#             cv2.HOUGH_GRADIENT,        # 方法：固定使用 HOUGH_GRADIENT
#             dp=1.2,                    # 累加器解析度與影像解析度的反比，例如=1 代表相同解析度
#             minDist=20,                # 圓心間最小距離（太小會重複偵測同一個圓）
#             param1=150,                # Canny 邊緣檢測的高門檻（低門檻會自動 = param1 * 0.5）
#             param2=30,                 # 霍夫累加器的閾值（越小找的圓越多，但可能雜訊）
#             minRadius=3,               # 圓半徑最小值（設 0 表示不限制）
#             maxRadius=20               # 圓半徑最大值（設 0 表示不限制）
#         )
    
#         return circles

# def sort_circle_centers(centers):
#     """
#     將四個圓心排序為左上、右上、右下、左下的順序
#     """
#     # 計算中心點
#     centroid = np.mean(centers, axis=0)
    
#     # 分類點到四個象限
#     top_left = []
#     top_right = []
#     bottom_left = []
#     bottom_right = []
    
#     for center in centers:
#         x, y = center
#         if x < centroid[0] and y < centroid[1]:
#             top_left.append(center)
#         elif x >= centroid[0] and y < centroid[1]:
#             top_right.append(center)
#         elif x >= centroid[0] and y >= centroid[1]:
#             bottom_right.append(center)
#         else:
#             bottom_left.append(center)
    
#     # 確保每個象限只有一個點
#     if len(top_left) == 1 and len(top_right) == 1 and len(bottom_right) == 1 and len(bottom_left) == 1:
#         return np.array([top_left[0], top_right[0], bottom_right[0], bottom_left[0]], dtype="float32")
#     else:
#         return None

# def perspective(circles):
#     if circles is not None and len(circles[0]) >= 4:
#         x = np.zeros(4, dtype=np.float32)
#         y = np.zeros(4, dtype=np.float32)


# cap = cv2.VideoCapture(2)
# while True:
#     ret, frame = cap.read()
#     if not ret:
#         print("無法讀取影像幀，退出。")
#         break
#     circles = circle_detect(frame)
#     if circles is not None:
#         circles = np.round(circles[0, :]).astype("int")
#         if len(circles) >= 4: 
#             circles = circles[:4]
#             centers = circles[:, :2]
#             sorted_centers = sort_circle_centers(centers)

#             if sorted_centers is not None:
#                 # 定義目標點（200x200 的正方形）
#                 target_points = np.array([[0, 0], [200, 0], [200, 200], [0, 200]], dtype="float32")
#                 # 計算透視轉換矩陣
#                 M = cv2.getPerspectiveTransform(sorted_centers, target_points)
#                 # 進行透視轉換
#                 warped = cv2.warpPerspective(frame, M, (640, 480))
#                 cv2.imshow("Warped Image", warped)
    
#     cv2.imshow("football",frame)
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break 
# cap.release()
# cv2.destroyAllWindows()

import cv2
import numpy as np


def circle_detect(frame):  
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (7,7), 0)
    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=30,
        param1=100,
        param2=30,
        minRadius=5,
        maxRadius=30
    )
    return circles

def sort_circle_centers(centers):
    centroid = np.mean(centers, axis=0)
    sorted_pts = [None] * 4  # [左上, 右上, 右下, 左下]

    for pt in centers:
        x, y = pt
        if x < centroid[0] and y < centroid[1]:
            sorted_pts[0] = pt  # 左上
        elif x >= centroid[0] and y < centroid[1]:
            sorted_pts[1] = pt  # 右上
        elif x >= centroid[0] and y >= centroid[1]:
            sorted_pts[2] = pt  # 右下
        else:
            sorted_pts[3] = pt  # 左下

    if all(pt is not None for pt in sorted_pts):
        return np.array(sorted_pts, dtype="float32")
    else:
        return None


cap = cv2.VideoCapture(2)  # 你可以換成 2

while True:
    ret, frame = cap.read()
    if not ret:
        print("無法讀取影像幀，退出。")
        break

    circles = circle_detect(frame)
    if circles is not None and len(circles[0]) >= 4:
        circles = np.round(circles[0, :]).astype("int")
        # 試著過濾出半徑最接近的4個圓（可選擇性使用）
        circles = sorted(circles, key=lambda c: c[2])[:4]  # 挑半徑最小的 4 個

        centers = np.array(circles)[:, :2]

        sorted_centers = sort_circle_centers(centers)

        if sorted_centers is not None:
            # 目標四角點：對應一個正矩形（寬 x 高）
            target_points = np.array([
                [0, 0],
                [300, 0],
                [300, 200],
                [0, 200]
            ], dtype="float32")

            M = cv2.getPerspectiveTransform(sorted_centers, target_points)
            warped = cv2.warpPerspective(frame, M, (300, 200))

            cv2.imshow("Warped", warped)

            # 顯示座標資訊（debug）
            for (x, y) in sorted_centers:
                cv2.circle(frame, (int(x), int(y)), 5, (0, 255, 0), -1)
                cv2.putText(frame, f"({x:.0f},{y:.0f})", (int(x)+10, int(y)-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    cv2.imshow("Original", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
