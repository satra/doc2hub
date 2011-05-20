# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from doc2hub.gd2gh import Converter

email_map = {'binary...com': "Arno Klein",
             'jbpol...com': "Jean-Baptiste Poline",
             'mill...com': "Jarrod Millman",
             'satra...com': "Satrajit Ghosh",
             'stnav...com': "Brian Avants"}

docname='OpenEvaluationArticle'
dirname ='testconversion'
auth_file = '/Users/satra/auth.config'

cvt = Converter(auth_file)
cvt.convert(docname, dirname, email_map)

