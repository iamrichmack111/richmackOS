# RichmackOS Bash login profile

if [ -f ~/.bashrc ]; then
    . ~/.bashrc
fi

# Launch RichmackOS only on the physical/local tty1 console.
# SSH sessions remain normal Bash administration shells.
if [[ "$(tty 2>/dev/null)" == "/dev/tty1" ]]; then
    exec /usr/local/bin/richmack-console
fi
