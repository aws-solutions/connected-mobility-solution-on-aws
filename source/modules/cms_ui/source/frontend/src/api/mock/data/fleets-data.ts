// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  VehicleItem,
  CampaignStatus,
  CampaignItem,
  SignalCatalogItem,
  DecoderManifestItem,
} from "@com.cms.fleetmanagement/api-client";

export enum FLEETS {
  "TEST_FLEET_1" = "test-fleet-1",
  "TEST_FLEET_2" = "test-fleet-2",
  "TEST_FLEET_3" = "test-fleet-3",
  "TEST_FLEET_4" = "test-fleet-4",
  "TEST_FLEET_5" = "test-fleet-5",
}

export interface FleetSummary {
  id: string;
  name: string;
}

const vehicleVins: string[] = [
  "1FDWF37S23EC10000",
  "1FDWF37S18EC10001",
  "1FDWF37S18EC10002",
  "1FDWF37S23EC10003",
  "1FDWF37S24EC10004",
  "1FDWF37S22EC10005",
  "1FDWF37S22EC10006",
  "1FDWF37S19EC10007",
  "1FDWF37S20EC10008",
  "1FDWF37S20EC10009",
  "1FDWF37S22EC10010",
  "1FDWF37S22EC10011",
  "1FDWF37S23EC10012",
  "1FDWF37S21EC10013",
  "1FDWF37S18EC10014",
  "1FDWF37S20EC10015",
  "1FDWF37S20EC10016",
  "1FDWF37S24EC10017",
  "1FDWF37S18EC10018",
  "1FDWF37S23EC10019",
  "1FDWF37S21EC10020",
  "1FDWF37S20EC10021",
  "1FDWF37S22EC10022",
  "1FDWF37S23EC10023",
  "1FDWF37S24EC10024",
  "1FDWF37S19EC10025",
  "1FDWF37S24EC10026",
  "1FDWF37S22EC10027",
  "1FDWF37S19EC10028",
  "1FDWF37S19EC10029",
  "1FDWF37S19EC10030",
  "1FDWF37S21EC10031",
  "1FDWF37S21EC10032",
  "1FDWF37S20EC10033",
  "1FDWF37S21EC10034",
  "1FDWF37S21EC10035",
  "1FDWF37S20EC10036",
  "1FDWF37S20EC10037",
  "1FDWF37S23EC10038",
  "1FDWF37S22EC10039",
  "1FDWF37S20EC10040",
  "1FDWF37S20EC10041",
  "1FDWF37S24EC10042",
  "1FDWF37S19EC10043",
  "1FDWF37S22EC10044",
  "1FDWF37S18EC10045",
  "1FDWF37S19EC10046",
  "1FDWF37S18EC10047",
  "1FDWF37S24EC10048",
  "1FDWF37S24EC10049",
  "1FDWF37S19EC10050",
  "1FDWF37S24EC10051",
  "1FDWF37S23EC10052",
  "1FDWF37S19EC10053",
  "1FDWF37S20EC10054",
  "1FDWF37S19EC10055",
  "1FDWF37S22EC10056",
  "1FDWF37S23EC10057",
  "1FDWF37S21EC10058",
  "1FDWF37S23EC10059",
  "1FDWF37S20EC10060",
  "1FDWF37S20EC10061",
  "1FDWF37S19EC10062",
  "1FDWF37S23EC10063",
  "1FDWF37S18EC10064",
  "1FDWF37S23EC10065",
  "1FDWF37S19EC10066",
  "1FDWF37S19EC10067",
  "1FDWF37S21EC10068",
  "1FDWF37S21EC10069",
  "1FDWF37S23EC10070",
  "1FDWF37S18EC10071",
  "1FDWF37S19EC10072",
  "1FDWF37S19EC10073",
  "1FDWF37S19EC10074",
  "1FDWF37S24EC10075",
  "1FDWF37S19EC10076",
  "1FDWF37S20EC10077",
  "1FDWF37S20EC10078",
  "1FDWF37S18EC10079",
  "1FDWF37S22EC10080",
  "1FDWF37S22EC10081",
  "1FDWF37S21EC10082",
  "1FDWF37S19EC10083",
  "1FDWF37S20EC10084",
  "1FDWF37S24EC10085",
  "1FDWF37S21EC10086",
  "1FDWF37S18EC10087",
  "1FDWF37S22EC10088",
  "1FDWF37S23EC10089",
  "1FDWF37S18EC10090",
  "1FDWF37S20EC10091",
  "1FDWF37S23EC10092",
  "1FDWF37S23EC10093",
  "1FDWF37S19EC10094",
  "1FDWF37S18EC10095",
  "1FDWF37S20EC10096",
  "1FDWF37S21EC10097",
  "1FDWF37S22EC10098",
  "1FDWF37S23EC10099",
];

