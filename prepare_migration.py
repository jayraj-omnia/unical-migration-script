import os
import json
import argparse
import logging
from github import Github
from sql_template import SQL_SUPPORT_FUNCTION
from odoo_templates import ODOO_CONF_TEMPLATE
from odoo_templates import ODOO_MIGRATE_TEMPLATE
from odoo_templates import ODOO_MIGRATE_TEMPLATE_14
from odoo_templates import ODOO_RUN_9
from odoo_templates import ODOO_RUN_UPDATE_9
from odoo_templates import ODOO_RUN
from odoo_templates import ODOO_RUN_UPDATE
from odoo_templates import INIT_SCRIPT_TEMPLATE

base_dir = os.path.dirname(os.path.realpath(__file__))
#
# create logger
#
logger = logging.getLogger('prepare_migration')
logger.setLevel(logging.INFO)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
#
DEBUG=True
#

ALLOWED_REPOS = {
    "OpenUpgrade",
}

def _getAllOCARepo(gitHub):
    result = []
    if os.path.exists("OcaRepo.json"):
        with open("OcaRepo.json", "r") as f:
            data = json.load(f)
            return [r for r in data if r.get("name") in ALLOWED_REPOS]

    for r in gitHub.get_user("OCA").get_repos():
        if r.name not in ALLOWED_REPOS:
            continue

        print(f"Get Data from {r.name}")

        result.append({
            "name": r.name,
            "html_url": r.html_url,
            "full_name": r.full_name,
            "branches": [b.name for b in r.get_branches()],
        })

    # Save only allowed repos
    with open("OcaRepo.json", "w") as f:
        json.dump(result, f, indent=2)
    return result

    
def getOcaRepors(odoo_version, oca_template_repo):
    out = {}
    for repo in oca_template_repo:
        repo_name = repo.get("name")

        # Skip unwanted repos
        if repo_name not in ALLOWED_REPOS:
            continue

        # Skip meta repos
        if repo_name in [".github", "openupgradelib"]:
            continue

        # Check branch exists
        if odoo_version not in repo.get("branches", []):
            print(f"Skipping {repo_name}: no branch {odoo_version}")
            continue

        repo_url = repo.get("html_url")
        rel_repo_to_name = f"OCA/{odoo_version}/{repo_name}"

        print(f"Repo clone - : {repo_name}")

        out[repo_name] = (
            f"git clone --depth=1 --branch={odoo_version} "
            f"--single-branch {repo_url} ../{rel_repo_to_name}",
            rel_repo_to_name
        )
    return out


