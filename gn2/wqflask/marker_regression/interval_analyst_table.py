"""Interval Analyst gene table generation.

The "Interval Analyst" table on the mapping-results page lists the genes in
the mapped interval for the selected chromosome/range. It is built here (rather
than inline in ``DisplayMappingResults``) because it is produced by two
callers that must agree exactly:

* the initial server-side render of ``mapping_results.html``
  (``DisplayMappingResults.geneTable``), and
* ``POST /mapping/interval_analyst_data``, used by the interactive d3 figure to
  refresh the table when the chromosome/range is changed client-side.

Gene data itself comes from ``GeneUtil.loadGenes``; this module only formats it
into the header list and body rows that the template renders.
"""


def make_link(href, text, target=None, Class=None):
    """Build an HTML <a> tag string."""
    attrs = f'href="{href}"'
    if target:
        attrs += f' target="{target}"'
    if Class:
        attrs += f' class="{Class}"'
    return f'<a {attrs}>{text}</a>'


def build_gene_table(gene_col, species, diff_col=None, debug_links=True):
    """Return ``(header_list, body_rows)`` for the Interval Analyst table.

    ``gene_col`` is a list of gene dicts as returned by ``GeneUtil.loadGenes``.
    ``diff_col`` is the pair of Strain Ids used for the SNP-browser links.
    ``debug_links`` mirrors the legacy ``ALEX_DEBUG_BOOL_PRINT_GENE_LIST`` flag;
    when it is false the mouse rows are emitted empty, as before.

    Only mouse and rat are supported (matching the page, which shows this table
    for those species); anything else yields an empty header/body.
    """
    gene_col = gene_col or []

    if species == "mouse":
        header = ["",
                  "Index",
                  "Symbol",
                  "Mb Start",
                  "Length (Kb)",
                  "SNP Count",
                  "SNP Density",
                  "Avg Expr",
                  "Human Chr",
                  "Mb Start (hg19)",
                  "Gene Description"]
        return header, _mouse_rows(gene_col, diff_col, debug_links)

    if species == "rat":
        header = ["",
                  "Index",
                  "Symbol",
                  "Mb Start",
                  "Length (Kb)",
                  "Avg Expr",
                  "Mouse Chr",
                  "Mb Start (mm9)",
                  "Human Chr",
                  "Mb Start (hg19)",
                  "Gene Description"]
        return header, _rat_rows(gene_col)

    return [], []


def _other_species(the_go, key):
    """Return the merged other-species dict for *key*, or {}.

    ``GeneUtil.loadGenes`` always creates these keys, but they are empty dicts
    when no ortholog was found, so guard against missing inner keys.
    """
    return the_go.get(key) or {}


