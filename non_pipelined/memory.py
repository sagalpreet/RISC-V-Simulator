from collections import deque

'''
Whenever read from memory is called, read from Cache can also be called simultaneously.
Memory content will be read from primary memory only but the cache will update the number of miss
and hits accordingly.
'''

class Cache:
  def __init__(self, numSets, numBlocksPerSet, blockSize, name):
    self.name = name
    self.numSets = numSets
    self.numBlocksPerSet = numBlocksPerSet
    self.blockSize = blockSize

    self.sets = deque([Set(numBlocksPerSet, blockSize) for i in range(numSets)])

    self.numAccesses = 0
    self.hits = 0
    self.conflictMiss, self.coldMiss, self.capacityMiss = 0, 0, 0
    self.MCT = set()

  def readWrite(self, address):
    self.numAccesses += 1
    setNumber = address % self.numSets
    index = address % self.blockSize    # not required though

    match = False

    for block in self.sets[setNumber]:
      if block.tag == index:
        self.hits += 1
        match = block
        self.sets[setNumber].remove(block)
        self.sets[setNumber].appendleft(block)
    
    if match != False:
      self.sets[setNumber].remove(match)
      self.sets[setNumber].appendleft(match)
      return

    # miss
    if index in self.MCT:
      self.conflictMiss += 1
    else:
      self.coldMiss += 1
    
    self.sets[setNumber].pop()
    new = Blocks(self.blockSize)
    new.tag = index
    self.sets[setNumber].appendleft(new)
    self.MCT.add(index)

  def __del__(self):
    print('Cache details for '+self.name+' memory:')
    print('Number of accesses:', self.numAccesses)
    print('Number of hits:', self.hits)
    print('Number of cold misses:', self.coldMiss)
    print('Number of capacity misses:', self.capacityMiss)
    print('Number of conflict misses:', self.conflictMiss)

class Set:
  def __init__ (self, numBlocks, blockSize):
    self.numBlocks = numBlocks
    self.blocks = [Blocks(blockSize) for i in range(numBlocks)]

class Blocks:
  def __init__ (self, blockSize):
    self.tag = None
    self.data = None # not required though
    self.blockSize = blockSize


class ProcessorMemoryInterface:
    """
    Mimics the "Processor Memory Interface"
    The word size can be configured.
    """
    BYTE = 0
    HALFWORD = 1
    WORD = 2
    DOUBLEWORD = 3

    def __init__(self, wordSizeInBytes: int, numSets: int, numBlocksPerSet: int, blockSize: int, name: str):
        self.__wordSizeInBytes = wordSizeInBytes
        self.memory = ByteAddressableMemory(wordSizeInBytes=wordSizeInBytes)
        self.__MAR = None
        self.__MDR = None
        self.mem_read = False
        self.mem_write = False
        self.dataType = -1
        self.cache = Cache(numSets, numBlocksPerSet, blockSize, name)

    def __isValidDatatype(self, dataType: int):
        return dataType in [self.BYTE, self.HALFWORD, self.WORD, self.DOUBLEWORD]

    def update(self, rz: int, iag: int, rm: int, mux_control):
        """
        Updates MDR and memory

        mux_control: 0 -> rz
                     1 -> iag
        """
        self.__MAR = rz if mux_control==0 else iag
        self.__MDR = rm
        if self.mem_read:
            print(f"\tReading {['byte', 'halfword', 'word', 'doubleword'][self.dataType]} from memory location 0x{self.__MAR:08x}")
            self.mem_read = False
            self.cache.readWrite(self.__MAR)
            self.__MDR = self.__readFromMemory(self.__MAR, self.dataType)
            self.dataType = -1
        if self.mem_write:
            print(f"\tWriting {['byte', 'halfword', 'word', 'doubleword'][self.dataType]} 0x{self.__MDR:08x} to memory location 0x{self.__MAR:08x}")
            assert self.__isValidDatatype(self.dataType), f'Invalid dataType (value: {self.dataType})'
            self.cache.readWrite(self.__MAR)
            self.__writeToMemory(self.__MAR, self.dataType, self.__MDR)
            self.mem_write = False
            self.dataType = -1

    def __readFromMemory(self, address: int, dataType: int):
        """
        Returns value of `dataType` at `address` from memory
        """
        assert self.__isValidDatatype(dataType), f'Invalid dataType (value: {dataType})'
        if dataType == self.BYTE:
            return self.memory.getByteAtAddress(address)
        elif dataType == self.HALFWORD:
            return self.memory.getHalfwordAtAddress(address)
        elif dataType == self.WORD:
            return self.memory.getWordAtAddress(address)
        elif dataType == self.DOUBLEWORD:
            return self.memory.getDoublewordAtAddress(address)

    def __writeToMemory(self, address: int, dataType: int, value: int):
        """
        Writes `value` of `dataType` at `address` to memory
        """
        assert self.__isValidDatatype(dataType), f'Invalid dataType (value: {dataType})'
        if dataType == self.BYTE:
            self.memory.setByteAtAddress(address, value)
        elif dataType == self.HALFWORD:
            self.memory.setHalfwordAtAddress(address, value)
        elif dataType == self.WORD:
            self.memory.setWordAtAddress(address, value)
        elif dataType == self.DOUBLEWORD:
            self.memory.setDoublewordAtAddress(address, value)

    def getMDR(self):
        """
        Returns the value stored in MDR
        """
        return self.__MDR

