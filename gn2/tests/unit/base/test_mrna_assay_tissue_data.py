import pytest
from gn2.base.mrna_assay_tissue_data import MrnaAssayTissueData


@pytest.mark.parametrize(
    ('gene_symbols', 'expected_query', 'sql_fetch_all_results'),
    (
        (None,
         (("SELECT t.Symbol, t.GeneId, t.DataId, "
           "t.Chr, t.Mb, t.description, "
           "t.Probe_Target_Description "
           "FROM (SELECT Symbol, "
           "max(Mean) AS maxmean "
           "FROM TissueProbeSetXRef WHERE "
           "TissueProbeSetFreezeId=1 AND "
           "Symbol != '' AND Symbol IS NOT "
           "Null GROUP BY Symbol) "
           "AS x INNER JOIN TissueProbeSetXRef "
           "AS t ON t.Symbol = x.Symbol "
           "AND t.Mean = x.maxmean"),),
         (("symbol", "gene_id",
           "data_id", "chr", "mb",
           "description",
           "probe_target_description"),)),
        (["k1", "k2", "k3"],
         ("SELECT t.Symbol, t.GeneId, t.DataId, "
          "t.Chr, t.Mb, t.description, "
          "t.Probe_Target_Description FROM (SELECT Symbol, "
          "max(Mean) AS maxmean "
          "FROM TissueProbeSetXRef WHERE "
          "TissueProbeSetFreezeId=1 AND "
          "Symbol IN (%s, %s, %s) "
          "GROUP BY Symbol) AS x INNER JOIN "
          "TissueProbeSetXRef AS "
          "t ON t.Symbol = x.Symbol "
          "AND t.Mean = x.maxmean",
          ("k1", "k2", "k3")),
         (("k1", "203",
           "112", "xy", "20.11",
           "Sample Description",
           "Sample Probe Target Description"),)),
    ),
)
def test_mrna_assay_tissue_data_initialisation(mocker, gene_symbols,
                                               expected_query,
                                               sql_fetch_all_results):
    mock_conn = mocker.MagicMock()
    with mock_conn.cursor() as cursor:
        cursor.fetchall.return_value = sql_fetch_all_results
        MrnaAssayTissueData(conn=mock_conn, gene_symbols=gene_symbols)
        cursor.execute.assert_called_with(*expected_query)


def test_get_trait_symbol_and_tissue_values(mocker):
    """Test for getting trait symbol and tissue_values"""
    mock_conn = mocker.MagicMock()
    with mock_conn.cursor() as cursor:
        cursor.fetchall.side_effect = [
            (("k1", "203",
              "112", "xy", "20.11",
              "Sample Description",
              "Sample Probe Target Description"),),
            (("k1", "v1"),
             ("k2", "v2"),
             ("k3", "v3")),
        ]
        _m = MrnaAssayTissueData(conn=mock_conn,
                                 gene_symbols=["k1", "k2", "k3"])
        assert _m.get_symbol_values_pairs() == {
            "k1": ["v1"],
            "k2": ["v2"],
            "k3": ["v3"],
        }
        cursor.execute.assert_called_with(
            "SELECT TissueProbeSetXRef.Symbol, "
            "TissueProbeSetData.value FROM "
            "TissueProbeSetXRef, TissueProbeSetData "
            "WHERE TissueProbeSetData.Id IN (%s) "
            "AND TissueProbeSetXRef.DataId = "
            "TissueProbeSetData.Id",
            ('112',))
