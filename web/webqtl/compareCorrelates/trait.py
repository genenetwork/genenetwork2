#Trait.py
#
#--Individual functions are already annotated, more or less.
#
#Classes:
#RawPoint
#Trait
#ProbeSetTrait
#GenotypeTrait
#PublishTrait
#TempTrait
#-KA

# trait.py: a data structure to represent a trait
import time
import string

CONFIG_pubMedLinkURL = "http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&list_uids=%s&dopt=Abstract"

# RawPoint: to store information about the relationship between two particular
# traits
# RawPoint represents directly the input file
class RawPoint:
    def __init__(self, i, j):
        self.i = i
        self.j = j
        
    def __eq__(self, other):
        return (self.i == other.i and
                self.j == other.j and
                self.spearman == other.spearman and
                self.pearson == other.pearson)
    
    def __str__(self):
        return "(%s,%s,%s,%s)" % (self.i, self.j, self.spearman, self.pearson)

def tdEscapeList(cols, align="left"):
    """
    A helper function used by tableRow
    in Trait that will convert a list of strings into a set of
    table cells enclosed by <td>%s</td> tags
    """
    html = ""
    for col in cols:
        html += '<td style="text-align: %s">%s</td>' % (align, col)
    return html

def thEscapeList(cols):
    """
    A helper function used by tableRowHeader
    in Trait that will convert a list of strings into a set of
    table cells enclosed by <td>%s</td> tags
    """
    html = ""
    for col in cols:
        html += "<th>%s</th>" % col
    return html

def commaEscapeList(cols):
    """
    A helper function used by csvHeader and csvRow.
    Really it's just a wrapper for string.join
    """
    return '"' + string.join(cols, '","') + '"'


class Trait:
    """
    A trait represents an attribute of an object. In the WebQTL database, traits are stored
    as ProbeSets; that is, the average values of a set of probes are stored.
    """
    def __init__(self, id="", name="", description="", symbol="", href=""):
        self.id  = id
        self.name = name
	self.dbName = ""
        self.symbol = symbol
        self.href = href
        self.strainData = {}

    def populateDataId(self, cursor, freezeId):
        """
        Retrieve the dataId for trait data corresponding to the given database
        The way to do this depends on the particular type of trait, so we leave implementation
        to subclasses.
        """
        raise NotImplementedError
    
    def populateStrainData(self, cursor):
        """
        Load this trait full of train data corresponding to the data id
        The data id can either come from populateDataId
        or can be set manually by the user of this class.
        Xiaodong added: The way to do this depends on the particular type of trait,
        so we leave implementation to subclasses.

        """
        raise NotImplementedError

    def shortName(self):
        """
        To return a short name for this trait; this name should be
        appropriate for a row or column title
        """
        return self.name

    def nameNoDB(self):
        """
        To return only the short name without the database attached
        """
        strArray = self.shortName().split('::')
        
        return strArray[1]
    
    def datasetName(self):
        """
        To return only the name of the dataset
        """
        strArray = self.shortName().split('::')
        
        return strArray[0].strip()

    def longName(self):
        """
        To return a long name for this trait; this name should be
        appropriate for a key to a table
        """
        return self.shortName()

    def __str__(self):
        return self.shortName()

    def tableRowHelper(self, beforeCols, afterCols, color, thisRow):
        """
        tableRowHelper: (arrayof String) -. String
        To generate a table row to represent this object, appending
        the additional information in beforeCols and afterCols
        to the beginning and the end
        """
        thisRow[0] = '<a href="%s">%s</a>' % (self.traitInfoLink(),
                                              self.name)
        html = '<tr bgcolor="%s">' % color
        html += tdEscapeList(beforeCols + thisRow)
        html += tdEscapeList(afterCols, align="right")
        html += "</tr>"
        
        return html


    def header(self):
        """
        header: (listof String)
        To generate a list of strings describing each piece of data
        returned by row
        """
        raise NotImplementedError

    def row(self):
        """
        row: (listof String)
        To generate a list of strings describing this object. The
        elements of this list should be described by header()
        """
        raise NotImplementedError
    
    def tableRowHeader(self, beforeCols, afterCols, color):
        """
        tableRowHeader: (arrayof String) -> (arrayof String) -> String
        To generate a table row header to represent this object,
        appending the additional information in beforeCols and
        afterCols to the beginning and end
        """
        html = '<tr bgcolor="%s">' % color
        html += thEscapeList(beforeCols + self.header() +
                             afterCols)
        html += "</tr>"
        return html

    def csvHeader(self, beforeCols, afterCols):
        return commaEscapeList(beforeCols + self.header() + afterCols)
    
    def csvRow(self, beforeCols, afterCols):
        return commaEscapeList(beforeCols + self.row() + afterCols)
    
        
    def traitInfoLink(self):
        """
        To build a trait info link to show information about this
        trait. We assume that the database attribute is properly set
        on the hidden form on the page where this link will go.
        """
        return "javascript:showDatabase2('%s','%s','')" % (self.dbName, self.name)

