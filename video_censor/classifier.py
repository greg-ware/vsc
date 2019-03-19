import os
import zmq
import mss
import json
import cv2
import numpy as np
import random
# from tensorflow import keras
from prefetch_generator import background


@background(max_prefetch=1)
def screenshot(monitor):
    """Generate and preprocess screenshot"""
    while True:
        img = np.asarray(sct.grab(monitor))[:,:,:3]
        img =  cv2.resize(img, (224, 224)) / 255.0
        yield img


def predict(img):
    pred = model.predict(np.asarray([img]))[0][0]
    return pred


def crop(size, crop):
    w, h = size
    top, left, right, bottom = crop
    w -= (left + right)
    h -= (top + bottom)
    return w, h

def scale(info):
    w, h =  info["source_size"]
    top, left, right, bottom = info["crop"]
    scale_x, scale_y = info["scale"]
    for val in [w, left, right]:
        val *= scale_x
    for val in [h, top, bottom]:
        val *= scale_y
    return w, h, top, left, right, bottom

def update_monitor(monitor, info):
    if monitor["width"] == info["source_size"][0]:
        w, h = crop(info["source_size"], info["crop"])
        monitor["top"] += info["crop"][0]
        monitor["left"] += info["crop"][1]
        monitor["width"] = w
        monitor["height"] = h
        scale = 0
    else:
        scale = monitor["width"]/info["source_size"][0]
        w, h = crop(info["source_size"], info["crop"])
        monitor["top"] += int(info["crop"][0]*scale)
        monitor["left"] += int(info["crop"][1]*scale)
        monitor["width"] = int(w*scale)
        monitor["height"] = int(h*scale)
    return monitor


def connect(port, socket_type=zmq.REQ):
    context = zmq.Context()
    socket = context.socket(socket_type)
    socket.connect(f"tcp://127.0.0.1:{port}")
    return socket


def parse_conf():
    with open("conf.json", 'r') as f:
        conf = json.load(f)
    return conf["monitor"], conf["monitor_info"], conf["port"]


if __name__=='__main__':
    mon, mon_info, port = parse_conf()
    producer = connect(port)
    with mss.mss() as sct:
        monitor = update_monitor(sct.monitors[mon], mon_info)
        sct_img = sct.grab(monitor)
        mss.tools.to_png(sct_img.rgb, sct_img.size, output="test.png")

    # model = keras.models.load_model('mobilenet1.3.h5')

    #     for img in screenshot(monitor):
    #         pred = predict(img)
    #         producer.send_pyobj(pred)
    #         producer.recv()
    #         print(pred)
