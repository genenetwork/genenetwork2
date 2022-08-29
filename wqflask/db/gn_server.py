# Backend query functions (logic)

from db.call import gn_server


def menu_main():
    return gn_server("/int/menu/main.json")
