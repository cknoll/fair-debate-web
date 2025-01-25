import time
import os
import sys
import os
from os.path import join as pjoin

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



du.argparser.add_argument("-o", "--omit-tests", help="omit test execution (e.g. for dev branches)", action="store_true")
du.argparser.add_argument("-d", "--omit-database",
                          help="omit database-related-stuff (and requirements)", action="store_true")
du.argparser.add_argument("-s", "--omit-static", help="omit static file handling", action="store_true")
du.argparser.add_argument("-x", "--omit-backup",
                          help="omit db-backup (avoid problems with changed models)", action="store_true")
du.argparser.add_argument(
    "-q",
    "--omit-requirements",
    action="store_true",
    help="do not install requirements (allows to speed up deployment)",
)
du.argparser.add_argument("-p", "--purge", help="purge target directory before deploying", action="store_true")
du.argparser.add_argument("--debug", help="start debug interactive mode (IPS), then exit", action="store_true")

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

print(du.bred("Currently no backup will be done during deployment (not yet implemented)."))
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
PATH_ENV = c.run("echo $PATH").stdout
c.env_variables["PATH"] = f"/home/{user}/.local/bin:{PATH_ENV}"


def create_and_setup_venv(c: du.StateConnection):


    # TODO: check if venv exists

    c.run(f"{pipc} install --user virtualenv")

    print("create and activate a virtual environment inside $HOME")
    c.chdir("~")

    c.run(f"rm -rf {venv}")
    c.run(f"virtualenv -p {python_version} {venv}")

    c.activate_venv(f"~/{venv}/bin/activate")

    c.run(f"pip install --upgrade pip")
    c.run(f"pip install --upgrade setuptools")

    print("\n", "install gunicorn", "\n")
    c.run(f"pip install gunicorn")

    # ensure that the same version of deploymentutils like on the controller-pc is also in the server
    c.deploy_this_package()


def render_and_upload_config_files(c):
    """
    Use some variables from project config file (toml), put them in the template,
    create service specific config files (ini) and upload them.

    Currently only one config file is created.
    """

    c.activate_venv(f"~/{venv}/bin/activate")

    # generate the general service ini-file
    tmpl_dir = os.path.join("uberspace", "etc", "services.d")
    tmpl_name = "template_PROJECT_NAME_gunicorn.ini"
    target_name = "PROJECT_NAME_gunicorn.ini".replace("PROJECT_NAME", project_name)

    time_stamp = time.strftime(r"%Y-%m-%d %H-%M-%S")
    du.render_template(
        tmpl_path=pjoin(asset_dir, tmpl_dir, tmpl_name),
        target_path=pjoin(temp_workdir, tmpl_dir, target_name),
        context=dict(
            venv_abs_bin_path=f"{venv_path}/bin", project_name=project_name, port=port, time_stamp=time_stamp
        ),
    )

    #
    # ## upload config files to remote $HOME ##
    #
    srcpath1 = os.path.join(temp_workdir, "uberspace")
    filters = "--exclude='**/README.md' --exclude='**/template_*'"  # these files would be harmless but might be confusing
    c.rsync_upload(srcpath1 + "/", "~", filters=filters, target_spec="remote")


def update_supervisorctl(c):

    c.activate_venv(f"~/{venv}/bin/activate")

    c.run("supervisorctl reread", target_spec="remote")
    c.run("supervisorctl update", target_spec="remote")
    print("waiting 16s for service to start")
    time.sleep(16)

    res1 = c.run(f"supervisorctl status gunicorn-{project_name}", target_spec="remote")
    assert "RUNNING" in res1.stdout


def set_web_backend(c):
    c.activate_venv(f"~/{venv}/bin/activate")

    c.run(
        f"uberspace web backend set {django_base_domain}{django_url_prefix} --http --port {port}", target_spec="remote"
    )

    # note 1: the static files which are used by django are served under '{static_url_prefix}'/
    # (not {django_url_prefix}}{static_url_prefix})
    # they are served by apache from ~/html{static_url_prefix}, e.g. ~/html/markpad1-static

    c.run(f"uberspace web backend set {django_base_domain}{static_url_prefix} --apache", target_spec="remote")

    # this is usefull for making the service accessible from other domains:
    if 0:
        url2 = "fair-debate.kddk.eu"
        cmd1 = f"uberspace web backend set {url2} --http --port {port}"
        cmd2 = f"uberspace web backend set {url2}{static_url_prefix} --apache"
        # c.run(cmd1)
        # c.run(cmd2)




def upload_files(c):
    print("\n", "ensure that deployment path exists", "\n")
    c.run(f"mkdir -p {target_deployment_path}", target_spec="both")

    c.activate_venv(f"~/{venv}/bin/activate")

    print("\n", "upload config file", "\n")
    c.rsync_upload(config.path, target_deployment_path, target_spec="remote")

    c.chdir(target_deployment_path)

    print("\n", "upload current application files for deployment", "\n")
    # omit irrelevant files (like .git)
    # TODO: this should be done more elegantly

    db_file_name = config("DB_FILE_NAME")
    filters = f"--exclude='.git/' --exclude='.idea/' --exclude='{db_file_name}' "

    c.rsync_upload(
        project_src_path + "/", target_deployment_path, filters=filters, target_spec="both"
    )

    c.run(f"touch requirements.txt", target_spec="remote")


