
# source of this is the getInverterData() function in SBFspot.cpp
# getInverterData
# todo, remove datatype from this list, add the 16, 28, 40 length, and no of elements (or better to get from packet length)?
# Dictionary, used to lookup SMA data request parameters
# Seems to represent a range of registers in the SMA device memory.
# :param type:  SMA request type mostly 0x0200
# :param subtype:SMA request subtype  often 0x5100
# :param arg1: pointer to range: from
# :param arg2: pointer to range: to
# :param extra: normally 0
# response_data_type, string, used to determine how to format and store the response
#  e.g. sma28 is 1 to n 28-byte groups
sma_request_type ={
# // SPOT_UAC1, SPOT_UAC2, SPOT_UAC3, SPOT_IAC1, SPOT_IAC2, SPOT_IAC3
'SpotACVoltage': (0x0200, 0x5100, 0x00464800, 0x004655FF, 0, 28),
'SpotGridFrequency': (0x0200, 0x5100, 0x00465700, 0x004657FF, 0, 28),   # // SPOT_FREQ
'MaxACPower': (0x0200, 0x5100, 0x00411E00, 0x004120FF, 0, 28),          # // INV_PACMAX1, INV_PACMAX2, INV_PACMAX3
'MaxACPower2': (0x0200, 0x5100, 0x00832A00, 0x00832AFF, 0, 28),         # // INV_PACMAX1_2
'SpotACTotalPower': (0x0200, 0x5100, 0x00263F00, 0x00263FFF, 0, 28),    # // SPOT_PACTOT
'EnergyProduction': (0x0200, 0x5400, 0x00260100, 0x002622FF, 0, 16),    # // SPOT_ETODAY, SPOT_ETOTAL
'SpotDCPower': (0x0200, 0x5380, 0x00251E00, 0x00251EFF, 0, 28),
'SpotDCVoltage': (0x0200, 0x5380, 0x00451F00, 0x004521FF, 0, 28),       # // SPOT_UDC1, SPOT_UDC2, SPOT_IDC1, SPOT_IDC2
'TypeLabel': (0x0200, 0x5800, 0x00821E00, 0x008220FF, 0, 40),           # // INV_NAME, INV_TYPE, INV_CLASS
'SoftwareVersion': (0x0200, 0x5800, 0x00823400, 0x008234FF, 0, 40),      # // INV_SWVERSION
'DeviceStatus': (0x0200, 0x5180, 0x00214800, 0x002148FF, 0, 40),         # // INV_STATUS
'GridRelayStatus': (0x0200, 0x5180, 0x00416400, 0x004164FF, 0, 40),      # // INV_GRIDRELAY
}

# Exploring binary formation of these SMA data types
# 0x5100  10100010 0000000    MaxACPower
# 0x5140  10100010 1000000
# 0x5180  10100011 0000000    Status
# 0x5200  10100100 0000000
# 0x5380  10100111 0000000    Spot DC (2 strings)
# 0x5400  10101000 0000000    Spot AC Power
# 0x5800  10110000 0000000    Version/type string


