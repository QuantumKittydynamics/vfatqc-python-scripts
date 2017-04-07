#!/usr/bin/env python

import sys, os, random, time
sys.path.append('${GEM_PYTHON_PATH}')

from gempython.utils.rate_calculator import rateConverter
from gempython.tools.glib_system_info_uhal import *
from gempython.tools.amc_user_functions_uhal import *
from gempython.tools.optohybrid_user_functions_uhal import *
from gempython.tools.vfat_user_functions_uhal import *

Passed = '\033[92m   > Passed... \033[0m'
NotRun = '\033[90m   > NotRun... \033[0m'
Failed = '\033[91m   > Failed... \033[0m'

def txtTitle(str):
    print '\033[1m' + str + '\033[0m'
    return

class TEST_PARAMS:
    def __init__(self,namc=100,noh=100,ni2c=100,ntrk=100,writeout=False):
        self.AMC_REG_TEST = namc
        self.OH_REG_TEST   = noh
        self.I2C_TEST      = ni2c
        self.TK_RD_TEST    = ntrk
        self.RATE_WRITE    = writeout

        return

class GEMDAQTestSuite:
    """
    This python script will test the AMC, optical links, OH, and VFAT2 functionalities.
    Simply follow the instructions on the screen in order to diagnose the setup.
    Thomas Lenzi - tlenzi@ulb.ac.be
    Jared Sturdy - sturdy@cern.ch (Adapted for uHAL)
    """

    uhal.setLogLevelTo( uhal.LogLevel.FATAL )

    allTests = ["A","B","C","D","E","F","G","H","I","J"]

    def __init__(self,slot,gtx,shelf=1,tests="",test_params=TEST_PARAMS(),debug=False):
        """
        """
        self.slot   = slot
        self.shelf  = shelf
        self.gtx    = gtx

        self.tests = tests.upper().split(',')

        if ("J" in self.tests):
            self.tests.append("B")
            pass
        if ("I" in self.tests):
            self.tests.append("E")
            pass
        if ("H" in self.tests):
            self.tests.append("G")
            pass
        if ("G" in self.tests):
            self.tests.append("E")
            pass
        if ("F" in self.tests):
            self.tests.append("E")
            pass
        if ("E" in self.tests):
            self.tests.append("B")
            pass
        if ("D" in self.tests):
            self.tests.append("B")
            pass
        if ("C" in self.tests):
            self.tests.append("A")
            pass
        if ("B" in self.tests):
            self.tests.append("A")
            pass

        self.tests = list(set(self.tests))

        self.test_params = test_params

        self.debug         = debug

        self.amc     = getAMCObject(self.slot,self.shelf)
        self.ohboard = getOHObject(self.slot,self.gtx,self.shelf)

        self.presentVFAT2sSingle = []
        self.presentVFAT2sFifo   = []
        self.chipIDs  = None
        self.vfatmask = 0xff000000

        self.test = {}
        self.test["A"] = False
        self.test["B"] = False
        self.test["C"] = False
        self.test["D"] = False
        self.test["E"] = False
        self.test["F"] = False
        self.test["G"] = False
        self.test["H"] = False
        self.test["I"] = False
        self.test["J"] = False

        return

    ####################################################
    def AMCPresenceTest(self):
        txtTitle("A. Testing the AMC's presence")
        print "   Trying to read the AMC board ID... If this test fails, the script will stop."

        if (getBoardID(self.amc) != 0):
            print Passed
        else:
            print Failed
            sys.exit()
            pass
        self.test["A"] = True
        print

    ####################################################
    def OptoHybridPresenceTest(self):
        txtTitle("B. Testing the OH's presence")
        print "   Trying to set the OptoHybrid registers... If this test fails, the script will stop."

        # setReferenceClock( self.ohboard, self.gtx, 1)
        setTriggerSource(  self.ohboard, self.gtx, 1)
        setTriggerThrottle(self.ohboard, self.gtx, 0)


        if (getTriggerSource(self.ohboard, self.gtx) == 1):
            print Passed
        else:
            print Failed, "oh_trigger_source %d"%(getTriggerSource(self.ohboard, self.gtx))
            sys.exit()
            pass

        # if (getReferenceClock(self.ohboard,self.gtx) == 1):
        #     print Passed
        # else:
        #     print Failed, "oh_clk_src %d"%(getReferenceClock(self.ohboard,self.gtx))
        #     sys.exit()
        #     pass

        if (getTriggerThrottle(self.ohboard,self.gtx) == 0):
            print Passed
        else:
            print Failed, "oh_trg_throttle %d"%(getTriggerThrottle(self.ohboard,self.gtx))
            sys.exit()
            pass

        self.test["B"] = True

        print

        return

    ####################################################
    def AMCRegisterTest(self):
        txtTitle("C. Testing the AMC registers")
        print "   Performing single reads on the AMC counters and ensuring they increment."

        # countersSingle = []
        # countersTest = True

        # for i in range(0, self.test_params.AMC_REG_TEST):
        #     countersSingle.append(readRegister(self.amc,"AMC.COUNTERS.IPBus.Strobe.Counters"))
        #     pass

        # for i in range(1, self.test_params.AMC_REG_TEST):
        #     if (countersSingle[i - 1] + 1 != countersSingle[i]):
        #         print "\033[91m   > #%d previous %d, current %d \033[0m"%(i, countersSingle[i-1], countersSingle[i])
        #         countersTest = False
        #         pass
        #     pass
        # if (countersTest):
        #     print Passed
        # else:
        #     print Failed
        #     pass

        # self.test["C"] = countersTest

        print

        return

    ####################################################
    def OptoHybridRegisterTest(self):
        txtTitle("D. Testing the OH registers")
        print "   Performing single reads on the OptoHybrid counters and ensuring they increment."

        countersSingle = []
        countersTest = True

        for i in range(0, self.test_params.OH_REG_TEST):
            countersSingle.append(readRegister(self.ohboard,"%s.COUNTERS.WB.MASTER.Strobe.GTX"%(self.oh_basenode)))
            pass

        for i in range(1, self.test_params.OH_REG_TEST):
            if (countersSingle[i - 1] + 1 != countersSingle[i]):
                print "\033[91m   > #%d previous %d, current %d \033[0m"%(i, countersSingle[i-1], countersSingle[i])
                countersTest = False
                pass
            pass

        if (countersTest):
            print Passed
        else:
            print Failed
            pass

        self.test["D"] = countersTest

        print

        return

    ####################################################
    def OptoHybridT1ControllerTest(self):
        txtTitle("Testing the OH T1 controller")

        initialSrc = getTriggerSource(self.ohboard,self.gtx)
        print "  T1 Controller Status: 0x%08x"%(getLocalT1Status(self.ohboard,self.gtx))
        resetLocalT1(self.ohboard,self.gtx)
        setTriggerSource(self.ohboard,self.gtx,0x1)

        # send 1000 L1As
        print "  Testing sequential L1As"
        sentL1AsInitial = optohybridCounters(self.ohboard,self.gtx)["T1"]["SENT"]["L1A"]
        sendL1A(self.ohboard,self.gtx,interval=100,number=1000)
        sleep(1)
        sentL1As = optohybridCounters(self.ohboard,self.gtx)["T1"]["SENT"]["L1A"]
        print "  L1A: %d, Expected:%d"%(sentL1As-sentL1AsInitial, 1000)

        # send 1000 CalPulses+L1As
        sentL1AsInitial      = optohybridCounters(self.ohboard,self.gtx)["T1"]["SENT"]["L1A"]
        sentCalPulsesInitial = optohybridCounters(self.ohboard,self.gtx)["T1"]["SENT"]["CalPulse"]
        sendL1ACalPulse(self.ohboard,self.gtx,delay=0x40,interval=300,number=1000)
        sleep(1)
        sentL1As = optohybridCounters(self.ohboard,self.gtx)["T1"]["SENT"]["L1A"]
        sentCalPulses = optohybridCounters(self.ohboard,self.gtx)["T1"]["SENT"]["CalPulse"]
        print "  Testing sequential CalPulse+L1As"
        print "  L1A: %d, CalPulse: %d, Expected:%d"%(sentL1As-sentL1AsInitial, sentCalPulses-sentCalPulsesInitial, 1000)

        # return to original state
        resetLocalT1(self.ohboard,self.gtx)
        setTriggerSource(self.ohboard,self.gtx,initialSrc)

        return

    ####################################################
    def VFAT2DetectionTest(self):
        txtTitle("E. Detecting the VFAT2s over I2C")
        print "   Detecting VFAT2s on the GEM by reading out their chip ID."

        # writeRegister(self.ohboard,"%s.GEB.Broadcast.Reset"%(self.oh_basenode), 0)
        # readRegister(self.ohboard,"%s.GEB.Broadcast.Request.ChipID0"%(self.oh_basenode))
        self.chipIDs = getAllChipIDs(self.ohboard,self.gtx)

        for i in range(0, 24):
            # missing VFAT shows 0x0003XX00 in I2C broadcast result
            #                    0x05XX0800
            # XX is slot number
            # so if ((result >> 16) & 0x3) == 0x3, chip is missing
            # or if ((result) & 0x30000)   == 0x30000, chip is missing
            if (((readRegister(self.ohboard,"%s.GEB.VFATS.VFAT%d.ChipID0"%(self.oh_basenode,i)) >> 24) & 0x5) != 0x5):
                self.presentVFAT2sSingle.append(i)
                pass
            if (self.chipIDs[i] not in [0x0000,0xdead]):
                self.presentVFAT2sFifo.append(i)
                pass
            pass
        if (self.presentVFAT2sSingle == self.presentVFAT2sFifo):
            print Passed
            pass
        else:
            print Failed
            pass

        self.test["E"] = True

        print "   Detected", str(len(self.presentVFAT2sSingle)), "VFAT2s:", str(self.presentVFAT2sSingle)
        print

        self.vfatmask = setVFATTrackingMask(self.ohboard,self.gtx)

        return

    ####################################################
    def VFAT2I2CRegisterTest(self):
        txtTitle("F. Testing the I2C communication with the VFAT2s")
        print "   Performing random read/write operation on each connect VFAT2."

        self.test["F"] = True

        for i in self.presentVFAT2sSingle:
            validOperations = 0
            for j in range(0, self.test_params.I2C_TEST):
                writeData = random.randint(0, 255)
                writeVFAT(self.ohboard,self.gtx,i,"ContReg3",writeData)
                readData = (readVFAT(self.ohboard,self.gtx,i,"ContReg3")&0xff)
                if (readData == writeData):
                    validOperations += 1
                    pass
                else:
                    print "0x%02x not 0x%02x"%(readData,writeData)
                pass
            writeVFAT(self.ohboard,self.gtx,i,"ContReg3",0)
            if (validOperations == self.test_params.I2C_TEST):
                print Passed, "#%d"%(i)
            else:
                print Failed, "#%d received %d, expected %d"%(i, validOperations, self.test_params.I2C_TEST)
                self.test["F"] = False
                pass
            pass

        print

        return

    ####################################################
    def VFAT2ChannelRegisterTest(self):
        # self.test

        for i in self.presentVFAT2sSingle:
            validOperations = 0
            for chan in range(128):
                initialValue = (getChannelRegister(self.ohboard,self.gtx,i,chan)&0xff)
                for j in range(0,self.test_params.I2C_TEST):
                    writeData    = random.randint(0, 255)
                    setChannelRegister(self.ohboard,self.gtx,i,chan,writeData)
                    readData     = (getChannelRegister(self.ohboard,self.gtx,i,chan)&0xff)
                    if (readData == writeData):
                        validOperations += 1
                        pass
                    else:
                        print "0x%02x not 0x%02x"%(readData,writeData)
                        pass
                    pass
                writeVFAT(self.ohboard,self.gtx,i,chan,initialValue)
                pass
            if (validOperations == 128*self.test_params.I2C_TEST):
                print Passed, "#%d"%(i)
            else:
                print Failed, "#%d valid operations: %d, expected: %d"%(i, validOperations, 128*self.test_params.I2C_TEST)
                # self.test["F"] = False
                pass
            pass

        print

        return

    ####################################################
    def TrackingDataReadoutTest(self):
        txtTitle("G. Reading out tracking data")
        print "   Sending triggers and testing if the Event Counter adds up."

        broadcastWrite(self.ohboard,self.gtx,"ContReg0", 0x36)

        self.test["G"] = True

        for i in self.presentVFAT2sSingle:
            t1_mode     =  0
            t1_type     =  0
            t1_n        =  self.test_params.TK_RD_TEST
            t1_interval =  400
            resetLocalT1(self.ohboard,self.gtx) 
            writeVFAT(self.ohboard,self.gtx,i,"ContReg0",0x37)
            setVFATTrackingMask(self.ohboard,self.gtx, ~(0x1 << i))
            flushTrackingFIFO(self.amc,self.gtx)

            nPackets = 0
            timeOut = 0
            ecs = []

            sendL1A(self.ohboard,self.gtx,t1_interval,t1_n)

            while ((readFIFODepth(self.amc,self.gtx)["Occupancy"]) != 7 * self.test_params.TK_RD_TEST):
                timeOut += 1
                if (timeOut == 10 * self.test_params.TK_RD_TEST):
                    break
                pass
            while ((readFIFODepth(self.amc,self.gtx)["isEMPTY"]) != 1):
                packets = readTrackingInfo(self.amc,self.gtx)
                if (len(packets) == 0):
                    print "read data packet length is 0"
                    continue
                ec = int((0x00000ff0 & packets[0]) >> 4)
                nPackets += 1
                ecs.append(ec)
                pass
            writeVFAT(self.ohboard,self.gtx,i,"ContReg0",0x36)

            if (nPackets != self.test_params.TK_RD_TEST):
                print Failed, "#%d received %d, expected %d"%(i, nPackets, self.test_params.TK_RD_TEST)
                if self.debug:
                    raw_input("press enter to continue")
                    pass
            else:
                followingECS = True
                for j in range(0, self.test_params.TK_RD_TEST - 1):
                    if (ecs[j + 1] == 0 and ecs[j] == 255):
                        pass
                    elif (ecs[j + 1] - ecs[j] != 1):
                        followingECS = False
                        print "\033[91m   > #%d previous %d, current %d \033[0m"%(i, ecs[j], ecs[j+1])
                        pass
                    pass
                if (followingECS):
                    print Passed, "#" + str(i)
                else:
                    print Failed, "#%d received %d, expected %d, noncontinuous ECs"%(i, nPackets, self.test_params.TK_RD_TEST)
                    if self.debug:
                        raw_input("press enter to continue")
                        pass
                    self.test["G"] = False
                    pass
                pass
            pass

        print

        return

    ####################################################
    def SimultaneousTrackingDataReadoutTest(self):
        txtTitle("H. Reading out tracking data")
        print "   Turning on all VFAT2s and looking that all the Event Counters add up."

        self.test["H"] = True

        if (self.test["G"]):
            broadcastWrite(self.ohboard,self.gtx,"ContReg0", 0x37)

            mask = 0
            for i in self.presentVFAT2sSingle:
                mask |= (0x1 << i)
                pass
            setVFATTrackingMask(self.ohboard,self.gtx, ~(mask))

            sendResync(self.ohboard,self.gtx, 10, 1)

            flushTrackingFIFO(self.amc,self.gtx)

            t1_mode     =  0
            t1_type     =  0
            t1_n        =  self.test_params.TK_RD_TEST
            t1_interval =  400
            resetLocalT1(self.ohboard,self.gtx)

            nPackets = 0
            timeOut = 0
            ecs = []

            sendL1A(self.ohboard,self.gtx,t1_interval,t1_n)

            while ((readFIFODepth(self.amc,self.gtx)["Occupancy"]) != len(self.presentVFAT2sSingle) * self.test_params.TK_RD_TEST):
                timeOut += 1
                if (timeOut == 20 * self.test_params.TK_RD_TEST): break
                pass
            while ((readFIFODepth(self.amc,self.gtx)["isEMPTY"]) != 1):
                packets = readTrackingInfo(self.amc,self.gtx)
                ec = int((0x00000ff0 & packets[0]) >> 4)
                nPackets += 1
                ecs.append(ec)
                pass
            broadcastWrite(self.ohboard,self.gtx,"ContReg0", 0x36)

            if (nPackets != len(self.presentVFAT2sSingle) * self.test_params.TK_RD_TEST):
                print Failed, "#%d received: %d, expected: %d"%(i,nPackets, len(self.presentVFAT2sSingle) * self.test_params.TK_RD_TEST)
            else:
                followingECS = True
                for i in range(0, self.test_params.TK_RD_TEST - 1):
                    for j in range(0, len(self.presentVFAT2sSingle) - 1):
                        if (ecs[i * len(self.presentVFAT2sSingle) + j + 1] != ecs[i * len(self.presentVFAT2sSingle) + j]):
                            print "\033[91m   > #%d saw %d, %d saw %d \033[0m"%(j+1, ecs[i * len(self.presentVFAT2sSingle) + j + 1],
                                                                                j, ecs[i * len(self.presentVFAT2sSingle) + j])
                            followingECS = False
                            pass
                        pass
                    if (ecs[(i + 1) * len(self.presentVFAT2sSingle)]  == 0 and ecs[i * len(self.presentVFAT2sSingle)] == 255):
                        pass
                    elif (ecs[(i + 1) * len(self.presentVFAT2sSingle)] - ecs[i * len(self.presentVFAT2sSingle)] != 1):
                        print "\033[91m   > #%d previous %d, current %d \033[0m"%(i, ecs[i * len(self.presentVFAT2sSingle)],
                                                                                  ecs[(i+1) * len(self.presentVFAT2sSingle)])
                        followingECS = False
                        pass
                    pass
                if (followingECS): print Passed
                else:
                    print Failed
                    self.test["H"] = False
                    pass
                pass
            resetLocalT1(self.ohboard,self.gtx)
            pass
        else:
            print "   Skipping this test as the previous test did not succeed..."
            self.test["H"] = False
            pass

        print

        return

    ####################################################
    def TrackingDataReadoutRateTest(self):
        txtTitle("I. Testing the tracking data readout rate")
        print "   Sending triggers at a given rate and looking at the maximum readout rate that can be achieved."

        broadcastWrite(self.ohboard,self.gtx,"ContReg0", 0x36)

        writeVFAT(self.ohboard,self.gtx,self.presentVFAT2sSingle[0],"ContReg0",0x37)
        setVFATTrackingMask(self.ohboard,self.gtx, ~(0x1 << self.presentVFAT2sSingle[0]))

        f = open('out.log', 'w')

        values = [
                  100, 200, 300, 400, 500, 600, 700, 800, 900,
                  1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000,
                  10000, 20000, 30000, 40000, 50000, 60000, 70000, 80000, 90000,
                  100000, 125000, 150000, 175000, 200000
                ]

        previous = 0

        for i in values:
            isFull = False

            t1_mode     =  0
            t1_type     =  0
            t1_n        =  0
            t1_interval =  40000000 / i

            resetLocalT1(self.ohboard,self.gtx)
            flushTrackingFIFO(self.amc,self.gtx)
            sendL1A(self.ohboard,self.gtx,t1_interval,t1_n)

            if (self.test_params.RATE_WRITE):
                for j in range(0, 1000):
                    depth = readFIFODepth(self.amc,self.gtx)["Occupancy"]
                    if (depth > 0):
                        data = readTrackingInfo(self.amc,self.gtx,1*depth/7)
                        for d in data:
                            f.write(str(d))
                            pass
                        pass
                    if ((readFIFODepth(self.amc,self.gtx)["isFULL"]) == 1):
                        isFull = True
                        break
            else:
                for j in range(0, 1000):
                    depth = readFIFODepth(self.amc,self.gtx)["Occupancy"]
                    data = readTrackingInfo(self.amc,self.gtx,1*depth/7)
                    if ((readFIFODepth(self.amc,self.gtx)["isFULL"]) == 1):
                        isFull = True
                        break
                    pass
                pass

            if (isFull):
                print "   Maximum readout rate %4d %sHz"%(rateConverter(previous))
                break

            previous = i
            if self.debug:
                print "   Readout succeeded at %4d %sHz"%(rateConverter(previous))
                pass

            time.sleep(0.01)

        f.close()

        resetLocalT1(self.ohboard,self.gtx)
        writeVFAT(self.ohboard,self.gtx,self.presentVFAT2sSingle[0],"ContReg0",0x36)

        self.test["I"] = True

        setVFATTrackingMask(self.ohboard,self.gtx,self.vfatmask)

        print

        return

    ####################################################
    def OpticalLinkErrorTest(self):
        txtTitle("J. Testing the optical link error rate")

        # writeRegister(self.amc,"GLIB.COUNTERS.GTX%d.TRK_ERR.Reset"%(self.gtx), 1)
        # time.sleep(1)
        # glib_tk_error_reg = readRegister(self.amc,"GLIB.COUNTERS.GTX%d.TRK_ERR"%(self.gtx))

        # writeRegister(self.amc,"GLIB.COUNTERS.GTX%d.TRG_ERR.Reset"%(self.gtx), 1)
        # time.sleep(1)
        # glib_tr_error_reg = readRegister(self.amc,"GLIB.COUNTERS.GTX%d.TRG_ERR"%(self.gtx))

        # writeRegister(self.amc,"%s.COUNTERS.GTX.TRK_ERR"%(self.oh_basenode), 1)
        # time.sleep(1)
        # oh_tk_error_reg = readRegister(self.amc,"%s.COUNTERS.GTX.TRK_ERR"%(self.oh_basenode))

        # writeRegister(self.amc,"%s.COUNTERS.GTX.TRG_ERR"%(self.oh_basenode), 1)
        # time.sleep(1)
        # oh_tr_error_reg = readRegister(self.amc,"%s.COUNTERS.GTX.TRG_ERR"%(self.oh_basenode))

        # print "   AMC tracking link error rate is of        %4d %sHz"%(rateConverter(1*glib_tk_error_reg))
        # print "   AMC trigger link error rate is of         %4d %sHz"%(rateConverter(1*glib_tr_error_reg))
        # print "   OptoHybrid tracking link error rate is of %4d %sHz"%(rateConverter(1*oh_tk_error_reg))
        # print "   OptoHybrid trigger link error rate is of  %4d %sHz"%(rateConverter(1*oh_tr_error_reg))

        # self.test["J"] = True

        print

        return

    ####################################################
    def runSelectedTests(self):
        if ("A" in self.tests):
            self.AMCPresenceTest()
            pass
        if ("B" in self.tests):
            self.OptoHybridPresenceTest()
            pass
        if ("C" in self.tests):
            self.AMCRegisterTest()
            pass
        if ("D" in self.tests):
            self.OptoHybridRegisterTest()
            self.OptoHybridT1ControllerTest()
            pass
        if ("E" in self.tests):
            self.VFAT2DetectionTest()
            pass
        if ("F" in self.tests):
            self.VFAT2I2CRegisterTest()
            self.VFAT2ChannelRegisterTest()
            pass
        if ("G" in self.tests):
            self.TrackingDataReadoutTest()
            pass
        if ("H" in self.tests):
            self.SimultaneousTrackingDataReadoutTest()
            pass
        if ("I" in self.tests):
            self.TrackingDataReadoutRateTest()
            pass
        if ("J" in self.tests):
            self.OpticalLinkErrorTest()
            pass
        return

    ####################################################
    def runAllTests(self):
        self.AMCPresenceTest()
        self.OptoHybridPresenceTest()
        self.AMCRegisterTest()
        self.OptoHybridRegisterTest()
        self.VFAT2DetectionTest()
        self.VFAT2I2CRegisterTest()
        self.TrackingDataReadoutTest()
        self.SimultaneousTrackingDataReadoutTest()
        self.TrackingDataReadoutRateTest()
        self.OpticalLinkErrorTest()
        return

    ####################################################
    def report(self):
        txtTitle("K. Results")

        for test in self.allTests:
            if (test in self.tests):
                print "   %s.%s"%(test,(Passed if self.test[test] else Failed))
            else:
                print "   %s.%s"%(test,NotRun)
                pass
            pass
        return

if __name__ == "__main__":
    from qcoptions import parser

    (options, args) = parser.parse_args()

    test_params = TEST_PARAMS(namc=options.namc,
                              noh=options.noh,
                              ni2c=options.ni2c,
                              ntrk=options.ntrk,
                              writeout=options.writeout)

    testSuite = GEMDAQTestSuite(slot=options.slot,
                                gtx=options.gtx,
                                shelf=options.shelf,
                                tests=options.tests,
                                test_params=test_params,
                                debug=options.debug)

    testSuite.runSelectedTests()
    testSuite.report()
