import json
from pathlib import Path
from types import SimpleNamespace


class ConfigException(Exception):
    def __init__(self, option: str):
        self.option = option


class MissingConfigOption(ConfigException):
    def __str__(self):
        return f"Option {self.option} not found in config!"


class WhitespaceConfigOption(ConfigException):
    def __str__(self):
        return f"Config option {self.option} contains only whitespace!"


class ConfigNamespace(SimpleNamespace):
    def __getattribute__(self, item):
        attr = super().__getattribute__(item)
        if len(str(attr).strip()) > 0:
            return attr

        error = WhitespaceConfigOption(item)
        print("Config", f"{error}")
        raise error

    def __getattr__(self, item):
        error = MissingConfigOption(item)
        print("Config", f"{error}")
        raise error


class Config:
    __config = None
    CONFIG_PATH = Path(__file__).parent / "config.json"

    @classmethod
    def get(cls) -> ConfigNamespace:
        if cls.__config is None:
            cls.refresh()
        return cls.__config

    @classmethod
    def __convert_to_dict(cls, namespace: ConfigNamespace) -> dict:
        d = namespace.__dict__
        for key in d.keys():
            if type(d[key]) is ConfigNamespace:
                d[key] = cls.__convert_to_dict(d[key])
        return d

    @classmethod
    def save(cls):
        with open(cls.CONFIG_PATH, "w") as f:
            json.dump(cls.__convert_to_dict(cls.get()), f, indent=4)

    @classmethod
    def __read(cls) -> ConfigNamespace:
        with open(cls.CONFIG_PATH, "r") as f:
            return json.load(f, object_hook=lambda d: ConfigNamespace(**d))

    @classmethod
    def refresh(cls):
        cls.__config = cls.__read()