# getInverterData function in SBFspot.cpp October 2019
# int getInverterData(InverterData *devList[], enum getInverterDataType type)
# {
#     if (DEBUG_NORMAL) printf("getInverterData(%d)\n", type);
#     const char *strWatt = "%-12s: %ld (W) %s";
#     const char *strVolt = "%-12s: %.2f (V) %s";
#     const char *strAmp = "%-12s: %.3f (A) %s";
#     const char *strkWh = "%-12s: %.3f (kWh) %s";
#     const char *strHour = "%-12s: %.3f (h) %s";
#
#     int rc = E_OK;
#
#     int recordsize = 0;
#     int validPcktID = 0;
#
#     unsigned long command;
#     unsigned long first;
#     unsigned long last;
#
#     switch(type)
#     {
#     case EnergyProduction:
#         // SPOT_ETODAY, SPOT_ETOTAL
#         command = 0x54000200;
#         first = 0x00260100;
#         last = 0x002622FF;
#         break;
#
#     case SpotDCPower:
#         // SPOT_PDC1, SPOT_PDC2
#         command = 0x53800200;
#         first = 0x00251E00;
#         last = 0x00251EFF;
#         break;
#
#     case SpotDCVoltage:
#         // SPOT_UDC1, SPOT_UDC2, SPOT_IDC1, SPOT_IDC2
#         command = 0x53800200;
#         first = 0x00451F00;
#         last = 0x004521FF;
#         break;
#
#     case SpotACPower:
#         // SPOT_PAC1, SPOT_PAC2, SPOT_PAC3
#         command = 0x51000200;
#         first = 0x00464000;
#         last = 0x004642FF;
#         break;
#
#     case SpotACVoltage:
#         // SPOT_UAC1, SPOT_UAC2, SPOT_UAC3, SPOT_IAC1, SPOT_IAC2, SPOT_IAC3
#         command = 0x51000200;
#         first = 0x00464800;
#         last = 0x004655FF;
#         break;
#
#     case SpotGridFrequency:
#         // SPOT_FREQ
#         command = 0x51000200;
#         first = 0x00465700;
#         last = 0x004657FF;
#         break;
#
#     case MaxACPower:
#         // INV_PACMAX1, INV_PACMAX2, INV_PACMAX3
#         command = 0x51000200;
#         first = 0x00411E00;
#         last = 0x004120FF;
#         break;
#
#     case MaxACPower2:
#         // INV_PACMAX1_2
#         command = 0x51000200;
#         first = 0x00832A00;
#         last = 0x00832AFF;
#         break;
#
#     case SpotACTotalPower:
#         // SPOT_PACTOT
#         command = 0x51000200;
#         first = 0x00263F00;
#         last = 0x00263FFF;
#         break;
#
#     case TypeLabel:
#         // INV_NAME, INV_TYPE, INV_CLASS
#         command = 0x58000200;
#         first = 0x00821E00;
#         last = 0x008220FF;
#         break;
#
#     case SoftwareVersion:
#         // INV_SWVERSION
#         command = 0x58000200;
#         first = 0x00823400;
#         last = 0x008234FF;
#         break;
#
#     case DeviceStatus:
#         // INV_STATUS
#         command = 0x51800200;
#         first = 0x00214800;
#         last = 0x002148FF;
#         break;
#
#     case GridRelayStatus:
#         // INV_GRIDRELAY
#         command = 0x51800200;
#         first = 0x00416400;
#         last = 0x004164FF;
#         break;
#
#     case OperationTime:
#         // SPOT_OPERTM, SPOT_FEEDTM
#         command = 0x54000200;
#         first = 0x00462E00;
#         last = 0x00462FFF;
#         break;
#
#     case BatteryChargeStatus:
#         command = 0x51000200;
#         first = 0x00295A00;
#         last = 0x00295AFF;
#         break;
#
#     case BatteryInfo:
#         command = 0x51000200;
#         first = 0x00491E00;
#         last = 0x00495DFF;
#         break;
#
# 	case InverterTemperature:
# 		command = 0x52000200;
# 		first = 0x00237700;
# 		last = 0x002377FF;
# 		break;
#
# 	case MeteringGridMsTotW:
# 		command = 0x51000200;
# 		first = 0x00463600;
# 		last = 0x004637FF;
# 		break;
#
# 	case sbftest:
# 		command = 0x64020200;
# 		first = 0x00618C00;
# 		last = 0x00618FFF;
# 		break;