def createDefaultTemplate(odoo_version,
                          db_user,
                          from_db,
                          to_db,
                          version,
                          datadir,
                          to_dir,
                          oca_template_repo,
                          bef_version,
                          extra_repo=[]):
    s_lines = []
    addons_path = []
    for _repository_name , path in getOcaRepors(odoo_version,
                                               oca_template_repo).items():
        addons_path.append(os.path.join(to_dir,path[1]))
        s_lines.append(path[0] +'\n')
    for url, repo_name in extra_repo:
        s_lines.append(f"git clone --depth=1 --branch={odoo_version} --single-branch {url} ../EXTRA/{odoo_version}/{repo_name}\n")       
    
    if int(version)>=17:
        s_lines.append("python3.10 -m venv python\n")
    elif int(version)>=14:
        s_lines.append("python3.8 -m venv python\n")
    elif int(version)>=11:
        s_lines.append("python3.7 -m venv python\n")
    elif int(version) <=10:
        s_lines.append("virtualenv -p python2.7 python\n")
        
    s_lines.append("source  ./python/bin/activate\n")
    s_lines.append("python -m pip install --upgrade pip\n")    
    s_lines.append(f"pip install -r ../OCA/{odoo_version}/OpenUpgrade/requirements.txt\n")
    s_lines.append(f"pip install -r ../OCA/{odoo_version}/OCB/requirements.txt\n")
    s_lines.append("pip install pysftp\n")
    s_lines.append("pip install pyxb==1.2.6\n")
    s_lines.append("pip install codicefiscale\n")
    s_lines.append("pip install odfpy\n")
    if int(version) <=10:
        s_lines.append("pip install cachetools\n")
    s_lines.append("pip install paramiko\n")
    s_lines.append("pip install watchdog\n")
    s_lines.append("pip install unidecode\n")
    s_lines.append("pip install cups\n")
    s_lines.append("pip install asn1crypto\n")
    s_lines.append("pip install unicodecsv\n")
    s_lines.append("pip uninstall -y openupgradelib\n")
    s_lines.append("pip install git+https://github.com/OCA/openupgradelib.git\n")
    #
    # add odoo ocb path
    #
    if int(version) ==9:
        addons_path.append(os.path.join(to_dir, odoo_version, 'OCA/OpenUpgrade/addons'))
        addons_path.append(os.path.join(to_dir, odoo_version, 'OCA/OpenUpgrade/openerp/addons'))
    if int(version) >9:
        addons_path.append(os.path.join(to_dir, odoo_version, 'OCA/OpenUpgrade/addons'))
        addons_path.append(os.path.join(to_dir, odoo_version, 'OCA/OpenUpgrade/odoo/addons'))
    if int(version) >=14:
        addons_path.append(os.path.join(to_dir, odoo_version, 'OCA/OCB/addons'))
        addons_path.append(os.path.join(to_dir, odoo_version, 'OCA/OCB/odoo/addons'))    
    #
    # create odoo.conf
    #
    if os.path.exists("odoo.conf"):
        logger.warning("odoo.conf File for %s already present Unable to update" % odoo_version)
    else:
        with open("odoo.conf", "w") as odoo_conf:
            base_migration_path = os.path.join(os.path.dirname(os.path.dirname(to_dir)),'DataDir')
            try:
                os.makedirs(base_migration_path)
            except FileExistsError:
                pass
            odoo_conf.write(ODOO_CONF_TEMPLATE % (",\n\t".join(addons_path),
                                                  db_user,
                                                  base_migration_path))
    #
    # Create Migrate
    #
    _create_migration(odoo_version,
                      datadir,
                      from_db,
                      to_db,
                      version,
                      db_user)
    _create_runs(version,
                 to_db)
    return s_lines

def _create_runs(version,
                to_db):
    odoo_run = ODOO_RUN
    odoo_run_update=ODOO_RUN_UPDATE
    if int(version) ==9:
        odoo_run = ODOO_RUN_9
        odoo_run_update=ODOO_RUN_UPDATE_9
    #
    with open("run.sh", "w") as f:
        f.write(odoo_run.format(to_db=to_db))
    os.system("chmod +x run.sh")
    #      
    with open("run_update.sh", "w") as f:
        f.write(odoo_run_update.format(to_db=to_db))
    os.system("chmod +x run_update.sh") 
    
def _create_migration(odoo_version,
                      datadir,
                      from_db,
                      to_db,
                      version,
                      db_user):
    if os.path.exists("migrate.sh"):
        logger.warning("migrate.sh File for %s already present Unable to update" % odoo_version)
    else:
        with open("migrate.sh", "w") as odoo_conf:
            odoo_conf.write(INIT_SCRIPT_TEMPLATE)
            odoo_conf.write('echo"'+"*"*120)
            odoo_conf.write("\n")
            odoo_conf.write('echo "De comment the following line in order to syncronize the filestore folder\n"')
            odoo_conf.write("#rsync -avzh {from_datadir}filestore/{from_db} {from_datadir}filestore/{to_db}\n".format(from_datadir=datadir,
                                                                                                                  from_db=from_db,
                                                                                                                  to_db=to_db))
            odoo_conf.write('echo"'+"*"*120)
            odoo_conf.write("\n")
            #    
            if int(version)>=14:
                line = ODOO_MIGRATE_TEMPLATE_14.format(db_user=db_user,
                                                       from_db=from_db,
                                                       to_db=to_db,
                                                       from_datadir=datadir)
            else:
                line = ODOO_MIGRATE_TEMPLATE.format(db_user=db_user,
                                                    from_db=from_db,
                                                    to_db=to_db,
                                                    from_datadir=datadir)
            odoo_conf.write(line)
        #
        os.system("chmod +x migrate.sh") 

