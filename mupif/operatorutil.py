import smtplib
import imaplib
import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import getpass
import logging
log = logging.getLogger()


class OperatorInteraction:
    """
    Generic class to represent interaction with an operator.
    Derived classes implement different communication channels.
    """

    def contactOperator(self, workflowID, jobID, msgBody):
        """
        Contact operator.
        :param: str workflowID: unique workflow ID
        :param: str jobID: unique jobID
        :param: str msgBody: message to operator. Recomended to store all paramaters into dictionary and convert dictionary into json string representation.
        """
        pass

    def checkOperatorResponse(self, workflowID, jobID):
        """
        Check operator response and return received data
        :param: str workflowID: unique workflow ID
        :param: str jobID: unique jobID
        :return: tuple (ret, Data), where ret is False if response not received, True otherwise and Data contains the operator response.
        :rtype: (bool, str)
        """
        return False, None


class OperatorEMailInteraction(OperatorInteraction):
    """
    Derived class implementing different communication channels.
    """

    def __init__(self, From, To, smtpHost, smtpUser='', smtpPsswd='', smtpSSL=False, smtpTLS=False, smtpPort=25, imapHost='', imapUser='', imapPsswd='', imapPort=993, imapSSL=True):
        """
        Constructor setting up communication channels.
        :param: str From: email address where the response will be send to
        :param: str To: email address of the operator
        :param: str smtpHost: internet address of SMTP server for sending a message
        :param: str smtpUser: username for authentication on SMTP server
        :param: str smtpPsswd: optional string of SMTP authentication. If empty, it will ask
        :param: bool smtpSSL: if SSL encryption on STMP server should be used
        :param: bool smtpTLS: if TLS mode of IMAP server should be used
        :param: int smtpPort(int): port of SMTP server
        :param: str imapHost: IMAP server where the response is stored
        :param: str imapUser: IMAP user where the response is stored
        :param: str imapPsswd: optional string of IMAP user's password. If empty, it will ask
        :param: int imapPort: port of IMAP server
        :param: bool imapSSL: if SSL encryption on IMAP server should be used
        """
        self.From = From
        self.To = To
        self.smtp_tlsMode = smtpTLS
        self.smtp_sslMode = smtpSSL

        # smtp server 
        self.smtp_server = smtpHost
        self.smtp_serverPort = smtpPort
        self.smtp_username = smtpUser
        self.smtp_passwd = smtpPsswd  # if empty, then interactive input

        # imap server, ssl connection only
        self.imap_server = imapHost
        self.imap_serverPort = imapPort
        self.imap_username = imapUser
        self.imap_passwd = imapPsswd  # if empty, then interactive input
        self.imap_sslMode = imapSSL

    def contactOperator(self, workflowID, jobID, msgBody):
        """
        Sends an email to the operator.
        :param: str workflowID: unique workflow ID
        :param: str jobID: unique jobID
        :param: str msgBody: message from operator. The message should contain an empty dictionary entry which should be filled
        """
        log.info("Sending email to an operator using %s:%d" % (self.smtp_server, self.smtp_serverPort))
        if self.smtp_sslMode:
            server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_serverPort)
        else:
            server = smtplib.SMTP(self.smtp_server, self.smtp_serverPort)
        
        if self.smtp_tlsMode:
            server.starttls()
            # re-identify ourselves as an encrypted connection
            server.ehlo()
        # server.set_debuglevel(1)
        log.info("Logging to SMTP server")
        
        if self.smtp_username:
            if self.smtp_passwd:
                psswd = self.smtp_passwd
            else:
                psswd = getpass.getpass('Enter smtp server passwd: ')
            server.login(self.smtp_username, psswd)
        
        msg = MIMEMultipart()
        msg['From'] = self.From
        msg['To'] = self.To
        msg['Subject'] = workflowID+jobID
        msg.attach(MIMEText(msgBody, 'plain'))
        server.sendmail(self.From, self.To, msg.as_string())
        log.info("Email sent to operator as %s" % msg.as_string())
        server.quit()

    def checkOperatorResponse(self, workflowID, jobID):
        """
        Check IMAP server if there is operator's response.
        :param: str workflowID: unique workflow ID
        :param: str jobID: unique jobID
        :return: tuple of bool confirming existence of the message and body of the message
        :rtype: bool, str
        """
        log.info("Checking Imap4 server %s on port %s" % (self.imap_server, self.imap_serverPort))
        textBody = ''
        if self.imap_sslMode:
            server = imaplib.IMAP4_SSL(self.imap_server, self.imap_serverPort)
        else:
            server = imaplib.IMAP4(self.imap_server, self.imap_serverPort)
            
        if self.imap_passwd:
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

        criteria = "Subject %s" % (workflowID+jobID)
        log.info("Searching for message with %s" % criteria)
        typ, data = server.search(None, criteria)
        uids = data[0].split()
        log.info("Found %d messages as %s, taking only the first one" % (len(uids), uids))
        
        if len(uids):
            # print (uid)
            uid = uids[0]  # take the first message
            result, data = server.fetch(uid, '(RFC822)')  # fetch entire message

            msg = email.message_from_bytes(data[0][1])

            if result != 'OK':
                log.error("Error getting message %d", uid)
                return False, msg

            msg_type = msg.get_content_maintype()
            textBody = ''
            if msg_type == 'multipart':
                for part in msg.get_payload():
                    if part.get_content_maintype() == 'text':
                        textBody = part.get_payload()
            elif msg_type == 'text':
                textBody = msg.get_payload()
            
            # print ('New message :::::::::::::::::::::')
            # print (textBody)
            retCode = True
        else:
            retCode = False
            
        server.logout()
        return retCode, textBody
