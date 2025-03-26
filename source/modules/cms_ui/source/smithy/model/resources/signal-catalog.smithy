$version: "2.0"
namespace com.cms.fleetmanagement

resource SignalCatalog {
    identifiers: {
        name: ResourceName
    }
    list: ListSignalCatalogs
}

structure SignalCatalogItem for SignalCatalog {
    @required
    arn: ARN

    @required
    name: ResourceName
}

list SignalCatalogItems {
    member: SignalCatalogItem
}

@http(code: 200, method: "GET", uri: "/signal-catalog")
@readonly
operation ListSignalCatalogs {
    output := {
      signalCatalogs: SignalCatalogItems
    }
}
