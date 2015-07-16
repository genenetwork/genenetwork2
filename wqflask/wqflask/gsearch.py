from __future__ import absolute_import, print_function, division

from flask import Flask, g

class GSearch(object):

	def __init__(self, kw):
		if 'species' in kw and 'group' in kw:
			self.species = kw['species']
			self.group = kw['group']
			self.terms = kw['terms']
			sql = """
				SELECT InbredSet.`Id`
				FROM InbredSet,Species
				WHERE InbredSet.`Name` LIKE "%s"
				AND InbredSet.`SpeciesId`=Species.`Id`
				AND Species.`Name` LIKE "%s"
				""" % (self.group, self.species)
			dbre = g.db.execute(sql).fetchone()
			self.inbredset_id = dbre[0]
			sql = """
				SELECT DISTINCT 0,
				Tissue.`Name` AS tissue_name,
				ProbeSetFreeze.FullName AS probesetfreeze_fullname,
				ProbeSet.Name AS probeset_name,
				ProbeSet.Symbol AS probeset_symbol,
				ProbeSet.`description` AS probeset_description,
				ProbeSet.Chr AS chr,
				ProbeSet.Mb AS mb,
				ProbeSetXRef.Mean AS mean,
				ProbeSetXRef.LRS AS lrs,
				ProbeSetXRef.`Locus` AS locus,
				ProbeSetXRef.`pValue` AS pvalue,
				ProbeSetXRef.`additive` AS additive
				FROM InbredSet, ProbeSetXRef, ProbeSet, ProbeFreeze, ProbeSetFreeze, Tissue
				WHERE ProbeFreeze.InbredSetId=%s
				AND ProbeFreeze.`TissueId`=Tissue.`Id`
				AND ProbeSetFreeze.ProbeFreezeId=ProbeFreeze.Id
				AND ( MATCH (ProbeSet.Name,ProbeSet.description,ProbeSet.symbol,alias,GenbankId, UniGeneId, Probe_Target_Description) AGAINST ('%s' IN BOOLEAN MODE) )
				AND ProbeSet.Id = ProbeSetXRef.ProbeSetId
				AND ProbeSetXRef.ProbeSetFreezeId=ProbeSetFreeze.Id
				ORDER BY tissue_name, probesetfreeze_fullname, probeset_name
				LIMIT 1000
				""" % (self.inbredset_id, self.terms)
			self.results = g.db.execute(sql).fetchall()
		elif 'species' in kw:
			self.species = kw['species']
			self.terms = kw['terms']
			sql = """
				SELECT Species.`Id`
				FROM Species
				WHERE Species.`Name` LIKE "%s"
				""" % (self.species)
			dbre = g.db.execute(sql).fetchone()
			self.species_id = dbre[0]
			sql = """
				SELECT DISTINCT 0,
				InbredSet.`Name` AS inbredset_name,
				Tissue.`Name` AS tissue_name,
				ProbeSetFreeze.FullName AS probesetfreeze_fullname,
				ProbeSet.Name AS probeset_name,
				ProbeSet.Symbol AS probeset_symbol,
				ProbeSet.`description` AS probeset_description,
				ProbeSet.Chr AS chr,
				ProbeSet.Mb AS mb,
				ProbeSetXRef.Mean AS mean,
				ProbeSetXRef.LRS AS lrs,
				ProbeSetXRef.`Locus` AS locus,
				ProbeSetXRef.`pValue` AS pvalue,
				ProbeSetXRef.`additive` AS additive
				FROM InbredSet, ProbeSetXRef, ProbeSet, ProbeFreeze, ProbeSetFreeze, Tissue
				WHERE InbredSet.`SpeciesId`=%s
				AND ProbeFreeze.InbredSetId=InbredSet.`Id`
				AND ProbeFreeze.`TissueId`=Tissue.`Id`
				AND ProbeSetFreeze.ProbeFreezeId=ProbeFreeze.Id
				AND ( MATCH (ProbeSet.Name,ProbeSet.description,ProbeSet.symbol,alias,GenbankId, UniGeneId, Probe_Target_Description) AGAINST ('%s' IN BOOLEAN MODE) )
				AND ProbeSet.Id = ProbeSetXRef.ProbeSetId
				AND ProbeSetXRef.ProbeSetFreezeId=ProbeSetFreeze.Id
				ORDER BY inbredset_name, tissue_name, probesetfreeze_fullname, probeset_name
				LIMIT 1000
				""" % (self.species_id, self.terms)
			self.results = g.db.execute(sql).fetchall()
		else:
			self.terms = kw['terms']
			sql = """
				SELECT
				Species.`Name` AS species_name,
				InbredSet.`Name` AS inbredset_name,
				Tissue.`Name` AS tissue_name,
				ProbeSetFreeze.FullName AS probesetfreeze_fullname,
				ProbeSet.Name AS probeset_name,
				ProbeSet.Symbol AS probeset_symbol,
				ProbeSet.`description` AS probeset_description,
				ProbeSet.Chr AS chr,
				ProbeSet.Mb AS mb,
				ProbeSetXRef.Mean AS mean,
				ProbeSetXRef.LRS AS lrs,
				ProbeSetXRef.`Locus` AS locus,
				ProbeSetXRef.`pValue` AS pvalue,
				ProbeSetXRef.`additive` AS additive
				FROM Species, InbredSet, ProbeSetXRef, ProbeSet, ProbeFreeze, ProbeSetFreeze, Tissue
				WHERE InbredSet.`SpeciesId`=Species.`Id`
				AND ProbeFreeze.InbredSetId=InbredSet.`Id`
				AND ProbeFreeze.`TissueId`=Tissue.`Id`
				AND ProbeSetFreeze.ProbeFreezeId=ProbeFreeze.Id
				AND ( MATCH (ProbeSet.Name,ProbeSet.description,ProbeSet.symbol,alias,GenbankId, UniGeneId, Probe_Target_Description) AGAINST ('%s' IN BOOLEAN MODE) )
				AND ProbeSet.Id = ProbeSetXRef.ProbeSetId
				AND ProbeSetXRef.ProbeSetFreezeId=ProbeSetFreeze.Id
				ORDER BY species_name, inbredset_name, tissue_name, probesetfreeze_fullname, probeset_name
				LIMIT 1000
				""" % (self.terms)
			self.results = g.db.execute(sql).fetchall()
