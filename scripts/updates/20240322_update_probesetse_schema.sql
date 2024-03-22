-- Issue: https://github.com/genenetwork/gn-gemtext-threads/blob/9a15bae9743972d2aef5d3a4368104387bf8f78c/issues/database-ProbeSetSE-schema-bug.gmi
-- The `Strain`(`Id`) column's datatype was `INT(20)` before this is run
-- The related `ProbeSetSE`(`StrainId`) column was `SMALLINT(5)`
-- This would lead to errors when inserting, or data corruption
-- The query below updates the schema to make the dependent `ProbeSet(`StrainId`)`
-- column the same data type as the parent `Strain`(`Id`) column.
ALTER TABLE ProbeSetSE MODIFY StrainId INT(20) NOT NULL;
