# matrixclient

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
