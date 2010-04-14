ITWS allows you to deploy and maintain, in an easy way, multiple websites.
Each website could be customizable by a css file throught the backoffice's
interface. ITWS offers some high level components like:
- Sitemap
- News
- Tags cloud
- Slideshow
- RSS feeds: website's global, by tag or for news
- Sidebar which could contain statical's datas like web pages or dynamical
  datas like filtered news, tag cloud, table of content, ...
- Customizable Footer with multiple content which could be ordered or
  randomized


Requirements
=============

 - itools 0.61 (http://www.hforge.org/itools)
 - ikaaro 0.61 (http://www.hforge.org/ikaaro)


Deployment
===========

$ ./path/to/python/bin/icms-init.py -r itws INSTANCE_NAME
Type your email address: admin@localhost.com

*
* Welcome to ikaaro
* A user with administration rights has been created for you:
*   username: admin@localhost.com
*   password: xxx
*
* To start the new instance type:
*   icms-start.py INSTANCE_NAME
*

$ ./path/to/python/bin/icms-start.py INSTANCE_NAME
Listen :8080
^CShutting down the server (gracefully)...

Start and detach the server
$ ./path/to/python/bin/icms-start.py -d INSTANCE_NAME
$ firefox http://localhost:8080

Go to http://localhost:8080/;new_resource?type=WebSite
Choose "neutral website"

Set the virtual host of your website
http://localhost:8080/website/;control_panel
http://localhost:8080/website/;edit_virtual_hosts
add test.localhost and submit form.

Go to
http://test.localhost:8080/
