# -*- coding: utf-8 -*-
# ==============================================================================
# COPYRIGHT (C) 1991 - 2015  EDF R&D                  WWW.CODE-ASTER.ORG
# THIS PROGRAM IS FREE SOFTWARE; YOU CAN REDISTRIBUTE IT AND/OR MODIFY
# IT UNDER THE TERMS OF THE GNU GENERAL PUBLIC LICENSE AS PUBLISHED BY
# THE FREE SOFTWARE FOUNDATION; EITHER VERSION 2 OF THE LICENSE, OR
# (AT YOUR OPTION) ANY LATER VERSION.
#
# THIS PROGRAM IS DISTRIBUTED IN THE HOPE THAT IT WILL BE USEFUL, BUT
# WITHOUT ANY WARRANTY; WITHOUT EVEN THE IMPLIED WARRANTY OF
# MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE. SEE THE GNU
# GENERAL PUBLIC LICENSE FOR MORE DETAILS.
#
# YOU SHOULD HAVE RECEIVED A COPY OF THE GNU GENERAL PUBLIC LICENSE
# ALONG WITH THIS PROGRAM; IF NOT, WRITE TO EDF R&D CODE_ASTER,
#    1 AVENUE DU GENERAL DE GAULLE, 92141 CLAMART CEDEX, FRANCE.
# ==============================================================================
"""
Package info
"""

modname      = 'asrun'
numversion   = (1, 13, 8, 'final')
version      = '.'.join([str(num) for num in numversion if num != 'final'])
release      = '1'
date_release = "2016-06-07"

license      = 'GPL'
copyright    = 'Copyright (c) 2001-2016 EDF R&D - http://www.code-aster.org'

short_desc   = "interface to Code_Aster services"
long_desc    = """
 Its purposes are ::
    - running Code_Aster calculations,
    - giving status and interact on running jobs,
    - building a Code_Aster version from source and keep it up to date,
    - giving an easy access to source code,
    - checking the source code,
    - helping developers by extracting list of testcases, showing diff files,
    - running testcase, parametric study,
    - accessing to the internal bug tracker,
    - inserting an execution into the internal studies database,
    - ...
"""

author       = "EDF R&D"
author_email = "code-aster@edf.fr"
url          = "http://www.code-aster.org"
