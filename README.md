# Data_Lineage_Analyser_and_Document_Generator
Generates lineage and document for functions, triggers and stored procedures


to do:
1. change mermaid to show procedures calling other procedures too now it shows only procedures calling tables and column.
2. then add functions ka properties. so first you hvae to update the index schema and ast schema. index schema i can only try updating, but for sat schema i might need nikhils help
3. then i have to do the same for triggers.

according to my impact analysis, tool 1,2,4,5 will have to change code most. since new elements are being added. other tools just use this. tool 3 and tool 4 i will start workring. starting with tool 4