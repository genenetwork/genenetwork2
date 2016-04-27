# In these tests we navigate from the main page to search

class MainWebFunctionality
end

describe MainWebFunctionality do
  before do
    @agent = Mechanize.new
  end

  describe MainWebFunctionality do
    it "Get to trait page" do
      page = @agent.get($host)
      form = page.forms[1]
      form.buttons[0].value.must_equal "Search" 
      # http://localhost:5003/search?species=mouse&group=BXD&type=Hippocampus+mRNA&dataset=HC_M2_0606_P&search_terms_or=&search_terms_and=MEAN%3D%2815+16%29+LRS%3D%2823+46%29&FormID=searchResult
      form.fields[2].value = "MEAN=(15 16) LRS=(23 46)"
      form.fields[3].value = "mouse"
      form.fields[4].value = "BXD"
      form.fields[5].value = "Hippocampus mRNA"
      form.fields[6].value = "HC_M2_0606_P"
      search_page = @agent.submit(form, form.buttons.first)
      probe_link = search_page.links.find { |l| l.text =~ /1435395_s_at/ }
      probe_link.uri.to_s.must_equal "/show_trait?trait_id=1435395_s_at&dataset=HC_M2_0606_P"
      show_trait_page = probe_link.click
      # Get to trait page for 1435395_s_at
      form2 = show_trait_page.forms_with("trait_page")[0]
      form2.fields[30].name.must_equal  "value:DBA/2J"
      form2.fields[30].value.must_equal "15.287"
    end
  end
  
end

