from memAnalysis import MemAnalysis, Results
from math import log2, floor

maxLoadScore = 0
bestRegs = 2
bestResults = None
memAnalysis = MemAnalysis()
results = Results()
memAnalysis.generateGraph(results)
memAnalysis.findWorstPaths(results)
memAnalysis.findMemSizes(results)
memAnalysis.map(results)

regs = int(2**floor(log2((results.lregs + results.sregs + results.cregs)/2)))
while regs > 1:
    memAnalysis.loadStoreNumRegs = regs
    memAnalysis.loadStoreAnalyse(results)
    score = results.optimized2loadStore
    if score > maxLoadScore:
        maxLoadScore = score
        bestRegs = regs
        bestResults = results.copy()

    regs //= 2
bestResults.report(bestRegs, console=False, CSV=True)
