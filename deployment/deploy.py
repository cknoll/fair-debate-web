import time
import os
import sys
import os
from os.path import join as pjoin
from pathlib import Path

# these packages are not in requirements.txt but in deployment_requirements.txt
# noinspection PyUnresolvedReferences
from packaging import version

# noinspection PyUnresolvedReferences
from ipydex import IPS, activate_ips_on_exception

min_du_version = version.parse("0.9.0")
try:
    # this is not listed in the requirements because it is not needed on the deployment server
    # noinspection PyPackageRequirements,PyUnresolvedReferences
    import deploymentutils as du

    vsn = version.parse(du.__version__)
    if vsn < min_du_version:
        print(f"You need to install `deploymentutils` in version {min_du_version} or later. Quit.")
        exit()


except ImportError as err:
    print("You need to install the package `deploymentutils` to run this script.")


"""
This script serves to deploy and maintain the django app `fair_debate_web` on an uberspace account.
It is largely based on this tutorial: <https://lab.uberspace.de/guide_django.html> (but evolved away
from it over time)
"""

# call this before running the script:
# eval $(ssh-agent); ssh-add -t 10m


workdir = os.path.abspath(os.getcwd())
msg = (
    "This deployment script is expected to be run from the BASEDIR of the django project, i.e. "
    "from the same directory where manage.py is located. This seems not to be the case.\n"
    f"Your current workdir is {workdir}"
)

if not os.path.isfile(pjoin(workdir, "manage.py")):
    raise FileNotFoundError(msg)

# simplify debugging
activate_ips_on_exception()


# -------------------------- Essential Config section  ------------------------

config = du.get_nearest_config("config.toml")

remote = config("remote")
user = config("user")

# -------------------------- Begin Optional Config section -------------------------
# if you know what you are doing you can adapt these settings to your needs

# this is the root dir of the project (where setup.py lies)
# if you maintain more than one instance (and deploy.py lives outside the project dir, this has to change)
project_src_path = os.path.dirname(du.get_dir_of_this_file())
assert os.path.isfile(os.path.join(project_src_path, "manage.py"))

# directory for deployment files (e.g. database files)
app_name = config("app_name")
project_name = config("PROJECT_NAME")


# this is needed to distinguish different django instances on the same uberspace account
port = config("port")

django_base_domain = config("BASE_URL").strip("/")
django_url_prefix = config("django_url_prefix")
static_url_prefix = config("static_url_prefix")


asset_dir = pjoin(du.get_dir_of_this_file(), "files")  # contains the templates
temp_workdir = pjoin(du.get_dir_of_this_file(), "tmp_workdir")  # this will be deleted/overwritten

# -------------------------- End Config section -----------------------

# it should not be necessary to change the data below, but it might be interesting what happens.
# (After all, this code runs on your computer/server under your responsibility).


# name of the directory for the virtual environment:
venv = config("venv")
venv_path = f"/home/{user}/{venv}"

# because uberspace offers many python versions:
pipc = config("pip_command")
python_version = config("python_version")


du.argparser.add_argument(
    "-o", "--omit-tests", help="omit test execution (e.g. for dev branches)", action="store_true"
)
du.argparser.add_argument(
    "-d", "--omit-database", help="omit database-related-stuff (and requirements)", action="store_true"
)
du.argparser.add_argument("-s", "--omit-static", help="omit static file handling", action="store_true")
du.argparser.add_argument(
    "-x", "--omit-backup", help="omit db-backup (avoid problems with changed models)", action="store_true"
)
du.argparser.add_argument(
    "-q",
    "--omit-requirements",
    action="store_true",
    help="do not install requirements (allows to speed up deployment)",
)
du.argparser.add_argument(
    "-p", "--purge", help="purge target directory before deploying", action="store_true"
)
du.argparser.add_argument(
    "--debug", help="start debug interactive mode (IPS), then exit", action="store_true"
)
du.argparser.add_argument(
    "-be", "--backup-evaluation", help="download and evaluate backup files", action="store_true"
)

