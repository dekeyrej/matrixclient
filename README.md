# matrixclient

## Introduction

A modular display driver for RGB LED matrices, powered by real-time data streamed from an SSE-capable API server. Designed for external operation—no Redis or Postgres access required. Built to elegantly render environmental info, sports updates, system status, and more.

Inspired by years of ambient data visualization and play-by-play commentary à la NESN.

## Features

- Class-based architecture with internal state control
- SSE subscription for real-time updates and remote control (`webcontrol` messages)
- Modular display logic with support for cycling and pausing
- RGB LED matrix rendering using `rpi-rgb-led-matrix`
- Ready-to-run with systemd service integration

## WebControl Commands

Via SSE stream, matrixclient responds to the following commands:

| Command | Action                       |
|---------|------------------------------|
| `pp`    | Toggle play/pause cycle      |
| `fwd`   | Advance to next display      |
| `rew`   | Revert to previous display   |
| `out`   | Mark garbage as taken out    |

> **SSE-powered. Redis-free. Built for real-time elegance.**

## Setup

*Prerequisites*

*Install rpi-rgb-led-matrix*
- clone it from https://github.com/hzeller/rpi-rgb-led-matrix.git
- cd rpi-rgb-led-matrix ; run make
- cd bindings/python and sudo make install

*Clone the repo*
- clone repositiory someplace 'suitable'

*Setup the python environment*
- cd to matrixclient
- link rpi-rgb-led-matrix here
- python3 -m venv venv
- source venv/bin/activate
- pip install -r requirements.txt

*Setup the execution environment*
- copy sample_mc.sh mc.sh and edit 'DIR' for your current directory
- chmod +x mc.sh
- chmod 777 static/

*Setup your configuration/secrets*
- copy sample_config.py to config.json
- edit with your values

*Test the setup*
- sudo ./mc.sh

*To run as a Service (assuming systemctl)*
- after successfully testing via mc.sh
- copy sample_matrix.service matrix.service and edit ExecStart to point to full path of mc.sh
- copy matrix.service to /etc/systemd/system
- sudo systemctl enable matrix
- sudo systemctl start matrix
