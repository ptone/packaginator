from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

from package.models import Package
from package.repos.launchpad import LaunchpadHandler

class GenericPullTests(TestCase):

    def setUp(self):
        
        package = Package.objects.create(
            title="Django Piston",
            slug="django-piston",
            repo_url="https://bitbucket.org/jespern/django-piston",
        )
        package.save()        
        
        package = Package.objects.create(
            title="Django",
            slug="django",
            repo_url="https://github.com/django/django",
        )        
        package.save()
        
        if settings.LAUNCHPAD_ACTIVE:
            package = Package.objects.create(
                title="Django-PreFlight",
                slug="django-preflight",
                repo_url="https://code.launchpad.net/~canonical-isd-hackers/django-preflight/trunk",
            )
            package.save()
                
        # package list is needed throughout the app
        self.packages = Package.objects.all()
        

    def _resetting_packages(self, ):
        for package in self.packages:
            package.repo_watchers = 0
            package.repo_forks = 0
            package.repo_description = ''
            package.participants = ''

    def test_initial_data(self):
        for package in self.packages:
            self.assertTrue(package.repo)
            

    def test_repo_handler_fetch(self):

        # resetting package metadata
        self._resetting_packages()

        for package in self.packages:

            #fetching meta data from repo
            pulled_package = package.repo.fetch_metadata(package)

            # check if package metadata is not empty or incorrect
            self.assertTrue(package.repo_watchers)
            self.assertTrue(package.repo_forks)
            
            if isinstance(package.repo, LaunchpadHandler):
                self.assertTrue(isinstance(package.repo_description, str))
            else:
                self.assertTrue(package.repo_description)
            
            # TODO check if this is getting updated
            #self.assertTrue(package.participants)

    def test_package_model_fetch(self):

        # reset package metadata
        self._resetting_packages()

        for package in self.packages:

            # method being tested, which fills in the metadata fields
            package.fetch_metadata()

            # check that package metadata is not empty or incorrect
            self.assertTrue(package.repo_watchers)
            self.assertTrue(package.repo_forks)
            
            if isinstance(package.repo, LaunchpadHandler):
                self.assertTrue(isinstance(package.repo_description, str))
            else:
                self.assertTrue(package.repo_description)
            
            # TODO check if this is getting updated
            #self.assertTrue(package.participants)
