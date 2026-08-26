"""Track data (Gene Band / Homology Band / Haplotype Band) for the
interactive d3 mapping figure.

The d3 figure focuses chromosomes client-side, so the track data for a
given chromosome/range is fetched on demand via ``/mapping/track_data``.
This module builds that data, mirroring the original PIL band drawing in
``display_mapping_results.py`` (``drawGeneBand`` / ``drawHomologyBand`` /
``drawHaplotypeBand``).
"""
from gn2.base import data_set
from gn2.utility.tools import get_setting
from gn2.wqflask.interval_analyst import GeneUtil
from gn_libs.mysqldb import database_connection

# SNP-density thresholds used to colour the gene band (mirrors drawGeneBand).
GENE_DENSITIES = [
    1.0000000000000001e-05,
    0.094094033555233408,
    0.3306166377816987,
    0.88246026851027781,
    2.6690084029581951,
    4.1,
    61.0,
]


def gene_color(snp_density):
    """Colour for a gene based on SNP density (mirrors drawGeneBand)."""
    if snp_density < GENE_DENSITIES[0]:
        return "#000000"   # BLACK
    if snp_density < GENE_DENSITIES[1]:
        return "#800080"   # PURPLE
    if snp_density < GENE_DENSITIES[2]:
        return "#00008B"   # DARKBLUE
    if snp_density < GENE_DENSITIES[3]:
        return "#006400"   # DARKGREEN
    if snp_density < GENE_DENSITIES[4]:
        return "#FFD700"   # GOLD
    if snp_density < GENE_DENSITIES[5]:
        return "#FF8C00"   # DARKORANGE
    return "#8B0000"       # DARKRED


def _as_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _compact_gene(theGO, species, detail):
    """Reduce a loadGenes() dict to the fields the d3 figure needs.

    ``detail`` controls whether exon/UTR structure is included; it is only
    needed when the visible range is small enough (<= DRAW_DETAIL_MB) for the
    detail view, otherwise genes are drawn as simple rectangles.
    """
    exon_starts = []
    exon_ends = []
    if detail and theGO.get("exonStarts"):
        exon_starts = [
            _as_float(v) for v in str(theGO["exonStarts"]).split(",")[:-1]]
        exon_ends = [
            _as_float(v) for v in str(theGO["exonEnds"]).split(",")[:-1]]
    return {
        "sym": theGO.get("GeneSymbol", ""),
        "nm": theGO.get("NM_ID", ""),
        "strand": theGO.get("Strand", ""),
        "txStart": _as_float(theGO.get("TxStart")),
        "txEnd": _as_float(theGO.get("TxEnd")),
        "exons": [
            [s, e] for s, e in zip(exon_starts, exon_ends) if s is not None],
        "cdsStart": (_as_float(theGO.get("cdsStart")) if detail else None),
        "cdsEnd": (_as_float(theGO.get("cdsEnd")) if detail else None),
        "snpDensity": _as_float(theGO.get("snpDensity")) or 0.0,
    }


def _resolve_diff_col(diff_col):
    """Resolve strain symbols (e.g. 'B6J') to Strain Ids, keeping ints as-is.

    ``self.diffCol`` in the mapping flow is already resolved to Strain Ids, but
    this makes the endpoint robust to symbol-based input too.
    """
    resolved = []
    with database_connection(get_setting("SQL_URI")) as conn, conn.cursor() as cur:
        for entry in diff_col or []:
            if isinstance(entry, int):
                resolved.append(entry)
                continue
            cur.execute("SELECT Id FROM Strain WHERE Symbol = %s",
                        (str(entry),))
            row = cur.fetchone()
            resolved.append(row[0] if row else entry)
    return resolved


def build_genes(chr_name, diff_col, start_mb, end_mb, species, detail=False):
    """Compact gene list for the given chromosome/range (mouse & rat only)."""
    if species not in ("mouse", "rat"):
        return []
    diff_col = _resolve_diff_col(diff_col)
    # The other-species gene merge is unused for the track and costs a query
    # per gene; skip it so the endpoint stays fast for whole chromosomes.
    genes = GeneUtil.loadGenes(
        str(chr_name), diff_col or [], start_mb, end_mb, species,
        merge_other_species=False)
    out = []
    for theGO in genes:
        gene = _compact_gene(theGO, species, detail)
        # Rat has no exon/SNP data -> always DARKBLUE (mirrors drawGeneBand).
        gene["color"] = "#00008B" if species == "rat" else gene_color(
            gene["snpDensity"])
        out.append(gene)
    return out


def build_homology(chr_name, start_mb, end_mb, species):
    """Homology blocks for the given chromosome/range (mouse only)."""
    if species != "mouse":
        return []
    return GeneUtil.load_homology(
        str(chr_name), start_mb, end_mb, "mouse_to_human.csv")


# Cache the parsed genotype object per (dataset, genofile) so the haplotype
# band does not re-read the .geno file on every chromosome focus.
_GENOTYPE_CACHE = {}


def cache_genotype(dataset_name, genofile_string, genotype):
    """Pre-cache a genotype object that the mapping flow already parsed.

    Called at page-build time so the first client-side focus does not have
    to re-read the .geno file.
    """
    if not dataset_name or genotype is None:
        return
    key = (dataset_name, (genofile_string or "").split(":")[0])
    _GENOTYPE_CACHE.setdefault(key, genotype)


def build_haplotype(dataset_name, chr_name, genofile_string, sample_vals,
                    start_mb=None, end_mb=None):
    """Per-strain genotype + expression data for the haplotype band.

    Returns ``None`` if the dataset/genotype cannot be resolved. Markers
    outside the requested range are dropped (mirrors drawHaplotypeBand).
    """
    if not dataset_name or not chr_name:
        return None
    try:
        dataset = data_set.create_dataset(dataset_name)
    except Exception:
        return None
    if genofile_string:
        dataset.group.genofile = genofile_string.split(":")[0]
    cache_key = (dataset_name, dataset.group.genofile)
    if cache_key not in _GENOTYPE_CACHE:
        try:
            _GENOTYPE_CACHE[cache_key] = dataset.group.read_genotype_file()
        except Exception:
            return None
    genotype = _GENOTYPE_CACHE[cache_key]
    strains = list(getattr(genotype, "prgy", []) or [])
    markers = []
    for chr_ob in genotype:
        if str(chr_ob.name) == str(chr_name):
            for locus in chr_ob:
                mb = locus.Mb
                if start_mb is not None and mb is not None and mb < start_mb:
                    continue
                if end_mb is not None and mb is not None and mb > end_mb:
                    continue
                markers.append({
                    "n": locus.name,
                    "m": mb,
                    "g": list(locus.genotype),
                })
            break
    if not markers:
        return None
    return {
        "strains": strains,
        "markers": markers,
        "values": sample_vals or {},
    }