# ProbeSetTrait: a trait with data from a probeset
class ProbeSetTrait(Trait):
    def __init__(self, id="", name="", description="", symbol="", href="",
                 chromosome="", MB="", GeneId=""):
        Trait.__init__(self, id=id, name=name, href=href)
        self.description = description
        self.symbol = symbol
        self.chromosome = chromosome
        self.MB = MB
        self.GeneId = GeneId
        
    def populateDataId(self, cursor, freezeId):
        """
        Look up the data id for this trait given which
        freeze it came from.
        """
        cursor.execute('''
        SELECT
          ProbeSetXRef.DataId
        FROM
          ProbeSetXRef
        WHERE
          ProbeSetId = %s AND
          ProbeSetFreezeId = %s
        ''' % (self.id, freezeId))

        # we hope that there's only one record here
        row = cursor.fetchone()
        self.dataId = row[0]

    #XZ, 03/03/2009: Xiaodong implemented this fuction
    def populateStrainData(self, cursor):
        cursor.execute('''
        SELECT
          ProbeSetData.StrainId,
          ProbeSetData.value
        FROM
          ProbeSetData
        WHERE
          ProbeSetData.Id = %s''' % self.dataId)
        for row in cursor.fetchall():
            self.strainData[int(row[0])] = float(row[1])


    def shortName(self):
        """
        An improved string method that uses the gene symbol where
        we have it
        """
        if self.symbol != "":
            return self.symbol
        else:
            return Trait.shortName(self)

    def longName(self):
        """
        We use several bits of genetic information to give
        useful information about this trait and where it is
        """
        if self.chromosome != "":
            chrPart = " (%s on Chr %s @ %s Mb)" % (self.symbol,
                                                     self.chromosome,
                                                     self.MB)
        else:
            chrPart = ""

        return "%s%s: %s" % (self.name, chrPart, self.description)

    def header(self):
        return ["Name", "Symbol", "Description",
                "Chr", "Position (Mb)"]

    def row(self):
        if type(self.MB) is float:
            MB = "%.2f" % self.MB
        else:
            MB = ""
            
        return [self.name, self.symbol, self.description,
                self.chromosome, MB]
    
    def tableRow(self, beforeCols, afterCols, color):
        """
        tableRow: (arrayof String) -> (arrayof String) -> String
        To generate a table row to represent this object, appending
        the additional information in beforeCols and afterCols to the
        beginning and end
        """
        thisRow = self.row()

        # trim description
        if len(thisRow[2]) > 20:
            thisRow[2] = thisRow[2][:20] + "..."

        # add NCBI info link 
        thisRow[1] = self.ncbiInfoLink()

        return self.tableRowHelper(beforeCols, afterCols, color,
                                   thisRow)


    def ncbiInfoLink(self):
        """
        ncbiInfoLink :: String
        To generate an NCBI info link for this trait. If we have a GeneId,
        then we can go straight to the gene. If not, then we generate a search
        link based on the gene symbol. If we have none of them, then we don't
        generate a link at all.
        """
        if self.GeneId != "":
            cmd = "cmd=Retrieve&dopt=Graphics&list_uids=%s" % self.GeneId
        elif self.symbol != "":
            cmd = "cmd=Search&term=%s" % self.symbol
        else:
            return ""

        return '''
        <a target="_new"
           href="http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?db=gene&%s">
           %s</a> ''' % (cmd, self.symbol)


