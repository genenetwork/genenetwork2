from __future__ import absolute_import, print_function, division
import os
import math

import json
import itertools

from flask import Flask, g

from base import webqtlConfig
from dbFunction import webqtlDatabaseFunction
from utility import webqtlUtil

from MySQLdb import escape_string as escape
from pprint import pformat as pf


query = """ select ProbeSet.Name
            from ProbeSetXRef,
                 ProbeSetFreeze,
                 ProbeSet
            where ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id and
                  ProbeSetFreeze.Name = "EPFLMouseMuscleCDRMA1211" and
                  ProbeSetXRef.ProbeSetId = ProbeSet.Id;
        """

markers = g.db.execute(query).fetchall()
print("markers: ", pf(markers))

if __name__ == '__main__':
    main()