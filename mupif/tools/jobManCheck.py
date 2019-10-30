import sys
sys.path.extend(['/home/nitram/Documents/work/MUPIF/mupif'])
import os
from mupif import *
import Pyro4
import logging
log = logging.getLogger()
import time as timeT
import mupif.Physics.PhysicalQuantities as PQ



import smtplib, ssl

port = 587  # For starttls
smtp_server = "smtp.gmail.com"
sender_email = "mupifmonitor@gmail.com"
password = input("Type your password and press enter:")
admin_email = sender_email
nshost = '172.30.0.1'
nsport = 9090
hkey = 'mupif-secret-key'

file = open('jobmanName_email.txt','r')
jobManName2Email = eval(file.read())
file.close()



def sendEmail(jobManName, receiver_email):
	message = """\
	Subject: Jobmanager check

	The jobmanager""" +jobManName + """is down, please restart it.

	Kind regards,
	Mupif team"""

	context = ssl.create_default_context()
	with smtplib.SMTP(smtp_server, port) as server:
	    server.ehlo()  # Can be omitted
	    server.starttls(context=context)
	    server.ehlo()  # Can be omitted
	    server.login(sender_email, password)
	    server.sendmail(sender_email, receiver_email, message)


try:
        ns = PyroUtil.connectNameServer(nshost, nsport, hkey)
except Exception as e:
        log.exception(e)
        log.debug("Exception when connecting to nameserver occurs, sending email")
        sendEmail("nameserver", admin_email)	
            

for key in jobManName2Email:
    email = jobManName2Email.get(key)
    log.info('\n-------------------------------------------------------------------------------------------------------------------------------')            
    try:
        jobMan = PyroUtil.connectJobManager(ns, key,hkey)
        try:
            solver = PyroUtil.allocateApplicationWithJobManager( ns, jobMan, None, hkey)
            log.info('Job Created')            
        except Exception as e:
            log.exception(e)
            log.debug("Exception occurs, sending email")
            sendEmail(key, email)	
        else:
            if (solver is not None):
                solverSignature = solver.getApplicationSignature()
                log.info("Working solver on server " + solverSignature)
            else:
                log.debug("Connection to server failed, sending email")
                sendEmail(key, email)
        
    except Exception as e:
        log.exception(e)
        log.debug("Exception occurs, sending email")
        sendEmail(key, email)
            

        
