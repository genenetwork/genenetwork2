import csv
import os

input_dir = "/export2/local/home/zas1024/gn2-zach/hxbbxh-genotypes/hao/error0.001"
output_dir = "/export2/local/home/zas1024/gn2-zach/hxbbxh-genotypes/hao/output"

base_dict = {
    '0': 'B',
    '2': 'D',
    '1': 'H'
}

chromosomes = ["1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18","19","20","X","Y"]
sample_list = ["BXH2","BXH3","BXH5","BXH6","BXH8","BXH9","BXH10","BXH11","BXH12","BXH12a","BXH13","HXB1","HXB2","HXB3","HXB4","HXB5","HXB7","HXB9","HXB10","HXB13","HXB14","HXB15","HXB16","HXB17","HXB18","HXB19","HXB20","HXB21","HXB22","HXB23","HXB24","HXB25","HXB26","HXB27","HXB29","HXB30","HXB31"]

row_list = [
    ["#type riset or intercross"],
    ["@type:riset"],
    ["@name:HXB/BXH"],
    ["#abbreviation of maternal or paternal parents"],
    ["@mat:B"],
    ["@pat:D"],
    ["#heterozygous , optional, default is \"H\""],
    ["@het:H"],
    ["#Unknown , optional, default is \"U\""],
    ["@unk:U"]
]

file_sample_list = []
trimmed_samples = []

# This is a convoluted way to fix the order of samples to be the same as in GN
sample_mapping = []

for chromosome in chromosomes:
    f = os.path.join(input_dir, f"HXB_genotype_chr{chromosome}_dup_removed_smoothed_by_rqtl_error0.001_dup_removed_again_012.csv")
    if os.path.isfile(f):
        with open(f, "r") as the_file:
            all_rows = [row.split() for row in the_file]
            all_rows = [[item.replace('"', '') for item in col] for col in zip(*all_rows)]

            if not len(file_sample_list):
                file_sample_list = [sample.replace("_mRatNor1", "").split("_")[0] for sample in all_rows[0][4:-1]]
                for sample in sample_list:
                    if sample in file_sample_list:
                        trimmed_samples.append(sample)
                        sample_mapping.append(file_sample_list.index(sample))

            row_list.append(["Chr", "Locus", "cM", "Mb"] + trimmed_samples)
            for row in all_rows[1:]:
                this_mb = str(float(row[0].split(":")[1])/1000000)
                this_row = [row[1], row[0], row[2], this_mb]
                genotypes = row[4:-1]
                for i in range(len(trimmed_samples)):
                    this_row.append(base_dict[genotypes[sample_mapping[i]]])
                row_list.append(this_row)

with open(os.path.join(output_dir, "HXBBXH_new.geno"), "w") as out_file:
    for line in row_list:
        out_file.write("\t".join(line) + "\n")