export const FLEET_VEHICLES: Record<string, string[]> = {
  [FLEETS.TEST_FLEET_1]: Array.from({ length: 20 }, (_, i) => vehicleVins[i]), // 0-19
  [FLEETS.TEST_FLEET_2]: Array.from(
    { length: 30 },
    (_, i) => vehicleVins[i + 20],
  ),
  [FLEETS.TEST_FLEET_3]: Array.from(
    { length: 18 },
    (_, i) => vehicleVins[i + 50],
  ),
  [FLEETS.TEST_FLEET_4]: Array.from(
    { length: 9 },
    (_, i) => vehicleVins[i + 68],
  ),
  [FLEETS.TEST_FLEET_5]: Array.from(
    { length: 23 },
    (_, i) => vehicleVins[i + 77],
  ),
};

export const VEHICLES: VehicleItem[] = [
  {
    name: vehicleVins[0],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA4949",
    },
  },
  {
    name: vehicleVins[1],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA6708",
    },
  },
  {
    name: vehicleVins[2],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA7785",
    },
  },
  {
    name: vehicleVins[3],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA3361",
    },
  },
  {
    name: vehicleVins[4],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA6818",
    },
  },
  {
    name: vehicleVins[5],
    status: "INACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA6321",
    },
  },
  {
    name: vehicleVins[6],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA8033",
    },
  },
  {
    name: vehicleVins[7],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA7122",
    },
  },
  {
    name: vehicleVins[8],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA9708",
    },
  },
  {
    name: vehicleVins[9],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA8588",
    },
  },
  {
    name: vehicleVins[10],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA3603",
    },
  },
  {
    name: vehicleVins[11],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA7464",
    },
  },
  {
    name: vehicleVins[12],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA6226",
    },
  },
  {
    name: vehicleVins[13],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA3263",
    },
  },
  {
    name: vehicleVins[14],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA6828",
    },
  },
  {
    name: vehicleVins[15],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA5425",
    },
  },
  {
    name: vehicleVins[16],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA4079",
    },
  },
  {
    name: vehicleVins[17],
    status: "INACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA6300",
    },
  },
  {
    name: vehicleVins[18],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA4988",
    },
  },
  {
    name: vehicleVins[19],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA6724",
    },
  },
  {
    name: vehicleVins[20],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA2041",
    },
  },
  {
    name: vehicleVins[21],
    status: "INACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA2811",
    },
  },
  {
    name: vehicleVins[22],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA7399",
    },
  },
  {
    name: vehicleVins[23],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA3213",
    },
  },
  {
    name: vehicleVins[24],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA1308",
    },
  },
  {
    name: vehicleVins[25],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA3512",
    },
  },
  {
    name: vehicleVins[26],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA9070",
    },
  },
  {
    name: vehicleVins[27],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA1699",
    },
  },
  {
    name: vehicleVins[28],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA6470",
    },
  },
  {
    name: vehicleVins[29],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA5906",
    },
  },
  {
    name: vehicleVins[30],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA8339",
    },
  },
  {
    name: vehicleVins[31],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA8158",
    },
  },
  {
    name: vehicleVins[32],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA4312",
    },
  },
  {
    name: vehicleVins[33],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA1368",
    },
  },
  {
    name: vehicleVins[34],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA6707",
    },
  },
  {
    name: vehicleVins[35],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA6162",
    },
  },
  {
    name: vehicleVins[36],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA9011",
    },
  },
  {
    name: vehicleVins[37],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA2400",
    },
  },
  {
    name: vehicleVins[38],
    status: "INACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA4967",
    },
  },
  {
    name: vehicleVins[39],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA5825",
    },
  },
  {
    name: vehicleVins[40],
    status: "INACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA6689",
    },
  },
  {
    name: vehicleVins[41],
    status: "INACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA9746",
    },
  },
  {
    name: vehicleVins[42],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA1156",
    },
  },
  {
    name: vehicleVins[43],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA7540",
    },
  },
  {
    name: vehicleVins[44],
    status: "INACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA5690",
    },
  },
  {
    name: vehicleVins[45],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA1260",
    },
  },
  {
    name: vehicleVins[46],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA4332",
    },
  },
  {
    name: vehicleVins[47],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA5674",
    },
  },
  {
    name: vehicleVins[48],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA7193",
    },
  },
  {
    name: vehicleVins[49],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA1106",
    },
  },
  {
    name: vehicleVins[50],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA4974",
    },
  },
  {
    name: vehicleVins[51],
    status: "INACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA9268",
    },
  },
  {
    name: vehicleVins[52],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA6871",
    },
  },
  {
    name: vehicleVins[53],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA9904",
    },
  },
  {
    name: vehicleVins[54],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA9042",
    },
  },
  {
    name: vehicleVins[55],
    status: "INACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA1178",
    },
  },
  {
    name: vehicleVins[56],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA6028",
    },
  },
  {
    name: vehicleVins[57],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA3691",
    },
  },
  {
    name: vehicleVins[58],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA4513",
    },
  },
  {
    name: vehicleVins[59],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA9635",
    },
  },
  {
    name: vehicleVins[60],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA2702",
    },
  },
  {
    name: vehicleVins[61],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA1525",
    },
  },
  {
    name: vehicleVins[62],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA5849",
    },
  },
  {
    name: vehicleVins[63],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA3368",
    },
  },
  {
    name: vehicleVins[64],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA9753",
    },
  },
  {
    name: vehicleVins[65],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA3442",
    },
  },
  {
    name: vehicleVins[66],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA7424",
    },
  },
  {
    name: vehicleVins[67],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA3425",
    },
  },
  {
    name: vehicleVins[68],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA5247",
    },
  },
  {
    name: vehicleVins[69],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA8042",
    },
  },
  {
    name: vehicleVins[70],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA5111",
    },
  },
  {
    name: vehicleVins[71],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA1248",
    },
  },
  {
    name: vehicleVins[72],
    status: "INACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA1541",
    },
  },
  {
    name: vehicleVins[73],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA2612",
    },
  },
  {
    name: vehicleVins[74],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA6956",
    },
  },
  {
    name: vehicleVins[75],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA9228",
    },
  },
  {
    name: vehicleVins[76],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA8688",
    },
  },
  {
    name: vehicleVins[77],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA3827",
    },
  },
  {
    name: vehicleVins[78],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA3521",
    },
  },
  {
    name: vehicleVins[79],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA7565",
    },
  },
  {
    name: vehicleVins[80],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA1803",
    },
  },
  {
    name: vehicleVins[81],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA6473",
    },
  },
  {
    name: vehicleVins[82],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA2792",
    },
  },
  {
    name: vehicleVins[83],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA2162",
    },
  },
  {
    name: vehicleVins[84],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA2849",
    },
  },
  {
    name: vehicleVins[85],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA6789",
    },
  },
  {
    name: vehicleVins[86],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA3180",
    },
  },
  {
    name: vehicleVins[87],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA2597",
    },
  },
  {
    name: vehicleVins[88],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA2037",
    },
  },
  {
    name: vehicleVins[89],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA6543",
    },
  },
  {
    name: vehicleVins[90],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA5165",
    },
  },
  {
    name: vehicleVins[91],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA7406",
    },
  },
  {
    name: vehicleVins[92],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA9614",
    },
  },
  {
    name: vehicleVins[93],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA8634",
    },
  },
  {
    name: vehicleVins[94],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA3357",
    },
  },
  {
    name: vehicleVins[95],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA1762",
    },
  },
  {
    name: vehicleVins[96],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA5109",
    },
  },
  {
    name: vehicleVins[97],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA7840",
    },
  },
  {
    name: vehicleVins[98],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA4446",
    },
  },
  {
    name: vehicleVins[99],
    status: "ACTIVE",
    attributes: {
      make: "Acura",
      model: "ZDX",
      year: 2025,
      licensePlate: "HONDA8679",
    },
  },
];

