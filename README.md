# memAnalysis
This is a set of stricts for comparing the area performance of semi-aligned and fully aligned; load store and non load store memory architectures. 

# Files
- memAnalysis.py is the main script. It contains the analysis code for non-load/store architecture. The top of the file contains the parameters that can be customized. The results are saved on a CSV file called report.csv. 
- loadStoreAnalysis.py is the script that contains code that analyses load/store architecture. 
- analyseForBestReg.py is the script that runs the load/store analysis for different register counts. The best area result is seected.
- grpahGen directory is a separate repo for generating random call graphs. 
