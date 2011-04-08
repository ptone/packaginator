from distutils.version import StrictVersion, LooseVersion

def uniquer(seq, idfun=None):
    if idfun is None:
        def idfun(x): return x
    seen = {}
    result = []
    for item in seq:
        marker = idfun(item)
        if marker in seen: continue
        seen[marker] = 1
        result.append(item)
    return result


def compare_versions(version1, version2):
    try:
        return cmp(StrictVersion(version1), StrictVersion(version2))
    # in case of abnormal version number, fall back to LooseVersion
    except ValueError:
        return cmp(LooseVersion(version1), LooseVersion(version2))


def highest_version(versions):
    return reduce((lambda v1, v2: compare_versions(v1, v2) == 1 and v1 or v2), versions)

# -------------------------------------------------------
# simpler
"""
from distutils.version import LooseVersion as versioner

class VersionManager(models.Manager):
    def by_version(self, *args, **kwargs):
        qs = self.get_query_set().filter(*args, **kwargs)
        return sorted(qs,key=lambda v: versioner(v.number))
"""

