$version: "2.0"
namespace com.cms.fleetmanagement

resource Campaign {
    operations: [
      ListCampaigns
      ListCampaignsForTarget
      StartCampaign
      StopCampaign
      GetCampaign
    ]
    delete: DeleteCampaign
}

enum CampaignStatus {
    CREATING
    WAITING_FOR_APPROVAL
    RUNNING
    SUSPENDED
}

structure CampaignItem for Campaign {
    @required
    name: ResourceName

    @required
    targetId: ResourceName

    @required
    status: CampaignStatus
}

list CampaignItems {
    member: CampaignItem
}

enum CampaignTargetType {
    FLEET
    VEHICLE
}

@http(code: 200, method: "DELETE", uri: "/campaign/{name}")
@idempotent
operation DeleteCampaign {
    input := for Campaign {
        @httpLabel
        @required
        name: ResourceName
    }

    errors: [
        CampaignNotFound
    ]
}

@http(code: 200, method: "POST", uri: "/campaign/{name}/start")
@idempotent
operation StartCampaign {
    input := for Campaign {
        @httpLabel
        @required
        name: ResourceName
    }

    errors: [
        CampaignNotFound
        CampaignBeingModified
    ]
}

@http(code: 200, method: "POST", uri: "/campaign/{name}/stop")
@idempotent
operation StopCampaign {
    input := for Campaign {
        @httpLabel
        @required
        name: ResourceName
    }

    errors: [
        CampaignNotFound
        CampaignBeingModified
    ]
}

@http(code: 200, method: "GET", uri: "/campaign/list/{targetType}/{targetId}")
@readonly
operation ListCampaignsForTarget {
    input := {
        @httpLabel
        @required
        targetId: ResourceName

        @httpLabel
        @required
        targetType: CampaignTargetType
    }

    output := {
        campaigns: CampaignItems
    }
}

@http(code: 200, method: "GET", uri: "/campaign")
@readonly
operation ListCampaigns {
    output := {
        campaigns: CampaignItems
    }
}

@http(code: 200, method: "GET", uri: "/campaign/{name}")
@readonly
operation GetCampaign {
    input := for Campaign {
        @httpLabel
        @required
        name: ResourceName
    }

    output : CampaignItem

    errors: [
        CampaignNotFound
    ]
}

@httpError(404)
@error("client")
structure CampaignNotFound {
    message: String
    campaignName: ResourceName
}

@httpError(409)
@error("client")
structure CampaignBeingModified {
    message: String
    campaignName: ResourceName
}
