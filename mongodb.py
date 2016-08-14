# coding: utf-8

from fabkit import filer, env, run
from fablib.base import SimpleBase


class MongoDB(SimpleBase):
    def __init__(self):
        self.data_key = 'mongodb'
        self.data = {
            'users': {},
            'databases': {},
            'port': 27017,
        }

        self.services = ['mongod']

        self.packages = [
            'mongodb-org-server',
            'mongodb-org',
        ]

    def init_after(self):
        for cluster in self.data.get('cluster_map', {}).values():
            if env.host in cluster['hosts']:
                self.data.update(cluster)
                break

    def setup(self):
        data = self.init()

        if self.is_tag('package'):
            filer.template(src='mongodb.repo', dest='/etc/yum.repos.d/mongodb.repo')
            self.install_packages('--enablerepo mongodb-org')

        if self.is_tag('conf'):
            if filer.template('/etc/mongod.conf', data=data):
                self.handlers['restart_mongod'] = True

        if self.is_tag('service'):
            self.enable_services().start_services()
            self.exec_handlers()

        if self.is_tag('data'):
            for user in data['user_map'].values():
                for db in user['dbs']:
                    roles = '","'.join(user['roles'])
                    run('mongo --eval \''
                        'db = db.getSiblingDB("{0}");'
                        'if (db.getUser("{1}") == null) {{'
                        '    db.createUser({{user: "{1}", pwd: "{2}", roles: ["{3}"]}})'
                        '}}\''.format(db, user['user'], user['password'], roles))