export const FLEET_CAMPAIGNS: CampaignItem[] = [
  {
    targetId: FLEETS.TEST_FLEET_1,
    name: "Geo-Tracker--Test-Fleet-1",
    status: CampaignStatus.RUNNING,
  },
  {
    targetId: FLEETS.TEST_FLEET_1,
    name: "ADAS-Collection--Test-Fleet-1",
    status: CampaignStatus.SUSPENDED,
  },
  {
    targetId: FLEETS.TEST_FLEET_2,
    name: "Geo-Tracker--Test-Fleet-2",
    status: CampaignStatus.RUNNING,
  },
  {
    targetId: FLEETS.TEST_FLEET_2,
    name: "ADAS-Collection--Test-Fleet-2",
    status: CampaignStatus.SUSPENDED,
  },
  {
    targetId: FLEETS.TEST_FLEET_3,
    name: "Geo-Tracker--Test-Fleet-3",
    status: CampaignStatus.RUNNING,
  },
  {
    targetId: FLEETS.TEST_FLEET_4,
    name: "Geo-Tracker--Test-Fleet-4",
    status: CampaignStatus.RUNNING,
  },
  {
    targetId: FLEETS.TEST_FLEET_5,
    name: "Geo-Tracker--Test-Fleet-5",
    status: CampaignStatus.RUNNING,
  },
];