# source SBFspot.h
# uses bitwise shift left
# enum getInverterDataType
# {
	# EnergyProduction	    = 1 << 0,   01
	# SpotDCPower			= 1 << 1,   02
	# SpotDCVoltage		    = 1 << 2,   04
	# SpotACPower			= 1 << 3,   08
	# SpotACVoltage		    = 1 << 4,   10
	# SpotGridFrequency	    = 1 << 5,   20
	# MaxACPower			= 1 << 6,   40
	# MaxACPower2			= 1 << 7,   80
	# SpotACTotalPower	    = 1 << 8,   100
	# TypeLabel			    = 1 << 9,
	# OperationTime		    = 1 << 10,
	# SoftwareVersion		= 1 << 11,
	# DeviceStatus		    = 1 << 12,
	# GridRelayStatus		= 1 << 13,
	# BatteryChargeStatus   = 1 << 14,
	# BatteryInfo           = 1 << 15,
	# InverterTemperature	= 1 << 16,
	# MeteringGridMsTotW	= 1 << 17,

	# sbftest             = 1 << 31
# };

# Dictionary for SMA data types
# Unused - not relevant to have this Enum approach
# todo setup as  table on these types
# InverterDataType ={
# 0x0001: ('EnergyProduction'),
# 0x0002: ('SpotDCPower'),
# 0x0004: ('SpotDCVoltage'),
# 0x0008  ('SpotACPower'),
# 0x0010: ('SpotACVoltage'),
# 0x0020: ('SpotGridFrequency'),
# 0x0040: ('MaxACPower'),
# 0x0080: ('MaxACPower2'),
# 0x0100: ('SpotACTotalPower'),
# 0x0200: ('TypeLabel'),
# 0x0400: ('OperationTime'),
# 0x0800: ('SoftwareVersion')
# }
    # SpotDCPower			= 1 << 1,   02
	# SpotDCVoltage		    = 1 << 2,   04
	# SpotACPower			= 1 << 3,   08
	# SpotACVoltage		    = 1 << 4,   10
	# SpotGridFrequency	    = 1 << 5,   20
	# MaxACPower			= 1 << 6,   40
	# MaxACPower2			= 1 << 7,   80
	# SpotACTotalPower	    = 1 << 8,   100
	# TypeLabel			    = 1 << 9,
	# OperationTime		    = 1 << 10,
	# SoftwareVersion		= 1 << 11,
	# DeviceStatus		    = 1 << 12,
	# GridRelayStatus		= 1 << 13,
	# BatteryChargeStatus   = 1 << 14,
	# BatteryInfo           = 1 << 15,
	# InverterTemperature	= 1 << 16,
	# MeteringGridMsTotW	= 1 << 17,

	# sbftest             = 1 << 31





# Dictionary for SMA response numerical data types
# leading byte usually 00 or 40, byte 3 is usually 01 (meaning: string, object ID)
# 2 byte code, Description, Unit, LongUnit, divisor
# typical Medway values DC 6.7A, 244V; AC 13.6A 238V
# todo - do these represent the units in specific bits - can we derive from a bit mask rather than lookup?
# Used in sma_request to determine how to format and describe a numeric response from the SMA device
sma_data_unit ={
0x251e: ('DC spot Power String', 'W', 'Watts', 1),       #1880-1900 full power
0x251e: ('DC spot Power String', 'W', 'Watts', 1),

0x263f: ('Power now', 'W', 'Watts', 1),
0x2601: ('Total generated', 'Wh', 'Watt hours', 1),
0x2622: ('Total generated today', 'Wh', 'Watt hours', 1),

0x411e: ('Max power phase 1', 'W', 'Watts', 1),
0x411f: ('Max power phase 2', 'W', 'Watts', 1),
0x4120: ('Max power phase 3', 'W', 'Watts', 1),

0x462e: ('Inverter operating time', 's', 'Seconds', 1),
0x462f: ('Inverter feed-in time', 's', 'Seconds', 1),
0x451f: ('DC voltage String', 'V', 'Volts', 100),
0x4521: ('DC current String', 'mA', 'milli Amps', 1),

0x4648: ('AC spot line voltage phase 1', 'V', 'Volts', 100),
0x4649: ('AC spot line voltage phase 2', 'V', 'Volts', 100),
0x464A: ('AC spot line voltage phase 3', 'V', 'Volts', 100),
0x4650: ('AC spot current phase 1', 'mA', 'milli Amps', 1),
0x4651: ('AC spot current phase 2', 'mA', 'milli Amps', 1),
0x4652: ('AC spot current phase 3', 'mA', 'milli Amps', 1),
0x4656: ('??spot Grid frequency', 'Hz', 'Hertz', 100),
0x4657: ('spot Grid frequency', 'Hz', 'Hertz', 100),
0x4658: ('??spot Grid frequency', 'Hz', 'Hertz', 100),
0x4a1f: ('????	?', 'W', '?', 1),
}