# GenotypeTrait: a trait with data from the genotype
class GenotypeTrait(Trait):
    def __init__(self, id="", name="", href="", chromosome="", MB=""):
        Trait.__init__(self, id=id, name=name, href=href)
        self.chromosome = chromosome
        self.MB = MB

    def populateDataId(self, cursor, freezeId):
        """
        Look up the data id for this trait from the
        genotype.
        """
        cursor.execute('''
        SELECT
          GenoXRef.DataId
        FROM
          GenoXRef
        WHERE
          GenoId = %s AND
          GenoFreezeId = %s
        ''' % (self.id, freezeId))

        # we hope that there's only one record here
        row = cursor.fetchone()
        self.dataId = row[0]

    #XZ, 03/03/2009: Xiaodong implemented this fuction
    def populateStrainData(self, cursor):
        cursor.execute('''
        SELECT
          GenoData.StrainId,
          GenoData.value
        FROM
          GenoData
        WHERE
          GenoData.Id = %s''' % self.dataId)
        for row in cursor.fetchall():
            self.strainData[int(row[0])] = float(row[1])

    def header(self):
        return ["Locus", "Chr", "Position (Mb)"]

    def row(self):
        return [self.name, self.chromosome, "%.3f" % self.MB]

    def tableRow(self, beforeCols, afterCols, color):
        return self.tableRowHelper(beforeCols, afterCols, color, self.row())

# PublishTrait: a trait with data from publications
class PublishTrait(Trait):
    def __init__(self, id="", name="", href="", authors="", title="",
                 phenotype="", year=""):
        Trait.__init__(self, id=id, name=name, href=href)
        self.authors = authors
        self.title = title
        self.phenotype = phenotype
        self.year = year

    def populateDataId(self, cursor, freezeId):
        """
        Look up the data id for this trait from the
        published set. For the moment, we assume that there's
        only one publish freeze.
        """
        cursor.execute('''
        SELECT
          PublishXRef.DataId
        FROM
          PublishXRef, PublishFreeze
        WHERE
          PublishFreeze.Id = %s AND 
          PublishFreeze.InbredSetId = PublishXRef.InbredSetId AND
          PublishXRef.Id = %s 
        ''' % (freezeId, self.id))

        # we hope that there's only one record here
        row = cursor.fetchone()
        self.dataId = row[0]

    #XZ, 03/03/2009: Xiaodong implemented this fuction
    def populateStrainData(self, cursor):
        cursor.execute('''
        SELECT
          PublishData.StrainId,
          PublishData.value
        FROM
          PublishData
        WHERE
          PublishData.Id = %s''' % self.dataId)
        for row in cursor.fetchall():
            self.strainData[int(row[0])] = float(row[1])


    def longName(self):
        """
        A more intelligent string function that uses
        information about the publication from which this trait came
        """
        return "%s: %s by %s" % (self.name, self.title, self.authors)

    def header(self):
        return ["Record", "Phenotype", "Authors", "Year", "URL"]

    def row(self):
        return [self.name,
                self.phenotype,
                self.authors,
                str(self.year),
                ""]
    
    def tableRow(self, beforeCols, afterCols, color):
        """
        tableRow: (arrayof String) -> (arrayof String) ->  String
        To generate a table row to represent this object, appending
        the additional information in beforeCols and afterCols to the
        beginning and end
        """
        thisRow = self.row()

        # for multiple authors, use "et. al" after first two
        authors = thisRow[2].split(",")
        if len(authors) > 2:
            thisRow[2] = string.join(authors[:2], ",") + ", et al"

        # clip phenotype to 20 chars
        if len(thisRow[1]) > 20:
            thisRow[1] = thisRow[1][:20] + "..."

        # add Pub Med URL
        thisRow[4] = '<a href="%s" target="_new">Pub Med</a>' % (CONFIG_pubMedLinkURL % self.href)

        return self.tableRowHelper(beforeCols, afterCols, color,
                                   thisRow)


# TempTrait: a trait with data generate by user and stored in temp table
class TempTrait(Trait):
    def __init__(self, id="", name="", href="", description=""):
        Trait.__init__(self, id=id, name=name, href=href)
        self.description = description

    def populateDataId(self, cursor, freeezeId):
        """
        Look up the data id for this trait from the Temp table, freezeId isn't used, 
        it just for fixing the inherit
        """
        cursor.execute('''
        SELECT
          DataId
        FROM
          Temp
        WHERE
          Id=%s
        ''' % (self.id))

        # we hope that there's only one record here
        row = cursor.fetchone()
        self.dataId = row[0]

    #XZ, 03/03/2009: Xiaodong implemented this fuction
    def populateStrainData(self, cursor):
        cursor.execute('''
        SELECT
          TempData.StrainId,
          TempData.value
        FROM
          TempData
        WHERE
          TempData.Id = %s''' % self.dataId)
        for row in cursor.fetchall():
            self.strainData[int(row[0])] = float(row[1])


    def row(self):
        return [self.id,
                self.name,
                self.description,
                ""]
    

    def longName(self):
        """
        For temp trait, the description always contents whole useful information
        """
        return self.description


