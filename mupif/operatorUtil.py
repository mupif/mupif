import smtplib
import imaplib
import email
from enum import IntEnum
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import getpass
import logging
log = logging.getLogger()

"""
Generic class to represent interaction with an operator. 
Derived classes implement different communication channels.
"""
class OperatorInteraction:
    """
    Contact operator.
    @param workflowID(str): unique workflow ID
    @param jobID(str): unique jobID
    @param msgBody(str): message to operator. Recomended to store all paramaters into dictionary and convert dictionary into json string representation.
    """
    def contactOperator (self, workflowID, jobID, msgBody):
        pass
    
    """
    Check operator response and return received data
    @param workflowID(str): unique workflow ID
    @param jobID(str): unique jobID
    @param msgBody(str): message from operator. The message should contain a filled dictionary entry which is extracted. 
    @return ret(bool),data(str): ret is False if response not received, True otherwise. Data contains the operator response.
    """
    def checkOperatorResponse (self, workflowID, jobID):
        return (False, None)

"""
Derived class implementing different communication channels.
"""
class OperatorEMailInteraction(OperatorInteraction):
    """
    Constructor setting up communication channels.
    @param From(str): email address where the response will be send to
    @param To(str): email address of the operator
    @param smtpHost(str): internet address of SMTP server for sending a message
    @param smtpUser(str): username for authentication on SMTP server
    @param smtpPsswd(str): optional string of SMTP authentication. If empty, it will ask
    @param smtpSSL(bool): if SSL encryption on STMP server should be used
    @param smtpTLS(bool): if TLS mode of IMAP server should be used
    @param smtpPort(int): port of SMTP server
    @param imapHost(str): IMAP server where the response is stored
    @param imapUser(str): IMAP user where the response is stored
    @param imapPsswd(str): optional string of IMAP user's password. If empty, it will ask
    @param imapPort(int): port of IMAP server
    @param imapSSL(bool): if SSL encryption on IMAP server should be used
    """
    def __init__(self, From, To, smtpHost, smtpUser='', smtpPsswd='', smtpSSL=False, smtpTLS=False, smtpPort=25, imapHost='', imapUser='', imapPsswd='', imapPort=993, imapSSL=True):
        self.From = From
        self.To = To
        self.smtp_tlsMode = smtpTLS
        self.smtp_sslMode=smtpSSL

        # smtp server 
        self.smtp_server=smtpHost
        self.smtp_serverPort=smtpPort
        self.smtp_username=smtpUser
        self.smtp_passwd=smtpPsswd #if empty, then interactive input

        # imap server, ssl connection only
        self.imap_server=imapHost
        self.imap_serverPort=imapPort
        self.imap_username=imapUser
        self.imap_passwd=imapPsswd #if empty, then interactive input
        self.imap_sslMode = imapSSL

    """
    Sends an email to the operator.
    @param workflowID(str): unique workflow ID
    @param jobID(str): unique jobID
    @param msgBody(str): message from operator. The message should contain an empty dictionary entry which should be filled
    """
    def contactOperator (self, workflowID, jobID, msgBody):
        log.info("Sending email to an operator using %s:%d" % (self.smtp_server, self.smtp_serverPort) )
        if (self.smtp_sslMode):
            server = smtplib.SMTP_SSL (self.smtp_server, self.smtp_serverPort)
        else:
            server = smtplib.SMTP(self.smtp_server, self.smtp_serverPort)
        
        if (self.smtp_tlsMode):
            server.starttls()
            # re-identify ourselves as an encrypted connection
            server.ehlo()
        #server.set_debuglevel(1)
        log.info("Logging to SMTP server")
        
        if self.smtp_username:
            if (self.smtp_passwd):
                psswd = self.smtp_passwd
            else:
                psswd = getpass.getpass('Enter imap server passwd: ')
            server.login(self.smtp_username, psswd)
        
        msg = MIMEMultipart()
        msg['From']=self.From
        msg['To']=self.To
        msg['Subject']= workflowID+jobID
        msg.attach(MIMEText(msgBody,'plain'))
        server.sendmail(self.From, self.To, msg.as_string())
        log.info("Email sent to operator as %s" % msg.as_string())
        server.quit()

    """
    Check IMAP server if there is operator's response.
    @param workflowID(str): unique workflow ID
    @param jobID(str): unique jobID
    :return: tuple whether the message exists and body of the message
    :rtype: bool, str
    """
    def checkOperatorResponse (self, workflowID, jobID):
        log.info("Checking Imap4 server %s on port %s" % (self.imap_server, self.imap_serverPort) )
        textBody = ''
        if (self.imap_sslMode):
            server = imaplib.IMAP4_SSL(self.imap_server, self.imap_serverPort)
        else:
            server = imaplib.IMAP4 (self.imap_server, self.imap_serverPort)
            
        if (self.imap_passwd):
            psswd = self.imap_passwd
        else:
            psswd = getpass.getpass('Enter imap server passwd: ')

        try:
            server.login(self.imap_username, psswd)
        except Exception as e:
            log.info("Imap4 login failed with username %s and %s ", self.imap_username, psswd)
            log.exception(e)
            return False, textBody
        log.info("Imap4 login OK")
    
        server.select('INBOX')
        
        uid_max =0 
        criteria = "Subject %s"%(workflowID+jobID)
        log.info("Searching for message with %s" % criteria)
        typ, data = server.search(None, criteria)
        uids = data[0].split()
        log.info("Found %d messages as %s, taking only the first one" % (len(uids), uids) )
        
        if len(uids):
            # print (uid)
            uid=uids[0] # take the first message
            result, data = server.fetch(uid, '(RFC822)')  # fetch entire message
            if result != 'OK':
                log.error("Error getting message %d", uid)
                return False, msg
            msg = email.message_from_bytes(data[0][1])

            type = msg.get_content_maintype()
            textBody=''
            if type == 'multipart':
                for part in msg.get_payload():
                    if (part.get_content_maintype()=='text'):
                        textBody= part.get_payload()
            elif type == 'text':
                textBody =  msg.get_payload()
            
            #print ('New message :::::::::::::::::::::')
            #print (textBody)
            retCode = True
        else:
            retCode =  False
            
        server.logout()
        return retCode, textBody