# From SBFSpot.h October 2019
# Lists all the data elements from SMA device and their data types
# Does not indicate that the SMA device stores these data sequentially
# typedef struct
# {
#     char DeviceName[33];    //32 bytes + terminating zero
# 	unsigned char BTAddress[6];
# 	char IPAddress[20];
# 	unsigned short SUSyID;
#     unsigned long Serial;
# 	unsigned char NetID;
# 	float BT_Signal;
#     time_t InverterDatetime;
#     time_t WakeupTime;
#     time_t SleepTime;
#     long Pdc1;
#     long Pdc2;
#     long Udc1;
#     long Udc2;
#     long Idc1;
#     long Idc2;
#     long Pmax1;
#     long Pmax2;
#     long Pmax3;
#     long TotalPac;
#     long Pac1;
#     long Pac2;
#     long Pac3;
#     long Uac1;
#     long Uac2;
#     long Uac3;
#     long Iac1;
#     long Iac2;
#     long Iac3;
#     long GridFreq;
# 	long long OperationTime;
#     long long FeedInTime;
#     long long EToday;
#     long long ETotal;
# 	unsigned short modelID;
# 	char DeviceType[64];
# 	char DeviceClass[64];
# 	DEVICECLASS DevClass;
# 	char SWVersion[16];	//"03.01.05.R"
# 	int DeviceStatus;
# 	int GridRelayStatus;
# 	int flags;
# 	DayData dayData[288];
# 	MonthData monthData[31];
# 	bool hasMonthData;
# 	time_t monthDataOffset;	// Issue 115
# 	std::vector<EventData> eventData;
# 	long calPdcTot;
# 	long calPacTot;
# 	float calEfficiency;
# 	unsigned long BatChaStt;			// Current battery charge status
#     unsigned long BatDiagCapacThrpCnt;	// Number of battery charge throughputs
#     unsigned long BatDiagTotAhIn;		// Amp hours counter for battery charge
#     unsigned long BatDiagTotAhOut;		// Amp hours counter for battery discharge
#     unsigned long BatTmpVal;			// Battery temperature
#     unsigned long BatVol;				// Battery voltage
#     long BatAmp;						// Battery current
# 	long Temperature;					// Inverter Temperature
# 	int32_t	MeteringGridMsTotWOut;		// Power grid feed-in (Out)
# 	int32_t MeteringGridMsTotWIn;		// Power grid reference (In)
# 	bool hasBattery;					// Smart Energy device
# } InverterData;

# From SBFSpot.h October 2019
# Lists all the SMA device types
# Todo confirm this is ENUM or actual SMA device, incorporate in data request unpacking
# part of TypeLabel response INV_CLASS
# typedef enum
# {
#     AllDevices = 8000,          // DevClss0
#     SolarInverter = 8001,       // DevClss1
#     WindTurbineInverter = 8002, // DevClss2
#     BatteryInverter = 8007,     // DevClss7
#     Consumer = 8033,            // DevClss33
#     SensorSystem = 8064,        // DevClss64
#     ElectricityMeter = 8065,    // DevClss65
#     CommunicationProduct = 8128 // DevClss128
# } DEVICECLASS;

