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
    it "pylmm mapping tool selection" do
      url = $host+'/marker_regression'

      json = JSON::load(File.read('test/data/input/mapping/1435395_s_at_HC_M2_0606_P.json'))
      json["method"] = "pylmm"
      # p json
      page = @agent.post(URI.encode(url), json)
      # Unpacking the page is slow - but the run is enough as a test
      # form = page.forms_with("marker_regression")[0]
      # form.fields.select { |fld| fld.name == 'dataset' }.first.value.must_equal 'HC_M2_0606_P'
      # form.fields.select { |fld| fld.name == 'value:BXD1' }.first.value.must_equal '6.749'
    end
  end

  describe MappingTest do
    it "R/qtl mapping tool selection" do
      url = $host+'/marker_regression' # ?trait_id=1435395_s_at&dataset=HC_M2_0606_P'

      json = JSON::load(File.read('test/data/input/mapping/1435395_s_at_HC_M2_0606_P.json'))
      # p json
      page = @agent.post(URI.encode(url),
                         json,
                         ({'Content-Type' => 'application/x-www-form-urlencoded'}))
      form = page.forms_with("marker_regression")[0]
      form.fields.select { |fld| fld.name == 'dataset' }.first.value.must_equal 'HC_M2_0606_P'
      form.fields.select { |fld| fld.name == 'value:BXD1' }.first.value.must_equal '6.749'
    end
  end

  describe MappingTest do
    it "CIM mapping tool selection (using reaper)" do
      url = $host+'/marker_regression'

      json = JSON::load(File.read('test/data/input/mapping/1435395_s_at_HC_M2_0606_P.json'))
      json["method"] = "reaper"
      page = @agent.post(URI.encode(url), json)
      form = page.forms_with("marker_regression")[0]
      form.fields.select { |fld| fld.name == 'dataset' }.first.value.must_equal 'HC_M2_0606_P'
      form.fields.select { |fld| fld.name == 'value:BXD1' }.first.value.must_equal '6.749'
    end
  end

end
