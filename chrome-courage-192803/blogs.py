import webapp2
import logging
import jinja2
import os
import re
from google.appengine.ext import db
import hmac
import random
import string
import hashlib
import time

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)

# Method to pass user id and hash value with a secret seed
# used to set cookie on client browser
SECRET = 'kigdc@lkkjy9VV56%#&hhfr;lkuiad0976bvdu?'


def make_secure_val(val):
    return "%s|%s" % (val, hmac.new(SECRET, val).hexdigest())


def check_secure_val(secure_val):
    val = secure_val.split("|")[0]
    if secure_val == make_secure_val(val):
        return val


def make_salt():
    # Method to hash username and password and a random salt to
    # make rainbow table lookups harder.
    return ''.join(random.choice(string.letters) for x in xrange(5))


def make_pw_hash(name, pw, salt=None):
    if not salt:
        salt = make_salt()
    hash = hashlib.sha256(name + pw + salt).hexdigest()
    return "%s,%s" % (salt, hash)


def valid_pw(name, pw, h):
    salt = h.split(",")[0]
    return h == make_pw_hash(name, pw, salt)


def users_key(group='default'):
    return db.Key.from_path('users', group)


# Basis webapp2 request handler
class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))


# DB model for user class
class User(db.Model):
    # class object representing the users using the blog site
    name = db.StringProperty(required=True)
    pw_hash = db.StringProperty(required=True)
    email = db.StringProperty()

    @classmethod
    # class method to instantiate user based on key
    def by_id(cls, user_id):
        return User.get_by_id(user_id, parent=users_key())

    # class method to find if users exists with the same
    # user name, used before user is registered.
    @classmethod
    def by_name(cls, name):
        # Return user object that matches passed name variable
        q = User.gql("WHERE name="+"'%s'" % (name))
        if q.count() > 0:
            return q[0]

    # Store signup data to database (google data store user table)
    # password and user and a random salt is converted to a hash
    # and the salt and hash is stored in pw_hash attribute.
    @classmethod
    def register(cls, name, pw, email=None):
        pw_hash = make_pw_hash(name, pw)
        user = User(parent=users_key(),
                    name=name,
                    pw_hash=pw_hash,
                    email=email)
        user.put()
        return user

    # locate if a user exists by that name. then,
    # verify if user name and password match hash, and if passed,
    # set the logged in user object to the handler instance.
    @classmethod
    def login(self, name, pw):
        user = User.by_name(name)
        if user:
            valid = valid_pw(name, pw, user.pw_hash)
            if valid:
                return user


# DB model for Blogs and additional class methods
# like lookup by id is defined here.
# I could have moved delete and add also here, but
# it was already defined outside so it was not moved.
class Blog(db.Model):
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    author = db.StringProperty(required=True)

    @classmethod
    # class method to instantiate blog based on key
    def by_id(cls, blogid):
        return Blog.get_by_id(long(blogid), parent=None)


# Comments class methods and db model defined here.
class Comment(db.Model):
    blog = db.ReferenceProperty(Blog,
                                collection_name='comments')
    content = db.TextProperty(required=True)
    username = db.StringProperty(required=True)

    @classmethod
    def add(cls, blogid, content, username):
        blog = Blog.by_id(blogid)
        if blog:
            comment = Comment(blog=blog, content=content, username=username)
            comment.put()
            time.sleep(0.25)
            return comment
        # return True

    @classmethod
    def by_id(cls, commentid):
        return Comment.get_by_id(commentid, parent=None)

    @property
    def commentid(self):
        # comment = Comment.get_by_id(commentid, parent=None)
        return str(self.key().id())


# Like class methods
class Like(db.Model):
    blog = db.ReferenceProperty(Blog,
                                collection_name='likes')
    username = db.StringProperty(required=True)

    @classmethod
    def add(cls, blogid, username):
        blog = Blog.by_id(blogid)
        if blog:
            # used a unique key_name to ensure user can
            # like a blog only once
            like = Like(blog=blog, username=username,
                        key_name=str(blogid)+'.'+username)
            like.put()
            time.sleep(0.25)
            return like
        # return True

    @classmethod
    def by_name(cls, username):
        # Return user object that matches passed name variable
        q = Like.gql("WHERE username="+"'%s'" % (username))
        if q.count() > 0:
            return q[0]