# queryGenotypeTraitByName : Cursor -> string -> GenotypeTrait
def queryGenotypeTraitByName(cursor, speciesId, name):
    qry = '''
    SELECT
      Geno.Id,
      Geno.Name,
      Geno.Chr,
      Geno.Mb
    FROM
      Geno
    WHERE
      Geno.SpeciesId = %s and Geno.Name = "%s" ''' % (speciesId, name)

    cursor.execute(qry)
    row = cursor.fetchone()
    return GenotypeTrait(id=row[0], name=row[1],
                         chromosome=row[2], MB=row[3])

# queryPublishTraitByName : Cursor -> string -> PublishTrait
def queryPublishTraitByName(cursor, freezeId, name):
    qry = '''
    SELECT
      PublishXRef.Id,
      Phenotype.Id,
      Publication.Authors,
      Publication.Title,
      Publication.Year,
      Publication.PubMed_ID
    FROM
      Publication, PublishXRef, Phenotype, PublishFreeze
    WHERE
      PublishFreeze.Id = %s AND 
      PublishFreeze.InbredSetId = PublishXRef.InbredSetId AND
      PublishXRef.Id = %s AND 
      PublishXRef.PublicationId = Publication.Id AND
      PublishXRef.PhenotypeId = Phenotype.Id 
      ''' % (freezeId, name)

    cursor.execute(qry)
    if cursor.rowcount == 0:
        return None
    else:
        row = cursor.fetchone()
        
        return PublishTrait(id=row[0], name='%s'%row[0],
                            authors=row[2], title=row[3],
                            year=row[4], href=row[5])


def queryTempTraitByName(cursor, name):
    name=name.strip()
    qry = '''
    SELECT
      Temp.Id,
      Temp.Name,
      Temp.description
    FROM
      Temp
    WHERE
      Temp.Name= "%s"
      ''' % (name)

    cursor.execute(qry)
    if cursor.rowcount == 0:
        return None
    else:
        row = cursor.fetchone()
        return TempTrait(id=row[0], name=row[1], description=row[2], href='')

# queryPopulatedProbeSetTraits: Cursor -> Integer -> dictof Trait
# to retrieve an entire probeset fully populated with data
# this query can take 15+ sec the old way (22,000 traits * 35 strains = half
# a million records)
# so we ask for the data in bulk
#
# cursor should be SSCursor for MySQL so rows are stored on the server side
# and tuples are used
# we explicitly close the cursor here as well
#XZ, 03/04/2009: It seems to me that this function is never be executed.
#XZ: Although it can be called from multitrait.loadDatabase,
#XZ: but the loadDatabase function will not be called
#XZ: if the targetDatabaseType is probeset.
#XZ: The probeset traits of target database are retrieved by execute
#XZ: queryPopulatedProbeSetTraits2 from correlation.calcProbeSetPearsonMatrix
def queryPopulatedProbeSetTraits(cursor, freezeId):
    step1 = time.time()
    traits = queryProbeSetTraits(cursor, freezeId)
    traitDict = {}
    for trait in traits:
        traitDict[trait.id] = trait
        
    step2 = time.time()
    print 
    #XZ, 03/04/2009: Xiaodong changed Data to ProbeSetData
    cursor.execute('''
    SELECT
      ProbeSetXRef.ProbeSetId,
      ProbeSetData.StrainId,
      ProbeSetData.value
    FROM
      ProbeSetXRef
    Left Join ProbeSetData ON
      ProbeSetXRef.DataId = ProbeSetData.Id
    WHERE
      ProbeSetXRef.ProbeSetFreezeId = %s
    ''' % freezeId)

    step3 = time.time()
    totalrows = 0
    somerows = cursor.fetchmany(1000)
    while len(somerows) > 0:
        totalrows += len(somerows)
        for row in somerows:
            # this line of code can execute more than one million times
            traitDict[row[0]].strainData[int(row[1])] = row[2]
        somerows = cursor.fetchmany(1000)

    #cursor.close()
    step4 = time.time()
    
    time1 = step2 - step1
    time2 = step3 - step2
    time3 = step4 - step3
    time4 = step4 - step1
    #print "%f %f %f %f %d rows" % (round(time1, 2),
    #                               round(time2, 2),
    #                               round(time3, 2),
    #                               round(time4, 2),
    #                               totalrows)
    #print "Fetched %d traits" % len(traits)
    return traits


