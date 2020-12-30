Apr 12 14:49:53 ##hostname## usermod[##number##]: change user '##user##' password
Apr 17 15:28:10 ##hostname## sshd[##number##]: pam_unix(sshd:auth): check pass; user ##user##
Apr 16 08:42:20 ##hostname## sshd[##number##]: Invalid user ##user## from ##ip##
Apr 14 07:02:58 ##hostname## sshd[##number##]: Failed password for ##user## from ##ip## port ##ipport## ssh2
Apr 14 07:07:23 ##hostname## sshd[##number##]: pam_unix(sshd:auth): authentication failure; logname= uid=0 euid=0 tty=ssh ruser= rhost=##ip##
Apr 13 19:24:16 ##hostname## sshd[##number##]: pam_unix(sshd:auth): authentication failure; logname= uid=0 euid=0 tty=ssh ruser= rhost=##rhost_domain##  user=##user##
Apr 16 08:42:07 ##hostname## sshd[##number##]: Failed password for invalid user ##user## from ##ip## port ##ipport## ssh2
Apr 29 14:53:59 ##hostname## sshd[##number##]: [ID ##number## auth.info] Failed publickey for ##user## from ##ip## port ##ipport## ssh2
Apr 16 14:05:40 ##hostname## sshd[##number##]: Accepted password for ##user## from ##ip## port ##ipport## ssh2
Apr 13 01:48:13 ##hostname## sshd[##number##]: Did not receive identification string from ##ip##
Apr 25 06:32:30 ##user## telnetd[##number##]: gethostbyaddr: acmepayroll.acme.local. != ##ip##
Apr 16 14:05:40 ##hostname## sshd[##number##]: subsystem request for ##user##
Apr 29 14:53:59 ##hostname## sshd[##number##]: [ID ##number## auth.notice] Failed none for ##user## from ##ip## port ##ipport## ssh2
Apr 18 05:44:51 ##hostname## sshd[##number##]: reverse mapping checking getaddrinfo for ##rhost_domain##[##rhost_ip##] failed - POSSIBLE BREAK-IN ATTEMPT!
Apr 12 14:49:53 ##hostname## groupadd[##number##]: new group: name=##user##, GID=##number##
Apr 12 14:49:53 ##hostname## groupadd[##number##]: group added to /etc/group: name=##user##, GID=##number##
Apr 14 03:17:01 ##hostname## CRON[##number##]: pam_unix(cron:session): session opened for user ##user## by (uid=0)
Apr 14 20:17:01 ##hostname## CRON[##number##]: pam_unix(cron:session): session closed for user ##user##
Apr 16 12:40:44 ##hostname## sudo: ##user## : TTY=##tty## ; PWD=/home/##user## ; USER=root ; COMMAND=/bin/su -
Apr 12 12:19:21 ##hostname## sudo:  ##user## : TTY=##tty## ; PWD=##pwd## ; USER=root ; COMMAND=##command##
May 25 08:56:40 ##hostname## ftpd[##number##]: [ID ##number## daemon.info] USER ##user##
May 25 08:56:40 ##hostname## ftpd[##number##]: [ID ##number## daemon.info] USER ##user##
Jun 10 12:17:50 ##hostname## proftpd[##number##]: ##rhost_domain## (##rhost_ip##[##rhost_ip##]) - USER ##user##: no such user found from ##ip## [##rhost_ip##] to ##ip##:21
Apr 12 14:49:53 ##hostname## chage[##number##]: changed password expiry for ##user##
Apr 16 13:24:52 ##hostname## su[##number##]: + /dev/pts/1 ##user##:##user##
Apr 14 08:07:39 ##hostname## su[##number##]: Successful su for ##user## by ##user##
Oct 14 08:51:23 ##ip## auth|security:crit su: [ID ##number## auth.crit] 'su ##user##' failed for ##user## on /dev/pts/##number##
Oct 14 08:55:59 ##ip## auth|security:notice login: [ID ##number## auth.notice] Login failure on /dev/pts/##number## from ##ip## 
Oct 14 08:42:39 ##rhost_ip## auth|security:info su: [ID ##number## auth.info] 'su ##user##' succeeded for ##user## on /dev/???
Apr 12 14:49:53 ##hostname## useradd[##number##]: new user: name=##user##, UID=##number##, GID=##number##, home=/home/##user##, shell=/bin/false
Apr 14 08:07:39 ##hostname## su[##number##]: pam_unix(su:session): session opened for user ##user## by ##user##(uid=0)