# This class will be called by other handlers
# Users logged in status will be tracked on
# all user actions.  Common logout and login
# actions are defined here.
class SecureHandler(Handler):
    loggedin = False

    def set_secure_cookie(self, name, val):
        cookie_val = make_secure_val(val)
        cookie_string = str("%s=%s; Path=/" % (name, cookie_val))
        self.response.headers.add_header('Set-Cookie', cookie_string)

    def read_secure_cookie(self, name):
        secure_cookie = self.request.cookies.get(name)
        # if secure cookie was received and if the value|hash
        # passes security validations then return the value
        return secure_cookie and check_secure_val(secure_cookie)

    def verify_logged_in_status(self):
        if not self.loggedin:
            self.redirect("/login")

    def login(self, user):
        self.loggedin = True
        self.set_secure_cookie('user_id', str(user.key().id()))

    def logout(self):
        self.loggedin = False
        self.response.headers.add_header('Set-Cookie', 'user_id=;Path=/')

    def initialize(self, *args, **kwargs):
        # Overriding __init__()  To override the
        # webapp2.RequestHandler.__init__() method, we call
        # webapp2.RequestHandler.initialize() at the beginning of the method.
        webapp2.RequestHandler.initialize(self, *args, **kwargs)
        user_id = self.read_secure_cookie('user_id')
        if user_id and user_id.isdigit():
            user = User.by_id(int(user_id))
            if user:
                self.user = user
                self.loggedin = True
            else:
                self.logout

    # While initiailizing pass the user name and logged in status to
    # template rendering common to all pages using base template.
    def render(self, template, **kw):
        if self.loggedin:
            name = self.user.name
        else:
            name = ""
        self.write(self.render_str(template, **dict(kw, loggedin=self.loggedin,
                                   username=name)))


class SignupHandler(SecureHandler):
    # Initial request for signup page entry point
    def get(self):
        self.render('signup.html')

    # Signup form submission enry point
    def post(self):
        signup_errors = {}
        username = self.request.get("username")
        password = self.request.get("password")
        verify = self.request.get("verify")
        email = self.request.get("email")

        signup_errors = self.validate_signup(username, password, verify, email)

        if signup_errors['status'] == 'OK':
            if User.by_name(username):
                signup_errors['username_error'] = """A user with
                                                that name exists"""
                self.logout()
                self.render('signup.html', **signup_errors)
            else:
                user = User.register(username, password, email)
                if user:
                    self.login(user)
                    self.redirect("/welcome")
                else:
                    signup_errors['username_error'] = """Unknown error while
                                                    registering."""
                    self.logout()
                    self.render('signup.html', **signup_errors)
        else:
            self.render('signup.html', **signup_errors)

    # Ensure name, password, email on signup meets complexity rules
    # if security rules are violated, send back with error message
    def validate_signup(self, username, password, verify, email):
        signup_errors = {}
        username_pattern = "^[a-zA-Z0-9_-]{3,20}$"
        password_pattern = "^.{3,20}$"
        email_pattern = "^[\S]+@[\S]+.[\S]+$"

        username_error = ''
        password_error = ''
        verify_error = ''
        email_error = ''
        status = 'OK'

        if not re.match(username_pattern, username):
            username_error = "That's not a valid user name"
        if not re.match(password_pattern, password):
            password_error = "That was not a valid password"
        elif password != verify:
            verify_error = "Your passwords didn't match"
        if email and not re.match(email_pattern, email):
            email_error = "That's not a valid email"

        signup_errors['username'] = username
        signup_errors['password'] = password
        signup_errors['verify'] = verify
        signup_errors['email'] = email
        signup_errors['username_error'] = username_error
        signup_errors['password_error'] = password_error
        signup_errors['verify_error'] = verify_error
        signup_errors['email_error'] = email_error

        if username_error or password_error or verify_error or email_error:
            status = 'ERRORS'

        signup_errors['status'] = status

        return signup_errors