# always pass remote as argument (reason: legacy)

# assumes call starts with with `python deployment/deploy.py`
args = du.parse_args(sys.argv[1:] + ["remote"])


final_msg = f"Deployment script {du.bgreen('done')}."

if args.target == "remote":
    # this is where the code will live after deployment
    target_deployment_path = config("deployment_path")
    static_root_dir = f"{target_deployment_path}/collected_static"
    debug_mode = False

    # todo: read this from config
    allowed_hosts = [f"{user}.uber.space"]
else:
    raise NotImplementedError("local deployment is not supported by this script")


# TODO: review
init_fixture_path = os.path.join(target_deployment_path, "tests/testdata/fixtures01.json")


# print a warning for data destruction

print(du.bred("Currently no full backup will be done during deployment (not yet implemented)."))
time.sleep(1)
du.warn_user(
    app_name,
    args.target,
    args.unsafe,
    deployment_path=target_deployment_path,
    user=user,
    host=remote,
)


# ensure clean workdir
os.system(f"rm -rf {temp_workdir}")
os.makedirs(temp_workdir)

c = du.StateConnection(remote, user=user, target=args.target)
print("Connection established. Now adapting PATH ... ")
PATH_ENV = c.run("echo $PATH", hide=True).stdout
c.env_variables["PATH"] = f"/home/{user}/.local/bin:{PATH_ENV}"
assert c.last_result.return_code == 0
print(du.bgreen("OK."))


class MainManager:
    def __init__(self):
        self.c = c
        self.args = args
        self.target_deployment_path = target_deployment_path
        self.venv = venv
        self.venv_path = venv_path
        self.pipc = pipc
        self.python_version = python_version
        self.project_name = project_name
        self.app_name = app_name
        self.project_src_path = project_src_path
        self.asset_dir = asset_dir
        self.temp_workdir = temp_workdir
        self.django_base_domain = django_base_domain
        self.django_url_prefix = django_url_prefix
        self.static_url_prefix = static_url_prefix
        self.static_root_dir = static_root_dir
        self.init_fixture_path = init_fixture_path
        self.config = config


def create_and_setup_venv(self):
    c = self.c

    # TODO: check if venv exists

    c.run(f"{pipc} install --user virtualenv")

    print("create and activate a virtual environment inside $HOME")
    c.chdir("~")

    c.run(f"rm -rf {venv}")
    c.run(f"virtualenv -p {python_version} {venv}")

    c.run(f"pip install --upgrade pip")
    c.run(f"pip install --upgrade setuptools")

    print("\n", "install gunicorn", "\n")
    c.run(f"pip install gunicorn")

    # ensure that the same version of deploymentutils like on the controller-pc is also in the server
    c.deploy_this_package()


def render_and_upload_config_files(self):
    c = self.c
    c.activate_venv(f"~/{self.venv}/bin/activate")

    # generate the general service ini-file
    tmpl_dir = os.path.join("uberspace", "etc", "services.d")
    tmpl_name = "template_PROJECT_NAME_gunicorn.ini"
    target_name = "PROJECT_NAME_gunicorn.ini".replace("PROJECT_NAME", self.project_name)

    time_stamp = time.strftime(r"%Y-%m-%d %H-%M-%S")
    du.render_template(
        tmpl_path=pjoin(self.asset_dir, tmpl_dir, tmpl_name),
        target_path=pjoin(self.temp_workdir, tmpl_dir, target_name),
        context=dict(
            venv_abs_bin_path=f"{self.venv_path}/bin",
            project_name=self.project_name,
            port=config("port"),
            time_stamp=time_stamp,
        ),
    )

    #
    # ## upload config files to remote $HOME ##
    #
    srcpath1 = os.path.join(self.temp_workdir, "uberspace")
    filters = "--exclude='**/README.md' --exclude='**/template_*'"  # these files would be harmless but might be confusing
    c.rsync_upload(srcpath1 + "/", "~", filters=filters, target_spec="remote")


