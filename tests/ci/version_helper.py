#!/usr/bin/env python3
import datetime
import logging
import os.path as p
import subprocess
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from typing import Dict, Tuple, Union

from git_helper import Git, removeprefix

FILE_WITH_VERSION_PATH = "cmake/autogenerated_versions.txt"
CHANGELOG_IN_PATH = "debian/changelog.in"
CHANGELOG_PATH = "debian/changelog"
GENERATED_CONTRIBUTORS = "src/Storages/System/StorageSystemContributors.generated.cpp"

# It has {{ for plain "{"
CONTRIBUTORS_TEMPLATE = """// autogenerated by {executer}
const char * auto_contributors[] {{
{contributors}
    nullptr}};
"""

VERSIONS = Dict[str, Union[int, str]]

VERSIONS_TEMPLATE = """# This variables autochanged by release_lib.sh:

# NOTE: has nothing common with DBMS_TCP_PROTOCOL_VERSION,
# only DBMS_TCP_PROTOCOL_VERSION should be incremented on protocol changes.
SET(VERSION_REVISION {revision})
SET(VERSION_MAJOR {major})
SET(VERSION_MINOR {minor})
SET(VERSION_PATCH {patch})
SET(VERSION_GITHASH {githash})
SET(VERSION_DESCRIBE {describe})
SET(VERSION_STRING {string})
# end of autochange
"""

git = Git()


class ClickHouseVersion:
    """Immutable version class. On update returns a new instance"""

    def __init__(
        self,
        major: Union[int, str],
        minor: Union[int, str],
        patch: Union[int, str],
        revision: Union[int, str],
        git: Git,
    ):
        self._major = int(major)
        self._minor = int(minor)
        self._patch = int(patch)
        self._revision = int(revision)
        self._git = git
        self._describe = ""

    def update(self, part: str) -> "ClickHouseVersion":
        """If part is valid, returns a new version"""
        method = getattr(self, f"{part}_update")
        return method()

    def major_update(self) -> "ClickHouseVersion":
        return ClickHouseVersion(self.major + 1, 1, 1, self.revision + 1, self._git)

    def minor_update(self) -> "ClickHouseVersion":
        return ClickHouseVersion(
            self.major, self.minor + 1, 1, self.revision + 1, self._git
        )

    def patch_update(self) -> "ClickHouseVersion":
        return ClickHouseVersion(
            self.major, self.minor, self.patch + 1, self.revision, self._git
        )

    @property
    def major(self) -> int:
        return self._major

    @property
    def minor(self) -> int:
        return self._minor

    @property
    def patch(self) -> int:
        return self._patch

    @property
    def tweak(self) -> int:
        return self._git.tweak

    @property
    def revision(self) -> int:
        return self._revision

    @property
    def githash(self) -> str:
        return self._git.sha

    @property
    def describe(self):
        return self._describe

    @property
    def string(self):
        return ".".join(
            (str(self.major), str(self.minor), str(self.patch), str(self.tweak))
        )

    def as_dict(self) -> VERSIONS:
        return {
            "revision": self.revision,
            "major": self.major,
            "minor": self.minor,
            "patch": self.patch,
            "tweak": self.tweak,
            "githash": self.githash,
            "describe": self.describe,
            "string": self.string,
        }

    def as_tuple(self) -> Tuple[int, int, int, int]:
        return (self.major, self.minor, self.patch, self.tweak)

    def with_description(self, version_type):
        if version_type not in VersionType.VALID:
            raise ValueError(f"version type {version_type} not in {VersionType.VALID}")
        self._describe = f"v{self.string}-{version_type}"


class VersionType:
    LTS = "lts"
    PRESTABLE = "prestable"
    STABLE = "stable"
    TESTING = "testing"
    VALID = (TESTING, PRESTABLE, STABLE, LTS)


def validate_version(version: str):
    parts = version.split(".")
    if len(parts) != 4:
        raise ValueError(f"{version} does not contain 4 parts")
    for part in parts:
        int(part)


def get_abs_path(path: str) -> str:
    return p.abspath(p.join(git.root, path))


