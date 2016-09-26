# In these tests we navigate from the main page to a specific trait then hit the different mapping tool buttons (In this case pylMM and r/qtl) followed by computing the results (marker regressions).

require 'gntest'

class MappingTest
end

describe MappingTest do
  before do
    @agent = Mechanize.new
    @agent.agent.http.ca_file = '/etc/ssl/certs/ca-certificates.crt'
  end

  describe MappingTest do
    it "R/qtl mapping tool selection" do
      url = $host+'/marker_regression' # ?trait_id=1435395_s_at&dataset=HC_M2_0606_P'

      json = JSON::load(File.read('test/data/input/mapping/1435395_s_at_HC_M2_0606_P.json'))
      # p json
      page = @agent.post(URI.encode(url),
                         json,
                         ({'Content-Type' => 'application/x-www-form-urlencoded'}))
      p page
    end
  end

end
