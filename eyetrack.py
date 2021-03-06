import cv2
import numpy as np
from scipy.io import savemat
from scipy.misc import imresize
from time import clock, sleep
from math import floor

import tracking

# PARAMETERS
dorec = False
dosave = True
dotrack = True
outname = "data"

# INPUT MOVIE
if dorec:
    film = cv2.VideoCapture(2)
else:
    film = cv2.VideoCapture("mouseeyetracking.avi")

# Check frame size
ret, frame = film.read()
while frame is None:
    ret, frame = film.read()
print ret
print film.isOpened()
print frame.shape
if frame.ndim == 3:
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

# follow speed of processing frames
nprocessed = 0
idle = False
t0 = clock()


# USER SELECTS ROI
if dorec:
    # wait for user ready
    while film.isOpened():
        ret, frame = film.read()
        if not ret:
            if not idle:
                idle = True
                print 'some idle time after processing',nprocessed,'frames'
                processed = 0
            sleep(.001)
            continue

        # follow speed of processing frames
        t = clock()
        nprocessed += 1
        idle = False
        if t>t0+1:
            print 'processing frames at',nprocessed/(t-t0),'Hz'
            t0 = t
            nprocessed = 0

        if frame.ndim == 3:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        cv2.imshow('image2',frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # user select ROI
    roi = tracking.select_roi(frame)
else:
    # fixed ROI
    roi = {'x1': 222, 'y1': 163, 'x2': 268, 'y2': 210}

eye = tracking.resize_roi(frame, roi)

# OUTPUT MOVIE
if dosave:
    # ROI for saving must be at least 65x65 otherwise buffer might be to small
    roisave = roi.copy()
    nxsave, nysave = roi['x2']-roi['x1'], roi['y2']-roi['y1']
    if nxsave<65:
        roisave['x1'] = roi['x1'] - floor((65-nxsave)/2)
        nxsave = 65
        roisave['x2'] = roisave['x1'] + nxsave
    if nysave<65:
        roisave['y1'] = roi['y1'] - floor((65-nysave)/2)
        nysave = 65
        roisave['y2'] = roisave['y1'] + nysave

    # Create movie
    fourcc = cv2.VideoWriter_fourcc(*'i420')
    out = cv2.VideoWriter(outname+'.avi', fourcc, 60.0, (nysave, nxsave))

    # Time vector
    timevector = []


# INIT TRACKER
if dotrack:
    T = tracking.Tracker(eye)

# PROCESS MOVIE
while film.isOpened():
    ret, frame = film.read()
    if not ret:
        if dorec:
            if not idle:
                idle = True
                print 'some idle time after processing',nprocessed,'frames'
                processed = 0
            sleep(.001)
            continue
        else:
            break

    # follow speed of processing frames
    t = clock()
    nprocessed += 1
    idle = False
    if t>t0+1:
        print 'processing frames at',nprocessed/(t-t0),'Hz'
        t0 = t
        nprocessed = 0

    # save
    if dosave:
        img = tracking.resize_roi(frame, roisave)
        out.write(img)
        timevector.append(clock())

    # convert to single channel
    if frame.ndim == 3:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # crop
    eye = tracking.resize_roi(frame, roi)

    # track
    if dotrack:
        T.track(eye)

    # display
    scale = 4
    s = eye.shape
    img = imresize(eye, (s[0]*scale, s[1]*scale))
    if dotrack:
        circle = T.fit*scale
        cv2.circle(img,(int(circle[0]),int(circle[1])),int(circle[2]),255,1)
    cv2.imshow('eye',img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


# When everything done, release the capture
cv2.destroyAllWindows()
film.release()
if dosave:
    out.release()
    savedata = {'timevector': timevector}
    if dotrack:
        savedata['xshift'] = T.xshift
        savedata['yshift'] = T.yshift
        savedata['rshift'] = T.rshift
    savemat(outname+'.mat', savedata)
if dotrack:
    T.summary()