def update_supervisorctl(self):
    c = self.c
    c.activate_venv(f"~/{self.venv}/bin/activate")

    c.run("supervisorctl reread", target_spec="remote")
    c.run("supervisorctl update", target_spec="remote")
    print("waiting 16s for service to start")
    time.sleep(16)

    res1 = c.run(f"supervisorctl status gunicorn-{self.project_name}", target_spec="remote")
    assert "RUNNING" in res1.stdout


def set_web_backend(self):
    c = self.c
    c.activate_venv(f"~/{self.venv}/bin/activate")

    c.run(
        f"uberspace web backend set {self.django_base_domain}{self.django_url_prefix} --http --port {config('port')}",
        target_spec="remote",
    )

    # note 1: the static files which are used by django are served under '{static_url_prefix}'/
    # (not {django_url_prefix}}{static_url_prefix})
    # they are served by apache from ~/html{static_url_prefix}, e.g. ~/html/markpad1-static

    c.run(
        f"uberspace web backend set {self.django_base_domain}{self.static_url_prefix} --apache",
        target_spec="remote",
    )

    # this is usefull for making the service accessible from other domains:
    if 0:
        url2 = "fair-debate.kddk.eu"
        cmd1 = f"uberspace web backend set {url2} --http --port {config('port')}"
        cmd2 = f"uberspace web backend set {url2}{self.static_url_prefix} --apache"
        # c.run(cmd1)
        # c.run(cmd2)


def upload_files(self):
    c = self.c
    print("\n", "ensure that deployment path exists", "\n")
    c.run(f"mkdir -p {self.target_deployment_path}", target_spec="both")

    c.activate_venv(f"~/{self.venv}/bin/activate")

    print("\n", "upload config file", "\n")
    c.rsync_upload(config.path, self.target_deployment_path, target_spec="remote")

    c.chdir(self.target_deployment_path)

    print("\n", "upload current application files for deployment", "\n")
    # omit irrelevant files (like .git)
    # TODO: this should be done more elegantly

    db_file_name = config("DB_FILE_NAME")
    filters = f"--exclude='.git/' --exclude='.idea/' --exclude='{db_file_name}' "

    c.rsync_upload(
        self.project_src_path + "/", self.target_deployment_path, filters=filters, target_spec="both"
    )

    c.run(f"touch requirements.txt", target_spec="remote")


def purge_deployment_dir(self):
    c = self.c
    if not self.args.omit_backup:
        print(
            "\n",
            du.bred("  The `--purge` option explicitly requires the `--omit-backup` option. Quit."),
            "\n",
        )
        exit()
    else:
        answer = input(f" -> {du.yellow('purging')} <{self.args.target}>/{self.target_deployment_path} (y/N)")
        if answer != "y":
            print(du.bred("Aborted."))
            exit()
        c.run(f"rm -r {self.target_deployment_path}", target_spec="both")


def install_app(self):
    c = self.c
    c.activate_venv(f"~/{self.venv}/bin/activate")

    c.chdir(self.target_deployment_path)
    c.run(f"pip install -r requirements.txt", target_spec="both")


def perform_backup_if_not_omitted(self):
    c = self.c
    if self.args.omit_backup:
        print("\n", du.yellow("backup omitted"), "\n")
        return

    c.chdir(self.target_deployment_path)
    print("\n", "backup content repos", "\n")

    time_stamp_str = time.strftime("%Y-%m-%d__%H-%M-%S")
    repo_backup_path = f"../fair_debate_repo_backups/{time_stamp_str}"
    c.run(f"mkdir -p {repo_backup_path}")
    res_repos = c.run(f"cp -r ./content_repos {repo_backup_path}", warn="smart")
    assert res_repos.exited == 0, "Could not backup content repos"

    print("\n", "backup database to json", "\n")

    # this uses settings.BACKUP_PATH which is defined in config.toml
    res_db = c.run("python manage.py savefixtures --backup", warn=True)
    assert res_db.exited == 0, "Could not backup database to json"


