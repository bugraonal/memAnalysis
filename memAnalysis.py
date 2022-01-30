from graphGen.graphGen import DAGgen
from loadStoreAnalysis import LoadStoreAnalysis
import random
import graphviz
import math
from os.path import exists
from os import system
import argparse


class MemAnalysis:

    # s/=\(.*\) # \(.*\)$/=\2 # \1
    # randomization parameters
    numNodesLow =15  #  50   
    numNodesHigh =50  #  500   
    numLevelsLow =5  #  15   
    numLevelsHigh =10  #  50   
    varPerFuncHigh =10  #  30   
    varPerFuncLow =0  #  0   
    instrPerFuncHigh = 500
    instrPerFuncLow = 5

    # load store parameters
    loadStoreNumRegs = 32
    loadStoreRegCost = 0.67
    loadStoreMemCost = 1.33
    numOperands = 3

    # result parameters
    opcodeSize = 4
    programFactor = 0.5

    def run(self):
        results = Results()
        self.generateGraph(results)
        self.findWorstPaths(results)
        self.findMemSizes(results)
        self.map(results)
        self.loadStoreAnalyse(results)
        return results

    def packedCost(self, tup):
        return tup[0] + tup[1] * 0.5 + tup[2] * 0.25

    def optimizedCost(self, tup):
        return tup[0], tup[0] + tup[1],  tup[0] + tup[1] + tup[2]

    def generateGraph(self, results):
        numNodes = random.randint(self.numNodesLow, self.numNodesHigh)
        numLevels = random.randint(self.numLevelsLow, min(self.numLevelsHigh, numNodes))
        saturationFraction = 2/3
        gen = DAGgen(numNodes, numLevels, saturationFraction)
        levels = gen.generate(view=False)

        vars = {}
        instr = {}
        instrCount = 0

        for l in levels:
            lim = self.varPerFuncHigh
            for n in l:
                vars[n.name] = (random.randint(0, lim), random.randint(0, lim), random.randint(0, lim))
                i = random.randint(self.instrPerFuncLow, self.instrPerFuncHigh)
                instr[n.name] = i
                instrCount += i

        results.numNodes = numNodes
        results.levels = levels
        results.instrCount = instrCount
        results.instr = instr
        results.vars = vars

    def findWorstPaths(self, results):

        main = results.levels[0][0]
        current = main
        visited = {'main': []}
        path = [main]
        currentPacked = self.packedCost(results.vars['main'])
        maxPacked = currentPacked
        maxPackedPath = [main]

        currentLong, currentLongShort, currentLongShortChar = self.optimizedCost(results.vars['main'])

        maxLong = 0
        maxLongShort = 0
        maxLongShortChar = 0

        maxPathLong = []
        maxPathLongShort = []
        maxPathLongShortChar = []

        while (True):
            skip = False
            for n in current.callees:
                if n not in visited[current.name]:
                    visited[current.name].append(n)
                    current = n
                    path.append(n)
                    # [print(p.name, end=' ') for p in path]
                    # print()
                    visited[current.name] = []
                    var = results.vars[current.name]
                    currentPacked = currentPacked + self.packedCost(var)
                    lCost, lsCost, lscCost = self.optimizedCost(var)
                    currentLong += lCost
                    currentLongShort += lsCost
                    currentLongShortChar += lscCost
                    if currentPacked > maxPacked:
                        maxPacked = currentPacked
                        maxPackedPath = path.copy()
                    if currentLong > maxLong:
                        maxLong = currentLong
                        maxPathLong = path.copy()
                    if currentLongShort > maxLongShort:
                        maxLongShort = currentLongShort
                        maxPathLongShort = path.copy()
                    if currentLongShortChar > maxLongShortChar:
                        maxLongShortChar = currentLongShortChar
                        maxPathLongShortChar = path.copy()
                    skip = True
                    break
            if skip:
                continue
            var = results.vars[current.name]
            lCost, lsCost, lscCost = self.optimizedCost(var)
            currentLong -= lCost
            currentLongShort -= lsCost
            currentLongShortChar -= lscCost
            currentPacked -= self.packedCost(var)
            path.pop()
            if len(path) == 0:
                break
            current = path[-1]

        results.maxPackedPath = maxPackedPath
        results.maxPacked = maxPacked
        results.maxPathLong = maxPathLong
        results.maxPathLongShort = maxPathLongShort
        results.maxPathLongShortChar = maxPathLongShortChar
        results.maxLong = maxLong
        results.maxLongShort = maxLongShort
        results.maxLongShortChar = maxLongShortChar

    def findMemSizes(self, results):
        packedOperandSize = math.ceil(math.log2(results.maxPacked * 4)) - 2 + 3
        packedData = results.maxPacked*32
        packedWordSize = self.opcodeSize + packedOperandSize * 2
        packedProgram = results.instrCount*packedWordSize
        packedTotal = packedProgram * self.programFactor + packedData

        lregs = results.maxLong
        sregs = results.maxLongShort - results.maxLong
        cregs = results.maxLongShortChar - results.maxLongShort
        optimizedData = lregs*32 + sregs*16 + cregs*8
        optimizedOperandSize = math.ceil(math.log2(lregs + sregs + cregs))
        optimizedWordSize = self.opcodeSize + 2 * optimizedOperandSize
        optimizedProgram = results.instrCount*optimizedWordSize
        optimizedTotal = optimizedProgram * self.programFactor + optimizedData

        results.packedOperandSize = packedOperandSize
        results.optimizedOperandSize = optimizedOperandSize
        results.packedData = packedData
        results.optimizedData = optimizedData
        results.packedProgram = packedProgram
        results.optimizedProgram = optimizedProgram
        results.lregs = lregs
        results.sregs = sregs
        results.cregs = cregs
        results.packedTotal = packedTotal
        results.optimizedTotal = optimizedTotal
        results.optimized2packed = optimizedTotal / packedTotal

    def map(self, results):
        lines = []
        for lev in results.levels:
            for func in lev:
                lines.append(func.name + ': ' + ' '.join([f.name for f in func.callees]) + '\n')
                locals = results.vars[func.name]
                localLs = [func.name + '_l' + str(i) for i in range(locals[0])]
                localSs = [func.name + '_s' + str(i) for i in range(locals[1])]
                localCs = [func.name + '_c' + str(i) for i in range(locals[2])]
                for loc in localLs:
                    lines.append('Float ' + loc + '\n')
                for loc in localSs:
                    lines.append('Short ' + loc + '\n')
                for loc in localCs:
                    lines.append('Char ' + loc + '\n')
                lines.append('\n')

        with open('callgraphandlocals.txt', 'w') as f:
            f.writelines(lines)

        system('java -jar ~/thesis/Compiler/LocalVarOptimizer/bin/LocalVarOptimzer.jar callgraphandlocals.txt > /dev/null')

    def loadStoreAnalyse(self, results):
        loadStoreAnalysis = LoadStoreAnalysis(self.loadStoreNumRegs, results.instr)
        loadStoreOperandSize, loadStoreData, loadStoreProgram, loadStoreTotal = loadStoreAnalysis.analyse(self.loadStoreRegCost, self.loadStoreMemCost, self.opcodeSize, self.numOperands)
        results.loadStoreOperandSize = loadStoreOperandSize
        results.loadStoreData = loadStoreData
        results.loadStoreProgram = loadStoreProgram        
        results.loadStoreTotal = loadStoreProgram * self.programFactor + loadStoreData
        results.optimized2loadStore = results.optimizedTotal / results.loadStoreTotal


