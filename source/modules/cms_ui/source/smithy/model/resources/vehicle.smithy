$version: "2.0"
namespace com.cms.fleetmanagement

resource Vehicle {
    identifiers: {
        name: ResourceName
    }
    operations: [
        ListFleetsForVehicle
        DisassociateVehicle
    ]
    create: CreateVehicle
    read: GetVehicle
    list: ListVehicles
    delete: DeleteVehicle
    update: EditVehicle
}

enum VehicleStatus {
    ACTIVE
    INACTIVE
}

structure VehicleAttributes {
    @required
    vin: String

    @required
    make: NonEmptyString

    @required
    model: NonEmptyString

    @required
    year: Integer

    @required
    licensePlate: NonEmptyString
}

structure VehicleItem for Vehicle {
    @required
    $name

    @required
    status: VehicleStatus

    @required
    attributes: VehicleAttributes

    tags: Tags
}

list VehicleItems {
    member: VehicleItem
}

structure CreateVehicleEntry for Vehicle {
    @required
    $name

    @required
    decoderManifestName: ResourceName

    @required
    vin: NonEmptyString

    @required
    make: NonEmptyString

    @required
    model: NonEmptyString

    @required
    @range(min: 1)
    year: Integer

    @required
    licensePlate: NonEmptyString

    tags: Tags
}

structure EditVehicleEntry for Vehicle {
    @required
    $name

    @required
    vin: NonEmptyString

    @required
    make: NonEmptyString

    @required
    model: NonEmptyString

    @required
    @range(min: 1)
    year: Integer

    @required
    licensePlate: NonEmptyString

    tags: Tags
}

@http(code: 200, method: "POST", uri: "/vehicle")
operation CreateVehicle {
    input := for Vehicle {
        @httpPayload
        @required
        entry: CreateVehicleEntry
    }
}

@http(code: 200, method: "PATCH", uri: "/vehicle/{name}")
operation EditVehicle {
    input := for Vehicle {
        @httpLabel
        @required
        $name

        @httpPayload
        @required
        entry: EditVehicleEntry
    }

    errors: [
        VehicleNotFound
        VehicleBeingModified
    ]
}


@http(code: 200, method: "GET", uri: "/vehicle")
@readonly
operation ListVehicles {
    output := {
        vehicles: VehicleItems
    }
}

@http(code: 200, method: "GET", uri: "/vehicle/{name}")
@readonly
operation GetVehicle {
    input := for Vehicle {
        @httpLabel
        @required
        $name
    }

    output : VehicleItem

    errors: [
        VehicleNotFound
    ]
}

@http(code: 200, method: "DELETE", uri: "/vehicle/{name}")
@idempotent
operation DeleteVehicle {
    input := for Vehicle {
        @httpLabel
        @required
        $name
    }

    errors: [
        VehicleNotFound
    ]
}

@http(code: 200, method: "POST", uri: "/vehicle/{name}/disassociate-fleet/{fleetId}")
@idempotent
operation DisassociateVehicle {
    input := for Vehicle {
        @httpLabel
        @required
        $name

        @httpLabel
        @required
        fleetId: ResourceName
    }

    errors: [
        VehicleNotFound
    ]
}

structure FleetSummary {
  @required
  id: ResourceName

  @required
  name: ResourceName
}

list FleetSummaries {
    member: FleetSummary
}

@http(code: 200, method: "GET", uri: "/vehicle/{name}/fleets")
@readonly
operation ListFleetsForVehicle {
    input := for Vehicle {
        @httpLabel
        @required
        $name
    }

    output := {
        fleets: FleetSummaries
    }

    errors: [
        VehicleNotFound
    ]
}

@httpError(404)
@error("client")
structure VehicleNotFound {
    message: String
    vehicleName: ResourceName
}

@httpError(409)
@error("client")
structure VehicleBeingModified {
    message: String
    vehicleName: ResourceName
}