# todo - use this?
# from Archdata.cpp
# ArchiveDayData
# writeLong(pcktBuf, 0x70000200);
# writeLong(pcktBuf, startTime - 300);
# writeLong(pcktBuf, startTime + 86100);
#
# ArchiveMonthData
# writeLong(pcktBuf, 0x70200200);
# writeLong(pcktBuf, startTime - 86400 - 86400);
# writeLong(pcktBuf, startTime + 86400 * (sizeof(inverters[inv]->monthData) / sizeof(MonthData) + 1));
#
# ArchiveEventData
# writeLong(pcktBuf, UserGroup == UG_USER ? 0x70100200 : 0x70120200);
# writeLong(pcktBuf, startTime);
# writeLong(pcktBuf, endTime);
#


# source of this is the LriDef in SBFspot.h
# todo, add datatype to this list
# Dictionary, used to lookup SMA data element parameters
# :param type:  SMA request type mostly 0x0200
# :param subtype:SMA request subtype  often 0x5100

# :param arg1: pointer to range: from
# :param element_name: short name for element
# data type code, SMA, 4 values  0x10 =text, 0x08 = status, 0x00, 0x40 = Dword 64 bit data
# :param extra: normally 0
# todo - add these items and merge the two lists, or consider multi-language?
## 0x4658: ('??spot Grid frequency', 'Hz', 'Hertz', 100),