# Landing page after login
class WelcomeHandler(SecureHandler):
    def get(self):
        if not self.loggedin:
            self.redirect("/login")
        else:
            self.render('welcome.html', user=self.user.name)


# logout and remove user id and hash key
# send user back to login page
class LogoutHandler(SecureHandler):
    def get(self):
        self.logout()
        self.redirect("/login")


# Verify user passed correct
# user name and password and if pass
# redirect to welcome page.
class LoginHandler(SecureHandler):
    def get(self):
        self.logout()
        self.render('login.html')

    def post(self):
        name = self.request.get("name")
        pw = self.request.get("pw")

        if name and pw:
            error = ""
            user = User.login(name, pw)
            if user:
                self.login(user)
                self.redirect("/welcome")
            else:
                error = "Invalid user name or password"
                self.render('login.html', error=error)
        else:
            error = "We need both user name and password"
            self.render('login.html', error=error)


# Primary class to display all blogs
# Most recent 10 blog posts with
# most recent on top.
class BlogList(SecureHandler):
    def get(self):
        if not self.loggedin:
            self.redirect("/login")
        else:
            self.list_blogs()

    def list_blogs(self):
        blogs = db.GqlQuery("SELECT * FROM Blog "
                            "ORDER BY created desc LIMIT 10")
        self.render('blog_list.html', blogs=blogs, user=self.user)


# Handle new or edit blog requests
class NewBlog(SecureHandler):
    def get(self):
        if not self.loggedin:
            self.redirect("/login")
        else:
            self.new_blog()

    # Edit blog (with existing blog id) or
    # New blog creation requests are redirected
    # to blog_newpost.html template. Edit requests
    # will show existing values.
    def new_blog(self, subject="", content="", error="", blogid=""):
        blogid = self.request.get("blogid")
        if blogid and blogid.isdigit():
            id = long(blogid)
            a = Blog.by_id(id)
            if a:
                subject = a.subject
                content = a.content
        self.render('blog_newpost.html', subject=subject, content=content,
                    error=error, user=self.user, blogid=blogid)

    # Form submissions from New Blog post page is handled here
    # Blogs are either created or edited, gets saved to DB here.
    def post(self):
        if not self.loggedin:
            self.redirect("/login")
        else:
            subject = self.request.get("subject")
            content = self.request.get("content")
            blogid = self.request.get("blogid")
            author = self.user.name

            if subject and content:
                error = ""
                if blogid:
                    # Edits to blogs are saved here
                    id = int(blogid)
                    a = Blog.by_id(id)
                    if a:
                        a.subject = subject
                        a.content = content
                        a.put()
                        # Delay to ensure DB save completes
                        # before redirect
                        time.sleep(0.25)
                        self.redirect("/blog/"+str(id))
                else:
                    # New Blogs are added and user redirected to
                    # individual post page
                    a = Blog(subject=subject, content=content, author=author)
                    a.put()
                    id = a.key().id()
                    self.redirect("/blog/"+str(id))
            else:
                error = "We need both subject and content"
                self.new_blog(subject, content, error)


