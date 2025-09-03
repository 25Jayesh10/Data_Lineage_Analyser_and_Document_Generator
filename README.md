# Data_Lineage_Analyser_and_Document_Generator
Generates lineage and document for functions, triggers and stored procedures


to do:
1. change mermaid to show procedures calling other procedures too now it shows only procedures calling tables and column.
2. then add functions ka properties. so first you hvae to update the index schema and ast schema. index schema i can only try updating, but for sat schema i might need nikhils help
3. then i have to do the same for triggers.
4. update lineage elements name. the "calls" will change to "called by" in the table section. the procedure should also include one more element called "called by" which should include the names of procedures that are calling this procedure
5. after including the function the lineage should also have the element "calling function" which will have list of all the functins that are calling this procedure and same for triggers.
according to my impact analysis, tool 1,2,4,5 will have to change code most. since new elements are being added. other tools just use this. tool 3 and tool 4 i will start workring. starting with tool 4





to check if present:
columns, tables, procedures, funcitons, triggers
all the tables mentioned in each of them shoould be present
all the columns accessed in each of them should be mentioned
then the type of access made
then generate the mermaid diagram