#!/usr/bin/env python3

"""Git-get.

Package manager for git repositories.

Usage:
    git-get check
    git-get edit (packages|config)
    git-get install <package_location> --local
    git-get list
    git-get move <package_name> <end_location>
    git-get remove <package_name> --soft
    git-get setup
    git-get upgrade

Options:
    --debug  Increases verbosity of output

"""


import argparse  # Parses command line arguments
import logging  # Allows unified logging
import os  # Allows os-interface
import subprocess  # Calls and handles subprocesses
import yaml  # Parses and writes yaml file

from termcolor import colored  # Allows unified color parsing
from sys import argv  # Command line arguments


def set_logger(debug_level="info", detail_level=2):
    """Initialises the logger.

    Args:
        Debug_level (str): Minimum logger level to display.
            - debug
            - info
        Detail level (int): Level of detail for the formatter.
            - 0: Only messages
            - 1: Messages and time
            - 2 (default): Messages, time and debug level

    Returns:
        None: Creates a global variable ``logger``

    """
    global logger
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    logger.addHandler(handler)
    # set logger format
    if detail_level == 0:
        formatter = logging.Formatter("%(message)s")
    elif detail_level == 1:
        formatter = logging.Formatter("%(asctime)s %(message)s", "%H:%M:%S")
    elif detail_level == 2:
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)-8s %(message)s" "%H:%M:%S"
        )
    handler.setFormatter(formatter)
    # set logger verboisty
    if debug_level == "info":
        logger.setLevel(logging.INFO)
    elif debug_level == "debug":
        logger.setLevel(logging.DEBUG)
    else:
        logger.error("Logger level " + debug_level + " not a valid option")


def get_yaml(name, filename):
    """Loads and handles content from yaml files.

    Args:
        Name (str): Name of the file being opened, to be used in the logger.
        Filename (str): Location of file being opened.

    Returns:
        Dictionary: Contains the information from the YAML file.

    """
    try:
        with open(os.path.expanduser(filename)) as file:
            config = yaml.safe_load(file)
            logger.debug("Loaded " + name)
    except FileNotFoundError:
        lost_filename = name[0].upper() + name[1:]
        logger.error(lost_filename + " not found, try running `git-get setup`")
        exit(1)
    return config


def get_config():
    """Loads configuration file.

    Returns:
        Dictionary: Contains the configuration options.
    """
    return get_yaml("config file", "~/.git-get/config.yml")


def get_package_list():
    """Loads package list from file.

    Returns:
        Dictionary: Contains the package list. The key to each package is the
            name, formatted either ``username/package`` or ``local_package``.
            This item contains the key ``location``, describing where the
            package is stored locally.

    """
    package_list = get_yaml("package list", "~/.git-get/packages.yml")
    if package_list is None:
        package_list = {}
    return package_list


def write_package_list(package_list):
    """Writes the package list to file.

    Args:
        Package_list (list): Contains the package list (see get_package_list()
            for more information).

    """
    with open(os.path.expanduser("~/.git-get/packages.yml"), "w") as file:
        file.write(yaml.dump(package_list, default_flow_style=False))


