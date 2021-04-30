import utility.logger
logger = utility.logger.getLogger(__name__)


class genotype:
    """
    Replacement for reaper.Dataset so we can remove qtlreaper use while still generating mapping output figure
    """

    def __init__(self, filename):
        self.group = None
        self.type = "riset"
        self.prgy = []
        self.nprgy = 0
        self.mat = -1
        self.pat = 1
        self.het = 0
        self.unk = "U"
        self.filler = False
        self.mb_exists = False

        # ZS: This is because I'm not sure if some files switch the column that contains Mb/cM positions; might be unnecessary
        self.cm_column = 2
        self.mb_column = 3

        self.chromosomes = []

        self.read_file(filename)

    def __iter__(self):
        return iter(self.chromosomes)

    def __getitem__(self, index):
        return self.chromosomes[index]

    def __len__(self):
        return len(self.chromosomes)

    def read_rdata_output(self, qtl_results):
        # ZS: This is necessary because R/qtl requires centimorgan marker positions, which it normally gets from the .geno file, but that doesn't exist for HET3-ITP (which only has RData), so it needs to read in the marker cM positions from the results
        # ZS: Overwriting since the .geno file's contents are just placeholders
        self.chromosomes = []

        this_chr = ""  # ZS: This is so it can track when the chromosome changes as it iterates through markers
        chr_ob = None
        for marker in qtl_results:
            locus = Locus(self)
            # ZS: This is really awkward but works as a temporary fix
            if (str(marker['chr']) != this_chr) and this_chr != "X":
                if this_chr != "":
                    self.chromosomes.append(chr_ob)
                this_chr = str(marker['chr'])
                if this_chr == "20":
                    this_chr = "X"
                chr_ob = Chr(this_chr, self)
            if 'chr' in marker:
                locus.chr = str(marker['chr'])
            if 'name' in marker:
                locus.name = marker['name']
            if 'Mb' in marker:
                locus.Mb = marker['Mb']
            if 'cM' in marker:
                locus.cM = marker['cM']
            chr_ob.loci.append(locus)

        self.chromosomes.append(chr_ob)

        return self

    def read_file(self, filename):
        with open(filename, 'r') as geno_file:
            lines = geno_file.readlines()

            this_chr = ""  # ZS: This is so it can track when the chromosome changes as it iterates through markers
            chr_ob = None
            for line in lines:
                if line[0] == "#":
                    continue
                elif line[0] == "@":
                    label = line.split(":")[0][1:]
                    if label == "name":
                        self.group = line.split(":")[1].strip()
                    elif label == "filler":
                        if line.split(":")[1].strip() == "yes":
                            self.filler = True
                    elif label == "type":
                        self.type = line.split(":")[1].strip()
                    elif label == "mat":
                        self.mat = line.split(":")[1].strip()
                    elif label == "pat":
                        self.pat = line.split(":")[1].strip()
                    elif label == "het":
                        self.het = line.split(":")[1].strip()
                    elif label == "unk":
                        self.unk = line.split(":")[1].strip()
                    else:
                        continue
                elif line[:3] == "Chr":
                    header_row = line.split("\t")
                    if header_row[2] == "Mb":
                        self.mb_exists = True
                        self.mb_column = 2
                        self.cm_column = 3
                    elif header_row[3] == "Mb":
                        self.mb_exists = True
                        self.mb_column = 3
                    elif header_row[2] == "cM":
                        self.cm_column = 2

                    if self.mb_exists:
                        self.prgy = header_row[4:]
                    else:
                        self.prgy = header_row[3:]
                    self.nprgy = len(self.prgy)
                else:
                    if line.split("\t")[0] != this_chr:
                        if this_chr != "":
                            self.chromosomes.append(chr_ob)
                        this_chr = line.split("\t")[0]
                        chr_ob = Chr(line.split("\t")[0], self)
                    chr_ob.add_marker(line.split("\t"))

            self.chromosomes.append(chr_ob)


class Chr:
    def __init__(self, name, geno_ob):
        self.name = name
        self.loci = []
        self.mb_exists = geno_ob.mb_exists
        self.cm_column = geno_ob.cm_column
        self.mb_column = geno_ob.mb_column
        self.geno_ob = geno_ob

    def __iter__(self):
        return iter(self.loci)

    def __getitem__(self, index):
        return self.loci[index]

    def __len__(self):
        return len(self.loci)

    def add_marker(self, marker_row):
        self.loci.append(Locus(self.geno_ob, marker_row))


class Locus:
    def __init__(self, geno_ob, marker_row=None):
        self.chr = None
        self.name = None
        self.cM = None
        self.Mb = None
        self.genotype = []
        if marker_row:
            self.chr = marker_row[0]
            self.name = marker_row[1]
            try:
                self.cM = float(marker_row[geno_ob.cm_column])
            except:
                self.cM = float(
                    marker_row[geno_ob.mb_column]) if geno_ob.mb_exists else 0
            try:
                self.Mb = float(
                    marker_row[geno_ob.mb_column]) if geno_ob.mb_exists else None
            except:
                self.Mb = self.cM

            geno_table = {
                geno_ob.mat: -1,
                geno_ob.pat: 1,
                geno_ob.het: 0,
                geno_ob.unk: "U"
            }

            self.genotype = []
            if geno_ob.mb_exists:
                start_pos = 4
            else:
                start_pos = 3

            for allele in marker_row[start_pos:]:
                if allele in list(geno_table.keys()):
                    self.genotype.append(geno_table[allele])
                else:  # ZS: Some genotype appears that isn't specified in the metadata, make it unknown
                    self.genotype.append("U")
