# Check Point CEF Add On For Splunk
**August 2018**


## Table of Contents

### OVERVIEW

- About Check Point CEF Add On For Splunk
- Release notes
- Prerequisites and requirements
- Support and resources

### INSTALLATION

- Hardware and OS requirements
- Installation steps
- Deployment

### USER GUIDE

- Check Point Configuration 
    * Configure syslog export 


---
### OVERVIEW

#### About Check Point Block Alert Action For Splunk

| Author | Tom Kopchak, Hurricane Labs |
| --- | --- |
| App Version | 1.0.1 |
| Vendor Products | Check Point |
| Has index-time operations | true |
| Create an index | false |
| Implements summarization | false |

The Check Point CEF Add On For Splunk provides knowledge objects to allow for the Check Point Log Exporter to function within Splunk.  This replaces the traditional method of using OPSEC LEA for collecting this data.  

This app supports the new Log Exporter method for Check Point logging.  This resolves several limitations of the OPSEC LEA method:
- A Linux heavy forwarder is no longer required for bringing in Check Point logs.  All Splunk platforms are supported. 
- The OPSEC LEA forwarder is no longer a single point of failure for Check Point logging.  This method supports all syslog redundancy mechanisms. 
- There is not a gap in logging that occurs during a logrotate on the management server (this commonly resulted in missing logs occuring daily at midnight). 

#### Release notes

Version 1.0.1 is the second release. It adds support for audit logging and contains minor edits to version 1.0.0. 

##### About this release

Version 1.0.1 of the Check Point CEF Add On For Slunk For Splunk is compatible with:

| Splunk Enterprise versions | 6.6, 7.0, 7.1 |
| --- | --- |
| Platforms | Platform independent |
| Vendor Products | Check Point Management Server, Check Point R77.30, R80.10, R80.20 |
| Vendor Tools | Log Exporter - Check Point Log Export (see sk122323) |
| Lookup file changes | None |

##### Prerequisites and Requirements

This app requires that the Check Point management server controlling gateways be running a version which supports the Check Point Log Exporter, which is documented in sk122323.  At the time of this writing, this includes versions R77.30, R80.10 and R80.20.  Gateways do not necessarily need to be running a version supporting the Log Exporter as long as they are centrally logging to a managment server or log server capable of running the Log Exporter.


##### Support

TO DO: App to become officially Splunk supported, Hurricane Labs will transfer ownership of app to Splunk for this purpose. 

## INSTALLATION AND CONFIGURATION

### Hardware and software requirements

#### Hardware requirements

Check Point CEF Add On For Splunk supports the following server platforms in the versions supported by Splunk Enterprise:

- Platform independent (knowledge objects only)

#### Splunk Enterprise system requirements

Because this add-on runs on Splunk Enterprise, all of the [Splunk Enterprise system requirements](http://docs.splunk.com/Documentation/Splunk/latest/Installation/Systemrequirements) apply.

#### Installation steps

Note: it is recommended that a dedicated syslog receiver (such as syslog-ng) be used to collect the data associated with this app, as opposed to a direct TCP/UDP input in Splunk. TCP is recommended over UDP for this data input. 

#### Check Point configuration

**Install Log Exporter**

1. Follow the installation instructions for your version of Check Point detailed in sk122323.  
2. After completing the Splunk configuration below, configure the Log Exporter to forward logs to your Splunk environment.  CEF format should be specified in the cp_log_export command.

### Single-instance
**Install to search head**

1. Install the app.
2. Configure Splunk to receive and ingest the syslog data from the Check Point management server, as appropriate in your environment. 

### Distributed
**Install to search head and the first Splunk Enterprise system to receive data**

The app has index-time sourcetyping operations.  This app should be deployed to your search head as well as the first Splunk Enterprise system to receive your data.  If you are reciving syslog on a Universal Forwarder, this app should be installed on the indexing tier.  If you are receiving syslog on a Heavy Forwarder, this app should be installed on the Heavy Forwarder.

1. Install the app.
2. Configure Splunk to receive and ingest the syslog data from the Check Point management server, as appropriate in your environment.


#### Known Issues
- Several field extractions are currently untested


#### Acknowledgements
- App is written to mirror functionality in the Splunk Add-on for Check Point OPSEC LEA, https://splunkbase.splunk.com/app/3197/
- CEF processing is based on Igor Sher's CEF Extraction Add-on for Splunk app, https://splunkbase.splunk.com/app/487/
