#!/bin/bash
# http://stackoverflow.com/a/246128/761090
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# make sure permissions on keys are right
chmod go-rwx $DIR/test_ssh_server_rsa_key $DIR/test_ssh_client_rsa_key

echo $DIR

/usr/sbin/sshd -f /dev/null -oPort=2024 -oProtocol=2 -oListenAddress=127.0.0.1 -oForceCommand=/sbin/nologin -oHostKey=$DIR/test_ssh_server_rsa_key -oAuthorizedKeysFile=$DIR/test_ssh_client_rsa_key.pub -oPubkeyAuthentication=yes -oPasswordAuthentication=no

