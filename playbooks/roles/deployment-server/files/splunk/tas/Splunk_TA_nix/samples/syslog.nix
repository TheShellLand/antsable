Apr 20 06:40:12 ##hostname## rsyslogd: [origin software="rsyslogd" swVersion="##swversion_rsyslogd##" x-pid="##xpid_rsyslogd##" x-info="##xinfo_rsyslogd##"] rsyslogd was HUPed, type '##type_rsyslogd##'.
Apr 20 07:17:01 ##hostname## CRON[##cron_number##]: (##cron_user##) CMD (   ##cron_command##)
Apr 20 09:24:29 ##hostname## ntpd[##ntpd_id##]: synchronized to ##synchronized_to_ip##, stratum 2
Apr 20 09:24:29 ##hostname## ntpd[##ntpd_id##]: kernel time sync status change ##ntpd_num##
Apr 30 18:54:07 ##hostname## ftpd[##ftpd_number##]: [ID ##ftpd_id## daemon.info] TYPE Image
Apr 30 18:54:07 ##hostname## ftpd[##ftpd_number##]: [ID ##ftpd_id## daemon.info] CWD ..
Apr 30 18:54:07 ##hostname## ftpd[##ftpd_number##]: [ID ##ftpd_id## daemon.info] CWD ccinfo
Apr 30 18:54:07 ##hostname## ftpd[##ftpd_number##]: [ID ##ftpd_id## daemon.info] FTP LOGIN FROM ##ftpd_ip## [##ftpd_ip##], ##ftpd_user##
Apr 30 12:18:51 ##hostname## syslog: 04/30/10 12:18:51 ##syslog_id## wksh: HANDLING TELNET CALL (User: ##syslog_user##, Branch: ##syslog_branch##, Client: ##syslog_client##) pid=##syslog_pid##
Apr 30 12:18:51 ##hostname## passwd: pam_unix(passwd:chauthtok): password changed for ##syslog_user##
