require 'minitest/autorun'
require 'mechanize'
require 'json'

# ---- Use some default parameters if not set
$host = "http://localhost:5003" if !$host
