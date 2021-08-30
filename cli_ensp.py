#!/usr/bin/env python3

import telnetlib
import time
import datetime
import re
import argparse
import os
from rich.console import Console

HOST = "192.168.180.55"
PORT = "2000"

cli_getconf = "dis current-configuration"
# cli_getconf = "dis ip int br"
cli_init = "\nreturn\n"
cli_terminal_length_off = "user-interface con 0 \nscreen-length 0 \nquit"
cli_terminal_length_on = "user-interface con 0 \nundo screen-length \nquit"
cli_conf = "system-view"
cli_return = "return"
cli_save = "save\ny\n"
output_dir = "output"
sleep_time = 1
description = "cli_ensp: Run commands on routers/switches eNSP "
epilog = "https://github.com/alexeykr@gmail.com"


def cmdArgsParser():
    parser = argparse.ArgumentParser(description=description, epilog=epilog)
    parser.add_argument("-i", "--ip", help="Ip address eNSP", action="store", dest="ip", default="")
    parser.add_argument("-n", "--num", help="Total Numbers of routers/switches", action="store", dest="num", default="5")
    parser.add_argument("-c", "--cmd", help="Run command on routers/switches", action="store", dest="cmd", default="")
    parser.add_argument("-s", "--save", help="Save configuration in txt file", action="store_true", dest="save", default=False)
    parser.add_argument("-d", "--dirsave", help="Sub directory in output dir for save configuration", action="store", dest="savedir")
    parser.add_argument("-w", "--write", help="Write config to flash on routers/switches", dest="write", action="store_true", default=False)
    parser.add_argument("-v", "--verbose", help="Verbose some debug information", action="store_true", dest="verbose", default=False)
    parser.add_argument("-p", "--port", help="First port for routers/switches", action="store", dest="port", default="2000")
    parser.add_argument("-r", "--routers", help="List of routers(numeric)", action="store", dest="routers", default="")

    return parser.parse_args()


def get_date():
    # Get date
    now = datetime.datetime.now()
    day = str(now.day)
    month = str(now.month)
    year = str(now.year)
    hour = str(now.hour)
    minute = str(now.minute)
    sec = str(now.second)

    if len(day) == 1:
        day = '0' + day
    if len(month) == 1:
        month = '0' + month
    return year, month, day, hour, minute, sec


def write_result(pre_name_file, namehost, write_messsage, flagNewFile=True):
    # Write to file result
    year, month, day, hour, minute, sec = get_date()
    file_name_long = '_'.join([pre_name_file, namehost, year, month, day, hour, minute, sec + ".txt"])
    file_name_short = '_'.join([pre_name_file, namehost + ".txt"])
    for file_name in [file_name_long, file_name_short]:
        with open(f'{output_dir}/{file_name}', 'w') as id_config_file:
            id_config_file.write(write_messsage)
            id_config_file.write("\n\n")


def send_command(cmd, prompt=[b">", b"]"]):
    # Send command to router/switch
    tn.read_very_eager()
    tn.write(cmd.encode('utf-8') + b"\n")
    # time.sleep(sleep_time)
    index, m, data = tn.expect(prompt, timeout=5)
    resp = data.decode("utf-8")
    if verbose:
        console.print(f'send_command: {cmd} return: {resp}')
    return resp


def get_host_name():
    # Get hosname
    # system_view(False)
    bf = send_command(cli_init)
    # console.print(f'buffer: {bf}')
    hostname = str(re.match(r'[\<\[]([^\>\]]*)[\>\]]', bf.split("\n")[-1]).group(1))
    console.print(f'[magenta]hostname: [orange1 bold]{hostname}')
    return hostname


def system_view(sv_flag):
    # Enable or disable system-view
    if sv_flag:
        send_command(cli_conf, bpromptsys)
    else:
        send_command(cli_return, bprompt)


def save_configuration():
    # Save configuration from routers/switches
    console.print("Write configuration to flash ...")
    res = send_command(cli_save, bprompt)
    console.print(f'{res}')


def set_terminal_length(tl_flag=True):
    # Set terminal length
    system_view(True)
    if tl_flag:
        send_command(cli_terminal_length_off, bpromptsys)
    else:
        send_command(cli_terminal_length_on, bprompt)
    system_view(False)


def get_configuration(name):
    # Send command to routers/switches from command line
    console.print("Save configuration ...")
    # [b"return"]
    dt = send_command(cli_getconf, bprompt)
    write_result("conf", name, dt)


if __name__ == "__main__":
    console = Console()
    cmd_args = cmdArgsParser()
    lst_host = [i for i in range(int(cmd_args.num))]

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    if cmd_args.savedir:
        if not os.path.exists(f'{output_dir}/{cmd_args.savedir}'):
            os.makedirs(f'{output_dir}/{cmd_args.savedir}')
        output_dir = f'{output_dir}/{cmd_args.savedir}'
    if cmd_args.routers:
        lst_host = [int(i) - 1 for i in str(cmd_args.routers).split(",")]
    verbose = bool(cmd_args.verbose)
    if cmd_args.ip != "":
        HOST = cmd_args.ip
    if cmd_args.port:
        PORT = cmd_args.port
    for i in lst_host:
        # inc = int(i) - 1
        inc = int(i)
        console.rule(characters="=", style='white')
        console.print(f'[magenta]Connect to eNSP: [orange1 bold]{HOST} port: {int(PORT) + inc}')
        console.rule(characters="=", style='white')
        try:
            tn = telnetlib.Telnet(HOST, int(PORT) + inc)
            namehost = get_host_name()
            bprompt = [bytes(f'<{namehost}>', 'utf-8')]
            bpromptsys = [bytes(f'[{namehost}]', 'utf-8')]
            set_terminal_length()
            if cmd_args.save:
                get_configuration(namehost.lower())
                time.sleep(sleep_time)
            if cmd_args.cmd:
                console.print(f'Run cmd: {cmd_args.cmd}')
                resp = send_command(cmd_args.cmd, bprompt)
                console.print(f'{resp}')
            if cmd_args.write:
                save_configuration()
            # set_terminal_length(False)
            tn.close()
        except Exception as error:
            console.print(f'{error}')
