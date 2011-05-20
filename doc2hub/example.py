# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from doc2hub.gd2gh import Converter

email_map = {'binarybottle@gmail.com': "Arno Klein",
             'jbpoline@gmail.com': "Jean-Baptiste Poline",
             'millman.ucb@gmail.com': "Jarrod Millman",
             'satrajit.ghosh@gmail.com': "Satrajit Ghosh",
             'stnava@gmail.com': "Brian Avants"}

docname='OpenEvaluationArticle'
dirname ='testconversion'
auth_file = '/Users/satra/auth.config'

cvt = Converter(auth_file)
cvt.convert(docname, dirname, email_map)

