import re
from django.db import models
from django.core import validators
from django.utils.translation import ugettext_lazy as _
from django.utils.http import urlquote
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils import timezone


MAX_LENGTH = 255

#class LongnameUserManager(UserManager):
#    class Meta:
#        model = get_user_model()

class LongnameUser(AbstractBaseUser, PermissionsMixin):
    """
    Copy (non-abstract) of AbstractUser with longer username. Removed profile support as it
    is deprecated in django 1.5.

    Username, password and email are required. Other fields are optional.
    """
    username = models.CharField(_('username'), max_length=MAX_LENGTH, unique=True,
        help_text=_('Required. %s characters or fewer. Letters, numbers and '
                    '@/./+/-/_ characters' % MAX_LENGTH),
        validators=[
            validators.RegexValidator(re.compile('^[\w.@+-]+$'), _('Enter a valid username.'), 'invalid')
        ])
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    email = models.EmailField(_('email address'), blank=True)
    is_staff = models.BooleanField(_('staff status'), default=False,
        help_text=_('Designates whether the user can log into this admin '
                    'site.'))
    is_active = models.BooleanField(_('active'), default=True,
        help_text=_('Designates whether this user should be treated as '
                    'active. Unselect this instead of deleting accounts.'))
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    #objects = LongnameUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        db_table = 'auth_user'
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def get_absolute_url(self):
        return "/users/%s/" % urlquote(self.username)

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        "Returns the short name for the user."
        return self.first_name

    def email_user(self, subject, message, from_email=None):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email])