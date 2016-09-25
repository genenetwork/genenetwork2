# In these tests we navigate from the main page to a specific trait then hit the different mapping tool buttons (In this case pylMM and r/qtl) followed by computing the results (marker regressions).


class MappingTest
end

describe MappingTest do
  before do
    @agent = Mechanize.new
    @agent.agent.http.ca_file = '/etc/ssl/certs/ca-certificates.crt'
  end

  describe MappingTest do
    it "pyLMM mapping tool selection" do
      break if $options[:skip_broken]
      page = @agent.get($host+'/show_trait?trait_id=1435395_s_at&dataset=HC_M2_0606_P')
#Navigates to http://localhost:5003/show_trait?trait_id=1435395_s_at&dataset=HC_M2_0606_P and clicks respective buttons.
      link = page.link_with(text: 'pyLMM')
      page = link.click
      puts page.uri
      link = page.link_with(text: 'Compute')
      page = link.click
      puts page.uri
      probe_link.uri.to_s.must_equal "/marker_regression"
    end
  end

end

describe MappingTest do
    it "R/qtl mapping tool selection" do
      break if $options[:skip_broken]
      page = @agent.get($host+'/show_trait?trait_id=1435395_s_at&dataset=HC_M2_0606_P')
      link = page.link_with(text: 'R/qtl')
      page = link.click
      puts page.uri
      form.field_with(:name => 'Methods').options[2].select
      link = page.link_with(text: 'Compute')
      page = link.click
      puts page.uri
      probe_link.uri.to_s.must_equal "/marker_regression"
    end
end
