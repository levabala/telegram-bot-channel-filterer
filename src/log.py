from datetime import datetime


def log(*args):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(timestamp, *args)
