# Kamailio header smuggling demonstration

Docker-compose environment for identifying and reproducing header smuggling issues in Kamailio. Please refer to the advisory and related blog post on the Communication Breakdown blog (rtcsec.com).

## Getting started

Ensure that you have installed docker-compose. Then run `docker-compose up`.

## Reproducing the finding

Make use of `quickdemo.py` to reproduce the vulnerability. To simulate finding the vulnerability, run `find-bypass.py`.

## Other files

`inviterequest.tpl` is to be used with [SIPVicious PRO](https://sipvicious.pro) as the SIP template to reproduce this issue.

