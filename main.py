import json
import os
import requests
import shutil
import sys


def do_release(mod_path):
    assert os.path.isdir(mod_path), f'not a directory: {mod_path}'

    version = get_version(mod_path)
    archive = create_mod_zip(mod_path, version)
    set_fix_mod_version(mod_path, version)
    increase_info_version(mod_path, version)

    success = test([mod_path])
    if not success:
        set_info_version(mod_path, version)
        return 1

    return upload_mod(archive)
    # TODO: update changelog.txt


def run_tests():
    print("Run tests.")
    result = input("Proceed (Yes/No)? ")

    if result != "Yes":
        print("Aborting. END.")
        return False
    return True


def init_upload(mod_name):
    url = 'https://mods.factorio.com/api/v2/mods/releases/init_upload'
    form_data = {'mod': mod_name}
    server = requests.post(url, data=form_data, headers=api_header())
    output = json.loads(server.text)
    url_key = 'upload_url'
    assert url_key in output, str(output)
    return output[url_key]


def api_header():
    api_key = os.getenv('FACTORIO_MOD_API_KEY')
    headers = {'Authorization': f'Bearer {api_key}'}
    return headers


def upload_mod(archive):
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


def get_mod_name(path):
    _, filename = os.path.split(path)
    return filename.split('_')[0]


def info_file(path):
    return os.path.join(path, "info.json")


def read_info_file(path):
    with open(info_file(path)) as file:
        return json.load(file)


def get_version(path):
    data = read_info_file(path)
    return data["version"]


def set_info_version(path, version):
    data = read_info_file(path)
    data["version"] = version

    with open(info_file(path), 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def increase_info_version(path, version):
    version_parts = [int(part) for part in version.split('.')]
    version_parts[2] = version_parts[2]+1
    new_version = ".".join([str(i) for i in version_parts])
    set_info_version(path, new_version)


def set_fix_mod_version(path, version):
    parent_dir, mod_dir = os.path.split(path)
    mod_list_file = os.path.join(parent_dir, "mod-list.json")
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


def create_mod_zip(path, version):
    new_path = path.replace('0.0.0', version)
    shutil.copytree(path, new_path, ignore=shutil.ignore_patterns('.git*', '.idea', '.test'))
    parent_dir, mod_dir = os.path.split(new_path)
    archive_path = shutil.make_archive(new_path, 'zip', root_dir=parent_dir, base_dir=mod_dir)
    shutil.rmtree(new_path)
    return archive_path


def main(argv):
    argv.pop(0)  # remove script name

    command = argv.pop(0)
    if command == "release":
        return release(argv)
    elif command == "test":
        return test(argv)
    else:
        print(f"unknown command {command}")
        return 2


def test(argv):
    assert (len(argv) == 1)
    mod_path = argv[0]
    print(f'Testing {mod_path}')
    return run_tests()


def release(argv):
    assert (len(argv) == 1)
    mod_path = argv[0]
    print(f'Release for {mod_path}')
    do_release(mod_path)


if __name__ == '__main__':
    rc = main(sys.argv)
    exit(rc)