export const ALL_FLEETS = [
  {
    id: FLEETS.TEST_FLEET_1,
    name: "Fleet 1",
  },
  {
    id: FLEETS.TEST_FLEET_2,
    name: "Fleet 2",
  },
  {
    id: FLEETS.TEST_FLEET_3,
    name: "Fleet 3",
  },
  {
    id: FLEETS.TEST_FLEET_4,
    name: "Fleet 4",
  },
  {
    id: FLEETS.TEST_FLEET_5,
    name: "Fleet 5",
  },
] as FleetSummary[];

export function getDemoContextForFleet(
  fleet: FleetSummary,
  isDemoMode: boolean,
) {
  if (!isDemoMode) {
    //if real fleet is created matching the id of a demo fleet, use it.
    if (ALL_FLEETS.map((x) => x.id).includes(fleet.id)) {
      return fleet;
    }
    return ALL_FLEETS[0];
  }

  return fleet;
}

export function getFleets(
  fleets: FleetSummary[],
  vehicles: VehicleItem[],
  fleetVehicles: Record<string, string[]>,
  fleetCampaigns: CampaignItem[],
) {
  return fleets.map((fleetSummary) => ({
    id: fleetSummary.id,
    name: fleetSummary.name,
    numTotalVehicles: getVehiclesForFleet(
      fleetSummary.id,
      vehicles,
      fleetVehicles,
    ).length,
    numConnectedVehicles: getVehiclesForFleet(
      fleetSummary.id,
      vehicles,
      fleetVehicles,
    ).filter((x) => x?.status == "ACTIVE").length,
    numActiveCampaigns: fleetCampaigns.filter(
      (campaign) =>
        campaign.targetId === fleetSummary.id &&
        campaign.status === CampaignStatus.RUNNING,
    ).length,
    numTotalCampaigns: fleetCampaigns.filter(
      (campaign) => campaign.targetId === fleetSummary.id,
    ).length,
    createdTime: "2022-10-10T12:37:57.209Z",
    lastModifiedTime: "2022-10-10T12:37:57.209Z",
  }));
}

export function getVehiclesForFleet(
  fleetId: string,
  vehicles: VehicleItem[],
  fleetVehicles: Record<string, string[]>,
) {
  if (!fleetId) {
    return [];
  }
  const vehicleMap = new Map<string, VehicleItem>(
    vehicles.map((vehicle) => [vehicle.name, vehicle] as [string, VehicleItem]),
  );

  return fleetVehicles[fleetId].map((x) => {
    return vehicleMap.get(x);
  });
}

export const SIGNAL_CATALOGS: SignalCatalogItem[] = [
  {
    arn: "arn:aws:iotfleetwise:us-east-1:123456789012:signal-catalog/test_signal_catalog",
    name: "test_signal_catalog",
  },
];

export const DECODER_MANIFESTS: DecoderManifestItem[] = [
  {
    name: "test_decoder_manifest",
    arn: "arn:aws:iotfleetwise:us-east-1:123456789012:decoder-manifest/test_decoder_manifest",
    modelManifestArn:
      "arn:aws:iotfleetwise:us-east-1:123456789012:model-manifest/test_model_manifest",
  },
];