# queryPopulatedProbeSetTraits2: Cursor -> Integer -> dictof Trait
# to retrieve probeset fully populated whose ProbeSetId in a range
# a special ProbeSetId with data
# this query can take 15+ sec the old way (22,000 traits * 35 strains = half
# a million records)
# so we ask for the data in bulk
#
# cursor should be SSCursor for MySQL so rows are stored on the server side
# and tuples are used
# we explicitly close the cursor here as well
def queryPopulatedProbeSetTraits2(cursor, freezeId, ProbeSetId1, ProbeSetId2):
    step1 = time.time()
    traits = queryProbeSetTraits2(cursor, freezeId, ProbeSetId1, ProbeSetId2)
    traitDict = {}
    for trait in traits:
        traitDict[trait.id] = trait

    step2 = time.time()
    print
    #XZ, 03/04/2009: Xiaodong changed Data to ProbeSetData
    cursor.execute('''
    SELECT
      ProbeSetXRef.ProbeSetId,
      ProbeSetData.StrainId,
      ProbeSetData.value
    FROM
      ProbeSetXRef
    Left Join ProbeSetData ON
      ProbeSetXRef.DataId = ProbeSetData.Id
    WHERE
      ProbeSetXRef.ProbeSetFreezeId = %s AND
      ProbeSetXRef.ProbeSetId >= %s AND
      ProbeSetXRef.ProbeSetId <= %s
      ''' % (freezeId, ProbeSetId1, ProbeSetId2))

    step3 = time.time()
    totalrows = 0
    somerows = cursor.fetchmany(1000)
    while len(somerows) > 0:
        totalrows += len(somerows)
        for row in somerows:
            # this line of code can execute more than one million times
            traitDict[row[0]].strainData[int(row[1])] = row[2]
        somerows = cursor.fetchmany(1000)

    #cursor.close()
    step4 = time.time()

    time1 = step2 - step1
    time2 = step3 - step2
    time3 = step4 - step3
    time4 = step4 - step1
    #print "%f %f %f %f %d rows" % (round(time1, 2),
    #                               round(time2, 2),
    #                               round(time3, 2),
    #                               round(time4, 2),
    #                               totalrows)
    #print "Fetched %d traits" % len(traits)
    return traits


# def noneFilter : string or none -> string
# to replace a possible None by an empty string
def noneFilter(x):
    if x is None:
        return ""
    else:
        return x

# queryProbeSetTraits: Cursor -> Integer -> dictof Trait
def queryProbeSetTraits(cursor, freezeId):
    """
    To locate all of the traits in a particular probeset
    """
    qry = '''
    SELECT
      ProbeSet.Id,
      ProbeSet.Name,
      ProbeSet.description,
      ProbeSet.symbol,
      ProbeSet.Chr,
      ProbeSet.Mb,
      ProbeSet.GeneId,
      ProbeSetXRef.DataId
    FROM
      ProbeSet,
      ProbeSetXRef
    WHERE
      ProbeSetXRef.ProbeSetId = ProbeSet.Id AND
      ProbeSetXRef.ProbeSetFreezeId = %s
    ORDER BY ProbeSet.Id
    ''' % freezeId

    cursor.execute(qry)
    rows = cursor.fetchall()
    traits = []

    for row in rows:
        row = map(noneFilter, row)
        trait = ProbeSetTrait(id=row[0], name=row[1],
                              description=row[2],
                              chromosome=row[4],
                              MB=row[5],
                              symbol=row[3],
                              GeneId=row[6])
        trait.dataId = row[7]
        traits.append(trait)

    return traits