def purge_deployment_dir(c):
    if not args.omit_backup:
        print(
            "\n",
            du.bred("  The `--purge` option explicitly requires the `--omit-backup` option. Quit."),
            "\n",
        )
        exit()
    else:
        answer = input(f" -> {du.yellow('purging')} <{args.target}>/{target_deployment_path} (y/N)")
        if answer != "y":
            print(du.bred("Aborted."))
            exit()
        c.run(f"rm -r {target_deployment_path}", target_spec="both")


def install_app(c):
    c.activate_venv(f"~/{venv}/bin/activate")

    c.chdir(target_deployment_path)
    c.run(f"pip install -r requirements.txt", target_spec="both")


def initialize_db(c):

    c.chdir(target_deployment_path)

    # try to backup db before (re-)initialization and changing database layout
    # print("\n", "backup old database", "\n")
    _ = c.run("python manage.py savefixtures --backup", warn=False)


    c.run("python manage.py makemigrations", target_spec="both")

    # delete old db
    c.run("rm -f db.sqlite3", target_spec="both")

    # this creates the new database
    c.run("python manage.py migrate --run-syncdb", target_spec="both")

    # create superuser with password from config
    c.chdir(target_deployment_path)
    cmd = f'export DJANGO_SUPERUSER_PASSWORD="{config("ADMIN_PASS")}"; '
    cmd += 'python manage.py createsuperuser --noinput --username admin --email "a@b.org"'
    c.run(cmd)

    # print("\n", "install initial data", "\n")

    # TODO: implement option to load latest backup
    c.run(f"python manage.py loaddata {init_fixture_path}", target_spec="both")

# TODO: this has to change for production phase (or even for beta-testing)
def initialize_test_repos(c):
    c.activate_venv(f"~/{venv}/bin/activate")
    c.chdir(target_deployment_path)

    c.run('git config --global user.email "system@fair-debate.org"')
    c.run('git config --global user.name "fair-debate-system"')
    c.run("fdmd unpack-repos ./content_repos")


def generate_static_files(c):

    c.chdir(target_deployment_path)

    # TODO: this does not yet work (and must be run and copied manually)

    c.run("python manage.py collectstatic --no-input", target_spec="remote")

    print("\n", "copy static files to the right place", "\n")
    targetdir = f"/var/www/virtual/{user}/{django_base_domain}"
    c.run(f"mkdir -p {targetdir}")
    c.chdir(targetdir)
    c.run(f"rm -rf ./{static_url_prefix}")
    c.run(f"cp -r {static_root_dir} ./{static_url_prefix}")

    # static files for second domain etc.
    for further_domain in config("ALLOWED_HOSTS")[1:]:
        targetdir = f"/var/www/virtual/{user}/{further_domain}"
        c.run(f"mkdir -p {targetdir}")
        c.chdir(targetdir)
        c.run(f"rm -rf ./{static_url_prefix}")
        c.run(f"cp -r {static_root_dir} ./{static_url_prefix}")

    c.chdir(target_deployment_path)


# TODO: make more generic and move this into deployment utils
def deploy_local_dependency(c: du.StateConnection):
    import inspect
    import fair_debate_md
    from pathlib import Path
    module_path = inspect.getfile(fair_debate_md)
    assert module_path.endswith("fair-debate-md/src/fair_debate_md/__init__.py")

    # path of dir which contains pyproject.toml as direct child
    project_path = Path(module_path).parents[2].as_posix()
    c.deploy_local_package(local_path=project_path, package_name="fair_debate_md")


def finalize(c):
    c.run(f"touch ~/_this_is_uberspace.txt", target_spec="remote")
    py_cmd = "import time; print(time.strftime(r'%Y-%m-%d %H:%M:%S'))"
    c.run(f"""python3 -c "{py_cmd}" > deployment_date.txt""", target_spec="remote")
    print("\n", "restart webservice", "\n")
    c.run(f"supervisorctl restart gunicorn-{project_name}", target_spec="remote")

    print(final_msg)


def debug():

    c.activate_venv(f"~/{venv}/bin/activate")
    # c.deploy_this_package()
    # render_and_upload_config_files(c)
    # deploy_local_dependency(c)
    # upload_files(c)
    # update_supervisorctl(c)

    # set_web_backend(c)
    # initialize_db(c)

    upload_files(c)
    generate_static_files(c)
    # deploy_local_dependency(c)
    # initialize_test_repos(c)
    finalize(c)

    exit()

    # create_and_setup_venv(c)
    c.activate_venv(f"{venv_path}/bin/activate")

    c.deploy_this_package()

    # set_web_backend(c)

    IPS()
    exit()

if args.debug:
    debug()

if args.initial:

    # this shall prevent unexpected domain errors
    print(
        "\n",
        du.yellow(f"Make sure that the domain {django_base_domain} is set up correctly on your uberspace."),
        "\n",
    )
    res = input("Continue (N/y)? ")
    if res.lower() != "y":
        print(du.bred("Aborted."))
        exit()

    create_and_setup_venv(c)
    render_and_upload_config_files(c)
    update_supervisorctl(c)
    set_web_backend(c)

if args.purge:
    purge_deployment_dir(c)

upload_files(c)

if not args.omit_requirements:
    deploy_local_dependency(c)
    install_app(c)

if not args.omit_database:
    initialize_db(c)
    initialize_test_repos(c)

if not args.omit_static:
    generate_static_files(c)


finalize(c)
