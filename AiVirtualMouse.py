import cv2
import numpy as np
import HandTrackingModule as htm
import time
import pyautogui  # REPLACING autopy
import subprocess  # Built-in Python library to open programs

# import autopy

# Auto-open MS Paint
print("Launching MS Paint...")
subprocess.Popen("mspaint")
time.sleep(2)  # Give Paint 2 seconds to open before the camera starts

#######################
wCam, hCam = 648, 488
frameR = 100  # Frame reduction
smoothening = 10

isDrawing = False
prevPinchDist = 0
#########################

pTime = 0
plocX, plocY = 0, 0
clocX, clocY = 0, 0
cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)
detector = htm.handDetector(maxHands=1)
wScr, hScr = pyautogui.size()
# print(wScr,hScr)


while True:
    # 1-Find hand Landmarks
    success, img = cap.read()
    img = detector.findHands(img)
    lmList, bbox = detector.findPosition(img)

    # 2- Get the tip of the index and middle fingers
    if len(lmList) != 0:
        x1, y1 = lmList[8][1:]
        x2, y2 = lmList[12][1:]

        # 3- check which fingers are up
        fingers = detector.fingersUp()

        # 5- Convert Coordinates (Moved up so all modes can use it)
        x3 = np.interp(x1, (frameR, wCam - frameR), (0, wScr - 1))
        y3 = np.interp(y1, (frameR, hCam - frameR), (0, hScr - 1))

        # 6- smoothen Values
        clocX = plocX + (x3 - plocX) / smoothening
        clocY = plocY + (y3 - plocY) / smoothening

        cv2.rectangle(img, (frameR, frameR), (wCam - frameR, hCam - frameR), (255, 0, 255), 2)

        # 4- Only index finger : Moving Mode (Hovering over paint)
        if fingers[1] == 1 and fingers[2] == 0 and fingers[0] == 0:
            # 7- Move Mouse
            pyautogui.moveTo(wScr - clocX, clocY)
            cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)
            plocX, plocY = clocX, clocY

        # 8- Both Index and middle fingers are up : Drawing Mode
        if fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0:
            pyautogui.moveTo(wScr - clocX, clocY)
            if not isDrawing:
                pyautogui.mouseDown()
                isDrawing = True
            cv2.circle(img, (x1, y1), 15, (0, 255, 0), cv2.FILLED)
            plocX, plocY = clocX, clocY
        else:
            if isDrawing:
                pyautogui.mouseUp()
                isDrawing = False

        # 9- Thumb and Index are up : Zooming Mode
        if fingers[0] == 1 and fingers[1] == 1 and fingers[2] == 0:
            # Find distance between thumb and index
            length, img, lineInfo = detector.findDistance(4, 8, img)

            if prevPinchDist != 0:
                delta = length - prevPinchDist
                if abs(delta) > 5:
                    pyautogui.keyDown('ctrl')
                    if delta > 0:
                        pyautogui.scroll(150)
                        cv2.putText(img, "ZOOM IN", (50, 100), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 0), 3)
                    else:
                        pyautogui.scroll(-150)
                        cv2.putText(img, "ZOOM OUT", (50, 100), cv2.FONT_HERSHEY_PLAIN, 3, (0, 0, 255), 3)
                    pyautogui.keyUp('ctrl')

            prevPinchDist = length
        else:
            prevPinchDist = 0

    # 11- Frame Rate
    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime
    cv2.putText(img, str(int(fps)), (20, 50), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 0), 3)

    # 12- Display
    cv2.imshow("Image", img)
    cv2.waitKey(1)