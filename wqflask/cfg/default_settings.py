LOGFILE = """/tmp/flask_gn_log"""

#This is needed because Flask turns key errors into a
#400 bad request response with no exception/log 
TRAP_BAD_REQUEST_ERRORS = True
