# In these tests we navigate from the main page to search

class MainWebFunctionality
end

describe MainWebFunctionality do
  before do
    @agent = Mechanize.new
    @agent.agent.http.ca_file = '/etc/ssl/certs/ca-certificates.crt'
  end

  describe MainWebFunctionality do

    it "Get to trait page" do
      page = @agent.get($host)
      p page
      form = page.forms[1]
      form.buttons[0].value.must_equal "Search" # main menu is loaded

      # http://localhost:5003/search?species=mouse&group=BXD&type=Hippocampus+mRNA&dataset=HC_M2_0606_P&search_terms_or=&search_terms_and=MEAN%3D%2815+16%29+LRS%3D%2823+46%29&FormID=searchResult
      form.fields[0].value.must_equal "searchResult"
      form.fields[2].value = "MEAN=(15 16) LRS=(23 46)"
      form.fields[3].value = "mouse"
      form.fields[4].value = "BXD"
      form.fields[5].value = "Hippocampus mRNA"
      form.fields[6].value = "HC_M2_0606_P"
      search_page = @agent.submit(form, form.buttons.first)
      p "=================="
      p search_page
      probe_link = search_page.links.find { |l| l.text =~ /1435395_s_at/ }
      probe_link.uri.to_s.must_equal "/show_trait?trait_id=1435395_s_at&dataset=HC_M2_0606_P"
      show_trait_page = probe_link.click
      # p show_trait_page

      # Get to trait page for 1435395_s_at

      form2 = show_trait_page.forms_with("trait_page")[0]
      # [name: corr_dataset value: HC_M2_0606_P]
      form2.fields.select { |fld| fld.name == 'corr_dataset' }.first.value.must_equal 'HC_M2_0606_P'
      if $options[:database] == :small
        form2.fields[30].name.must_equal  "value:DBA/2J"
      else
        form2.fields[30].name.must_equal  "variance:C57BL/6J"
      end
      # form2.fields[30].value.must_equal "15.287"

      # Test every link on the page to check if it's broken or not
      break if not $options[:link_checker]
      show_trait_page.links.each do |link|
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
