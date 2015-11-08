# coding: utf-8

import socket
from fabkit import filer, api, sudo, env, run
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
            'mongodb-server',
            'mongodb',
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
            self.install_packages()

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

        # if self.is_tag('data'):
        #     # get root_password or init root_password
        #     if filer.exists('/root/.my.cnf'):
        #         root_password = sudo("grep ^password /root/.my.cnf | head -1 | awk '{print $3}'")
        #     else:
        #         root_password = sudo('cat /dev/urandom | tr -dc "[:alnum:]" | head -c 32')
        #         sudo('mysqladmin password {0} -uroot'.format(root_password))
        #         filer.template('/root/.my.cnf', data={'root_password': root_password})

        #     self.create_users()
        #     self.delete_default_users()
        #     if env.host == cluster['hosts'][0]:
        #         self.create_databases()

    # def setup_slave(self):
    #     self.init()
    #     cluster = self.data['mysql_cluster']

    #     if len(cluster['hosts']) == 2:
    #         for host in cluster['hosts']:
    #             if env.host != host:
    #                 master_ip = socket.gethostbyname(host)
    #                 break

    #         slave_user = cluster['users'][cluster['slave_user']]
    #         result = self.sql('show slave status')
    #         if result.find(master_ip) == -1:
    #             self.sql("change master to "
    #                      "master_host = '{master_ip}', "
    #                      "master_port=3306, "
    #                      "master_user='{slave_user[user]}', "
    #                      "master_password='{slave_user[password]}', "
    #                      "master_auto_position=1;".format(
    #                          master_ip=master_ip, slave_user=slave_user))

    #             self.sql("start slave")

    # def sql(self, query):
    #     self.init()
    #     return sudo('mysql -uroot -e"{0}"'.format(query))

    # def create_users(self):
    #     self.init()
    #     cluster = self.data['mysql_cluster']
    #     for user in cluster['users'].values():
    #         for src_host in user.get('src_hosts', ['localhost']):
    #             query = 'GRANT {privileges} ON {table} TO \'{user}\'@\'{host}\' IDENTIFIED BY \'{password}\''.format(  # noqa
    #                 privileges=user.get('privileges', 'ALL PRIVILEGES'),
    #                 table=user.get('table', '*.*'),
    #                 user=user['user'],
    #                 password=user['password'],
    #                 host=src_host,
    #             )

    #             self.sql(query)

    # def delete_default_users(self):
    #     self.init()
    #     self.sql("delete from mysql.user where user='root' and host!='localhost'")
    #     self.sql("delete from mysql.user where user=''")

    # def create_databases(self):
    #     data = self.init()
    #     cluster = data['mysql_cluster']
    #     with api.warn_only():
    #         for db in cluster['dbs']:
    #             result = self.sql('use {0}'.format(db))
    #             if result.return_code != 0:
    #                 self.sql('CREATE DATABASE {0} DEFAULT CHARACTER SET utf8;'.format(db))