# queryProbeSetTraits2: Cursor -> Integer -> dictof Trait
def queryProbeSetTraits2(cursor, freezeId, ProbeSetId1, ProbeSetId2):
    """
    To locate all of the traits in a particular probeset
    """
    qry = '''
    SELECT
      ProbeSet.Id,
      ProbeSet.Name,
      ProbeSet.description,
      ProbeSet.symbol,
      ProbeSet.Chr,
      ProbeSet.Mb,
      ProbeSet.GeneId,
      ProbeSetXRef.DataId
    FROM
      ProbeSet,
      ProbeSetXRef
    WHERE
      ProbeSetXRef.ProbeSetId = ProbeSet.Id AND
      ProbeSetXRef.ProbeSetFreezeId = %s AND
      ProbeSet.Id >= %s AND
      ProbeSet.Id <= %s
    ORDER BY ProbeSet.Id
    ''' % (freezeId, ProbeSetId1, ProbeSetId2)

    cursor.execute(qry)
    rows = cursor.fetchall()
    traits = []

    for row in rows:
        row = map(noneFilter, row)
        trait = ProbeSetTrait(id=row[0], name=row[1],
                              description=row[2],
                              chromosome=row[4],
                              MB=row[5],
                              symbol=row[3],
                              GeneId=row[6])
        trait.dataId = row[7]
        traits.append(trait)

    return traits


# queryPublishTraits : Cursor -> arrayof Trait
def queryPublishTraits(cursor, freezeId):
    """
    To locate all published traits
    """
    qry = '''
    SELECT
      Publication.Id,
      Publication.Name,
      Publication.PhenoType,
      Publication.Authors,
      Publication.Title,
      Publication.Year,
      Publication.PubMed_ID,
      PublishXRef.DataId
    FROM
      Publication,
      PublishXRef
    WHERE
      PublishXRef.PublishFreezeId = %s AND
      PublishXRef.PublishId = Publication.Id
    ''' % freezeId
    
    qry = '''
    SELECT
      Publication.Id,
      PublishXRef.Id,
      Phenotype.Pre_publication_description,
      Phenotype.Post_publication_description,
      Publication.Authors,
      Publication.Title,
      Publication.Year,
      Publication.PubMed_ID,
      PublishXRef.DataId
    FROM
      Publication, PublishXRef, Phenotype, PublishFreeze
    WHERE
      PublishFreeze.Id = %s AND 
      PublishFreeze.InbredSetId = PublishXRef.InbredSetId AND
      PublishXRef.PublicationId = Publication.Id AND
      PublishXRef.PhenotypeId = Phenotype.Id 
      ''' % freezeId
    cursor.execute(qry)
    rows = cursor.fetchall()
    traits = []
    for row in rows:
        PhenotypeString = row[3]
        if not row[7] and row[2]:
            PhenotypeString = row[2]
        trait = PublishTrait(id=row[0], name= '%s' %row[1],
                             phenotype=PhenotypeString,
                             authors=row[4],
                             title=row[5],
                             year=row[6],
                             href=row[7])
        trait.dataId = row[8]
        traits.append(trait)
        
    return traits

# queryGenotypeTraits : Cursor -> arrayof Trait
def queryGenotypeTraits(cursor, freezeId):
    """
    To locate all traits in the genotype
    """
    qry =    '''
    SELECT
      Geno.Id,
      Geno.Name,
      Geno.Chr,
      GenoXRef.DataId,
      Geno.Mb
    FROM
      Geno,
      GenoXRef
    WHERE
      GenoXRef.GenoId = Geno.Id
      AND GenoXRef.GenoFreezeId = %s
    ''' % freezeId
    cursor.execute(qry)
    rows = cursor.fetchall()
    traits = []
    
    for row in rows:
        trait = GenotypeTrait(id=row[0], name=row[1],
                              chromosome=row[2], MB=row[4])
        trait.dataId = row[3]
        traits.append(trait)
        
    return traits

# queryProbeSetTraitByName : Cursor -> string -> Trait
# to find a particular trait given its name 
def queryProbeSetTraitByName(cursor, name):
    qry = '''
    SELECT
      ProbeSet.Id,
      ProbeSet.Name,
      ProbeSet.description,
      ProbeSet.symbol,
      ProbeSet.Chr,
      ProbeSet.Mb,
      ProbeSet.GeneId
    FROM
      ProbeSet
    WHERE
      ProbeSet.Name = "%s"
    ''' % name
    #print qry
    cursor.execute(qry)
    row = cursor.fetchone()

    # convert a MySQL NULL value to an empty string
    # for gene symbol
    if row[3] is None:
        sym = ""
    else:
        sym = row[3]
        
    return ProbeSetTrait(id=row[0], name=row[1], description=row[2],
                         symbol=sym, chromosome=row[4], MB=row[5],
                         GeneId=row[6])
    
                     
