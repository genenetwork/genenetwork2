# Backend query functions (logic)

from db.call import gn_server

from utility.logger import getLogger
logger = getLogger(__name__)


def menu_main():
    return gn_server("/int/menu/main.json")
