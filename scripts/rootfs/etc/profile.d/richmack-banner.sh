#!/bin/bash

# Only display in interactive shells
[[ $- != *i* ]] && return

clear

# RichmackOS ANSI logo
cat /opt/richmack/assets/logo.ans
printf '\033[0m\n'

# OS title
printf '\033[1;36m'
figlet -f slant "RICHMACK OS"
printf '\033[0m'

printf '\033[1;35mTerminal-First Linux Workspace\033[0m\n'
printf '\033[38;5;45m────────────────────────────────────────────\033[0m\n'
printf '\033[1;33mVersion:\033[0m  0.1.0\n'
printf '\033[1;32mUser:\033[0m     %s\n' "$(whoami)"
printf '\033[1;32mHost:\033[0m     %s\n' "$(hostname)"
printf '\033[1;32mKernel:\033[0m   %s\n' "$(uname -r)"
printf '\033[1;32mArch:\033[0m     %s\n' "$(uname -m)"
printf '\033[38;5;45m────────────────────────────────────────────\033[0m\n'
printf '\033[1;35mWorkspace:\033[0m richmack\n\n'
