from config import log, logging, num_of_dock
from pms.pms import wakeUpDock
from time import sleep

log.setLevel(logging.INFO)

if __name__ == '__main__':
    for dock in range(1,num_of_dock+1):
        wakeUpDock(dock)