def read_versions(versions_path: str = FILE_WITH_VERSION_PATH) -> VERSIONS:
    versions = {}
    path_to_file = get_abs_path(versions_path)
    with open(path_to_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line.startswith("SET("):
                continue

            value = 0  # type: Union[int, str]
            name, value = line[4:-1].split(maxsplit=1)
            name = removeprefix(name, "VERSION_").lower()
            try:
                value = int(value)
            except ValueError:
                pass
            versions[name] = value

    return versions


def get_version_from_repo(
    versions_path: str = FILE_WITH_VERSION_PATH,
) -> ClickHouseVersion:
    versions = read_versions(versions_path)
    return ClickHouseVersion(
        versions["major"],
        versions["minor"],
        versions["patch"],
        versions["revision"],
        git,
    )


def update_cmake_version(
    version: ClickHouseVersion,
    versions_path: str = FILE_WITH_VERSION_PATH,
):
    path_to_file = get_abs_path(versions_path)
    with open(path_to_file, "w", encoding="utf-8") as f:
        f.write(VERSIONS_TEMPLATE.format_map(version.as_dict()))


def _update_changelog(repo_path: str, version: ClickHouseVersion):
    cmd = """sed \
        -e "s/[@]VERSION_STRING[@]/{version_str}/g" \
        -e "s/[@]DATE[@]/{date}/g" \
        -e "s/[@]AUTHOR[@]/clickhouse-release/g" \
        -e "s/[@]EMAIL[@]/clickhouse-release@yandex-team.ru/g" \
        < {in_path} > {changelog_path}
    """.format(
        version_str=version.string,
        date=datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S") + " +0300",
        in_path=p.join(repo_path, CHANGELOG_IN_PATH),
        changelog_path=p.join(repo_path, CHANGELOG_PATH),
    )
    subprocess.check_call(cmd, shell=True)


def update_contributors(
    relative_contributors_path: str = GENERATED_CONTRIBUTORS, force: bool = False
):
    # Check if we have shallow checkout by comparing number of lines
    # '--is-shallow-repository' is in git since 2.15, 2017-10-30
    if git.run("git rev-parse --is-shallow-repository") == "true" and not force:
        logging.warning("The repository is shallow, refusing to update contributors")
        return

    contributors = git.run("git shortlog HEAD --summary")
    contributors = sorted(
        [c.split(maxsplit=1)[-1].replace('"', r"\"") for c in contributors.split("\n")],
    )
    contributors = [f'    "{c}",' for c in contributors]

    executer = p.relpath(p.realpath(__file__), git.root)
    content = CONTRIBUTORS_TEMPLATE.format(
        executer=executer, contributors="\n".join(contributors)
    )
    contributors_path = get_abs_path(relative_contributors_path)
    with open(contributors_path, "w", encoding="utf-8") as cfd:
        cfd.write(content)


def _update_dockerfile(repo_path: str, version: ClickHouseVersion):
    version_str_for_docker = ".".join(
        [str(version.major), str(version.minor), str(version.patch), "*"]
    )
    cmd = "ls -1 {path}/docker/*/Dockerfile | xargs sed -i -r -e 's/ARG version=.+$/ARG version='{ver}'/'".format(
        path=repo_path, ver=version_str_for_docker
    )
    subprocess.check_call(cmd, shell=True)


def update_version_local(repo_path, version, version_type="testing"):
    update_contributors()
    version.with_description(version_type)
    update_cmake_version(version)
    _update_changelog(repo_path, version)
    _update_dockerfile(repo_path, version)


def main():
    """The simplest thing it does - reads versions from cmake and produce the
    environment variables that may be sourced in bash scripts"""
    parser = ArgumentParser(
        formatter_class=ArgumentDefaultsHelpFormatter,
        description="The script reads versions from cmake and produce ENV variables",
    )
    parser.add_argument(
        "--version-path",
        "-p",
        default=FILE_WITH_VERSION_PATH,
        help="relative path to the cmake file with versions",
    )
    parser.add_argument(
        "--version-type",
        "-t",
        choices=VersionType.VALID,
        help="optional parameter to generate DESCRIBE",
    )
    parser.add_argument(
        "--export",
        "-e",
        action="store_true",
        help="if the ENV variables should be exported",
    )
    parser.add_argument(
        "--update",
        "-u",
        choices=("major", "minor", "patch"),
        help="the version part to update, tweak is always calculated from commits",
    )
    parser.add_argument(
        "--update-contributors",
        "-c",
        action="store_true",
        help=f"update {GENERATED_CONTRIBUTORS} file and exit, "
        "doesn't work on shallow repo",
    )
    args = parser.parse_args()

    if args.update_contributors:
        update_contributors()
        return

    version = get_version_from_repo(args.version_path)

    if args.update:
        version = version.update(args.update)

    if args.version_type:
        version.with_description(args.version_type)

    if args.update:
        update_cmake_version(version)

    for k, v in version.as_dict().items():
        name = f"CLICKHOUSE_VERSION_{k.upper()}"
        print(f"{name}='{v}'")
        if args.export:
            print(f"export {name}")


if __name__ == "__main__":
    main()
