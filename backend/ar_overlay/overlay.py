import cv2
import numpy as np
import requests
import os

# ----------------------------
# Fetch first ad from FastAPI
# ----------------------------
API_URL = "http://localhost:8000/api/ads"

try:
    ads = requests.get(API_URL).json()
except Exception as e:
    print("❌ Failed to fetch ads:", e)
    exit()

if not ads:
    print("❌ No ads found in the backend!")
    exit()

# Pick the first ad
ad = ads[0]

# Convert URL to local file path
marker_path = ad["imageUrl"].replace("/static", "backend/static")
video_path = ad["videoUrl"].replace("/static", "backend/static")

# ----------------------------
# Load marker image
# ----------------------------
marker = cv2.imread(marker_path, cv2.IMREAD_GRAYSCALE)
if marker is None:
    print("❌ Marker image not found at", marker_path)
    exit()

orb = cv2.ORB_create(1000)
kp_marker, des_marker = orb.detectAndCompute(marker, None)

# ----------------------------
# Load overlay video
# ----------------------------
overlay_video = cv2.VideoCapture(video_path)
if not overlay_video.isOpened():
    print("❌ Failed to open video at", video_path)
    exit()

# ----------------------------
# Initialize webcam and matcher
# ----------------------------
cap = cv2.VideoCapture(0)
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)

paused = False
show_matches = False

# ----------------------------
# Main loop
# ----------------------------
while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    kp_frame, des_frame = orb.detectAndCompute(gray, None)

    if des_frame is not None:
        knn = bf.knnMatch(des_marker, des_frame, k=2)
        good = []

        for m_n in knn:
            if len(m_n) == 2:
                m, n = m_n
                if m.distance < 0.75 * n.distance:
                    good.append(m)

        if len(good) > 15:
            src_pts = np.float32([kp_marker[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
            dst_pts = np.float32([kp_frame[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

            H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

            if H is not None:
                h, w = marker.shape
                pts = np.float32([[0, 0], [w, 0], [w, h], [0, h]]).reshape(-1, 1, 2)
                dst = cv2.perspectiveTransform(pts, H)

                # Draw outline
                cv2.polylines(frame, [np.int32(dst)], True, (0, 255, 0), 3)

                # Get next frame from video
                if not paused:
                    ret_vid, vid_frame = overlay_video.read()
                    if not ret_vid:
                        overlay_video.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        ret_vid, vid_frame = overlay_video.read()
                else:
                    ret_vid = False

                if ret_vid:
                    vid_frame = cv2.resize(vid_frame, (w, h))
                    warp_matrix = cv2.getPerspectiveTransform(
                        np.float32([[0, 0], [w, 0], [w, h], [0, h]]),
                        dst.reshape(4, 2).astype(np.float32)
                    )
                    warped = cv2.warpPerspective(vid_frame, warp_matrix, (frame.shape[1], frame.shape[0]))

                    mask_new = np.zeros((frame.shape[0], frame.shape[1]), dtype=np.uint8)
                    cv2.fillConvexPoly(mask_new, np.int32(dst), 255)
                    mask_3ch = cv2.merge([mask_new, mask_new, mask_new])

                    frame = cv2.bitwise_and(frame, 255 - mask_3ch)
                    frame = cv2.add(frame, warped)

        if show_matches:
            match_vis = cv2.drawMatches(marker, kp_marker, frame, kp_frame, good, None, flags=2)
            cv2.imshow("Matches", match_vis)

    cv2.imshow("AR Overlay", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('p'):
        paused = not paused
    elif key == ord('m'):
        show_matches = not show_matches

# ----------------------------
# Cleanup
# ----------------------------
cap.release()
overlay_video.release()
cv2.destroyAllWindows()
