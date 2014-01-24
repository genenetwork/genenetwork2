from __future__ import absolute_import, print_function, division

from base import data_set
from base.species import TheSpecies
    
    def run(dataset_name, vals, temp_uuid):
        """Generates p-values for each marker"""

        tempdata = temp_data.TempData(temp_uuid)
        
        dataset = data_set.create_dataset(dataset_name)
        species = TheSpecies(dataset=dataset)

        samples = [] # Want only ones with values
        vals = vals

        for sample in dataset.group.samplelist:
            samples.append(str(sample))
            
        gen_data(dataset, vals, tempdata)


    def gen_data(dataset, vals)
        dataset.group.get_markers()

        pheno_vector = np.array([val == "x" and np.nan or float(val) for val in vals])

        if dataset.group.species == "human":
            p_values, t_stats = gen_human_results(pheno_vector, tempdata)
        else:
            genotype_data = [marker['genotypes'] for marker in self.dataset.group.markers.markers]
            
            no_val_samples = self.identify_empty_samples()
            trimmed_genotype_data = self.trim_genotypes(genotype_data, no_val_samples)
            
            genotype_matrix = np.array(trimmed_genotype_data).T
            
            #print("pheno_vector: ", pf(pheno_vector))
            #print("genotype_matrix: ", pf(genotype_matrix))
            #print("genotype_matrix.shape: ", pf(genotype_matrix.shape))
            
            t_stats, p_values = lmm.run(
                pheno_vector,
                genotype_matrix,
                restricted_max_likelihood=True,
                refit=False,
                temp_data=tempdata
            )
            #print("p_values:", p_values)
        
        self.dataset.group.markers.add_pvalues(p_values)
        return self.dataset.group.markers.markers


    def gen_human_results(self, pheno_vector, tempdata):
        file_base = os.path.join(webqtlConfig.PYLMM_PATH, self.dataset.group.name)

        plink_input = input.plink(file_base, type='b')
        input_file_name = os.path.join(webqtlConfig.SNP_PATH, self.dataset.group.name + ".snps.gz")

        pheno_vector = pheno_vector.reshape((len(pheno_vector), 1))
        covariate_matrix = np.ones((pheno_vector.shape[0],1))
        kinship_matrix = np.fromfile(open(file_base + '.kin','r'),sep=" ")
        kinship_matrix.resize((len(plink_input.indivs),len(plink_input.indivs)))

        p_values, t_stats = lmm.run_human(
                pheno_vector,
                covariate_matrix,
                input_file_name,
                kinship_matrix,
                loading_progress=tempdata
            )

        return p_values, t_stats
    
if __name__ == '__main__':
    run(dataset_name, vals, temp_uuid)