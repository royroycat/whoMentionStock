from pony.orm import *

def define_entity(db):
    class Config(db.Entity):
        _table_ = "config"
        id = PrimaryKey(int, auto=True)
        name = Required(str, unique=True)
        value = Optional(str)
        
        @classmethod
        def get_value(cls, name):
            config = db.Config.select(lambda c: c.name == name).first()
            return config.value