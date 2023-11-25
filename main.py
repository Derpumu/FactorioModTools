import json
import os
import requests
import shutil
import sys


def do_release(mod_path):
    assert os.path.isdir(mod_path), f'not a directory: {mod_path}'

    version = get_version(mod_path)
    archive = create_mod_zip(mod_path, version)

    success = test(mod_path)
    if not success:
        return 1

    return upload_mod(archive)
    # TODO: increment version patch number in mod dev dir info.json
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


def get_version(path):
    info_file = os.path.join(path, "info.json")
    with open(info_file) as file:
        data = json.load(file)
        return data["version"]


def create_mod_zip(path, version):
    new_path = path.replace('0.0.0', version)
    shutil.copytree(path, new_path, ignore=shutil.ignore_patterns('.git', '.idea'))
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