class ByteAddressableMemory:
    """
    Creates a byte addressable memory.
    The word size can be configured.

    Caution: Odd word sizes (in bytes), halfword is int(word size/2)
    """

    def __init__(self, wordSizeInBytes: int, maxAddress:int=None, defaultWordValue:int=0x00000000):
        assert wordSizeInBytes>0, "Word size must be positive"
        self.byteData = {}
        self.__maxAddress = maxAddress
        self.__defaultValue = defaultWordValue
        self.__wordSizeInBytes = wordSizeInBytes

    def __isValidAddress(self, address):
        isNotNegative = not address<0
        isLessThanMaxAddress = True if self.getMaxAddress() is None else address <= self.getMaxAddress()
        return isNotNegative and isLessThanMaxAddress

    def __isValidValue(self, value, sizeInBytes):
        return value>=0 and value<=(2**(sizeInBytes*8) - 1)

    def getMaxAddress(self):
        """
        Returns the maximum address of the memory if any, None otherwise
        """
        return self.__maxAddress

    def getWordSizeInBytes(self):
        """
        Returns the word size in bytes
        """
        return self.__wordSizeInBytes

    def __getValueAtAddress(self, address: int, sizeInBytes: int) -> int:
        assert self.__isValidAddress(address), f'Address {hex(address)} is not valid'
        assert self.__isValidAddress(address+sizeInBytes-1), f'Not enough bytes in memory to read'
        assert sizeInBytes>0, f'Size of value must be a positive integer'
        valueBytes = [self.byteData.get(address+i, self.__defaultValue) for i in range(sizeInBytes)]
        value = sum([byte<<(i*8) for i, byte in enumerate(valueBytes)])
        return value

    def __setValueAtAddress(self, address: int, sizeInBytes: int, value: int) -> int:
        assert self.__isValidAddress(address), f'Address {hex(address)} is not valid'
        assert self.__isValidAddress(address+sizeInBytes-1), f'Not enough bytes in memory to write'
        assert sizeInBytes>0, f'Size of value must be a positive integer'
        assert self.__isValidValue(value, sizeInBytes), f'Value {hex(value)} is not a valid value of {sizeInBytes} bytes'
        for i in range(sizeInBytes):
            byteMask = 0xff<<(i*8)
            byte = (value & byteMask)>>(i*8)
            self.byteData[address+i] = byte

    def getByteAtAddress(self, address: int) -> int:
        """
        Returns the byte at `address`
        """
        return self.__getValueAtAddress(address, 1)

    def getHalfwordAtAddress(self, address: int) -> int:
        """
        Returns the halfword at `address`
        """
        return self.__getValueAtAddress(address, self.getWordSizeInBytes()//2)

    def getWordAtAddress(self, address: int) -> int:
        """
        Returns the word at `address`
        """
        return self.__getValueAtAddress(address, self.getWordSizeInBytes())

    def getDoublewordAtAddress(self, address: int) -> int:
        """
        Returns the doubleword at `address`
        """
        return self.__getValueAtAddress(address, self.getWordSizeInBytes()*2)

    def setByteAtAddress(self, address: int, value: int):
        """
        Updates the byte at `address` with `value`
        """
        self.__setValueAtAddress(address, 1, value)

    def setHalfwordAtAddress(self, address: int, value: int):
        """
        Updates the halfword at `address` with `value`
        """
        self.__setValueAtAddress(address, self.getWordSizeInBytes()//2, value)

    def setWordAtAddress(self, address: int, value: int):
        """
        Updates the word at `address` with `value`
        """
        self.__setValueAtAddress(address, self.getWordSizeInBytes(), value)

    def setDoublewordAtAddress(self, address: int, value: int):
        """
        Updates the doubleword at `address` with `value`
        """
        self.__setValueAtAddress(address, self.getWordSizeInBytes()*2, value)

