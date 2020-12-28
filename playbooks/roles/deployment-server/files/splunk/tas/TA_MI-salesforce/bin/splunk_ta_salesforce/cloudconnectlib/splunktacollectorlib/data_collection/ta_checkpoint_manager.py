from builtins import object
import json
import logging
import re

from . import ta_consts as c
from . import ta_helper as th
from ..common import log as stulog
from ...splunktalib import state_store as ss
from ...splunktalib.common.util import is_true


class TACheckPointMgr(object):
    SEPARATOR = "_" * 3

    # FIXME We'd better move all default values together
    _DEFAULT_MAX_CACHE_SECONDS = 5
    _MAXIMUM_MAX_CACHE_SECONDS = 3600

    def __init__(self, meta_config, task_config):
        self._task_config = task_config
        self._store = self._create_state_store(
            meta_config,
            task_config.get(c.checkpoint_storage_type),
            task_config[c.appname]
        )

    def _create_state_store(self, meta_config, storage_type, app_name):
        stulog.logger.debug('Got checkpoint storage type=%s', storage_type)

        if storage_type == c.checkpoint_kv_storage:
            collection_name = self._get_collection_name()
            stulog.logger.debug(
                'Creating KV state store, collection name=%s', collection_name
            )
            return ss.get_state_store(
                meta_config,
                appname=app_name,
                collection_name=collection_name,
                use_kv_store=True
            )

        use_cache_file = self._use_cache_file()
        max_cache_seconds = \
            self._get_max_cache_seconds() if use_cache_file else None

        stulog.logger.debug(
            'Creating file state store, use_cache_file=%s, max_cache_seconds=%s',
            use_cache_file, max_cache_seconds
        )

        return ss.get_state_store(
            meta_config,
            app_name,
            use_cache_file=use_cache_file,
            max_cache_seconds=max_cache_seconds
        )

    def _get_collection_name(self):
        collection = self._task_config.get(c.collection_name)
        collection = collection.strip() if collection else ''

        if not collection:
            input_name = self._task_config[c.mod_input_name]
            stulog.logger.info(
                'Collection name="%s" is empty, set it to "%s"',
                collection, input_name
            )
            collection = input_name
        return re.sub(r'[^\w]+', '_', collection)

    def _use_cache_file(self):
        # TODO Move the default value outside code
        use_cache_file = is_true(self._task_config.get(c.use_cache_file, True))
        if use_cache_file:
            stulog.logger.info(
                "Stanza=%s using cached file store to create checkpoint",
                self._task_config[c.stanza_name]
            )
        return use_cache_file

    def _get_max_cache_seconds(self):
        default = self._DEFAULT_MAX_CACHE_SECONDS
        seconds = self._task_config.get(
            c.max_cache_seconds, default
        )
        try:
            seconds = int(seconds)
        except ValueError:
            stulog.logger.warning(
                "The max_cache_seconds '%s' is not a valid integer,"
                " so set this variable to default value %s",
                seconds, default
            )
            seconds = default
        else:
            maximum = self._MAXIMUM_MAX_CACHE_SECONDS
            if not (1 <= seconds <= maximum):
                # for seconds>3600 set it to 3600. for seconds <=0 set it to default.
                adjusted = max(min(seconds, maximum), default)
                stulog.logger.warning(
                    "The max_cache_seconds (%s) is expected in range[1,%s],"
                    " set it to %s",
                    seconds, maximum, adjusted
                )
                seconds = adjusted
        return seconds

    def _get_ckpt_key(self, namespaces=None):
        if not namespaces:
            stanza = self._task_config[c.stanza_name]
            stulog.logger.info('Namespaces is empty, using stanza name [%s] instead.', stanza)
            namespaces = [stanza]
        key_str, hashed_file = self._hash_key(namespaces)
        stulog.logger.debug("raw_file='%s' hashed_file='%s'", key_str, hashed_file)
        return hashed_file, namespaces

    def get_ckpt(self, namespaces=None, show_namespaces=False):
        key, _ = self._get_ckpt_key(namespaces)
        raw_checkpoint = self._store.get_state(key)
        if stulog.logger.isEnabledFor(logging.DEBUG):
            stulog.logger.debug(
                "Get checkpoint key='%s' value='%s'", key, json.dumps(raw_checkpoint))
        if not show_namespaces and raw_checkpoint:
            return raw_checkpoint.get("data")
        return raw_checkpoint

    def delete_if_exists(self, namespaces=None):
        """Return true if exist and deleted else False"""
        key, _ = self._get_ckpt_key(namespaces)
        if self._store.exists(key):
            self._store.delete_state(key)
            return True
        return False

    def update_ckpt(self, ckpt, namespaces=None):
        if not ckpt:
            stulog.logger.warning("Checkpoint expect to be not empty.")
            return
        key, namespaces = self._get_ckpt_key(namespaces)
        value = {"namespaces": namespaces, "data": ckpt}
        stulog.logger.debug("Update checkpoint key='%s' value='%s'",
                            key, json.dumps(value))
        self._store.update_state(key, value)

    def remove_ckpt(self, namespaces=None):
        key, _ = self._get_ckpt_key(namespaces)
        self._store.delete_state(key)

    @staticmethod
    def _hash_key(namespaces=None):
        key_str = TACheckPointMgr.SEPARATOR.join(namespaces)
        hashed_file = th.format_name_for_file(key_str)
        return key_str, hashed_file

    def close(self, key=None):
        try:
            self._store.close(key)
            stulog.logger.info('Closed state store successfully. key=%s', key)
        except Exception:
            stulog.logger.exception('Error closing state store. key=%s', key)
