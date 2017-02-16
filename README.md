# letsenc_cpanel
Script for automatic creation let's encrypt certs and configs for cpanel's apache

====== Automatic installation ======
Download [[https://raw.githubusercontent.com/besco/letsenc_cpanel/master/LE_cpanel_certs.py|script]].
\\
Type commands:
<code>
wget https://raw.githubusercontent.com/besco/letsenc_cpanel/master/LE_cpanel_certs.py
chmod +x ./LE_cpanel_certs.py
./LE_cpanel_certs.py
</code>

Output after running the script
<code>
Error! Not enough parameters

Usege LE_cpanel_certs.py with parametres:
  For create new certs:
    LE_cpanel_certs.py --create --email=admin@doman.com -d domain1.tld www.domain2.tld subdomain.domain3.tld
</code>

==== How the script works ====

This script reads from config of the Apache **/etc/httpd/conf/httpd.conf** all virtual hosts and all aliases for each virtual host. If in the config there is a domain specified in the parameters, script create a certificate for all aliases of the domain. For example:
<code>
NameVirtualHost ip_addr:80
<VirtualHost ip_addr:80>
  ServerName hyperfy.zinng.com
  ServerAlias hyperfy.com mail.hyperfy.com www.hyperfy.zinng.com www.hyperfy.com
</code>
Apache config has a virtual host with the **ServerName hyperfy.zinng.com** and aliases **hyperfy.com mail.hyperfy.com www.hyperfy.zinng.com www.hyperfy.com**,the script will make the certificate for all aliases (**hyperfy.com mail.hyperfy.com www.hyperfy.zinng.com www.hyperfy.com**). The script then generates a configuration file for Apache with SSL and write it to the /etc/httpd/conf/includes/ssl_**SPECIFIED_DOMAIN**.conf and add include this file to **/etc/httpd/conf/includes/post_virtualhost_global.conf**.
\\
\\
Also, the script will download certbot script and cron script.


====== First time installation by hands ======

For first download and copy certbot-auto to /etc/letsencrypt/You want to make a certificate for a different domain?
<code>
cd /etc/letsencrypt/
wget https://dl.eff.org/certbot-auto
chmod a+x certbot-auto
</code>

then create new certificates (change path to web docroot and domains) :
<code>
/etc/letsencrypt/certbot-auto certonly --webroot -w /home/gethyper/public_html/hyperfy.com -d www.hyperfy.com -d hyperfy.com
</code>
(If you ran script first time, you must enter admin email and agree licence)

After that download script for renew certs to cron:
<code>
 cd /etc/cron.daily/
 wget https://raw.githubusercontent.com/evandiamond/le-update/master/renew_script_linux.sh
 chmod +x renew_script_linux.sh
</code>

if you use cpanel, create new config file **/etc/httpd/conf/includes/ssl_hyperfy.com.conf**, add lines (change the domain to your):
(In fact, you need to look at the configuration of the domain without SSL, that would make a similar configuration for SSL. I did just that.)
---------------------
<code>
 <VirtualHost 162.144.129.104:443>
   ServerName hyperfy.com                                 			#<------------- change it
   ServerAlias www.hyperfy.com                            			#<------------- change it
   DocumentRoot /home/gethyper/public_html/hyperfy.com    			#<------------- change it
   ServerAdmin webmaster@hyperfy.com 					 			 #<------------- change it
   UseCanonicalName Off
   CustomLog /usr/local/apache/domlogs/hyperfy.zinng.com combined  	#<------------- change it
   SSLEngine on
   SSLOptions +StrictRequire
   SSLProtocol -all +TLSv1 +TLSv1.1 +TLSv1.2
   SSLCipherSuite EECDH+AESGCM:EDH+AESGCM:AES256+EECDH:ECDHE-RSA-AES128-SHA:DHE-RSA-AES128- GCM-SHA256:AES256+EDH:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GC$
   SSLCertificateFile /etc/letsencrypt/live/www.hyperfy.com/fullchain.pem      #<------------- change it
   SSLCertificateKeyFile /etc/letsencrypt/live/www.hyperfy.com//privkey.pem    #<------------- change it
 
   SSLVerifyClient none
   SSLProxyEngine off
 
   AddType application/x-x509-ca-cert .crt
   AddType application/x-pkcs7-crl .crl
 
   <IfModule log_config_module>
     <IfModule logio_module>
       CustomLog /usr/local/apache/domlogs/hyperfy.zinng.com-bytes_log "%{%s}t %I .\n%{%s}t %O ."     #<------------- change it
     </IfModule>
   </IfModule>
   ## User gethyper # Needed for Cpanel::ApacheConf
   <IfModule userdir_module>
     <IfModule !mpm_itk.c>
       <IfModule !ruid2_module>
         UserDir enabled gethyper
       </IfModule>
     </IfModule>
   </IfModule>
 
   <IfModule include_module>
     <Directory "/home/gethyper/public_html/hyperfy.com">             #<------------- change it
       SSILegacyExprParser On
     </Directory>
   </IfModule>

   <IfModule suphp_module>
     suPHP_UserGroup gethyper gethyper
   </IfModule>
   <IfModule !mod_disable_suexec.c>
     <IfModule !mod_ruid2.c>
       SuexecUserGroup gethyper gethyper
     </IfModule>
   </IfModule>
   <IfModule ruid2_module>
     RMode config
     RUidGid gethyper gethyper
   </IfModule>
   <IfModule mpm_itk.c>
     AssignUserID gethyper gethyper
   </IfModule>
 
   <IfModule alias_module>
     ScriptAlias /cgi-bin/ /home/gethyper/public_html/hyperfy.com/cgi-bin/		#<------------- change  it
   </IfModule>
 </VirtualHost>
</code>
---------------------

Make sure that file included from the main config **/etc/httpd/conf/httpd.conf** on last line: \\
**Include "/usr/local/apache/conf/includes/ssl_hyperfy.com.conf"
**
and restart apache:
<code>
 /etc/init.d/httpd restart
</code>
