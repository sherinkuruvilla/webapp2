# webapp2

## Udacity Web Application development Proj#3

## Blogging Application
This cloud web application allows registered and signed in users to post new blogs, edit or deleting existing blogs.
Users can like or comment on blogs by other users.  Users can only like a blog once, and cannot like their own blogs.
Users can only edit or delete their own comments.

The blog data is stored in Google Datastore on the cloud, and will persist even after system is rebooted.  The application is built using WebApp2 framework and Python. The submitted URL is publicly accessible and hosted on Google Cloud.

The application security meets industry standards, and maintain user sessions by saving a hashed secure cookie.  The password hashes are also stored securely using a random salt.

**URL:**  http://chrome-courage-192803.appspot.com  

Login: - Users with valid user name and password can login from this screen.  Once user is logged in all other pages and functionality can be accessed without additional logins.
Sign up - Click on the sign up link to obtain a user account.  You may create a few additional test accounts to verify that permissions are setup correctly.
Welcome Page - Once logged in , user will be directed to a Welcome page.  Welcome page gives likes to logout, add new blow or blog listing.
Blog Listing Pag - Click on the title CS 253 Blod to go to the Blog Listing Page.  User can like a blog, and post comments or edit/delete comments from here.
From the Blog Listing page, initially there wil be no posts.
Add New Blog - Click on add new blog, and enter Blog title and Content. The blog will be stored with author assigned as the logged in user.
Blog Details- Once a new blog is saved, user will be directed to blog by ID page.  User can like a blog, and post comments or edit/delete comments from here as well.


## Deployment and Maintenance. 

Sign up for a free Google Cloud account, and get your free basic web site setup, as per instructions on site below.
From the console launch the dashboard - https://console.cloud.google.com, locate the URL for your web site.
In my case the URL is `chrome-courage-192803.appspot.com`  
Install Google App Engine SDK from https://cloud.google.com/appengine/downloads.  
Once the installation is complete, ensure the localhost:8080 is running.

Download the Python, app.yaml and HTML tempalte source files for the website from github.

a. Browse to this github location, https://github.com/sherinkuruvilla/webapp2
b. Select the "clone or download" open and choose "Download Zip". 
c. Extract the files to your local directory
d. Verify source files. Make any necessary changes and test in localhost. 
e. Deploy using Google App Engine SDK, deploy button.

Enjoy the Blogging site!

