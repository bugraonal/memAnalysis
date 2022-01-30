
def bits(n):
    b = 0
    while (n > 0):
        n = n >> 1
        b += 1
    return b


class LoadStoreAnalysis:

    def __init__(self, numRegs, funcNumInstr):
        self.numRegs = numRegs
        self.funcNumInstr = funcNumInstr

    def analyse(self, regInstrCost, memInstrCost, opcodeSize, numOperand):
        lines = None
        with open('localVarMapping.txt', 'r') as f:
            lines = f.readlines()

        locationCounts = {}
        mapping = {}
        totalVars = 0
        localVars = {}
        func = ''
        for line in lines:
            line = line.strip()
            if ':' in line:
                func = line.strip(':')
                localVars[func] = []
                continue
            totalVars += 1
            var, loc = line.split(' -> ')
            mapping[var] = loc
            if func in localVars:
                localVars[func].append(var)
            # else:
            #     localVars[func] = [var]

            if loc in locationCounts:
                locationCounts[loc] += 1
            else:
                locationCounts[loc] = 1

        sortedLocations = sorted(list(locationCounts.keys()), key=lambda x: locationCounts[x], reverse=True)
        inRegister = sortedLocations[:self.numRegs-2]
        inMemory = sortedLocations[self.numRegs-2:]

        data = 0
        for loc in sortedLocations:
            if loc[2] == 'L':
                data += 32
            elif loc[2] == 'S':
                data += 16
            elif loc[2] == 'C':
                data += 8
            else:
                raise ValueError(loc)

        program = 0
        operandSize = bits(len(inMemory))
        regInstrSize = opcodeSize + bits(self.numRegs) * numOperand
        memInstrSize = opcodeSize + bits(self.numRegs) + operandSize
#        memInstrNetSize = (regInstrSize * regInstrCost + memInstrSize * (memInstrCost - regInstrCost)) / memInstrCost
        for func, numInstr in self.funcNumInstr.items():
            vars = localVars[func]
            if len(vars) == 0:
                continue
            varInReg = [v for v in vars if mapping[v] in inRegister]
            numVarInReg = len(varInReg)
            numVarInMem = len(vars) - numVarInReg

            regOverTotal = numVarInReg / len(vars)
            memOverTotal = numVarInMem / len(vars)

#            numRegInstr = numInstr * regOverTotal * regInstrCost
            numRegInstr = numInstr * 1 * regInstrCost
            numMemInstr = numInstr * memOverTotal * memInstrCost

            program += numRegInstr * regInstrSize
            program += numMemInstr * memInstrSize

        totalMem = program + data

        return operandSize, data, program, totalMem


