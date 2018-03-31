import utility.logger
logger = utility.logger.getLogger(__name__ )

def gen_reaper_results(this_trait, dataset, samples_before, trait_vals, json_data, num_perm, bootCheck, num_bootstrap, do_control, control_marker, manhattan_plot):
    genotype = dataset.group.read_genotype_file()

    if manhattan_plot != True:
        genotype = genotype.addinterval()

    trimmed_samples = []
    trimmed_values = []
    for i in range(0, len(samples_before)):
        try:
            trimmed_values.append(float(trait_vals[i]))
            trimmed_samples.append(samples_before[i])
        except:
            pass

    perm_output = []
    bootstrap_results = []

    if num_perm < 100:
        suggestive = 0
        significant = 0
    else:
        perm_output = genotype.permutation(strains = trimmed_samples, trait = trimmed_values, nperm=num_perm)
        suggestive = perm_output[int(num_perm*0.37-1)]
        significant = perm_output[int(num_perm*0.95-1)]
        highly_significant = perm_output[int(num_perm*0.99-1)]

    json_data['suggestive'] = suggestive
    json_data['significant'] = significant

    if control_marker != "" and do_control == "true":
        reaper_results = genotype.regression(strains = trimmed_samples,
                                             trait = trimmed_values,
                                             control = str(control_marker))
        if bootCheck:
            control_geno = []
            control_geno2 = []
            _FIND = 0
            for _chr in genotype:
                for _locus in _chr:
                    if _locus.name == control_marker:
                        control_geno2 = _locus.genotype
                        _FIND = 1
                        break
                if _FIND:
                    break
            if control_geno2:
                _prgy = list(genotype.prgy)
                for _strain in trimmed_samples:
                    _idx = _prgy.index(_strain)
                    control_geno.append(control_geno2[_idx])

            bootstrap_results = genotype.bootstrap(strains = trimmed_samples,
                                                        trait = trimmed_values,
                                                        control = control_geno,
                                                        nboot = num_bootstrap)
    else:
        reaper_results = genotype.regression(strains = trimmed_samples,
                                             trait = trimmed_values)

        if bootCheck:
            bootstrap_results = genotype.bootstrap(strains = trimmed_samples,
                                                        trait = trimmed_values,
                                                        nboot = num_bootstrap)

    json_data['chr'] = []
    json_data['pos'] = []
    json_data['lod.hk'] = []
    json_data['markernames'] = []
    #if self.additive:
    #    self.json_data['additive'] = []

    #Need to convert the QTL objects that qtl reaper returns into a json serializable dictionary
    qtl_results = []
    for qtl in reaper_results:
        reaper_locus = qtl.locus
        #ZS: Convert chr to int
        converted_chr = reaper_locus.chr
        if reaper_locus.chr != "X" and reaper_locus.chr != "X/Y":
            converted_chr = int(reaper_locus.chr)
        json_data['chr'].append(converted_chr)
        json_data['pos'].append(reaper_locus.Mb)
        json_data['lod.hk'].append(qtl.lrs)
        json_data['markernames'].append(reaper_locus.name)
        #if self.additive:
        #    self.json_data['additive'].append(qtl.additive)
        locus = {"name":reaper_locus.name, "chr":reaper_locus.chr, "cM":reaper_locus.cM, "Mb":reaper_locus.Mb}
        qtl = {"lrs_value": qtl.lrs, "chr":converted_chr, "Mb":reaper_locus.Mb,
               "cM":reaper_locus.cM, "name":reaper_locus.name, "additive":qtl.additive, "dominance":qtl.dominance}
        qtl_results.append(qtl)
    return qtl_results, json_data, perm_output, suggestive, significant, bootstrap_results
