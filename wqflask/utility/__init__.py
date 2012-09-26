class Bunch(object):
    """Make the configuration a little cleaner"""
    def __init__(self, config_string = "", **kw):
        if config_string:
            td = yaml.load(config_string)
            self.__dict__.update(td)
        else:
            self.__dict__ = kw

    def __repr__(self):
        return yaml.dump(self.__dict__, default_flow_style=False)