sma_data_element ={
0x2148: ('OperationHealth', 0x08, 'Condition (aka INV_STATUS)'),
0x2377: ('CoolsysTmpNom', 0x40, 'Operating condition temperatures'),
0x251E: ('DcMsWatt', 0x40, 'DC power input (aka SPOT_PDC1 / SPOT_PDC2)'),
0x2601: ('MeteringTotWhOut', 0x00, 'Total yield (aka SPOT_ETOTAL)'),
0x2622: ('MeteringDyWhOut', 0x00, 'Day yield (aka SPOT_ETODAY)'),
0x263F: ('GridMsTotW', 0x40, 'Power (aka SPOT_PACTOT)'),
0x295A: ('BatChaStt', 0x00, 'Current battery charge status'),
0x411E: ('OperationHealthSttOk', 0x00, 'Nominal power in Ok Mode (aka INV_PACMAX1)'),
0x411F: ('OperationHealthSttWrn', 0x00, 'Nominal power in Warning Mode (aka INV_PACMAX2)'),
0x4120: ('OperationHealthSttAlm', 0x00, 'Nominal power in Fault Mode (aka INV_PACMAX3)'),
0x4164: ('OperationGriSwStt', 0x08, 'Grid relay/contactor (aka INV_GRIDRELAY)'),
0x4166: ('OperationRmgTms', 0x00, 'Waiting time until feed-in'),
0x451F: ('DcMsVol', 0x40, 'DC voltage input (aka SPOT_UDC1 / SPOT_UDC2)'),
0x4521: ('DcMsAmp', 0x40, 'DC current input (aka SPOT_IDC1 / SPOT_IDC2)'),
0x4623: ('MeteringPvMsTotWhOut', 0x00, 'PV generation counter reading'),
0x4624: ('MeteringGridMsTotWhOut', 0x00, 'Grid feed-in counter reading'),
0x4625: ('MeteringGridMsTotWhIn', 0x00, 'Grid reference counter reading'),
0x4626: ('MeteringCsmpTotWhIn', 0x00, 'Meter reading consumption meter'),
0x4627: ('MeteringGridMsDyWhOut', 0x00, '?'),
0x4628: ('MeteringGridMsDyWhIn', 0x00, '?'),
0x462E: ('MeteringTotOpTms', 0x00, 'Operating time (aka SPOT_OPERTM)'),
0x462F: ('MeteringTotFeedTms', 0x00, 'Feed-in time (aka SPOT_FEEDTM)'),
0x4631: ('MeteringGriFailTms', 0x00, 'Power outage'),
0x463A: ('MeteringWhIn', 0x00, 'Absorbed energy'),
0x463B: ('MeteringWhOut', 0x00, 'Released energy'),
0x4635: ('MeteringPvMsTotWOut', 0x40, 'PV power generated'),
0x4636: ('MeteringGridMsTotWOut', 0x40, 'Power grid feed-in'),
0x4637: ('MeteringGridMsTotWIn', 0x40, 'Power grid reference'),
0x4639: ('MeteringCsmpTotWIn', 0x40, 'Consumer power'),
0x4640: ('GridMsWphsA', 0x40, 'Power L1 (aka SPOT_PAC1)'),
0x4641: ('GridMsWphsB', 0x40, 'Power L2 (aka SPOT_PAC2)'),
0x4642: ('GridMsWphsC', 0x40, 'Power L3 (aka SPOT_PAC3)'),
0x4648: ('GridMsPhVphsA', 0x00, 'Grid voltage phase L1 (aka SPOT_UAC1)'),
0x4649: ('GridMsPhVphsB', 0x00, 'Grid voltage phase L2 (aka SPOT_UAC2)'),
0x464A: ('GridMsPhVphsC', 0x00, 'Grid voltage phase L3 (aka SPOT_UAC3)'),
0x4650: ('GridMsAphsA_1', 0x00, 'Grid current phase L1 (aka SPOT_IAC1)'),
0x4651: ('GridMsAphsB_1', 0x00, 'Grid current phase L2 (aka SPOT_IAC2)'),
0x4652: ('GridMsAphsC_1', 0x00, 'Grid current phase L3 (aka SPOT_IAC3)'),
0x4653: ('GridMsAphsA', 0x00, 'Grid current phase L1 (aka SPOT_IAC1_2)'),
0x4654: ('GridMsAphsB', 0x00, 'Grid current phase L2 (aka SPOT_IAC2_2)'),
0x4655: ('GridMsAphsC', 0x00, 'Grid current phase L3 (aka SPOT_IAC3_2)'),
0x4657: ('GridMsHz', 0x00, 'Grid frequency (aka SPOT_FREQ)'),
0x46AA: ('MeteringSelfCsmpSelfCsmpWh', 0x00, 'Energy consumed internally'),
0x46AB: ('MeteringSelfCsmpActlSelfCsmp', 0x00, 'Current self-consumption'),
0x46AC: ('MeteringSelfCsmpSelfCsmpInc', 0x00, 'Current rise in self-consumption'),
0x46AD: ('MeteringSelfCsmpAbsSelfCsmpInc', 0x00, 'Rise in self-consumption'),
0x46AE: ('MeteringSelfCsmpDySelfCsmpInc', 0x00, 'Rise in self-consumption today'),
0x491E: ('BatDiagCapacThrpCnt', 0x40, 'Number of battery charge throughputs'),
0x4926: ('BatDiagTotAhIn', 0x00, 'Amp hours counter for battery charge'),
0x4927: ('BatDiagTotAhOut', 0x00, 'Amp hours counter for battery discharge'),
0x495B: ('BatTmpVal', 0x40, 'Battery temperature'),
0x495C: ('BatVol', 0x40, 'Battery voltage'),
0x495D: ('BatAmp', 0x40, 'Battery current'),
0x821E: ('NameplateLocation', 0x10, 'Device name (aka INV_NAME)'),
0x821F: ('NameplateMainModel', 0x08, 'Device class (aka INV_CLASS)'),
0x8220: ('NameplateModel', 0x08, 'Device type (aka INV_TYPE)'),
0x8221: ('NameplateAvalGrpUsr', 0x00, 'Unknown'),
0x8234: ('NameplatePkgRev', 0x08, 'Software package (aka INV_SWVER)'),
0x832A: ('InverterWLim', 0x00, 'Maximum active power device (aka INV_PACMAX1_2) (Some inverters like SB3300/SB1200)'),
0x464B: ('GridMsPhVphsA2B6100', 0x00, 'Grid voltage new-undefined'),
0x464C: ('GridMsPhVphsB2C6100', 0x00, 'Grid voltage new-undefined'),
0x464D: ('GridMsPhVphsC2A6100', 0x00, 'Grid voltage new-undefined'),
}

