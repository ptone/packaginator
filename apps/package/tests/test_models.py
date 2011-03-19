from datetime import datetime, timedelta

from django.test import TestCase

try:
  from mock import Mock, patch
except ImportError:
  raise ImportError("Mock is a requirement for la_facebook tests")

from package.models import Package

mock_repo = Mock()

class VersionTests(TestCase):

    fixtures = ['apps/package/tests/test_data/versioner_test_fixture.json',
                'apps/package/tests/test_data/versioner_versions_fixture.json']

    def test_version_order(self):
        p = Package.objects.get(slug='django-cms')
        versions = p.version_set.by_version()
        expected_values = [ '2.0.0',
                            '2.0.1',
                            '2.0.2',
                            '2.1.0',
                            '2.1.0.beta3',
                            '2.1.0.rc1',
                            '2.1.0.rc2',
                            '2.1.0.rc3',
                            '2.1.1',
                            '2.1.2',
                            '2.1.3']
        returned_values = [v.number for v in versions]
        self.assertEquals(returned_values,expected_values)

class PackageMetaDataTests(TestCase):

    """
    test that last update of package meta data is stored on Package model
    """

    def setUp(self):
        self.package = Package(
                title='Packaginator',
                repo_url='https://github.com/cartwheelweb/packaginator')
        self.package.save()

    @patch('package.models.get_repo_for_repo_url', mock_repo)
    def test_metadata_store(self):
        self.assertTrue(self.package.metadata_last_fetched == None)
        self.package.fetch_metadata()
        self.assertTrue((datetime.now() - self.package.metadata_last_fetched) <
                timedelta(seconds=10))
        self.assertTrue(self.package.metadata_fetch_message)
        self.assertEquals(self.package.metadata_fetch_message, 'success')


# @@ TODO: tests that mock pypi API
# tests that test failure

