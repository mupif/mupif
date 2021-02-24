#!/usr/bin/env python3
import asyncio, asyncssh, sys, argparse, os.path, logging

thisDir=os.path.dirname(os.path.abspath(__file__))

parser=argparse.ArgumentParser('Run testing SSH server')
parser.add_argument('--port',default=2024,type=int,help='Listening server port')
args=parser.parse_args(sys.argv[1:])
log=logging.getLogger('mupif-ssh-server')

class MupifTestSSHServer(asyncssh.SSHServer):
    def password_auth_supported(self): return False
    def public_key_auth_supported(self): return True
    # no shell, command, sftp, scp, …
    def session_requested(self): return False
    # allow forward tunnel
    def connection_requested(self,dhost,dport,ohost,oport):
        log.info(f'connection {ohost}:{oport} → {dhost}:{dport} requested')
        return True
    # allow reverse tunnel
    def server_requested(self,lhost,lport):
        log.info(f'server {lhost}:{lport} requested')
        return True

async def start_server():
    await asyncssh.create_server(MupifTestSSHServer, '', args.port,
                                 server_host_keys=[thisDir+'/test_ssh_server_rsa_key'],
                                 authorized_client_keys=thisDir+'/test_ssh_client_rsa_key.pub')

loop = asyncio.get_event_loop()

try:
    loop.run_until_complete(start_server())
except (OSError, asyncssh.Error) as exc:
    sys.exit('SSH server failed: ' + str(exc))

loop.run_forever()
