#! /usr/bin/python3.5

# coding: UTF8

import re
import sys
import getopt
import subprocess
import os
import shlex

apache_conf_path = "/etc/httpd/conf/"
apache_conf = apache_conf_path + 'httpd.conf'
apache_conf_includes = apache_conf_path + 'includes/'
includes_conf = apache_conf_includes + "post_virtualhost_global.conf"
certbot_script = "/etc/letsencrypt/certbot-auto"
certbot_url = 'https://dl.eff.org/certbot-auto'
auto_renew_script = '/etc/cron.daily/renew_script_linux.sh'
auto_renew_url = 'https://raw.githubusercontent.com/besco/le-update/master/renew_script_linux.sh'

dry_mode = True


def certbot_dl(filename, url):
    dir = os.path.dirname(filename)

    try:
        print("Checking for " + dir + ": ", end="")
        os.stat(dir)
    except:
        print("failed. Creating dir")
        os.makedirs(dir)
    else:
        print("ok")

    try:
        print("Checking for " + filename + ": ", end="")
        f = open(filename, "r")
        f.close()
    except:
        print("failed. File not exist. Downloading. ")
        cmd = 'wget --directory-prefix=' + dir + ' ' + url
        ret = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        rc = ret.returncode
        if ret.returncode != 0:
            print("Something went wrong. Check errors and try again. Wget return code: " + str(
            ret.returncode))
            print("Output:")
            print(ret.stderr.decode("utf-8"))
            sys.exit(rc)
        else:
            print("Download complete")
            ret = subprocess.run(shlex.split('chmod +x ' + filename), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if ret.returncode != 0:
                print("Something went wrong. Check errors and try again. Chmod return code: " + str(
                ret.returncode))
                print("Output:")
                print(ret.stderr.decode("utf-8"))
                sys.exit(rc)
    else:
        print("ok")


def readfile(ifile):
    vhosts = list()
    try:
        f = open(ifile, 'r')
    except:
        print("File " + ifile + " not found or permissions denied.")
        sys.exit(3)
    while True:
        line = f.readline()
        if not line:
            break
        if re.match('<VirtualHost', line):
            vhosts.append(get_virtual_host(f, line))
    f.close()
    return vhosts


def get_virtual_host(filelink, line):
    i = 0
    lines = list()
    vhost = dict()
    vhost_config = dict()
    server_alias = list()
    server_name = ""
    server_docroot = ""

    lines.append(line.strip('\n'))
    while not re.match('</VirtualHost', line):
        line = filelink.readline()
        lines.append(line.strip('\n'))
        if line.strip(" \n").split(" ")[0] == "ServerName":
            server_name = line.strip(" \n").split(" ")[1]
        if line.strip(" \n").split(" ")[0] == "DocumentRoot":
            server_docroot = line.strip(" \n").split(" ")[1]
        if line.strip(" \n").split(" ")[0] == "ServerAlias":
            server_alias = line.strip(" \n").split(" ")
            server_alias.pop(0)
        i += 1

    vhost["config"] = lines
    vhost["name"] = server_name
    vhost["aliases"] = server_alias
    vhost["docroot"] = server_docroot
    vhost_config[server_name] = vhost
    return vhost_config


def main(argv):
    action = ''
    email = ''
    script_filename = os.path.basename(sys.argv[0])

    def print_usage():
        print("")
        print("Usege " + script_filename + " with parametres:")
        print("  For create new certs:")
        print("    " + script_filename + " --create --email=admin@doman.com -d domain1.tld www.domain2.tld subdomain.domain3.tld")
        #print("  For create new certs:")
        #print("    " + script_filename + " --renew")
        print("")

    if len(argv) == 0:
        print("Error! Not enough parameters")
        print_usage()
        sys.exit(2)

    domain_list = readfile(apache_conf)
    certbot_dl(certbot_script, certbot_url)
    certbot_dl(auto_renew_script, auto_renew_url)

    try:
       opts, args = getopt.getopt(argv, 'd', ['create', 'renew', 'email='])
    except getopt.GetoptError:
        print("Error! Unknown parameters")
        print_usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in '--email':
            email = arg
        if opt in '--create':
            action = 'create'
        elif opt in "--renew":
            action = "renew"

    if action == 'create':
        list_for_create = find_domains(args, domain_list)
        if len(list_for_create) != 0:
           rc, status = create_cert(list_for_create, email)
           print("Create certs:", status)
        else:
           rc = -1
        sys.exit(rc)
    elif action == "renew":
        rc = renew_cert()
        sys.exit(rc)
    else:
        print("Error! Not enough parameters")
        print_usage()
        exit(2)


def find_domains(args, domainlist):
    ret = list()
    for arg in args:
        for vdomain in domainlist:
            if arg not in vdomain:
                for host in vdomain:
                    if arg in vdomain[host]['aliases']:
                        ret.append(vdomain[host])
            else:
                ret.append(vdomain[arg])
        if len(ret) == 0:
          print("Domain "+arg+" not found in apache config file")
    return ret


def create_cert(dlist, email, status="ok"):
    rc = '-1'
    if dry_mode:
        dryrun = '--dry-run'
        print("Cert-bot will run in dry mode. Set dry_mode to false at the beginning of this script. Certificates will not be generated.")
    else:
       dryrun = ''
    if '@' not in email:
        print("Error in email: " + email)
        sys.exit(2)
    else:
        if len(dlist) != 0:
            for i in range(len(dlist)):
               dom_cmd = '-d ' + ' -d '.join(dlist[i]['aliases'])
               docroot_cmd = '-w ' + dlist[i]['docroot']
               cmd = './certbot-auto certonly ' + dryrun + ' --dry-run --agree-tos --email ' + email + ' --webroot ' + docroot_cmd + ' ' + dom_cmd
               ret = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
               rc = ret.returncode
               # change me
               if ret.returncode != 0:
                   print(dlist[i]['name'] + ": Something went wrong. Check errors and try again. Certbot-auto return code: " + str(ret.returncode))
                   print("Output:")
                   print(ret.stderr.decode("utf-8") )
                   status = "failed"
               else:
                   rc = 0
                   status = write_config(dlist[i])
        else:
            rc = 1
            status = "Failed. Domains not found " + " - ".join(dlist)
        return rc, status


def renew_cert(status = "ok"):
    cmd = 'certbot-auto renew'
    rc = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if rc.returncode != 0:
        print("Something went wrong. Check errors and try again. Certbot-auto return code: " + str(rc.returncode))
        print("Output:")
        print(rc.stderr)
    return rc.returncode, status


def write_config(domain):
    ssl_conf = """
  SSLEngine on
  SSLOptions +StrictRequire
  SSLProtocol -all +TLSv1 +TLSv1.1 +TLSv1.2
  SSLCipherSuite EECDH+AESGCM:EDH+AESGCM:AES256+EECDH:ECDHE-RSA-AES128-SHA:DHE-RSA-AES128-GCM-SHA256:AES256+EDH:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GC$

  SSLCertificateFile /etc/letsencrypt/live/""" + domain['aliases'][0] + """/fullchain.pem
  SSLCertificateKeyFile /etc/letsencrypt/live/""" + domain['aliases'][0] + """/privkey.pem

  SSLVerifyClient none
  SSLProxyEngine off

  AddType application/x-x509-ca-cert .crt
  AddType application/x-pkcs7-crl .crl
  """
    domain['config'][0] = domain['config'][0].replace(":80", ":443")

    for x in reversed(ssl_conf.split("\n")):
        domain['config'].insert(1, x)

    try:
        f = open(apache_conf_includes + "ssl_" + domain['name'] + ".conf", 'w')
        f.write('\n'.join(domain['config']))
        f.close()
    except:
        return 255, "Error: can't open " + apache_conf_includes + "ssl_" + domain['name'] + ".conf"

    try:
        f = open(includes_conf,"a")
        f.write("\nInclude \"" + apache_conf_includes + "ssl_" + domain['name'] + ".conf" + "\"\n")
        f.close()
    except:
        return 255, "Error: can't open " + apache_conf

    return "ok"


if __name__ == "__main__":
    main(sys.argv[1:])