# Display blog readonly (redirect here upon new blog
# or edit blog completion), or Add/Edit comments.
class BlogById(SecureHandler):
    def get(self, blogid):
        if not self.loggedin:
            self.redirect("/login")
        else:
            if blogid and blogid.isdigit():
                self.display_blog(blogid)
            else:
                self.redirect("/blog")

    # method to show a page for each blog id
    # and also allowing users to add brand new
    # comments.  This will also handle the
    # Edit comment and Delete comment buttons from
    # individual blog post and blog listing pages.
    def display_blog(self, blogid=""):
            blogid = long(blogid)
            blog = Blog.by_id(blogid)
            if blog:
                subject = blog.subject
                content = blog.content
                created = blog.created
                editcommentid = self.request.get("editcommentid")
                deletecommentid = self.request.get("deletecommentid")

                # if the query parameter has a deletecomment id passed
                # delete the comment and redirect back.
                if deletecommentid:
                    self.delete_comment(blogid=blogid,
                                        commentid=deletecommentid)
                else:
                    self.render('blog_byId.html', subject=subject,
                                content=content,
                                created=created, user=self.user, blog=blog,
                                editcommentid=editcommentid)

            else:
                self.redirect("/blog")

    # Form submission with new or modified comments is handled first here
    def post(self, blogid=""):
        if not self.loggedin:
            self.redirect("/login")
        else:
            if blogid and blogid.isdigit():
                blogid = long(blogid)
                self.add_comment(blogid=blogid)
            else:
                self.redirect("/blog")

    # Method to handle requests to add new or edit existing comments
    def add_comment(self, blogid="", commentid="", content=""):
        commentid = self.request.get("commentid")
        content = self.request.get("comment")
        username = self.user.name

        if content:
            if commentid and commentid.isdigit():
                # Existing comments are edited
                # if a comment id (key id) of comment
                # is passed as a query parameter.
                id = long(commentid)
                a = Comment.by_id(id)
                if a:
                    a.content = content
                    a.put()
                    time.sleep(0.25)
                    self.redirect("/blog/"+str(blogid))
            else:
                # New comments are saved
                comment = Comment.add(blogid=blogid, content=content,
                                      username=username)
                if comment:
                    self.redirect("/blog/"+str(blogid))
                else:
                    self.redirect("/blog")
        else:
            self.redirect("/blog")

    # Method to delete a comment based on blogid, commentid
    def delete_comment(self, blogid="", commentid=""):
        commentid = long(commentid)
        comment = Comment.by_id(commentid)
        if comment:
            comment.delete()
            # delay to ensure save is completed before redirect.
            time.sleep(0.25)
            self.redirect("/blog/"+str(blogid))


# Save to DB blog likes, and redirect back.
class LikeHandler(SecureHandler):
    def get(self):
        if not self.loggedin:
            self.redirect("/login")
        else:
            blogid = self.request.get("blogid")
            # Redirect user back to source page
            referralurl = self.request.get("referralurl")
            if blogid and blogid.isdigit():
                self.add_like(blogid=blogid, referralurl=referralurl)

    # Method to add likes.
    # The key name of blogid.username will ensure
    # user can only save their like once for each blog post.
    def add_like(self, blogid="", username="", referralurl=""):
        username = self.user.name
        like = True
        like = Like.add(blogid=blogid, username=username)
        if like:
            self.redirect(referralurl)


# Delete blogs based on blog id passed as a query parameter
class DeleteBlogHandler(SecureHandler):
    def get(self):
        if not self.loggedin:
            self.redirect("/login")
        else:
            blogid = self.request.get("blogid")
            if blogid and blogid.isdigit():
                self.delete_blog(blogid=blogid)

    # delete method
    def delete_blog(self, blogid=""):
        blogid = long(blogid)
        blog = Blog.by_id(blogid)
        if blog:
            blog.delete()
            # ensure insert has soome time to complete before redirect
            time.sleep(0.25)
            self.redirect('/blog')


# Custom message for 404 errors.
def handle_404(request, response, exception):
    logging.exception(exception)
    response.write('Oops! We do not have this page!<br><br>-Team 404')
    response.set_status(404)


# all the web request handlers.  Additional rules in app.yaml.
app = webapp2.WSGIApplication([
        (r'/blog', BlogList),
        (r'/blog/', BlogList),
        (r'/blog/newpost', NewBlog),
        (r'/blog/(\d+)', BlogById),
        (r'/welcome', WelcomeHandler),
        (r'/signup', SignupHandler),
        (r'/login', LoginHandler),
        (r'/', LoginHandler),
        (r'/logout', LogoutHandler),
        (r'/like', LikeHandler),
        (r'/deleteblog', DeleteBlogHandler),
        ], debug=True)

app.error_handlers[404] = handle_404
