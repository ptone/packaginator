# TODO - cleanup regex to do proper string subs
# TODO - add is_other field to repo

from datetime import datetime
from distutils.version import LooseVersion as versioner
from github2.client import Github
from urllib import urlopen
from xmlrpclib import ProtocolError
import logging
import os
import re
import sys

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from package.fields import CreationDateTimeField, ModificationDateTimeField
from package.pypi import fetch_releases
from package.repos import get_repo_for_repo_url
from package.repos import github

repo_url_help_text = settings.PACKAGINATOR_HELP_TEXT['REPO_URL']
pypi_url_help_text = settings.PACKAGINATOR_HELP_TEXT['PYPI_URL']
category_help_text = settings.PACKAGINATOR_HELP_TEXT['CATEGORY']

class NoPyPiVersionFound(Exception):
    pass

class BaseModel(models.Model):
    """ Base abstract base class to give creation and modified times """
    created     = CreationDateTimeField(_('created'))
    modified    = ModificationDateTimeField(_('modified'))

    class Meta:
        abstract = True

class Category(BaseModel):

    title = models.CharField(_("Title"), max_length="50")
    slug  = models.SlugField(_("slug"))
    description = models.TextField(_("description"), blank=True)
    title_plural = models.CharField(_("Title Plural"), max_length="50", blank=True)
    show_pypi = models.BooleanField(_("Show pypi stats & version"), default=True)

    class Meta:
        ordering = ['title']
        verbose_name_plural = 'Categories'

    def __unicode__(self):
        return self.title

class Package(BaseModel):

    title           = models.CharField(_("Title"), max_length="100")
    slug            = models.SlugField(_("Slug"), help_text="Slugs will be lowercased", unique=True)
    category        = models.ForeignKey(Category, verbose_name="Installation", help_text=category_help_text)
    repo_description= models.TextField(_("Repo Description"), blank=True)
    repo_url        = models.URLField(_("repo URL"), help_text=repo_url_help_text, blank=True,unique=True)
    repo_watchers   = models.IntegerField(_("repo watchers"), default=0)
    repo_forks      = models.IntegerField(_("repo forks"), default=0)
    repo_commits    = models.IntegerField(_("repo commits"), default=0)
    pypi_url        = models.URLField(_("PyPI slug"), help_text=pypi_url_help_text, blank=True, default='')
    pypi_downloads  = models.IntegerField(_("Pypi downloads"), default=0)
    related_packages    = models.ManyToManyField("self", blank=True)
    participants    = models.TextField(_("Participants"),
                        help_text="List of collaborats/participants on the project", blank=True)
    usage           = models.ManyToManyField(User, blank=True)
    created_by = models.ForeignKey(User, blank=True, null=True, related_name="creator")
    last_modified_by = models.ForeignKey(User, blank=True, null=True, related_name="modifier")
    pypi_home_page  = models.URLField(_("homepage on PyPI for a project"), blank=True, null=True)
    metadata_last_fetched = models.DateTimeField(blank=True, null=True)
    metadata_fetch_success = models.BooleanField(default=False)
    metadata_fetch_message = models.CharField(max_length=100, blank=True)

    @property
    def pypi_version(self):
        string_ver_list = self.version_set.values_list('number', flat=True)
        if string_ver_list:
            vers_list = [versioner(v) for v in string_ver_list]
            latest = sorted(vers_list)[-1]
            return str(latest)
        return ''

    @property
    def pypi_name(self):
        """ return the pypi name of a package"""

        if not self.pypi_url.strip():
            return ""

        name = self.pypi_url.replace("http://pypi.python.org/pypi/","")
        if "/" in name:
            return name[:name.index("/")]
        return name

    @property
    def last_updated(self):
        last_commit = self.commit_set.latest('commit_date')
        if last_commit:
            return last_commit.commit_date
        return None

    @property
    def repo(self):
        handler = get_repo_for_repo_url(self.repo_url)
        return handler

    def active_examples(self):
        return self.packageexample_set.filter(active=True)

    def grids(self):

        return (x.grid for x in self.gridpackage_set.all())

    def repo_name(self):
        return self.repo_url.replace(self.repo.url + '/','')

    def participant_list(self):

        return self.participants.split(',')

    def commits_over_52(self):
        from package.templatetags.package_tags import commits_over_52
        return commits_over_52(self)

    def fail_fetch_metadata(self,message):
        self.metadata_last_fetched = datetime.now()
        self.metadata_fetch_success = False
        self.metadata_fetch_message = message
        self.save()

    def fetch_metadata(self, *args, **kwargs):

        # Get the downloads from pypi
        if self.pypi_url.strip() and self.pypi_url != "http://pypi.python.org/pypi/":

            total_downloads = 0

            try:
                pypi_releases = fetch_releases(self.pypi_name)
            except ProtocolError, e:
                self.fail_fetch_metadata("Error fetching pypi releases: %s" % e)
                raise
            except:
                self.fail_fetch_metadata("Error fetching pypi releases")
                raise

            for release in pypi_releases:

                version, created = Version.objects.get_or_create(
                    package = self,
                    number = release.version
                )

                # add to total downloads
                total_downloads += release.downloads

                # add to versions
                version.downloads = release.downloads
                version.license = release.license
                version.hidden = release._pypi_hidden
                version.save()

            self.pypi_downloads = total_downloads

        try:
            self.repo.fetch_metadata(self)
        except:
            self.fail_fetch_metadata("Unable to fetch repo metadata")
            raise

        self.metadata_last_fetched = datetime.now()
        self.metadata_fetch_success = True
        self.metadata_fetch_message = "success"
        self.save()

    def fetch_commits(self):
        self.repo.fetch_commits(self)

    class Meta:
        ordering = ['title']

    def __unicode__(self):

        return self.title

    @models.permalink
    def get_absolute_url(self):
        return ("package", [self.slug])


class PackageExample(BaseModel):

    package = models.ForeignKey(Package)
    title = models.CharField(_("Title"), max_length="100")
    url = models.URLField(_("URL"))
    active = models.BooleanField(_("Active"), default=True, help_text="Moderators have to approve links before they are provided")

    class Meta:
        ordering = ['title']

    def __unicode__(self):
        return self.title

class Commit(BaseModel):

    package      = models.ForeignKey(Package)
    commit_date  = models.DateTimeField(_("Commit Date"))

    class Meta:
        ordering = ['-commit_date']

    def __unicode__(self):
        return "Commit for '%s' on %s" % (self.package.title, unicode(self.commit_date))

class VersionManager(models.Manager):
    def by_version(self, *args, **kwargs):
        qs = self.get_query_set().filter(*args, **kwargs)
        return sorted(qs,key=lambda v: versioner(v.number))
        return "Commit for '%s' on %s" % (self.package.title, unicode(self.commit_date))

class Version(BaseModel):

    package = models.ForeignKey(Package, blank=True, null=True)
    number = models.CharField(_("Version"), max_length="100", default="", blank="")
    downloads = models.IntegerField(_("downloads"), default=0)
    license = models.CharField(_("license"), max_length="100")
    hidden = models.BooleanField(_("hidden"), default=False)

    objects = VersionManager()
    hidden = models.BooleanField(_("hidden"), default=False)

    class Meta:
        get_latest_by = 'created'
        ordering = ['-created']

    def __unicode__(self):
        return "%s: %s" % (self.package.title, self.number)

