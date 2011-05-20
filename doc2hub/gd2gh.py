# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

"""
Config options needed are:

gmail_username
gmail_password

github username
github password

google_doc url

author mapping between google and github
"""

import json
import os
import re

import gdata.docs.data
import gdata.docs.client

class Converter(object):

    def __init__(self, authconfig_file):
        config = None
        with open(authconfig_file, 'rt') as fp:
            config=json.load(fp)
        if config is None:
            raise ValueError('Config is empty')
        self._config = config
        self._client = gdata.docs.client.DocsClient(source='Doc2Hub')
        self._client.ssl = True  # Force all API requests through HTTPS
        self._client.http_client.debug = False  # Set to True for debugging HTTP requests
        self._client.ClientLogin(config['gmail_username'], config['gmail_password'], self._client.source);

    def print_feed(self, regexp=None):
        feed = self._client.GetDocList()
        print '\n'
        if not feed.entry:
          print 'No entries in feed.\n'
        for entry in feed.entry:
            name = entry.title.text.encode('UTF-8')
            if re.match(regexp, name):
                print entry.title.text.encode('UTF-8'), entry.GetDocumentType(), entry.resource_id.text
                # List folders the document is in.
                for folder in entry.InFolders():
                    print folder.title

    def get_entries(self, docname):
        feed = self._client.GetDocList(uri='/feeds/default/private/full?title=%s&title-exact=false&max-results=5'%docname)
        if not feed.entry:
            raise ValueError('No entries in feed.')
        return feed.entry

    def get_revisions(self, entry):
        return self._client.GetRevisions(entry)

    def convert(self, docname, dirname, author_map):
        entry = self.get_entries(docname)
        if len(entry) == 1:
            entry = entry[0]
        else:
            raise ValueError('multiple entries for %s'%docname)
        pwd = os.getcwd()
        os.mkdir(dirname)
        os.chdir(dirname)
        os.system('git init')
        revision_feed = self._client.get_revisions(entry.resource_id.text)
        for rev in revision_feed.entry:
            email = rev.author[0].email.text
            name = author_map[email]
            date = rev.updated.text
            self._client.Export(rev.content.src, '/tmp/%s.zip'%docname)
            os.system('unzip -o /tmp/%s.zip'%docname)
            os.system('pandoc -f html -t rst -o %s.rst %s.html'%(docname, docname))
            if os.path.exists('images'):
                os.system('git add %s.rst images/*.png'%docname)
            else:
                os.system('git add %s.rst'%docname)
            os.system('git commit --date=%s --author="%s <%s>" -m "ref:%s"'%(date, name, email, rev.id.text))
            print "finished converting revision: %s"%rev.id.text.split('/')[-1]
        os.chdir(pwd)