# From SBFSpot.h October 2019
# Lists all the SMA requests with the arg1 parameter (start of range in SMA data register)
# for example, from dict sma_request_type, this entry:
#       // SPOT_UAC1, SPOT_UAC2, SPOT_UAC3, SPOT_IAC1, SPOT_IAC2, SPOT_IAC3
#       'SpotACVoltage': (0x0200, 0x5100, 0x00464800, 0x004655FF, 0),
# corresponds to the 0x00464800 line below:
#       GridMsPhVphsA                   = 0x00464800,   // *00* Grid voltage phase L1 (aka SPOT_UAC1)
# typedef enum
# {
#     OperationHealth                 = 0x00214800,   // *08* Condition (aka INV_STATUS)
# 	CoolsysTmpNom					= 0x00237700,	// *40* Operating condition temperatures
#     DcMsWatt                        = 0x00251E00,   // *40* DC power input (aka SPOT_PDC1 / SPOT_PDC2)
#     MeteringTotWhOut                = 0x00260100,   // *00* Total yield (aka SPOT_ETOTAL)
#     MeteringDyWhOut                 = 0x00262200,   // *00* Day yield (aka SPOT_ETODAY)
#     GridMsTotW                      = 0x00263F00,   // *40* Power (aka SPOT_PACTOT)
#     BatChaStt                       = 0x00295A00,   // *00* Current battery charge status
#     OperationHealthSttOk            = 0x00411E00,   // *00* Nominal power in Ok Mode (aka INV_PACMAX1)
#     OperationHealthSttWrn           = 0x00411F00,   // *00* Nominal power in Warning Mode (aka INV_PACMAX2)
#     OperationHealthSttAlm           = 0x00412000,   // *00* Nominal power in Fault Mode (aka INV_PACMAX3)
#     OperationGriSwStt               = 0x00416400,   // *08* Grid relay/contactor (aka INV_GRIDRELAY)
#     OperationRmgTms                 = 0x00416600,   // *00* Waiting time until feed-in
#     DcMsVol                         = 0x00451F00,   // *40* DC voltage input (aka SPOT_UDC1 / SPOT_UDC2)
#     DcMsAmp                         = 0x00452100,   // *40* DC current input (aka SPOT_IDC1 / SPOT_IDC2)
#     MeteringPvMsTotWhOut            = 0x00462300,   // *00* PV generation counter reading
#     MeteringGridMsTotWhOut          = 0x00462400,   // *00* Grid feed-in counter reading
#     MeteringGridMsTotWhIn           = 0x00462500,   // *00* Grid reference counter reading
#     MeteringCsmpTotWhIn             = 0x00462600,   // *00* Meter reading consumption meter
#     MeteringGridMsDyWhOut	        = 0x00462700,   // *00* ?
#     MeteringGridMsDyWhIn            = 0x00462800,   // *00* ?
#     MeteringTotOpTms                = 0x00462E00,   // *00* Operating time (aka SPOT_OPERTM)
#     MeteringTotFeedTms              = 0x00462F00,   // *00* Feed-in time (aka SPOT_FEEDTM)
#     MeteringGriFailTms              = 0x00463100,   // *00* Power outage
#     MeteringWhIn                    = 0x00463A00,   // *00* Absorbed energy
#     MeteringWhOut                   = 0x00463B00,   // *00* Released energy
#     MeteringPvMsTotWOut             = 0x00463500,   // *40* PV power generated
#     MeteringGridMsTotWOut           = 0x00463600,   // *40* Power grid feed-in
#     MeteringGridMsTotWIn            = 0x00463700,   // *40* Power grid reference
#     MeteringCsmpTotWIn              = 0x00463900,   // *40* Consumer power
#     GridMsWphsA                     = 0x00464000,   // *40* Power L1 (aka SPOT_PAC1)
#     GridMsWphsB                     = 0x00464100,   // *40* Power L2 (aka SPOT_PAC2)
#     GridMsWphsC                     = 0x00464200,   // *40* Power L3 (aka SPOT_PAC3)
#     GridMsPhVphsA                   = 0x00464800,   // *00* Grid voltage phase L1 (aka SPOT_UAC1)
#     GridMsPhVphsB                   = 0x00464900,   // *00* Grid voltage phase L2 (aka SPOT_UAC2)
#     GridMsPhVphsC                   = 0x00464A00,   // *00* Grid voltage phase L3 (aka SPOT_UAC3)
#     GridMsAphsA_1                   = 0x00465000,   // *00* Grid current phase L1 (aka SPOT_IAC1)
#     GridMsAphsB_1                   = 0x00465100,   // *00* Grid current phase L2 (aka SPOT_IAC2)
#     GridMsAphsC_1                   = 0x00465200,   // *00* Grid current phase L3 (aka SPOT_IAC3)
#     GridMsAphsA                     = 0x00465300,   // *00* Grid current phase L1 (aka SPOT_IAC1_2)
#     GridMsAphsB                     = 0x00465400,   // *00* Grid current phase L2 (aka SPOT_IAC2_2)
#     GridMsAphsC                     = 0x00465500,   // *00* Grid current phase L3 (aka SPOT_IAC3_2)
#     GridMsHz                        = 0x00465700,   // *00* Grid frequency (aka SPOT_FREQ)
#     MeteringSelfCsmpSelfCsmpWh      = 0x0046AA00,   // *00* Energy consumed internally
#     MeteringSelfCsmpActlSelfCsmp    = 0x0046AB00,   // *00* Current self-consumption
#     MeteringSelfCsmpSelfCsmpInc     = 0x0046AC00,   // *00* Current rise in self-consumption
#     MeteringSelfCsmpAbsSelfCsmpInc  = 0x0046AD00,   // *00* Rise in self-consumption
#     MeteringSelfCsmpDySelfCsmpInc   = 0x0046AE00,   // *00* Rise in self-consumption today
#     BatDiagCapacThrpCnt             = 0x00491E00,   // *40* Number of battery charge throughputs
#     BatDiagTotAhIn                  = 0x00492600,   // *00* Amp hours counter for battery charge
#     BatDiagTotAhOut                 = 0x00492700,   // *00* Amp hours counter for battery discharge
#     BatTmpVal                       = 0x00495B00,   // *40* Battery temperature
#     BatVol                          = 0x00495C00,   // *40* Battery voltage
#     BatAmp                          = 0x00495D00,   // *40* Battery current
#     NameplateLocation               = 0x00821E00,   // *10* Device name (aka INV_NAME)
#     NameplateMainModel              = 0x00821F00,   // *08* Device class (aka INV_CLASS)
#     NameplateModel                  = 0x00822000,   // *08* Device type (aka INV_TYPE)
#     NameplateAvalGrpUsr             = 0x00822100,   // *  * Unknown
#     NameplatePkgRev                 = 0x00823400,   // *08* Software package (aka INV_SWVER)
#     InverterWLim                    = 0x00832A00,   // *00* Maximum active power device (aka INV_PACMAX1_2) (Some inverters like SB3300/SB1200)
# 	GridMsPhVphsA2B6100             = 0x00464B00,
# 	GridMsPhVphsB2C6100             = 0x00464C00,
# 	GridMsPhVphsC2A6100             = 0x00464D00
# } LriDef;
