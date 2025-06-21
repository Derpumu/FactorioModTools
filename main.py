import json
import os
import pathlib
from typing import NewType, Dict, Mapping

import requests
import shutil
import subprocess
import sys

import testing

Version = NewType('Version', str)
Path = NewType('Path', str)


def do_release(mod_path: Path) -> int:
    assert os.path.isdir(mod_path), f'not a directory: {mod_path}'

    version: Version = get_version(mod_path)
    archive: Path = create_mod_zip(mod_path, version)
    set_mod_list_version(mod_path, version)

    success = run_tests(mod_path)
    if not success:
        return 1

    increase_info_version(mod_path, version)
    tag_git(mod_path, version)
    set_mod_list_version(mod_path, None)
    return upload_mod(archive)
    # TODO: update changelog.txt


def run_tests(mod_path: Path) -> bool:
    if testing.has_test_dir(pathlib.Path(mod_path)):
        print("running automated tests")
        return testing.test(pathlib.Path(mod_path))

    print("Run manual tests.")
    result: str = input("Proceed (Yes/No)? ")

    if result != "Yes":
        print("Aborting. END.")
        return False
    return True


def init_upload(mod_name: str) -> Mapping[str, object]:
    url = 'https://mods.factorio.com/api/v2/mods/releases/init_upload'
    form_data = {'mod': mod_name}
    server = requests.post(url, data=form_data, headers=api_header())
    output = json.loads(server.text)
    url_key = 'upload_url'
    assert url_key in output, str(output)
    return output[url_key]


def api_header() -> Mapping[str, str]:
    api_key: str = os.getenv('FACTORIO_MOD_API_KEY') or ""
    headers: Mapping[str, str] = {'Authorization': f'Bearer {api_key}'}
    return headers


def upload_mod(archive: Path) -> int:
    filename: str
    _, filename = os.path.split(archive)
    mod_name = get_mod_name(archive)
    upload_url = init_upload(mod_name)
    if input(f"Upload {filename} (Yes/No)? ") == "Yes":
        server = perform_upload(archive, filename, upload_url)
        print(server.text)
        return 0
    else:
        print("Upload canceled.")
        return 1


def perform_upload(archive, filename, upload_url):
    files = {'file': (filename, open(archive, 'rb'), 'application/x-zip-compressed')}
    server = requests.post(upload_url, files=files, headers=api_header())
    return server


def get_mod_name(path: Path) -> str:
    _, filename = os.path.split(path)
    return filename.split('_')[0]


def info_file(path):
    return os.path.join(path, "info.json")


def read_info_file(path: str):
    with open(info_file(path)) as file:
        return json.load(file)


def get_version(path: str) -> Version:
    data = read_info_file(path)
    return data["version"]


def set_info_version(path, version):
    data = read_info_file(path)
    data["version"] = version

    with open(info_file(path), 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def increase_info_version(path, version):
    version_parts = [int(part) for part in version.split('.')]
    version_parts[2] = version_parts[2] + 1
    new_version = ".".join([str(i) for i in version_parts])
    set_info_version(path, new_version)


def set_mod_list_version(path, version):
    parent_dir, mod_dir = os.path.split(path)
    mod_list_file = os.path.join(parent_dir, "mod-list.json")
    try:
        mod_list = None
        with open(mod_list_file) as file:
            mod_list = json.load(file)
        mod_name = get_mod_name(path)
        for entry in mod_list["mods"]:
            if entry["name"] == mod_name:
                entry["version"] = version
                break
        with open(mod_list_file, 'w', encoding='utf-8') as file:
            json.dump(mod_list, file, ensure_ascii=False, indent=2)
    except FileNotFoundError:
        pass


def create_mod_zip(path: Path, version: Version) -> Path:
    new_path: str = path.replace('0.0.0', version)
    shutil.copytree(path, new_path, ignore=shutil.ignore_patterns('.*'))
    parent_dir, mod_dir = os.path.split(new_path)
    archive_path = shutil.make_archive(new_path, 'zip', root_dir=parent_dir, base_dir=mod_dir)
    shutil.rmtree(new_path)
    return Path(archive_path)


def tag_git(path: Path, version: Version) -> None:
    git = shutil.which("git")
    assert git, "git not found"
    subprocess.call([git, "tag", version], cwd=path)
    subprocess.call([git, "push", "--tags"], cwd=path)


def main(argv: list[str]) -> int:
    argv.pop(0)  # remove script name

    command: str = argv.pop(0)
    if command == "release":
        return release(argv)
    elif command == "test":
        return test(argv)
    else:
        print(f"unknown command {command}")
        return 2


def test(argv) -> int:
    assert (len(argv) == 1)
    mod_path: Path = argv[0]
    print(f'Testing {mod_path}')
    return 0 if run_tests(mod_path) else 1


def release(argv) -> int:
    assert (len(argv) == 1)
    mod_path: Path = argv[0]
    print(f'Release for {mod_path}')
    return do_release(mod_path)


if __name__ == '__main__':
    rc = main(sys.argv)
    exit(rc)