# queryTraits : Cursor -> string -> string -> arrayof Traits
# to find all of the traits whose descriptions match a certain string in a
# particular database
def queryTraits(cursor, dbId, queryString):
    # we do this in two steps:
    # first we get the data id for the matching traits
    qry = '''
    SELECT
      ProbeSet.Id,
      ProbeSet.Name,
      ProbeSet.description,
      ProbeSetXRef.DataId
    FROM
      ProbeSet,
      ProbeSetXRef
    WHERE
      ProbeSetXRef.ProbeSetFreezeId = %s AND
      ProbeSet.Id = ProbeSetXRef.ProbeSetId AND
      ProbeSet.description LIKE "%%%s%%"
    ''' % (dbId, queryString)
    #    print qry
    cursor.execute(qry)

    if cursor.rowcount == 0:
        print "No traits found"
        return []
    else:
        print "%s traits found" % (cursor.rowcount)

    # maybe fetchall is bad; we will see
    traits = []
    for row in cursor.fetchall():
        myTrait = Trait(row[0], row[1], row[2])
        myTrait.dataId = row[3]
        traits.append(myTrait)

    # second we pull all of the strain data for each trait
    print "Retrieving individual trait data..."
    for trait in traits:
        trait.populateStrainData(cursor, trait.dataId)
        print "%s (%s) -- %s" % (trait.name, trait.id, trait.description)

    print "done"
    return traits

# queryProbeSetFreezes : Cursor -> arrayof String,String tuples
# to return the short and long name for each ProbeSetFreeze
# this function is designed specifically for building
# a database selector
def queryProbeSetFreezes(cursor):
    cursor.execute("""
    SELECT
      ProbeSetFreeze.Name,
      ProbeSetFreeze.FullName
    FROM
      ProbeSetFreeze
    ORDER BY
      ProbeSetFreeze.Name
    """)

    # for now, fetchall returns the data as a list of tuples
    # which is what we want
    return list(cursor.fetchall())

# queryProbeSetFreezeIdName: Cursor -> String -> String, String
# this function returns the
# id and the long name of a probesetfreeze given its name
# once again, it's designed specifically for building
# the database selector
def queryProbeSetFreezeIdName(cursor, name):
    qry = ('''
    SELECT
      ProbeSetFreeze.Id,
      ProbeSetFreeze.FullName
    FROM
      ProbeSetFreeze
    WHERE
      ProbeSetFreeze.Name = "%s" 
    ''' % name)
    #print qry
    cursor.execute(qry)

    row = cursor.fetchone()
    return row

# queryProbeSetFreezeName: Cursor -> String -> String
# to return the name of a probe set freeze given its id
def queryProbeSetFreezeName(cursor, id):
    cursor.execute('''
    SELECT
      ProbeSetFreeze.FullName
    FROM
      ProbeSetFreeze
    WHERE
      ProbeSetFreeze.Id = %s
    ''' % id)

    row = cursor.fetchone()
    return row[0]

# dbNameToTypeId : Cursor -> String -> (String, String)
# to convert a database name to a (type, id) pair
def dbNameToTypeId(cursor, name):
    types = ["ProbeSet", "Geno", "Publish"]
    for type_ in types:
        count = cursor.execute('''
        SELECT
          %sFreeze.Id
        FROM
          %sFreeze
        WHERE
          Name = "%s"
        ''' % (type_, type_,  name))

        if count != 0:
            id = cursor.fetchone()[0]
            return type_, id

    return None, None

# dbTypeIdToName : Cursor -> String -> String -> String
# to convert a database (type,id) pair into a name
def dbTypeIdToName(cursor, dbType, dbId):
    cursor.execute('''
    SELECT
      %sFreeze.Name
    FROM
      %sFreeze
    WHERE
    Id = %s
    ''' % (dbType, dbType, dbId))
    
    row = cursor.fetchone()
    return row[0]

#XZ, July 21, 2010: I add this function
def getSpeciesIdByDbTypeId (cursor, dbType, dbId):
    cursor.execute('''
    SELECT
      SpeciesId
    FROM
      InbredSet, %sFreeze
    WHERE
    %sFreeze.Id = %s
    and InbredSetId = InbredSet.Id
    ''' % (dbType, dbType, dbId))

    row = cursor.fetchone()
    return row[0]


# queryStrainCount : Cursor -> int
# return the number of strains in the database
def queryStrainCount(cursor):
    cursor.execute('''
    SELECT
      Max(Strain.Id)
    FROM
      Strain
    ''')
    return (cursor.fetchone())[0]
