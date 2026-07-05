import smtplib
import dns.resolver

def verify_email(email):
    domain = email.split('@')[1]
    try:
        records = dns.resolver.resolve(domain, 'MX')
        mxRecord = records[0].exchange
        mxRecord = str(mxRecord)
        
        server = smtplib.SMTP(timeout=5)
        server.set_debuglevel(0)
        server.connect(mxRecord)
        server.helo(server.local_hostname)
        server.mail('prachichoudhary.jun@gmail.com')
        code, message = server.rcpt(str(email))
        server.quit()
        
        if code == 250:
            return True
        else:
            return False
    except Exception as e:
        print("Error:", e)
        return False

print("johnabcd@gmail.com (fake):", verify_email("johnabcd@gmail.com"))
print("prachichoudhary.jun@gmail.com (real):", verify_email("prachichoudhary.jun@gmail.com"))
