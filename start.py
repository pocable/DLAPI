import sys
import json
import os

if __name__ == "__main__":
    conf = None
    try:
        # Development. DLAPI_KEYS_START.txt should be a JSON representation of the environment variables required.
        f = open('DLAPI_KEYS_START.txt', 'r')
        item = f.read()
        print(item)
        f.close()
        conf = json.loads(item)
    except:
        print("Failed to load environment.")
        sys.exit(1)

    for item in conf.keys():
        os.environ[item] = conf[item]

    # Note that the state is not saved when running this development file.
    import dlapi.DLAPI
    dlapi.DLAPI.main()
    input()
        
