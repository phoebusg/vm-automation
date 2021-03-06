import logging
import os
import re
import subprocess
#import multiprocessing

if __name__ == "__main__":
    print('This script only contains functions and cannot be called directly. See "demo.py" for usage example.')
    exit(1)

# Logging options
logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=logging.INFO)
logger = logging.getLogger('vm-automation')


# Wrapper for vboxmanage command
def vboxmanage(cmd, vboxmanage_path='vboxmanage', timeout=120):
    cmd = f'{vboxmanage_path} {cmd}'.split()
    logging.debug(f'Running command: {cmd}')
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=timeout, text=True)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        logging.critical('vboxmanage path is incorrect. Stopping.')
        exit(1)


# Return list of virtual machines
def list_vms(list=1):
    result = vboxmanage('list vms --sorted')
    if result[0] == 0:
        if list:
            vms_list = re.findall(r'^"(\w+)"', result[1], flags=re.MULTILINE)
        else:
            vms_list = result[1]
        return result[0], vms_list, result[2]
    else:
        logging.error(f'Unable to get list of VMs: {result[2]}')
        return result[0], result[1], result[2]


# Return list of snapshots for specific VM
def list_snapshots(vm, list=1):
    result = vboxmanage(f'snapshot {vm} list --machinereadable')
    if result[0] == 0:
        if list:
            snapshots_list = re.findall(r'^SnapshotName(?:-\d+)?="(\w+)"', result[1], flags=re.MULTILINE)
        else:
            snapshots_list = result[1]
        return result[0], snapshots_list, result[2]
    else:
        logging.error(f'Unable to get list of snapshots: {result[2]}')
        return result[0], result[1], result[2]


# Get list of IP addresses of guest
def list_ips(vm):
    result = vboxmanage(f'guestproperty enumerate {vm}')
    if result[0] == 0:
        ips_list = re.findall(r'V4\/IP,\svalue:\s(\d+\.\d+\.\d+\.\d+),\s', result[1], flags=re.MULTILINE)
        return result[0], ips_list, result[2]
    else:
        logging.error(f'Unable to get list of IP addresses: {result[2]}')
        return result[0], result[1], result[2]


# VirtualBox version
def vm_version():
    result = vboxmanage('--version')
    return result[0], result[1], result[2]


# Start virtual machine
def vm_start(vm, ui='gui'):
    logging.info(f'Starting VM "{vm}".')
    if ui not in ['gui', 'headless']:
        logging.error(f'Unknown ui type set. Assuming gui.')
        ui = 'gui'
    result = vboxmanage(f'startvm {vm} --type {ui}')
    if result[0] == 0:
        logging.info(f'VM started')
    else:
        logging.error(f'Error while starting VM: {result[2]}')
    return result[0], result[1], result[2]


# Stop virtual machine
def vm_stop(vm):
    logging.info(f'Stopping VM "{vm}".')
    result = vboxmanage(f'controlvm {vm} poweroff')
    if result[0] == 0:
        logging.debug('VM stopped.')
    else:
        logging.error(f'Error while stopping VM: {result[2]}')
    return result[0], result[1], result[2]


# Restore snapshot for virtual machine
def vm_restore(vm, snapshot):
    logging.info(f'Restoring VM "{vm}" to snapshot "{snapshot}".')
    result = vboxmanage(f'snapshot {vm} restore {snapshot}')
    if result[0] == 0:
        logging.debug('VM restored.')
    else:
        logging.error(f'Error while restoring snapshot: {result[2]}.')
    return result[0], result[1], result[2]


# Change network link state
def vm_network(vm, link_state='keep'):
    if link_state not in ['keep', 'on', 'off']:
        logging.info(f'Unknown link_state selected for VM {vm}. Assuming "keep".')
        link_state = 'keep'
    if link_state == 'keep':
        logging.debug(f'Keeping original network state for VM "{vm}".')
        return 0, 0, 0
    elif link_state in ['on', 'off']:
        logging.info(f'Setting network parameters to {link_state} for VM {vm}')
        result = vboxmanage(f'controlvm {vm} setlinkstate1 {link_state}')
        if result[0] == 0:
            logging.debug(f'Network state changed.')
        else:
            logging.error(f'Unable to change network state for VM: {result[2]}.')
        return result[0], result[1], result[2]


# Control screen resolution
def vm_set_resolution(vm, screen_resolution):
    logging.info(f'Changing screen resolution for VM "{vm}".')
    result = vboxmanage(f'controlvm {vm} setvideomodehint {screen_resolution}')
    if result[0] == 0:
        logging.debug('Screen resolution changed.')
    else:
        logging.error(f'Unable to change screen resolution: {result[2]}')
    return result[0], result[1], result[2]


# Execute file/command on VM
def vm_exec(vm, username, password, remote_file):
    logging.info(f'{vm}: Executing file "{remote_file}" on VM "{vm}".')
    result = vboxmanage(f'guestcontrol {vm} --username {username} --password {password} start {remote_file}')
    if result[0] == 0:
        logging.debug('File executed successfully.')
    else:
        logging.error(f'Error while executing file: {result[2]}')
    return result[0], result[1], result[2]


# Get information about file on VM
def vm_file_stat(vm, username, password, remote_file):
    logging.info(f'Checking if file "{remote_file}" exist on VM "{vm}".')
    result = vboxmanage(f'guestcontrol {vm} --username {username} --password {password} stat {remote_file}')
    if result[0] == 0:
        logging.debug('File exist.')
    else:
        logging.error(f'Error while checking for file: {result[2]}')
    return result[0], result[1], result[2]


# Upload file to VM
def vm_upload(vm, username, password, local_file, remote_file):
    logging.info(f'Uploading "{local_file}" as "{remote_file}" to VM "{vm}".')
    result = vboxmanage(
        f'guestcontrol {vm} --username {username} --password {password} copyto {local_file} {remote_file}')
    if result[0] == 0:
        logging.debug(f'File uploaded.')
    else:
        logging.error(f'Error while uploading file: {result[2]}')
    return result[0], result[1], result[2]


# Download file from VM
def vm_download(vm, username, password, local_file, remote_file):
    logging.info(f'Downloading file "{remote_file}" from VM "{vm}" as "{local_file}".')
    result = vboxmanage(
        f'guestcontrol {vm} --username {username} --password {password} copyfrom {remote_file} {local_file}')
    if result[0] == 0:
        logging.debug(f'File downloaded.')
    else:
        logging.error(f'Error while downloading file: {result[2]}')
    return result[0], result[1], result[2]


# Take screenshot
def vm_screenshot(vm, screenshot_name):
    screenshot_index = 1
    while screenshot_index < 10000:
        screenshot_name_num = f'{screenshot_name}_{screenshot_index}.png'
        if os.path.isfile(screenshot_name_num):
            screenshot_index += 1
        else:
            break

    logging.info(f'Taking screenshot "{screenshot_name_num}" on VM "{vm}".')
    result = vboxmanage(f'controlvm {vm} screenshotpng {screenshot_name_num}')
    if result[0] == 0:
        logging.debug('Screenshot created.')
    else:
        logging.error(f'Error while taking screenshot: {result[2]}')
    return result[0], result[1], result[2]