def initialize_db(self):
    c = self.c
    c.chdir(self.target_deployment_path)

    self.perform_backup_if_not_omitted(c)
    c.run("python manage.py makemigrations", target_spec="both")

    # delete old db
    c.run("rm -f db.sqlite3", target_spec="both")

    # this creates the new database
    c.run("python manage.py migrate --run-syncdb", target_spec="both")

    # create superuser with password from config
    c.chdir(self.target_deployment_path)
    cmd = f'export DJANGO_SUPERUSER_PASSWORD="{config("ADMIN_PASS")}"; '
    cmd += 'python manage.py createsuperuser --noinput --username admin --email "a@b.org"'
    c.run(cmd)

    # print("\n", "install initial data", "\n")

    # TODO: implement option to load latest backup
    c.run(f"python manage.py loaddata {self.init_fixture_path}", target_spec="both")
    # note: there is also the `fdmd unpack-repos ./content_repos` command below


# TODO: this has to change for production phase (or even for beta-testing)
def initialize_test_repos(self):
    c = self.c
    c.activate_venv(f"~/{self.venv}/bin/activate")
    c.chdir(self.target_deployment_path)

    c.run('git config --global user.email "system@fair-debate.org"')
    c.run('git config --global user.name "fair-debate-system"')

    # this will unpack the .patch files in the respective directory
    c.run("fdmd unpack-repos ./content_repos")

    # handle example debate:
    c.chdir(f"{self.target_deployment_path}/content_repos")
    c.run("rm -rf d00-explanatory-example-debate")
    cmd = (
        "fdmd process-content-dir __FIXTURES_RP__/d00-explanatory-example-debate__plain "
        "./d00-explanatory-example-debate --patches"
    )
    c.run(cmd)


def generate_static_files(self):
    c = self.c

    c.chdir(self.target_deployment_path)

    # TODO: this does not yet work (and must be run and copied manually)

    c.run("python manage.py collectstatic --no-input", target_spec="remote")

    print("\n", "copy static files to the right place", "\n")
    targetdir = f"/var/www/virtual/{config('user')}/{self.django_base_domain}"
    c.run(f"mkdir -p {targetdir}")
    c.chdir(targetdir)
    c.run(f"rm -rf ./{self.static_url_prefix}")
    c.run(f"cp -r {self.static_root_dir} ./{self.static_url_prefix}")

    # static files for second domain etc.
    for further_domain in config("ALLOWED_HOSTS")[1:]:
        targetdir = f"/var/www/virtual/{config('user')}/{further_domain}"
        c.run(f"mkdir -p {targetdir}")
        c.chdir(targetdir)
        c.run(f"rm -rf ./{self.static_url_prefix}")
        c.run(f"cp -r {self.static_root_dir} ./{self.static_url_prefix}")

    c.chdir(self.target_deployment_path)


# TODO: make more generic and move this into deployment utils
def deploy_local_dependency(self):
    c = self.c
    import inspect
    import fair_debate_md
    from pathlib import Path

    module_path = inspect.getfile(fair_debate_md)
    assert module_path.endswith("fair-debate-md/src/fair_debate_md/__init__.py")

    # path of dir which contains pyproject.toml as direct child
    project_path = Path(module_path).parents[2].as_posix()
    c.deploy_local_package(local_path=project_path, package_name="fair_debate_md")


def finalize(self):
    c = self.c
    c.run(f"touch ~/_this_is_uberspace.txt", target_spec="remote")
    py_cmd = "import time; print(time.strftime(r'%Y-%m-%d %H:%M:%S'))"
    c.run(f"""python3 -c "{py_cmd}" > deployment_date.txt""", target_spec="remote")
    print("\n", "restart webservice", "\n")
    c.run(f"supervisorctl restart gunicorn-{self.project_name}", target_spec="remote")

    print(final_msg)


