import json
import os
import requests
import shutil
import sys


def release(mod_path):
    assert os.path.isdir(mod_path)

    version = get_version(mod_path)
    archive = create_mod_zip(mod_path, version)

    success = run_tests()
    if not success:
        return

    upload_mod(archive)
    # TODO: increment version patch number in mod dev dir info.json
    # TODO: update changelog.txt


def run_tests():
    print("Run tests.")
    result = input("Proceed (Yes/No)?")

    if result != "Yes":
        print("Aborting. END.")
        return False
    return True


def init_upload(mod_name):
    url = 'https://mods.factorio.com/api/v2/mods/releases/init_upload'
    form_data = {'mod': mod_name}
    server = requests.post(url, data=form_data, headers=api_header())
    output = json.loads(server.text)
    return output['upload_url']


def api_header():
    api_key = os.getenv('FACTORIO_MOD_API_KEY')
    headers = {'Authorization': f'Bearer {api_key}'}
    return headers


def upload_mod(archive):
    _, filename = os.path.split(archive)
    mod_name = filename.split('_')[0]
    upload_url = init_upload(mod_name)
    files = {'file': (filename, open(archive,'rb'), 'application/x-zip-compressed')}
    server = requests.post(upload_url, files=files, headers=api_header())
    print(server.text)


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
    assert (len(argv) == 2)
    mod_path = argv[1]
    release(mod_path)


if __name__ == '__main__':
    main(sys.argv)
