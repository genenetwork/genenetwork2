class MainWebFunctionality
end

describe MainWebFunctionality do
  before do
    @agent = Mechanize.new
    page = @agent.get($host)
    # p page
    @form = page.forms[1]
    
  end

  describe MainWebFunctionality do
    it "The main page contains a search button" do
      @form.buttons[0].value.must_equal "Search" 
    end

    # http://localhost:5003/search?species=mouse&group=BXD&type=Hippocampus+mRNA&dataset=HC_M2_0606_P&search_terms_or=&search_terms_and=MEAN%3D%2815+16%29+LRS%3D%2823+46%29&FormID=searchResult
    it "Search for MEAN=(15 16) LRS=(23 46)" do
      @form.fields[2].value = "MEAN=(15 16) LRS=(23 46)"
      @form.fields[3].value = "mouse"
      @form.fields[4].value = "BXD"
      @form.fields[5].value = "Hippocampus mRNA"
      @form.fields[6].value = "HC_M2_0606_P"
      @searchpage = @agent.submit(@form, @form.buttons.first)
      probe_link = @searchpage.links.find { |l| l.text =~ /1435395_s_at/ }
      probe_link.uri.to_s.must_equal "/show_trait?trait_id=1435395_s_at&dataset=HC_M2_0606_P"
    end
  end
  
end

