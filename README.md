
## django-decide-host

Decide is an event-driven state-machine framework for running behavioral experiments with embeddable computers like the Beaglebone Black. This repository is a Django app that collates event and trial data from multiple devices running `decide` version 3.0 or later. It replaces [decide-host](https://github.com/melizalab/decide-host), which was a bit snazzier but becoming very difficult to maintain.

This should more or less be working but should be considered beta. You should continue to save trial information locally.

This software is licensed for you to use under the Gnu Public License, version 3. See COPYING for details

### Quick start

1. Install the package from source: `python setup.py install`. Worth putting in a virtualenv.

1. Add `decide_host` to your INSTALLED_APPS setting like this:

```python
INSTALLED_APPS = (
    ...
    'decide_host.apps.DecideHostConfig',
)
```

You'll also need to add `rest_framework` and `django_filters`.

2. Include the decide_host URLconf in your project urls.py like this::

```python
url(r'^decide_host/', include(decide_host.urls')),
```

3. Run `python manage.py migrate` to create the database tables.

4. Start the development server and point your browser to http://127.0.0.1:8000/decide-host/api/
   to view records and inspect the API.

### Importing trial data

If you have trial data in jsonl files that you'd like you import into the database, you can do this very easily. From your project site, run `manage.py import_trials -n <name> -a <addr> trials.jsonl`. You need to supply the name of the controller (addr) and the procedure (name). The import will not happen if there's a duplicate in the database, so no need to worry about this.

### Combining duplicate subjects

Subject names are set with user input, so there may be multiple records in the database that correspond to the same subject. To combine these records, run `manage.py merge_subjects <to_keep> <to_combine>`. Multiple names can be give for `<to_combine>`. It's easy to mess the database up badly doing this so be sure to take a snapshot!
