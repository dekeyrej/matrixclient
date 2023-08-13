# matrixclient

*Install rpi-rgb-led-matrix*
- clone it
- make it
- cd bindings/python and make that too

*Clone the repo*
- clone repositiory someplace 'suitable'

*Setup the python environment*
- cd to matrixclient
- link rpi-rgb-led-matrix here
- python3 -m venv venv
- source venv/bin/activate
- pip install -r requirements.txt

*Setup the execution environment*
- copy sample.env to .env and edit with your values ('ENC_SECRETS_PATH' is not currently used)
- copy sample_mc.sh mc.sh and edit 'DIR' for your current directory
- chmod +x mc.sh
- chmod 777 static/

*Setup your secrets*
- copy sample_secrets.json to secrets.json
- edit with your values

*Test the setup*
- sudo ./mc.sh

*To run as a Service (assuming systemctl)*
- after successfully testing via mc.sh
- copy sample_matrix.service matrix.service and edit ExecStart to point to full path of mc.sh
- copy matrix.service to /etc/systemd/system
- sudo systemctl enable matrix
- sudo systemctl start matrix

*Notes*
- (if you want to reencrypt your values in mysecrets.py)