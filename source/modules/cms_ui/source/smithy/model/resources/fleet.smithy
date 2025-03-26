$version: "2.0"
namespace com.cms.fleetmanagement

resource Fleet {
    identifiers: {
        id: ResourceName
    }
    operations: [
      ListVehiclesInFleet
      AssociateVehiclesToFleet
    ]
    read: GetFleet
    list: ListFleets
    create: CreateFleet
    delete: DeleteFleet
    update: EditFleet
}

structure FleetItem for Fleet {
    @required
    $id

    @required
    name: ResourceName

    @required
    numTotalVehicles: Integer

    @required
    numConnectedVehicles: Integer

    @required
    numActiveCampaigns: Integer

    @required
    numTotalCampaigns: Integer

    @required
    createdTime: String

    @required
    lastModifiedTime: String

    description: String

    tags: Tags
}

list FleetItems {
    member: FleetItem
}

@httpError(404)
@error("client")
structure FleetNotFound {
    message: String
    fleetId: ResourceName
}

@httpError(409)
@error("client")
structure FleetBeingModified {
    message: String
    fleetId: ResourceName
}

@http(code: 200, method: "GET", uri: "/fleet")
@readonly
operation ListFleets {
    output := {
        fleets: FleetItems
    }
}

@http(code: 200, method: "GET", uri: "/fleet/{id}")
@readonly
operation GetFleet {
    input := for Fleet {
        @httpLabel
        @required
        $id
    }

    output : FleetItem

    errors: [
        FleetNotFound
    ]
}

structure CreateFleetEntry for Fleet {
    @required
    $id

    @required
    name: ResourceName

    description: String

    @required
    signalCatalogArn: ARN

    tags: Tags
}

@http(code: 200, method: "POST", uri: "/fleet")
operation CreateFleet {
    input := for Fleet {
        @httpPayload
        @required
        entry: CreateFleetEntry
    }
}

structure EditFleetEntry for Fleet {
    @required
    $id

    @required
    name: ResourceName

    description: String

    tags: Tags
}

@http(code: 200, method: "PATCH", uri: "/fleet/{id}")
operation EditFleet {
    input := for Fleet {
        @httpLabel
        @required
        $id

        @httpPayload
        @required
        entry: EditFleetEntry
    }

    errors: [
        FleetNotFound
        FleetBeingModified
    ]
}

@http(code: 200, method: "DELETE", uri: "/fleet/{id}")
@idempotent
operation DeleteFleet {
    input := for Fleet {
        @httpLabel
        @required
        $id
    }

    errors: [
        FleetNotFound
    ]
}

list VehicleNames {
    member: ResourceName
}

@http(code: 200, method: "GET", uri: "/fleet/{id}/vehicles")
@readonly
operation ListVehiclesInFleet {
    input := for Fleet {
        @httpLabel
        @required
        $id
    }

    output := {
        vehicles: VehicleItems
    }

    errors: [
        FleetNotFound
    ]
}

@http(code: 200, method: "POST", uri: "/fleet/{id}/associate-vehicles")
@idempotent
operation AssociateVehiclesToFleet {
    input := for Fleet {
        @httpLabel
        @required
        $id

        vehicleNames: VehicleNames
    }

    errors: [
        FleetNotFound
    ]
}