def _mouse_rows(gene_col, diff_col=None, debug_links=True):
    rows = []

    for g_index, the_go in enumerate(gene_col):
        this_row = []
        select_check = ('<input type="checkbox" name="selectCheck" '
                        'value="{}" class="checkbox trait_checkbox">'
                        .format(the_go["GeneSymbol"]))

        gene_length = (the_go["TxEnd"] - the_go["TxStart"]) * 1000.0
        ten_percent_length = gene_length * 0.0001
        tx_start = the_go["TxStart"]
        tx_end = the_go["TxEnd"]
        the_go["snpDensity"] = the_go["snpCount"] / gene_length

        if debug_links:
            gene_id_string = (
                "http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?db=gene&"
                "cmd=Retrieve&dopt=Graphics&list_uids=%s" % the_go["GeneID"])

            if the_go["snpCount"]:
                snp_string = make_link(
                    ("http://genenetwork.org/webqtl/main.py?"
                     "FormID=snpBrowser&"
                     "chr={}&"
                     "start={}&"
                     "end={}&"
                     "geneName={}&"
                     "s1={}&s2=%d").format(
                         the_go["Chr"],
                         the_go["TxStart"],
                         the_go["TxEnd"],
                         the_go["GeneSymbol"],
                         (diff_col or [""])[0]),
                    str(the_go["snpCount"]),
                    target="_blank",
                    Class="normalsize")
            else:
                snp_string = 0

            mouse_start_string = (
                "http://genome.ucsc.edu/cgi-bin/hgTracks?clade=vertebrate&"
                "org=Mouse&db=mm10&position=chr" + the_go["Chr"] + "%3A" +
                str(int(the_go["TxStart"] * 1000000.0)) + "-" +
                str(int(the_go["TxEnd"] * 1000000.0)) +
                "&pix=620&Submit=submit")

            human = _other_species(the_go, "humanGene")
            if human:
                human_start = human.get("TxStart")
                if human_start in (None, ""):
                    human_start_display = ""
                else:
                    human_start_display = "%0.6f" % human_start
                human_chr = human.get("Chr")
                human_start_string = (
                    "http://genome.ucsc.edu/cgi-bin/hgTracks?"
                    "clade=vertebrate&org=Human&db=hg17&position=chr%s:%d-%d"
                    % (human_chr,
                       int(1000000 * (human.get("TxStart") or 0)),
                       int(1000000 * (human.get("TxEnd") or 0))))
            else:
                human_start_string = human_chr = human_start_display = "--"

            gene_description = the_go.get("GeneDescription") or ""
            if len(gene_description) > 70:
                gene_description = gene_description[:70] + "..."

            if the_go["snpDensity"] < 0.000001:
                snp_density_str = "0"
            else:
                snp_density_str = "%0.6f" % the_go["snpDensity"]

            # Avg Expr is not currently computed - the original left the value
            # commented out and always displayed "--".
            avg_expr = "--"

            if the_go["Chr"] == "X":
                chr_as_int = 19
            else:
                chr_as_int = int(the_go["Chr"]) - 1

            this_row = [
                select_check,
                str(g_index + 1),
                make_link(gene_id_string, the_go["GeneSymbol"],
                          target="_blank"),
                make_link(mouse_start_string, "{:.6f}".format(tx_start),
                          target="_blank"),
                make_link(
                    "javascript:rangeView('{}', {:f}, {:f})".format(
                        str(chr_as_int),
                        tx_start - ten_percent_length,
                        tx_end + ten_percent_length),
                    "{:.3f}".format(gene_length)),
                snp_string,
                snp_density_str,
                avg_expr,
                human_chr,
                make_link(human_start_string, human_start_display,
                          target="_blank"),
                gene_description,
            ]

        rows.append(this_row)

    return rows


def _rat_rows(gene_col):
    rows = []

    for g_index, the_go in enumerate(gene_col):
        select_check = ('<input type="checkbox" name="selectCheck" '
                        'class="checkbox trait_checkbox">')

        if the_go["GeneID"] != "":
            gene_symbol = make_link(
                "http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?db=gene&"
                "cmd=Retrieve&dopt=Graphics&list_uids={}".format(
                    the_go["GeneID"]),
                the_go["GeneSymbol"],
                Class="normalsize",
                target="_blank")
        else:
            gene_symbol = the_go["GeneSymbol"]

        gene_length = float(the_go["TxEnd"]) - float(the_go["TxStart"])
        gene_length_url = "javascript:rangeView('%s', %f, %f)" % (
            the_go["Chr"],
            float(the_go["TxStart"]) - (gene_length * 0.1),
            float(the_go["TxEnd"]) + (gene_length * 0.1))

        # Avg Expr is not currently computed (always blank, as in the original)
        avg_expr_val = ""

        mouse = _other_species(the_go, "mouseGene")
        if mouse:
            mouse_chr = mouse.get("Chr")
            mouse_tx_start = "%0.6f" % (mouse.get("TxStart") or 0)
        else:
            mouse_chr = mouse_tx_start = ""

        human = _other_species(the_go, "humanGene")
        if human:
            human_chr = human.get("Chr")
            human_tx_start = "%0.6f" % (human.get("TxStart") or 0)
        else:
            human_chr = human_tx_start = ""

        gene_desc = the_go.get("GeneDescription") or ""
        if gene_desc == "---":
            gene_desc = ""

        rows.append([
            select_check,
            str(g_index + 1),
            gene_symbol,
            "%0.6f" % the_go["TxStart"],
            make_link(gene_length_url, "{:.3f}".format(gene_length * 1000.0)),
            avg_expr_val,
            mouse_chr,
            mouse_tx_start,
            human_chr,
            human_tx_start,
            gene_desc,
        ])

    return rows