class Results:

    numNodes = None
    instrCount = None
    instr = None
    vars = None
    levels = None
    maxPackedPath = None
    maxPacked = None
    maxPathLong = None
    maxPathLongShort = None
    maxPathLongShortChar = None
    maxLong = None
    maxLongShort = None
    maxLongShortChar = None
    packedOperandSize = None
    packedData = None
    packedProgram = None
    packedTotal = None
    lregs = None
    sregs = None
    cregs = None
    optimizedData = None
    optimizedOperandSize = None
    optimizedProgram = None
    optimizedTotal = None
    loadStoreOperandSize = None
    loadStoreData = None
    loadStoreProgram = None
    loadStoreTotal = None
    optimized2packed = None
    optimized2loadStore = None

    def copy(self):
        other = Results()
        other.numNodes = self.numNodes
        other.instrCount = self.instrCount
        other.instr = self.instr
        other.vars = self.vars
        other.levels = self.levels
        other.maxPackedPath = self.maxPackedPath
        other.maxPacked = self.maxPacked
        other.maxPathLong = self.maxPathLong
        other.maxPathLongShort = self.maxPathLongShort
        other.maxPathLongShortChar = self.maxPathLongShortChar
        other.maxLong = self.maxLong
        other.maxLongShort = self.maxLongShort
        other.maxLongShortChar = self.maxLongShortChar
        other.packedOperandSize = self.packedOperandSize
        other.packedData = self.packedData
        other.packedProgram = self.packedProgram
        other.packedTotal = self.packedTotal
        other.lregs = self.lregs
        other.sregs = self.sregs
        other.cregs = self.cregs
        other.optimizedData = self.optimizedData
        other.optimizedOperandSize = self.optimizedOperandSize
        other.optimizedProgram = self.optimizedProgram
        other.optimizedTotal = self.optimizedTotal
        other.loadStoreOperandSize = self.loadStoreOperandSize
        other.loadStoreData = self.loadStoreData
        other.loadStoreProgram = self.loadStoreProgram
        other.loadStoreTotal = self.loadStoreTotal
        other.optimized2packed = self.optimized2packed
        other.optimized2loadStore = self.optimized2loadStore
        return other

    def report(self, loadStoreRegs, console=True, CSV=True):
        if console:
            print('# of Instruction:', self.instrCount)
            print('# of Functions:', self.levels[-1][-1].name[1:])
            print()
            print('Packed:')
            print('\t', end='')
            [print(p.name, end=' ') for p in self.maxPackedPath]
            print()
            print('\tOperand Size: ', self.packedOperandSize)
            print('\tData:', self.packedData, 'b')
            print('\tProgram:', self.packedProgram)
            print('\tTotal:', self.packedTotal)
            print()

            print('Optimized:')
            print('\tLong:')
            print('\t', end='')
            [print(p.name, end=' ') for p in self.maxPathLong]
            print('\n\t', self.maxLong)
            print('\tLongShort:')
            print('\t', end='')
            [print(p.name, end=' ') for p in self.maxPathLongShort]
            print('\n\t', self.maxLongShort)
            print('\tLongShortChar:')
            print('\t', end='')
            [print(p.name, end=' ') for p in self.maxPathLongShortChar]
            print('\n\t', self.maxLongShortChar)
            print('\tRegisters: L =', self.lregs, 'S =', self.sregs, 'C =', self.cregs)
            print('\tOperand Size: ', self.optimizedOperandSize)
            print('\tData:', self.optimizedData, 'b')
            print('\tProgram:', self.optimizedProgram)
            print('\tTotal:', self.optimizedTotal)
            print()

            print('Load Store:')
            print('Number of registers:', loadStoreRegs)
            print('\tOperand Size: ', self.loadStoreOperandSize)
            print('\tData: ', self.loadStoreData)
            print('\tProgram: ', self.loadStoreProgram)
            print('\tTotal: ', self.loadStoreTotal)
            print()

            print('Optimized / Packed:', self.optimizedTotal / self.packedTotal)
            print('Optimized / Load Store:', self.optimizedTotal / self.loadStoreTotal)

        if CSV:
            header = not exists('report.csv')

            with open('report.csv', 'a') as f:
                if header:
                    print('# of Function,# of instructions,Load Store Registers,\
                            Packed Operand,Optimized Operand,\
                            Load Store Operand,Packed Data,\
                            Optimized Data,Load Store Data,Packed Program,\
                            Optimized Program,Load Store Program,Packed Total,\
                            Optimized Total,Load Store Total,\
                            Optimized vs Packed,Optimized vs Load Store,\
                            L,S,C', file=f)
                print(self.levels[-1][-1].name[1:], self.instrCount,
                      loadStoreRegs, self.packedOperandSize,
                      self.optimizedOperandSize, self.loadStoreOperandSize,
                      self.packedData, self.optimizedData, self.loadStoreData,
                      self.packedProgram, self.optimizedProgram,
                      self.loadStoreProgram, self.packedTotal,
                      self.optimizedTotal, self.loadStoreTotal,
                      self.optimized2packed, self.optimized2loadStore,
                      self.lregs, self.sregs, self.cregs, file=f, sep=',')

    def annotateGraph(self):
        glines = []
        with open('graph.gv', 'r') as f:
            glines = f.readlines()

        newLines = []
        for line in glines:
            if 'label' in line:
                start = line.find('label') + 6
                end = line.find(']')
                name = line[start:end]
                var_ = self.vars[name]
                newLine = line[:start] + '\"' + name + '\\nL:' +\
                    str(var_[0]) + '\\nS:' + str(var_[1]) + '\\nC:' +\
                    str(var_[2]) + '\"' + line[end:]
                newLines.append(newLine)
            else:
                newLines.append(line)

        newEdges = []

        prev = self.maxPackedPath[0].ID
        for n in self.maxPackedPath[1:]:
            newEdges.append('\t' + prev + ' -> ' + n.ID + ' [color=\"red\"]')
            prev = n.ID

        prev = self.maxPathLong[0].ID
        for n in self.maxPathLong[1:]:
            newEdges.append('\t' + prev + ' -> ' + n.ID + ' [color=\"green\"]')
            prev = n.ID

        prev = self.maxPathLongShort[0].ID
        for n in self.maxPathLongShort[1:]:
            newEdges.append('\t' + prev + ' -> ' + n.ID + ' [color=\"blue\"]')
            prev = n.ID

        prev = self.maxPathLongShortChar[0].ID
        for n in self.maxPathLongShortChar[1:]:
            newEdges.append('\t' + prev + ' -> ' + n.ID + ' [color=\"purple\"]')
            prev = n.ID

        endLine = newLines.pop()
        newLines.extend(newEdges)
        newLines.append(endLine)

        with open('annotated.gv', 'w') as f:
            f.writelines(newLines)

        graphviz.render('dot', 'pdf', 'annotated.gv')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # s/=\(.*\)) # \(.*\)$/=\2) # \1
    parser.add_argument('numNodesLow',      default=15) # 50  
    parser.add_argument('numNodesHigh',     default=50) # 500 
    parser.add_argument('numLevelsLow',     default=5) # 15  
    parser.add_argument('numLevelsHigh',    default=10) # 50  
    parser.add_argument('varPerFuncHigh',   default=10) # 30  
    parser.add_argument('varPerFuncLow',    default=0   )
    parser.add_argument('instrPerFuncHigh', default=500 )
    parser.add_argument('instrPerFuncLow',  default=5   )
    parser.add_argument('loadStoreNumRegs', default=32  )
    parser.add_argument('loadStoreRegCost', default=0.67)
    parser.add_argument('loadStoreMemCost', default=1.33)
    parser.add_argument('numOperands',      default=3   )
    parser.add_argument('opcodeSize',       default=4   )
    parser.add_argument('programFactor',    default=0.5 )

    args = parser.parse_args()
    memAnalysis = MemAnalysis()

    memAnalysis.numNodesLow = args.numNodesLow
    memAnalysis.numNodesHigh = args.numNodesHigh
    memAnalysis.numLevelsLow = args.numLevelsLow
    memAnalysis.numLevelsHigh = args.numLevelsHigh
    memAnalysis.varPerFuncHigh = args.varPerFuncHigh
    memAnalysis.varPerFuncLow = args.varPerFuncLow
    memAnalysis.instrPerFuncHigh = args.instrPerFuncHigh
    memAnalysis.instrPerFuncLow = args.instrPerFuncLow
    memAnalysis.loadStoreNumRegs = args.loadStoreNumRegs
    memAnalysis.loadStoreRegCost = args.loadStoreRegCost
    memAnalysis.loadStoreMemCost = args.loadStoreMemCost
    memAnalysis.numOperands = args.numOperands
    memAnalysis.opcodeSize = args.opcodeSize
    memAnalysis.programFactor = args.programFactor

    results = memAnalysis.run()
    results.report(console=True, CSV=True)
    results.annotateGraph()
