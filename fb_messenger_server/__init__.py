import os
import yaml


class Config(dict):
    def __init__(self, *args, **kwargs):
        # load default config
        folder = os.path.split(os.path.realpath(__file__))[0]
        default_config_path = os.path.join(folder, "config_defaults.yml")
        with open(default_config_path) as f:
            config_dict = yaml.load(f, Loader=yaml.Loader)

        # load config
        fn = os.environ.get("CONFIG_PATH", "config.yml")
        if os.path.exists(fn):
            with open(os.environ.get("CONFIG_PATH", "config.yml"), 'r') as f:
                config_dict.update(yaml.load(f))

        self.config_dict = config_dict
        super(Config, self).__init__(*args, **kwargs)

    def __getitem__(self, item):
        # prioritize environmental variables
        return os.environ.get(item, self.config_dict.get(item))


config = Config()


import logging

# setup logging
logger = logging.getLogger("fb_messenger")
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.setLevel(logging.INFO)

from pymongo import MongoClient
client = MongoClient('mongodb://admin:admin1@ds239911.mlab.com:39911/nutrients')
db = client.nutrients
