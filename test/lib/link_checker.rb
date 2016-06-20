
class LinkChecker
end

describe LinkChecker do
  before do
    @agent = Mechanize.new
    @agent.agent.http.ca_file = '/etc/ssl/certs/ca-certificates.crt'
  end

  it "Get to front page" do
      page = @agent.get($host)
      page.links.each do |link|
        puts link.href
        if link.href !~ /static\/dbdoc\/Hippocampus/ and link.href !~ /glossary.html|sample_r|grits.eecs.utk.edu|correlationAnnotation.html/
           # Fetch link, program will crash with exception if link is broken
           linkpage = @agent.get(link.href)
          puts "Link to #{link.href} is valid, response code #{linkpage.code}"
        end
      end

    end

  describe LinkChecker do
    it "Get to trait page" do
      page = @agent.get($host+'/show_trait?trait_id=1435395_s_at&dataset=HC_M2_0606_P')
      # p page

      # Get to trait page for 1435395_s_at
      # form2 = show_trait_page.forms_with("trait_page")[0]
      # form2.fields[30].name.must_equal  "variance:C57BL/6J"
      # form2.fields[30].value.must_equal "15.287"

      # Test every link on the page to check if it's broken or not
      page.links.each do |link|
        puts link.href
        if link.href !~ /static\/dbdoc\/Hippocampus/ and link.href !~ /glossary.html|sample_r|grits.eecs.utk.edu|correlationAnnotation.html/
           # Fetch link, program will crash with exception if link is broken
           linkpage = @agent.get(link.href)
          puts "Link to #{link.href} is valid, response code #{linkpage.code}"
        end
      end

    end

  end

end
