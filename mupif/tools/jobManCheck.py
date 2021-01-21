import sys
sys.path.extend(['/home/nitram/Documents/work/MUPIF/mupif'])
import os
from mupif import *
import Pyro5
import logging
log = logging.getLogger()
import time as timeT
import mupif.physics.physicalquantities as PQ
import smtplib, ssl
import json


json_file = open('config.json', 'r')
json_str = json_file.read()
config_dict = json.loads(json_str)[0]

port = int(config_dict["port"])
smtp_server = config_dict["smtp_server"]
sender_email = config_dict["sender_email"]
password = config_dict["password"]
nshost = config_dict["nshost"]
nsport = int(config_dict["nsport"])
hkey = config_dict["hkey"]


json_file = open('jobMan2Email.json', 'r')
json_str = json_file.read()
jobManName2Email = json.loads(json_str)[0]

ns = pyroutil.connectNameServer(nshost, nsport, hkey)


jobManagerError = "JobManager is down, please restart it"
jobError = "JobManager is running, but it is not possible to allocate a job"

def sendEmail(sender_email, receiver_email, jobManName, error_cause):
        message = """\
Subject: Error of %s

%s

Kind regards,
Mupif team"""%(jobManName,error_cause)

        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, port) as server:
                server.ehlo()  # Can be omitted
                server.starttls(context=context)
                server.ehlo()  # Can be omitted
                server.login(sender_email, password)
                server.sendmail(sender_email, receiver_email, message)



for key in jobManName2Email:
        jobManName = key
        receiver_email = jobManName2Email.get(jobManName)
        log.info('\n-------------------------------------------------------------------------------------------------------------------------------')
        try:
                (jobManHostname, jobManPort, jobManNatHost, jobManNatport) = pyroutil.getNSConnectionInfo(ns, jobManName)
        except Exception as e:
                log.debug("Exception occurs, sending email")
                sendEmail(sender_email, receiver_email, jobManName, "%s\nJobManHostName:%s"%("Jobmanager is not registered at nameserver",jobManName) )
                continue
        try:
                jobMan = pyroutil.connectJobManager(ns, jobManName, hkey)
                try:
                        solver = pyroutil.allocateApplicationWithJobManager( ns, jobMan, None, hkey)
                except Exception as e:
                        log.debug("Exception occurs, sending email")
                        sendEmail(sender_email, receiver_email, jobManName, "%s\nJobManHostName:%s, jobManPort: %s"%(jobError,jobManHostname,jobManPort))	              
        except Exception as e:
                log.exception(e)
                log.debug("Exception occurs, sending email")
                sendEmail(sender_email, receiver_email, jobManName, "%s\nJobManHostName:%s, jobManPort: %s"%(jobManagerError,jobManName,jobManPort))