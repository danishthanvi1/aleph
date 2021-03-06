from urlparse import urljoin
import requests
import logging

from aleph.model import Role, Permission
from aleph.crawlers.crawler import EntityCrawler

log = logging.getLogger(__name__)

JSON_PATH = 'http://archive.pudo.org/opennames/latest/metadata.json'
IGNORE_SOURCES = ['EVERY-POLITICIAN']
SCHEMA = {
    'individual': '/entity/person.json#',
    'entity': '/entity/entity.json#'
}


class OpenNamesCrawler(EntityCrawler):  # pragma: no cover

    def crawl_source(self, source):
        if source.get('source_id') in IGNORE_SOURCES:
            return

        json_file = source.get('data', {}).get('json')
        url = urljoin(JSON_PATH, json_file)
        source_name = source.get('source') or source.get('source_id')
        label = '%s - %s' % (source.get('publisher'), source_name)
        collection = self.find_collection(url, {
            'label': label
        })
        Permission.grant_foreign(collection, Role.SYSTEM_GUEST, True, False)
        log.info(" > OpenNames collection: %s", collection.label)
        entities = requests.get(url).json().get('entities', [])
        for entity in entities:
            data = {
                'identifiers': [{
                    'scheme': 'opennames:%s' % source.get('source_id'),
                    'identifier': entity.get('uid')
                }],
                'other_names': [],
                'name': entity.get('name'),
                '$schema': SCHEMA.get(entity.get('type'),
                                      '/entity/entity.json#')
            }
            for on in entity.get('other_names', []):
                on['name'] = on.pop('other_name', None)
                data['other_names'].append(on)
            self.emit_entity(collection, data)
        self.emit_collection(collection)

    def crawl(self):
        data = requests.get(JSON_PATH).json()
        for source in data.get('sources', []):
            self.crawl_source(source)
