import smtplib
from email.mime.text import MIMEText
from email.header import Header

def SendMail(mail_content, sender, passwd) :
    try:
        message = MIMEText(mail_content, 'plain', 'utf-8')
        message['From'] = Header("EPC选课通知", 'utf-8')   # 发送者
        message['To'] =  Header("EPC选课通知", 'utf-8')     # 接收者
        message['Subject'] = Header('EPC', 'utf-8')
        
        mail_host = "mail.ustc.edu.cn"
        server = smtplib.SMTP(mail_host, 25)
        server.login(sender, passwd)

        server.sendmail(sender, [sender], message.as_string())
        server.quit()
    except smtplib.SMTPException:
        print("Send Email Failed")