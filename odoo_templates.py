# -*- coding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, ERP-PLM-CAD Open Source Solution
#    Copyright (C) 2011-2023 https://OmniaSolutions.website
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this prograIf not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
'''
Created on 13 Jan 2023

@author: mboscolo
'''

INIT_SCRIPT_TEMPLATE="""#!/bin/bash
#
"""

ODOO_CONF_TEMPLATE = """[options]
addons_path = %s
db_user = %s
# shared folder for filestore
#
# Shared forlder for addons syncronization must be set it up manually
#
data_dir=%s
 
"""

ODOO_MIGRATE_TEMPLATE = """
echo "Drop Database {to_db}"
psql -U {db_user} -d postgres -c "drop database {to_db};"
echo "Create database {to_db}"
set -e
set -o pipefail
psql -U {db_user} -d postgres -c "CREATE DATABASE {to_db} WITH TEMPLATE {from_db} OWNER odoo;"
echo "Perform security clean up {to_db}"
#
# support functions 
#
# psql -U {db_user} -d {to_db} -f ../support.sql
#
# disable mail server and jobs
#
psql -U {db_user} -d {to_db} -c "update fetchmail_server set active=false;"
psql -U {db_user} -d {to_db} -c "update ir_mail_server set active=false;"
psql -U {db_user} -d {to_db} -c "update ir_cron set active=false;"
#
# put here your database fixes
#
# es:  
# psql -U {db_user} -d {to_db} -c "select remove_all_views('sale');"
#
echo "Start Migration process"
source ./python/bin/activate
./OCA/OpenUpgrade/odoo-bin --config=odoo.conf --database={to_db} --update=all --stop-after-init
echo "Migration done use ./run.sh to test the migration !!"
"""
ODOO_MIGRATE_TEMPLATE_14 = """
echo "Drop Database {to_db}"
psql -U {db_user} -d postgres -c "drop database {to_db};"
echo "Create database {to_db}"
set -e
set -o pipefail
psql -U {db_user} -d postgres -c "CREATE DATABASE {to_db} WITH TEMPLATE {from_db} OWNER odoo;"
echo "Perform security clean up {to_db}"
#
# support functions 
#
# psql -U {db_user} -d {to_db} -f ../support.sql
#
psql -U {db_user} -d {to_db} -c "update fetchmail_server set active=false;"\n
psql -U {db_user} -d {to_db} -c "update ir_mail_server set active=false;"\n
psql -U {db_user} -d {to_db} -c "update ir_cron set active=false;"\n
#
# put here your database fixes
#
# es:  
# psql -U {db_user} -d {to_db} -c "select remove_all_views('sale');"
#
echo "Start Migration process"
source ./python/bin/activate
./OCA/OCB/odoo-bin --upgrade-path=./OCA/OpenUpgrade/openupgrade_scripts/scripts/ --load=base,web,openupgrade_framework --database={to_db} --update=all --stop-after-init --config=odoo.conf
echo "Migration done use ./run.sh to test the migration !!"
"""
ODOO_RUN_9 = """
source python/bin/activate
./OCA/OCB/odoo-bin --database={to_db} --db-filter={to_db} --config=odoo.conf
"""
ODOO_RUN_UPDATE_9 = """
source python/bin/activate
./OCA/OCB/odoo-bin --database={to_db} --db-filter={to_db} --config=odoo.conf --update=web
"""

ODOO_RUN = """
source python/bin/activate
./OCA/OpenUpgrade/odoo-bin --database={to_db} --db-filter={to_db} --config=odoo.conf
"""
ODOO_RUN_UPDATE = """
source python/bin/activate
./OCA/OpenUpgrade/odoo-bin --database={to_db} --db-filter={to_db} --config=odoo.conf --update=web
"""
