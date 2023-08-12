from securedict    import DecryptDicts
from secretsecrets import encsecrets
from datasourcelib import Database

import json
import arrow

dd = DecryptDicts()
dd.read_key_from_file('Do_Not_Copy/refKey.txt')
secrets = dd.decrypt_dict(encsecrets)
DBHOST = 'rocket3'
DBPORT = 5432
db_params = {"user": secrets['dbuser'], "pass": secrets['dbpass'], "host": DBHOST, "port":  DBPORT, "db_name": 'matrix', "tbl_name": 'feed'}
db = Database('postgres', db_params)

def saveDisplayConfig(db, cv):
    config = {}
    config['type'] = 'Display Config' # or 'Default Config'
    config['updated'] = arrow.now().to('US/Eastern').format('MM/DD/YYYY h:mm A ZZZ')
    config['valid'] = arrow.now().shift(hours=+1).to('US/Eastern').format('MM/DD/YYYY h:mm A ZZZ')
    config['values'] = cv
    db.write(config)

def loadDisplayConfig(path):
    with open(path) as f:
        config = json.loads(f.read())
    f.close()
    print(json.dumps(config, indent=2))
    return config

def saveDefaultConfig(db, ddict):
    db.write(ddict)

def loadDefaultConfig(path):
    with open(path) as f:
        config = json.loads(f.read())
    f.close()
    print(json.dumps(config, indent=2))
    return config

# loadDefaultConfig('static\default_config.txt')
# loadDisplayConfig('static\display_config.txt')

saveDefaultConfig(db, loadDefaultConfig('static\default_config.txt'))
saveDisplayConfig(db, loadDisplayConfig('static\display_config.txt'))
