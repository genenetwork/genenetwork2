from htmlgen import HTMLgen2 as HT

from base.templatePage import templatePage
from dbFunction import webqtlDatabaseFunction
import BasicStatisticsFunctions

#Window generated from the Trait Data and Analysis page (DataEditingPage.py) with updated stats figures; takes the page's values that can bed edited by the user
class updatedBasicStatisticsPage(templatePage):

    plotMinInformative = 4

    def __init__(self, fd):

        templatePage.__init__(self, fd)

        if not fd.genotype:
            fd.readGenotype()
            this_strainlist = fd.strainlist

        if fd.allstrainlist:
            this_strainlist = fd.allstrainlist

        fd.readData(this_strainlist)

        specialStrains = [] #This appears to be the "other/non-RISet strainlist" without parents/f1 strains; not sure what to name it
        setStrains = []
        for item in this_strainlist:
            if item not in fd.strainlist and item.find('F1') < 0:
                specialStrains.append(item)
            else:
                continue

        specialStrains.sort()
        if specialStrains:
            specialStrains = fd.f1list+fd.parlist+specialStrains

        self.dict['title'] = 'Basic Statistics'
        TD_LR = HT.TD(valign="top",width="100%",bgcolor="#fafafa")

        stats_row = HT.TR()
        stats_cell = HT.TD()
        stats_script = HT.Script(language="Javascript")

        #Get strain names, values, and variances
        strain_names = fd.formdata.getvalue('strainNames').split(',')
        strain_vals = fd.formdata.getvalue('strainVals').split(',')
        strain_vars = fd.formdata.getvalue('strainVars').split(',')

        vals = []
        if (len(strain_names) > 0):
            if (len(strain_names) > 3):
                #Need to create "vals" object
                for i in range(len(strain_names)):
                    try:
                        this_strain_val = float(strain_vals[i])
                    except:
                        continue
                    try:
                        this_strain_var = float(strain_vars[i])
                    except:
                        this_strain_var = None

                    thisValFull = [strain_names[i], this_strain_val, this_strain_var]
                    vals.append(thisValFull)

                stats_tab_list = [HT.Href(text="Basic Table", url="#statstabs-1", Class="stats_tab"),HT.Href(text="Probability Plot", url="#statstabs-2", Class="stats_tab"),
                                                HT.Href(text="Bar Graph (by name)", url="#statstabs-3", Class="stats_tab"), HT.Href(text="Bar Graph (by rank)", url="#statstabs-4", Class="stats_tab"),
                                                HT.Href(text="Box Plot", url="#statstabs-5", Class="stats_tab")]
                stats_tabs = HT.List(stats_tab_list)

                stats_container = HT.Div(id="stats_tabs", Class="ui-tabs")
                stats_container.append(stats_tabs)

                stats_script_text = """$(function() { $("#stats_tabs").tabs();});""" #Javascript enabling tabs

                table_div = HT.Div(id="statstabs-1", style="height:320px;width:740px;overflow:scroll;")
                table_container = HT.Paragraph()

                statsTable = HT.TableLite(cellspacing=0, cellpadding=0, width="100%")
                this_trait_type = fd.formdata.getvalue('trait_type', None)
                this_cellid = fd.formdata.getvalue('cellid', None)
                statsTableCell = BasicStatisticsFunctions.basicStatsTable(vals=vals, trait_type=this_trait_type, cellid=this_cellid)
                statsTable.append(HT.TR(HT.TD(statsTableCell)))

                table_container.append(statsTable)
                table_div.append(table_container)
                stats_container.append(table_div)

                normalplot_div = HT.Div(id="statstabs-2", style="height:540px;width:740px;overflow:scroll;")
                normalplot_container = HT.Paragraph()
                normalplot = HT.TableLite(cellspacing=0, cellpadding=0, width="100%")
                plotTitle = fd.formdata.getvalue("normalPlotTitle","")
                normalplot_img = BasicStatisticsFunctions.plotNormalProbability(vals=vals, RISet=fd.RISet, title=plotTitle, specialStrains=specialStrains)
                normalplot.append(HT.TR(HT.TD(normalplot_img)))
                normalplot.append(HT.TR(HT.TD(HT.BR(),HT.BR(),"This plot evaluates whether data are \
                normally distributed. Different symbols represent different groups.",HT.BR(),HT.BR(),
                "More about ", HT.Href(url="http://en.wikipedia.org/wiki/Normal_probability_plot",
                                target="_blank", text="Normal Probability Plots"), " and more about interpreting these plots from the ", HT.Href(url="/glossary.html#normal_probability", target="_blank", text="glossary"))))
                normalplot_container.append(normalplot)
                normalplot_div.append(normalplot_container)
                stats_container.append(normalplot_div)

                barName_div = HT.Div(id="statstabs-3", style="height:540px;width:740px;overflow:scroll;")
                barName_container = HT.Paragraph()
                barName = HT.TableLite(cellspacing=0, cellpadding=0, width="100%")
                barName_img = BasicStatisticsFunctions.plotBarGraph(identification=fd.identification, RISet=fd.RISet, vals=vals, type="name")
                barName.append(HT.TR(HT.TD(barName_img)))
                barName_container.append(barName)
                barName_div.append(barName_container)
                stats_container.append(barName_div)

                barRank_div = HT.Div(id="statstabs-4", style="height:540px;width:740px;overflow:scroll;")
                barRank_container = HT.Paragraph()
                barRank = HT.TableLite(cellspacing=0, cellpadding=0, width="100%")
                barRank_img = BasicStatisticsFunctions.plotBarGraph(identification=fd.identification, RISet=fd.RISet, vals=vals, type="rank")
                barRank.append(HT.TR(HT.TD(barRank_img)))
                barRank_container.append(barRank)
                barRank_div.append(barRank_container)
                stats_container.append(barRank_div)

                boxplot_div = HT.Div(id="statstabs-5", style="height:540px;width:740px;overflow:scroll;")
                boxplot_container = HT.Paragraph()
                boxplot = HT.TableLite(cellspacing=0, cellpadding=0, width="100%")
                boxplot_img, boxplot_link = BasicStatisticsFunctions.plotBoxPlot(vals)
                boxplot.append(HT.TR(HT.TD(boxplot_img, HT.P(), boxplot_link, align="left")))
                boxplot_container.append(boxplot)
                boxplot_div.append(boxplot_container)
                stats_container.append(boxplot_div)

                stats_cell.append(stats_container)
                stats_script.append(stats_script_text)

                submitTable = HT.TableLite(cellspacing=0, cellpadding=0, width="100%")
                stats_row.append(stats_cell)

                submitTable.append(stats_row)
                submitTable.append(stats_script)

                TD_LR.append(submitTable)
                self.dict['body'] = str(TD_LR)
            else:
                heading = "Basic Statistics"
                detail = ['Fewer than %d case data were entered for %s data set. No statitical analysis has been attempted.' % (self.plotMinInformative, fd.RISet)]
                self.error(heading=heading,detail=detail)
                return
        else:
            heading = "Basic Statistics"
            detail = ['Empty data set, please check your data.']
            self.error(heading=heading,detail=detail)
            return
