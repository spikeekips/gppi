# -*- coding: utf-8 -*-

import os
import sys

class DjangotTestSuite (object, ) :
    def __init__ (
                self, test_file, settings_module_name, test_modules=None,
                verbosity=2, interactive=True,
            ) :
        self._settings_module_name = settings_module_name
        self._test_file = test_file
        self._test_modules = test_modules
        self._verbosity = verbosity
        self._interactive = interactive

        self._extra_tests = list()

    def addTest (self, suite, ) :
        self._extra_tests.append(suite, )


    def __call__ (self, ) :
        os.environ["DJANGO_SETTINGS_MODULE"] = self._settings_module_name
        sys.path.insert(0, os.path.dirname(self._test_file, ), )

        from django.test.utils import get_runner
        from django.conf import settings

        _runner = get_runner(settings, )(
                verbosity=self._verbosity,
                interactive=self._interactive,
            )

        failures = _runner.run_tests(
                list() if self._test_modules is None else self._test_modules,
                extra_tests=self._extra_tests,
            )

        sys.exit(failures)


def run () :
    return DjangotTestSuite(__file__, "example.settings", test_modules=("package", ), )()