def debug(self):
    c = self.c
    c.activate_venv(f"~/{self.venv}/bin/activate")
    # c.deploy_this_package()
    # render_and_upload_config_files(c)
    # deploy_local_dependency(c)
    # upload_files(c)
    # update_supervisorctl(c)

    # set_web_backend(c)
    # initialize_db(c)

    self.upload_files()
    self.perform_backup_if_not_omitted(c)
    # generate_static_files(c)
    # deploy_local_dependency(c)
    # initialize_test_repos(c)
    # finalize(c)

    exit()

    # create_and_setup_venv(c)
    c.activate_venv(f"{self.venv_path}/bin/activate")

    c.deploy_this_package()

    # set_web_backend(c)

    IPS()
    exit()


def backup_evaluation(self):
    c = self.c
    self._download_latest_backup_files()
    self._compare_backups()
    IPS(-1)
    exit()


def _compare_backups(self):
    c = self.c
    pass


def _download_latest_backup_files(self):
    c = self.c
    print("backup-evaluation")

    LOCAL_BACKUP_PATH = f"{os.getcwd()}/_gitignore-backup-evaluation"
    # BASE_DIR = Path(__file__).resolve().parent.parent.as_posix()
    REMOTE_DB_BACKUP_PATH = os.path.abspath(
        self.config("BACKUP_PATH").replace("__BASEDIR__", f"{self.target_deployment_path}")
    )
    REMOTE_REPO_BACKUP_PATH = REMOTE_DB_BACKUP_PATH.replace("db_backups", "repo_backups")

    # download DATABASE backup

    c.chdir(REMOTE_DB_BACKUP_PATH)
    # file_names = c.run("ls -1 *.json | sort")
    # use find instead of ls to apply wildcard matching reliably
    file_names = c.run("find . -maxdepth 1 -type f -name '*.json' -printf '%f\n' | sort")
    file_name_list = file_names.stdout.strip().split("\n")
    assert file_name_list[-1].startswith("20")

    c.rsync_download(
        f"{REMOTE_DB_BACKUP_PATH}/{file_name_list[-1]}",
        f"{LOCAL_BACKUP_PATH}/{file_name_list[-1]}",
    )

    # download REPO backup

    c.chdir(REMOTE_REPO_BACKUP_PATH)
    # use find instead of ls to apply wildcard matching appropriately
    dir_names = c.run("find . -maxdepth 1 -type d -name '*__*' -printf '%f\n' | sort")
    dir_name_list = dir_names.stdout.strip().split("\n")
    assert dir_name_list[-1].startswith("20")

    c.rsync_download(
        f"{REMOTE_REPO_BACKUP_PATH}/{dir_name_list[-1]}/",
        f"{LOCAL_BACKUP_PATH}/{dir_name_list[-1]}/",
    )


if __name__ == "__main__":
    # Create an instance of MainManager
    mm = MainManager()

    if args.debug:
        mm.debug()

    elif args.backup_evaluation:
        mm.backup_evaluation()

    if args.initial:

        # this shall prevent unexpected domain errors
        print(
            "\n",
            du.yellow(
                f"Make sure that the domain {django_base_domain} is set up correctly on your uberspace."
            ),
            "\n",
        )
        res = input("Continue (N/y)? ")
        if res.lower() != "y":
            print(du.bred("Aborted."))
            exit()

        mm.create_and_setup_venv()
        mm.render_and_upload_config_files()
        mm.update_supervisorctl()
        mm.set_web_backend()

    if args.purge:
        mm.purge_deployment_dir()

    mm.upload_files()

    if not args.omit_requirements:
        mm.deploy_local_dependency()
        mm.install_app()

    if not args.omit_database:
        mm.initialize_db()
        mm.initialize_test_repos()

    if not args.omit_static:
        mm.generate_static_files()

    mm.finalize()
