import os
import sys
import boto3
import zipfile
import shutil
import logging
import argparse
import time
from botocore.client import Config
from config.test_config_reader import aws_config, test_header

logging.basicConfig()
logger = logging.getLogger('Prepare lambda')
logger.setLevel(logging.DEBUG)

"""
Script to prepare packages_folder, framework and tests into zip to upload to lambda function
"""


def constants() -> tuple:
    framework_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    packages_folder = os.path.join(framework_root, 'aws', 'python-packages')
    lambda_zip_file = os.path.join(framework_root, 'aws', 'lambda.zip')
    run_file = os.path.join(framework_root, 'load_generator.py')
    requirements_file = os.path.join(framework_root, 'aws', 'lambda_requirements.txt')
    docker_cmd = f'docker run ' \
        f'--volume={framework_root}/aws/python-packages:/python-packages ' \
        f'python:3.8 ' \
        '/bin/bash -c "pip install -r /python-packages/lambda_requirements.txt --target=/python-packages"'
    return framework_root, packages_folder, lambda_zip_file, run_file, requirements_file, docker_cmd


def please_confirm(prompt: str):
    confirm = input(f'Please, confirm: \n{prompt} y/n\n')
    if confirm.lower() != 'y':
        logger.info('Not confirmed, exiting...')
        sys.exit(0)


def zipdir(path: str, ziph: zipfile.ZipFile, base_path):
    """
    function to zip whole directory
    :param path: path to directory
    :param ziph: zip file handler
    :param base_path: base path to avoid absolute paths in zip
    :return:
    """
    for root, dirs, files in os.walk(path):
        head, tail = os.path.split(root)
        if tail != '__pycache__':
            for file in files:
                file_path = os.path.join(root, file)
                ziph.write(file_path, os.path.relpath(file_path, base_path))


def build_packages():
    """
    function to build python packages in Docker
    :return:
    """
    please_confirm('Are you sure you want to rebuild framework python packages in Docker '
                   'in the \'python-packages\' folder?')
    _, packages_folder, _, _, requirements_file, docker_cmd = constants()
    logger.info('Creating folder...')
    if os.path.isdir(packages_folder):
        shutil.rmtree(packages_folder)
    os.mkdir(packages_folder)
    logger.info('Installing requirements in Docker...')
    shutil.copy(requirements_file, packages_folder)
    os.system(docker_cmd)
    logger.info('Requirements packages build!')


def build_lambda_zip(rebuild_packages=False):
    """
    function to create zip-file for AWS lambda
    :param rebuild_packages: call build_packages?
    :return:
    """
    framework_root, packages_folder, lambda_zip_file, run_file, _, _ = constants()
    try:
        if os.path.exists(lambda_zip_file):
            os.remove(lambda_zip_file)
        if rebuild_packages:
            build_packages()
        logger.info('Zipping framework & tests...')
        with zipfile.ZipFile(lambda_zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for folder in ['config', 'framework']:
                zipdir(os.path.join(framework_root, folder), zipf, framework_root)
            zipdir(os.path.join(framework_root, 'tests', test_header['name']), zipf, framework_root)
            zipdir(packages_folder, zipf, packages_folder)
            zipf.write(run_file, os.path.relpath(run_file, framework_root))
        logger.info('lambda.zip file prepared!')
    except Exception as e:
        logger.exception(e)


def lambda_exists(client: boto3.client, name: str) -> bool:
    try:
        client.get_function(FunctionName=name)
    except client.exceptions.ResourceNotFoundException:
        return False
    return True


def create_new_lambda(client: boto3.client, zip_bytes: bytes):
    """
    function to create new lambda basing on config settings
    :param client: AWS client reference
    :return:
    """
    try:
        response = client.create_function(
            FunctionName=test_header['name'],
            Runtime='python3.8',
            Role=aws_config['new_lambda_role'],
            Handler='load_generator.start',
            Code={
                'ZipFile': zip_bytes
            },
            Description=test_header['description'],
            Timeout=900,
            MemorySize=aws_config['memory_size'],
            Publish=True
        )
        logger.info(f'Create response: {response}')
    except Exception as e:
        logger.exception(e)


def upload_lambda_code(zip_bytes: bytes, client: boto3.client) -> None:
    """
    Function to upload
    :param zip_bytes: bytes stream of zip to upload
    :param client: AWS client reference
    :return:
    """
    logger.info(f'Uploading zip package to lambda {test_header["name"]}')
    try:
        if lambda_exists(client=client,
                         name=test_header['name']):
            response = client.update_function_code(
                FunctionName=test_header['name'],
                ZipFile=zip_bytes,
                Publish=True
            )
            logger.info(f'Upload response: {response}')
        else:
            logger.info(f'No lambda named {test_header["name"]} found. Creating...')
            create_new_lambda(client=client,
                              zip_bytes=zip_bytes)
    except Exception as e:
        logger.exception(e)


def get_aws_client() -> boto3.client:
    """
    Function to get lambda client basing on config
    :return: boto3.client
    """
    session = boto3.session.Session(aws_access_key_id=aws_config['aws_access_key_id'],
                                    aws_secret_access_key=aws_config['aws_secret_access_key'],
                                    region_name=test_header['location'])
    config = Config(connect_timeout=10, read_timeout=310)
    client = session.client('lambda', config=config)
    return client


def main():
    start = time.time()
    _, _, lambda_zip_file, _, _, _ = constants()
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--build", action='store_true',
                        help="build lambda .zip file")
    parser.add_argument("-r", "--rebuild", action='store_true',
                        help="rebuild python packages")
    parser.add_argument("-u", "--upload", action='store_true',
                        help="upload lambda code")
    args = parser.parse_args()
    logger.info(f'Starting with args: {args}...')
    if args.build:
        build_lambda_zip(rebuild_packages=args.rebuild)
    if args.upload:
        please_confirm(f'Upload \"{test_header["name"]}\" test code to lambda in \"{test_header["location"]}\" location?')
        c = get_aws_client()
        with open(lambda_zip_file, 'rb') as zipb:
            upload_lambda_code(zip_bytes=zipb.read(), client=c)
    end = int(time.time() - start)
    logger.info(f'Completed in {end}s')


if __name__ == '__main__':
    main()
