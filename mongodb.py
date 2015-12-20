# coding: utf-8

from fabkit import filer, env, run
from fablib.base import SimpleBase


class MongoDB(SimpleBase):
    def __init__(self):
        self.data_key = 'mongodb'
        self.data = {
            'users': {},
            'databases': {},
        }

        self.services = ['mongod']

        self.packages = [
            'mongodb-org-server',
            'mongodb-org',
        ]

    def init_after(self):
        for cluster in self.data.values():
            if env.host in cluster['hosts']:
                self.data['mysql_cluster'] = cluster
                break

    def setup(self):
        self.init()
        cluster = self.data['mysql_cluster']

        if self.is_tag('package'):
            filer.template(src='mongodb.repo', dest='/etc/yum.repos.d/mongodb.repo')
            self.install_packages('--enablerepo mongodb-org')

        if self.is_tag('conf'):
            is_updated = filer.template('/etc/mongod.conf', data=self.data)

        if self.is_tag('service'):
            self.enable_services().start_services()
            if is_updated:
                self.restart_services()

        if self.is_tag('data'):
            for user in cluster['users'].values():
                roles = '","'.join(user['roles'])
                run('mongo --eval \''
                    'db = db.getSiblingDB("{0}");'
                    'if (db.getUser("{1}") == null) {{'
                    '    db.createUser({{user: "{1}", pwd: "{2}", roles: ["{3}"]}})'
                    '}}\''.format(user['db'], user['user'], user['password'], roles))