def run_command(command, die_on_err=True, verbosity=0):
    """Runs and handlles commands.

    Args:
        Command (str): Command to run.
        Die_on_err (bool) (optional): If True, the program exits when it
            encounters an error, otherwise the error is logged and execution
            continues.
        Verbosity (int) (optional): Describes level of logging.
        -   0 - logs all commands and errors
        -   1 - logs only errors
        -   2 - logs nothing

    Returns:
        Str: Output; The output of the command run.
        Integer: Exit_code; Exit code from the command run.

    """
    if verbosity < 1:
        logger.debug("Running: " + command)
    # run command and store output
    proc = subprocess.Popen(
        command.split(" "), stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    output = proc.communicate()[0].decode("utf-8")[:-1]
    exit_code = proc.returncode
    # die if required
    if die_on_err and exit_code != 0:
        logger.critical("Process died")
        logger.debug("Process exited with " + str(exit_code))
        exit(1)
    return output, exit_code


def check(*args):
    """Verifies integrity of files and packages.

    First, the core files are checked for. Both the configuration and the
    package list are looked for. If both are found the packages list is parsed
    and the location of every package is verified.

    """
    package_list = get_package_list()
    # check core files
    config_file = os.path.join("~", ".git-get", "config.yml")
    if os.path.exists(os.path.expanduser(config_file)):
        logger.info(colored("Config file exists", "green"))
    else:
        logger.error(colored("Config file not found", "red"))
        exit(1)
    packages_file = os.path.join("~", ".git-get", "packages.yml")
    if os.path.exists(os.path.expanduser(packages_file)):
        logger.info(colored("Packages list exists", "green"))
    else:
        logger.error(colored("Packages list not found", "red"))
        exit(1)
    # check packages
    all_found = True
    for package_name in package_list:
        if os.path.isdir(package_list[package_name]["location"]):
            logger.debug(colored("Pakage " + package_name + " found", "green"))
        else:
            logger.error(colored("Package " + package_name + " not found", "red"))
            all_found = False
    # messages
    if all_found:
        logger.info(colored("All packages found", "green"))
    else:
        logger.error(colored("Some packages are missing", "red"))
    logger.info("All checks complete")


def open_file_caller(args):
    """Calls open_file() function (required for argparse).

    Args:
        Args (namespace):
            Args.filename (str): Name of the file to open. Either "packages"
                for the packages list, or "config" for the configuratioon file.

    """
    open_file(args.filename)


def open_file(filename):
    """Opens file in default editor.

    Args:
        filename (str): Name of the file to open. Either "packages" for the
            packages list, or "config" for the configuratioon file.

    """
    filename = os.path.expanduser("~/.git-get/" + filename + ".yml")
    editor = os.getenv("EDITOR")
    if editor:
        # does not use `run_command` as output needs to be shown
        logger.debug("Running: " + editor + " " + filename)
        try:
            subprocess.call([editor, filename])
        except Exception as e:
            logger.critical("Could not open editor")
            logger.debug("Error message: " + str(e))
            exit(1)
        logger.info("File edited.")
        exit(0)
    else:
        logger.error("Editor not set, exiting")
        exit(1)


def install_caller(args):
    """Calls the appropriate installer (required for argpass).

    Args:
        Args (namespace):
            Args.Local (bool): True if package to install is local.
            Args.Package (list): Location of the package to install.

    """
    package = "".join(args.package_name)
    if args.local:
        install_local(package)
    else:
        install(package)


def install(remote_package):
    """Installs remote packages.

    Args:
        remote_package (str): Location of the package to install. Can be:
            - url to a git reposiotry, in which case the url is presumed to
              describe the username and repository at the end, seperate by
              slashes, eg ``website.com/username/repo``
            - username-repo combination for a github-hosted repository, e.g.
              ``abactel/git-get``.

    """
    # initialize
    package_list = get_package_list()
    # parse if package refers to direct URL
    if remote_package.startswith("http") or remote_package.startswith("git"):
        package_name = "/".join(remote_package.split("/")[-2:])
        if package_name.endswith(".git"):
            package_name = package_name[:-4]
    else:
        package_name = remote_package
        remote_package = "https://github.com/" + remote_package
    # install package or inform user already installed
    if package_name not in package_list:
        run_command("git clone " + remote_package)
        # add to packages list
        package_location = os.path.join(os.getcwd(), remote_package.split("/")[-1])
        package_list[str(package_name)] = {"location": package_location}
        write_package_list(package_list)
        logger.info("Successfully installed package.")
        exit(0)
    else:
        logger.error("Package already installed")
        exit(1)


def install_local(location):
    """Installs local packages.

    Args:
        Location (str): Location of the folder that should be installed.

    """
    package_list = get_package_list()
    # expand location
    location = os.path.expanduser(location)
    if not os.path.isdir(location):
        logger.error("Not a path: " + location)
        exit(1)
    package = "local_" + str(location.split("/")[-1])
    # modify package name
    if package in package_list:
        package = package + "_1"
    package_count = 0
    while package in package_list:
        package_count += 1
        package = package[:-1] + str(package_count)
    # install package
    package_location = os.path.join(os.getcwd(), location)
    package_list[package] = {"location": package_location}
    write_package_list(package_list)
    logger.info("Successfully installed package " + package + ".")
    exit(0)


def list_packages_caller(args):
    """Calls list_packages() function (required for argparse).

    Args:
        Args (namespace):
            List_filter (str) (optional): Describes filter for output.
                - Local: Displays only local repos.
                - Remote: Displays only remote repos.

    """
    if args.local and args.remote:
        logger.error("Only one filter option can be selecteds")
        exit(1)
    if args.local:
        list_filter = "local"
    elif args.remote:
        list_filter = "remote"
    else:
        list_filter = ""
    list_packages(list_filter=list_filter)


def list_packages(list_filter=" "):
    """List all packages and install locations.

    Args:
        List_filter (str) (optional): Describes filter for output.
            - Local: Displays only local repos.
            - Remote: Displays only remote repos.

    """
    package_list = get_package_list()
    justify = len(max(package_list, key=len)) + 2
    #  fix formatting
    if list_filter != " ":
        list_filter += " "
    # print information
    print((list_filter[0].upper() + list_filter[1:] + "packages:"))
    for package_name in package_list:
        # filters
        a = list_filter == "local" and not package_name.startswith("local_")
        b = list_filter == "remote" and package_name.startswith("local_")
        if a or b:
            break
        # location
        package_location = package_list[package_name]["location"]
        print("  " + (package_name).ljust(justify) + package_location)
    logger.info("Successfully Listed packages.")
    exit(0)


def move_package_caller(args):
    """Call move_package() (required for argparse).

    Args:
        Args (namespace):
            Args.package_name (str): Name of package to move.
            Args.location (str): Location to move package to.

    """
    move_package("".join(args.package_name), "".join(args.location))


def move_package(package_name, location):
    """Move a package.

    Args:
        Package_name (str): Name of package to move.
        Location (str): Location to move package to.

    """
    package_list = get_package_list()
    # check if package is installed
    if package_name not in package_list:
        logger.error("Package not found in package list")
        exit(1)
    # run command
    package_location = package_list[package_name]["location"]
    end_location = os.path.abspath(end_location)
    run_command("mv " + package_location + " " + end_location)
    # update packages list
    package_list[package_name]["location"] = end_location
    write_package_list(package_list)
    exit(0)


def remove_caller(args):
    """Calls remove() function (required for argpass).

    Args:
        Args (namespace):
            Args.package (str): Name of package to remove.
            Args.soft (bool): If True local folder is not deleted.

    """
    remove("".join(args.package_name), args.soft)


def remove(package, soft=False):
    """Removes packages.

    Args:
        package (str): Name of package to remove.
        soft (bool): If True local folder is not deleted.

    """
    package_list = get_package_list()
    # remove package or inform user not installed
    if package in package_list:
        if input("Remove " + package + "? (y/N)") == "y":
            if not soft:
                run_command("rm " + package_list[package]["location"] + " -rf")
            # write new package list
            del package_list[package]
            write_package_list(package_list)
            logger.info("Successfully removed package.")
            exit(0)
        else:
            logger.info("Quitting")
            exit(0)
    else:
        logger.error("Package not installed")
        exit(1)


def setup_files(*args):
    """Creates core configuration files.

    Files created:
        - config.yml
        - packages.yml

    """
    # check if folder already exist
    path = os.path.expanduser("~/.git-get")
    if os.path.isdir(path):
        logger.info("Folder `~/.git-get` exists")
    else:
        if os.path.exists(path):
            logger.error("File `~/.git-get` should be a folder")
        else:
            logger.info("Creating folder `~/.git-get`")
            os.makedirs(path)
    # check for package list
    path = os.path.expanduser("~/.git-get/packages.yml")
    if os.path.isfile(path):
        logger.info("Package list exists")
    else:
        if os.path.exists(path):
            logger.error("Folder `~/.git-get/packages.yml` should be a file")
        else:
            logger.info("Creating package list")
            with open(path, "w") as file:
                file.write("")
    # check for configuration file
    path = os.path.expanduser("~/.git-get/config.yml")
    if os.path.isfile(path):
        logger.info("Configuration file exists")
    else:
        if os.path.exists(path):
            logger.error("Folder `~/.git-get/config.yml` should be a file")
        else:
            logger.info("Creating configuration file")
            with open(path, "w") as file:
                file.write("")
    logger.info("Created required files")


def upgrade(*args):
    """Upgrades all possible packages.

    Packages are upgraded by running ``git pull -C [directory]``.
    """
    package_list = get_package_list()
    num_packages = str(len(package_list))
    for package_num, package_name in enumerate(package_list):
        # basic variable initiation
        package_location = package_list[package_name]["location"]
        base_command = "git -C " + package_location + " "
        # check for remotes
        output, tmp = run_command(base_command + "remote -v", die_on_err=False)
        # Create progress bar
        progress = "(" + str(package_num + 1) + "/" + str(num_packages) + ")"
        # Pull, figure out correct message and display
        if len(output) != 0:
            command = base_command + "pull"
            output, return_value = run_command(command, die_on_err=False)
            if output == "Already up-to-date." and return_value == 0:
                msg = (
                    "Package "
                    + package_name
                    + " already up to date. "
                    + colored(progress, "yellow")
                )
            elif return_value == 0:
                msg = (
                    "Package "
                    + package_name
                    + " successfully upgraded. "
                    + colored(progress, "green")
                )
            else:
                msg = (
                    "Package "
                    + package_name
                    + " could not be upgraded. "
                    + colored(progress, "red")
                )
        else:
            msg = (
                "Package "
                + package_name
                + " cannot be upgraded. "
                + colored(progress, "red")
            )
        logger.info(msg)
    logger.info("Upgraded all possible packages.")
    exit(0)


def main():
    """Main"""

    def get_help(function):
        """Generate help string from a function's docstring

        Returns:
            string - First line of the docstring of a function. The first
                letter is in lowercase and the the final fullstop is removed.
        """
        line = function.__doc__.split("\n")[0][:-1]
        return line[0].lower() + line[1:]

    # initialize parser
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title="subcommands")

    # debug flag
    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="increases verbosity of output",
    )

    # check
    check_parser = subparsers.add_parser("check", help=get_help(check))
    check_parser.set_defaults(function=check)

    # edit
    open_parser = subparsers.add_parser("edit", help=get_help(open_file))
    open_parser.add_argument(
        "filename", choices=["packages", "config"], help="name of file to edit"
    )
    open_parser.set_defaults(function=open_file_caller)

    # install
    install_parser = subparsers.add_parser("install", help="installs packages")
    install_parser.add_argument("package_name", help="location of package to install")
    install_parser.add_argument(
        "--local",
        action="store_true",
        default=False,
        help="specifies if the package is a locally\
                                      stored file",
    )
    install_parser.set_defaults(function=install_caller)

    # list
    list_parser = subparsers.add_parser("list", help=get_help(list_packages))
    list_parser.add_argument(
        "--local", action="store_true", help="display only local files"
    )
    list_parser.add_argument(
        "--remote", action="store_true", help="display only remote packages"
    )
    list_parser.set_defaults(function=list_packages_caller)

    # move
    move_parser = subparsers.add_parser("move", help=get_help(move_package))
    move_parser.add_argument("package_name", nargs=1, help="name of package to move")
    move_parser.add_argument("location", nargs=1, help="location to move to")
    move_parser.set_defaults(function=move_package_caller)

    # remove
    remove_parser = subparsers.add_parser("remove", help=get_help(remove))
    remove_parser.add_argument(
        "package_name", nargs=1, help="name of package to remove"
    )
    remove_parser.add_argument(
        "--soft",
        action="store_true",
        default=False,
        help="if true the files are not deleted",
    )
    remove_parser.set_defaults(function=remove_caller)

    # setup
    setup_parser = subparsers.add_parser("setup", help=get_help(setup_files))
    setup_parser.set_defaults(function=setup_files)

    # upgrade
    upgrade_parser = subparsers.add_parser("upgrade", help=get_help(upgrade))
    upgrade_parser.set_defaults(function=upgrade)

    args = parser.parse_args()

    # set logger
    if args.debug:
        set_logger(debug_level="debug")
    else:
        set_logger(debug_level="info")
    logging.info("Starting")

    # execute correct function or display help
    try:
        args.function(args)
    except AttributeError:
        args = parser.parse_args(["-h"])


if __name__ == "__main__":
    main()