def _generateFile(from_db,
                  from_version,
                  to_version,
                  user,
                  data_dir,
                  to_dir,
                  gitHub,
                  extra_repo=[],
                  ):
    oca_template_repo = _getAllOCARepo(gitHub)
    orig_db = from_db
    bef_version = False
    for i in range(int(from_version),int(to_version)+1):
        odoo_version = "%s.0" % i
        logger.info("Create script for version %s" % odoo_version)
        to_db = orig_db + "_" + str(i)
        try:
            os.makedirs(odoo_version)
        except FileExistsError:
            pass
        os.chdir(odoo_version)
        s_lines = createDefaultTemplate(odoo_version,
                                        user,
                                        from_db,  
                                        to_db,
                                        version=i,
                                        datadir=data_dir,
                                        to_dir=to_dir,
                                        oca_template_repo=oca_template_repo,
                                        bef_version=bef_version,
                                        extra_repo=extra_repo)
        from_db = to_db
        if os.path.exists("download_requirements.sh"):
            logger.warning("download_requirements.sh File for %s already present Unable to update" % odoo_version)
        else:
            with open("download_requirements.sh", "w") as create_migration:
                for line in s_lines:
                    create_migration.write(line)
            os.system("chmod +x download_requirements.sh") 
        os.chdir('..')
        bef_version=odoo_version

def generateFile(git_hub_account,
                 from_db,
                 from_version,
                 to_version,
                 user,
                 data_dir,
                 to_dir,
                 extra_repo,
                 ):
    gitHub = Github(git_hub_account)
    migrationWare = 'OdooMigration'
    if not to_dir:
        to_dir = base_dir
    migrationWare = os.path.join(to_dir, migrationWare)
    try:
        os.makedirs(migrationWare)
    except FileExistsError:
        pass
    os.chdir(migrationWare)
    # with open("support.sql", 'w') as f:
    #     f.write(SQL_SUPPORT_FUNCTION)
    _generateFile(from_db=from_db,
                  from_version=from_version,
                  to_version=to_version,
                  user=user,
                  data_dir=data_dir ,
                  to_dir=migrationWare,
                  gitHub=gitHub,
                  extra_repo=extra_repo
                  )
    generate_migration_all(from_db=from_db,
                           user_db=user,
                           from_version=from_version,
                           to_version=to_version)
    
def generate_migration_all(from_db,
                           user_db,
                           from_version,
                           to_version):
    to_write=['#!/bin/bash\n']
    to_write.append("set -e\n")
    to_write.append("set -o pipefail\n")
    to_write_1 = []
    is_first=True
    for i in range(int(from_version),int(to_version)+1):
        odoo_version = "%s.0" % i
        active_db_name = "{db_name}_{odoo_version}".format(db_name=from_db,odoo_version=i)
        to_write.append("""sql -U {db_user} -d postgres -c "drop database {db_name}"\n""".format(db_user=user_db,
                                                                                                  db_name=active_db_name))
        to_write_1.append("cd {odoo_version}\n".format(odoo_version=odoo_version))
        to_write_1.append("./migrate.sh\n")
        if not is_first:
            pre_db_name = "{db_name}_{odoo_version}".format(db_name=from_db,odoo_version=i-1)
            to_write_1.append("""psql -U odoo -d postgres -c "drop database {db_name};"\n""".format(db_name=pre_db_name))
        else:
            is_first=False
        to_write_1.append("cd ..\n")
    to_write.extend(to_write_1)
    to_write.append('echo "' +"*"*120)
    to_write.append('"\n')
    to_write.append('echo "' +"*"*120)
    to_write.append('"\n')
    to_write.append('echo "Migration fineshed !!"\n')
    to_write.append('echo "' +"*"*120)
    to_write.append('"\n')
    with open("migrate_all.sh", 'w') as f:
        f.writelines(to_write)
