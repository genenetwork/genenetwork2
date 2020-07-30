 #! /bin/bash
 #
 # Add missing columns to test db downloaded from:
 # https://s3.amazonaws.com/genenetwork2/db_webqtl_s.zip

 QUERY="
 ALTER TABLE InbredSet
 ADD Family varchar(20) AFTER FullName,
 ADD FamilyOrder varchar(20) AFTER Family,
 ADD MenuOrderId smallint(6) AFTER FamilyOrder,
 ADD InbredSetCode varchar(5) AFTER MenuOrderId;

 ALTER TABLE PublishXRef
 ADD mean double AFTER DataId;

 -- This takes some time
 ALTER TABLE ProbeSet
 ADD UniProtID varchar(20) AFTER ProteinName;
 "

 USER=gn2
 DBNAME=db_webqtl_s
 PASS=mysql_password
 mysql -u"$USER" -p"$PASS" -h localhost -D "$DBNAME" -e "$QUERY"
