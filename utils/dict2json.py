import json

secrets = {'dbuser': 'user', 
           'dbpass': 'password', 
           'wifi_connect_string': 'WIFI:S:eightchr;T:WPA;P:somerandopileofcharsoftherightlengthtooq;;', 
           'redis_password': 'someComplexPassword'}

print(json.dumps(secrets, indent=2))
with open('secrets.json', 'wt') as file:
    file.write(json.dumps(secrets, indent=1))
    file.close()

with open('secrets.json') as file:
    newsecrets = json.loads(file.read())
    file.close()

for k in newsecrets:
    print(f'{k}:{newsecrets[k]}')